import redis
import json
import time
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# Global Redis connection pool to prevent connection exhaustion
_redis_pool = None

def get_redis_pool():
    """Get or create a global Redis connection pool"""
    global _redis_pool
    if _redis_pool is None:
        try:
            _redis_pool = redis.BlockingConnectionPool(
                host=getattr(settings, 'redis_host', 'localhost'),
                port=getattr(settings, 'redis_port', 6379),
                db=getattr(settings, 'redis_db', 0),
                decode_responses=True,
                socket_timeout=30,
                socket_connect_timeout=10,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
                retry_on_timeout=True,
                max_connections=50,
                timeout=20,  # Wait up to 20 seconds for connection from pool
            )
            logger.info("✅ Redis connection pool created successfully")
        except Exception as e:
            logger.error(f"❌ Redis pool creation failed: {str(e)}")
            _redis_pool = None
    return _redis_pool


def get_redis_client():
    """Get a Redis client instance using the global connection pool"""
    try:
        pool = get_redis_pool()
        if pool is None:
            return None
            
        client = redis.Redis(connection_pool=pool)
        # Test connection
        client.ping()
        return client
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {str(e)}")
        return None


class RedisPublisher:
    """
    Redis publisher for streaming chat events to clients.
    Enhanced with better timeout handling and retry logic.
    """

    def __init__(self):
        self.redis_client = get_redis_client()
        self._connection_retries = 0
        self._max_retries = 3

        if self.redis_client:
            logger.info("✅ Redis publisher initialized successfully")
        else:
            logger.error("❌ Redis publisher initialization failed")

    def _reconnect(self) -> bool:
        """Attempt to reconnect to Redis"""
        if self._connection_retries >= self._max_retries:
            logger.error(f"❌ Max Redis reconnection attempts ({self._max_retries}) exceeded")
            return False

        self._connection_retries += 1
        logger.info(f"🔄 Attempting Redis reconnection ({self._connection_retries}/{self._max_retries})")

        self.redis_client = get_redis_client()
        if self.redis_client:
            logger.info("✅ Redis reconnection successful")
            self._connection_retries = 0  # Reset counter on successful connection
            return True
        else:
            logger.warning(f"⚠️ Redis reconnection attempt {self._connection_retries} failed")
            return False

    def publish(self, channel: str, message: str) -> bool:
        """
        Publish a message to a Redis channel with retry logic.

        Args:
            channel: Redis channel name
            message: Message to publish (JSON string)

        Returns:
            bool: True if published successfully, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis not available, cannot publish message")
            return False

        max_publish_retries = 3
        for attempt in range(max_publish_retries):
            try:
                # Add timestamp if not present
                try:
                    msg_data = json.loads(message)
                    if 'timestamp' not in msg_data:
                        msg_data['timestamp'] = time.time()
                    message = json.dumps(msg_data)
                except json.JSONDecodeError:
                    pass

                # Publish to channel
                subscribers = self.redis_client.publish(channel, message)
                logger.debug(f"📡 Published to channel '{channel}': {subscribers} subscribers")

                # Store message in channel history (optional, for replay capability)
                self._store_message_history(channel, message)

                return True

            except redis.TimeoutError:
                logger.warning(f"⏰ Redis timeout on publish attempt {attempt + 1}/{max_publish_retries}")
                if attempt < max_publish_retries - 1:
                    # Try to reconnect and retry
                    if not self._reconnect():
                        continue
                else:
                    logger.error(f"❌ Redis publish failed after {max_publish_retries} attempts due to timeouts")
                    return False

            except redis.ConnectionError:
                logger.warning(f"🔗 Redis connection error on attempt {attempt + 1}/{max_publish_retries}")
                if attempt < max_publish_retries - 1:
                    if not self._reconnect():
                        continue
                else:
                    logger.error(
                        f"❌ Redis publish failed after {max_publish_retries} attempts due to connection errors")
                    return False

            except Exception as e:
                logger.error(f"❌ Unexpected error publishing to channel '{channel}': {str(e)}")
                return False

        return False

    def _store_message_history(self, channel: str, message: str, max_history: int = 100):
        """Store message in channel history for replay capability"""
        try:
            history_key = f"stream_history:{channel}"

            # Add message to list
            self.redis_client.lpush(history_key, message)

            # Trim to max history size
            self.redis_client.ltrim(history_key, 0, max_history - 1)

            # Set expiration (24 hours)
            self.redis_client.expire(history_key, 86400)

        except redis.TimeoutError:
            logger.warning(f"⏰ Timeout storing message history for channel: {channel}")
        except Exception as e:
            logger.warning(f"Failed to store message history: {str(e)}")


class RedisSubscriber:
    """
    Redis subscriber for receiving streaming events.
    Enhanced with better timeout handling and connection management.
    """

    def __init__(self):
        self.redis_client = get_redis_client()
        self.pubsub = None
        self._connection_retries = 0
        self._max_retries = 3

        if self.redis_client:
            try:
                self.pubsub = self.redis_client.pubsub()
                logger.info("✅ Redis subscriber initialized successfully")
            except Exception as e:
                logger.error(f"❌ Redis pubsub initialization failed: {str(e)}")
                self.pubsub = None
        else:
            self.pubsub = None

    def _reconnect(self) -> bool:
        """Attempt to reconnect to Redis"""
        if self._connection_retries >= self._max_retries:
            logger.error(f"❌ Max Redis subscriber reconnection attempts ({self._max_retries}) exceeded")
            return False

        self._connection_retries += 1
        logger.info(f"🔄 Attempting Redis subscriber reconnection ({self._connection_retries}/{self._max_retries})")

        self.redis_client = get_redis_client()
        if self.redis_client:
            try:
                self.pubsub = self.redis_client.pubsub()
                logger.info("✅ Redis subscriber reconnection successful")
                self._connection_retries = 0  # Reset counter on successful connection
                return True
            except Exception as e:
                logger.error(f"❌ Failed to create pubsub after reconnection: {str(e)}")
                return False
        else:
            logger.warning(f"⚠️ Redis subscriber reconnection attempt {self._connection_retries} failed")
            return False

    def subscribe(self, channel: str) -> bool:
        """Subscribe to a Redis channel"""
        if not self.pubsub:
            return False

        try:
            self.pubsub.subscribe(channel)
            logger.info(f"📡 Subscribed to channel: {channel}")
            return True
        except redis.TimeoutError:
            logger.warning(f"⏰ Timeout subscribing to channel: {channel}")
            return False
        except Exception as e:
            logger.error(f"Failed to subscribe to channel '{channel}': {str(e)}")
            return False

    def get_message(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Get a single message from subscribed channels with timeout.

        Args:
            timeout: Timeout in seconds for waiting for a message

        Returns:
            Dict containing message data, or None if no message/timeout
        """
        if not self.pubsub:
            logger.error("❌ No pubsub connection available")
            return None

        try:
            # Use get_message with timeout
            message = self.pubsub.get_message(timeout=timeout)

            if message is None:
                return None

            # Process different message types
            if message.get('type') == 'message':
                try:
                    # FIXED: Always try to parse JSON first, fallback to raw data
                    raw_data = message['data']

                    if isinstance(raw_data, str) or isinstance(raw_data, bytes):
                        try:
                            # Parse JSON and return as data
                            parsed_data = json.loads(raw_data)
                            return {
                                'type': 'message',
                                'channel': message['channel'],
                                'data': parsed_data  # Return parsed dict
                            }
                        except json.JSONDecodeError:
                            # If JSON parsing fails, return raw string
                            logger.warning(f"Could not parse JSON from message: {raw_data}")
                            return {
                                'type': 'message',
                                'channel': message['channel'],
                                'data': str(raw_data)
                            }
                    else:
                        # Return raw data if not string/bytes
                        return {
                            'type': 'message',
                            'channel': message['channel'],
                            'data': raw_data
                        }

                except Exception as e:
                    logger.warning(f"Error processing message data: {str(e)}")
                    return {
                        'type': 'message',
                        'channel': message['channel'],
                        'data': str(message.get('data', ''))
                    }

            elif message.get('type') == 'subscribe':
                logger.debug(f"Subscribed to channel: {message['channel']}")
                return {
                    'type': 'subscribe',
                    'channel': message['channel']
                }

            elif message.get('type') == 'unsubscribe':
                logger.debug(f"Unsubscribed from channel: {message['channel']}")
                return {
                    'type': 'unsubscribe',
                    'channel': message['channel']
                }

            else:
                # Other message types
                return {
                    'type': message.get('type'),
                    'channel': message.get('channel'),
                    'data': message.get('data')
                }

        except redis.TimeoutError:
            # Timeout is expected behavior, not an error
            return None

        except redis.ConnectionError:
            logger.warning("🔗 Redis connection error while getting message")
            # Try to reconnect
            if self._reconnect():
                return self.get_message(timeout)
            return None

        except Exception as e:
            logger.error(f"❌ Unexpected error getting message: {str(e)}")
            return None

    def listen(self):
        """Listen for messages on subscribed channels with enhanced error handling"""
        if not self.pubsub:
            logger.error("❌ No pubsub connection available")
            return

        retry_count = 0
        max_retries = 3

        while retry_count <= max_retries:
            try:
                for message in self.pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            yield data
                            retry_count = 0  # Reset retry count on successful message
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in message: {message['data']}")
                            continue
                    elif message['type'] == 'subscribe':
                        logger.debug(f"Subscribed to channel: {message['channel']}")

            except redis.TimeoutError:
                retry_count += 1
                logger.warning(f"⏰ Redis timeout listening to messages (attempt {retry_count}/{max_retries + 1})")

                if retry_count <= max_retries:
                    logger.info("🔄 Attempting to reconnect and continue listening...")
                    if self._reconnect():
                        continue
                    else:
                        time.sleep(1)  # Brief pause before retry
                        continue
                else:
                    logger.error("❌ Max retries exceeded for Redis listening")
                    break

            except redis.ConnectionError:
                retry_count += 1
                logger.warning(
                    f"🔗 Redis connection error listening to messages (attempt {retry_count}/{max_retries + 1})")

                if retry_count <= max_retries:
                    if self._reconnect():
                        continue
                    else:
                        time.sleep(1)
                        continue
                else:
                    logger.error("❌ Max retries exceeded for Redis connection")
                    break

            except Exception as e:
                logger.error(f"❌ Unexpected error listening to Redis messages: {str(e)}")
                break

    def unsubscribe(self, channel: str = None):
        """Unsubscribe from channel(s)"""
        if not self.pubsub:
            return

        try:
            if channel:
                self.pubsub.unsubscribe(channel)
                logger.info(f"Unsubscribed from channel: {channel}")
            else:
                self.pubsub.unsubscribe()
                logger.info("Unsubscribed from all channels")
        except redis.TimeoutError:
            logger.warning(f"⏰ Timeout unsubscribing from channel: {channel}")
        except Exception as e:
            logger.error(f"Error unsubscribing: {str(e)}")

    def close(self):
        """Close the pubsub connection"""
        if self.pubsub:
            try:
                self.pubsub.close()
                logger.info("Redis subscriber connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis subscriber: {str(e)}")


# Enhanced wait function for chat_assistant_tasks.py
def wait_for_frontend_ready(redis, stream_channel, timeout=45):
    """Wait for frontend ready signal with better error handling"""
    import time
    from app.core.logger import get_logger
    logger = get_logger(__name__)

    start = time.time()
    ready_key = f"ready:{stream_channel}"

    while time.time() - start < timeout:
        try:
            value = redis.get(ready_key)
            logger.info(f"[READY HANDSHAKE] Checking ready key: {ready_key} value={value}")

            if value == "1" or value == b"1":  # Handle both string and bytes
                logger.info(f"✅ Frontend ready signal received for {stream_channel}")
                return True

        except redis.TimeoutError:
            logger.warning(f"⏰ Redis timeout while checking ready key: {ready_key}")
            # Continue trying until overall timeout
        except redis.ConnectionError:
            logger.warning(f"🔗 Redis connection error while checking ready key: {ready_key}")
            # Brief pause before retry
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"❌ Error checking ready key: {str(e)}")

        time.sleep(0.2)  # Slightly longer sleep to reduce Redis load

    logger.error(f"❌ Frontend ready timeout after {timeout}s for {stream_channel}")
    return False
