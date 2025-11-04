// lib/websocketManager.ts

class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string | null = null;
  private listeners: ((event: MessageEvent) => void)[] = [];
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private isReconnecting: boolean = false;

  private connect() {
    if (!this.url) return;
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);

    if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
      this.ws.onclose = null;
      this.ws.close();
    }

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log("WebSocket Manager: Connection established.");
      this.reconnectAttempts = 0;
      this.isReconnecting = false;
      this.startHeartbeat();
    };

    this.ws.onclose = (event) => {
      this.ws = null;
      this.stopHeartbeat();
      
      // Don't reconnect if it was a clean close or authentication error
      if (event.code === 1000 || event.code === 1008) {
        return;
      }
      
      this.scheduleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket Manager Error:", error);
      this.ws?.close();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle pong response
        if (data.type === 'pong') {
          return;
        }
        
        // Forward to listeners
        this.listeners.forEach(listener => listener(event));
      } catch (error) {
        console.error('WebSocket Manager: Error parsing message:', error);
        // Forward raw message anyway
        this.listeners.forEach(listener => listener(event));
      }
    };
  }

  private startHeartbeat() {
    this.stopHeartbeat(); // Clear any existing interval
    
    // Send ping every 30 seconds
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({ type: 'ping' }));
        } catch (error) {
          console.error('WebSocket Manager: Error sending ping:', error);
          this.ws.close();
        }
      }
    }, 30000);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private scheduleReconnect() {
    if (this.isReconnecting) return;
    
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("WebSocket Manager: Max reconnection attempts reached. Giving up.");
      return;
    }
    
    this.isReconnecting = true;
    this.reconnectAttempts++;
    
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, then 30s max
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`WebSocket Manager: Scheduling reconnect in ${delay}ms`);
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  public getInstance(url: string) {
    if (!this.ws || this.url !== url) {
      this.url = url;
      this.connect();
    }
    return this;
  }

  public addListener(callback: (event: MessageEvent) => void) {
    if (!this.listeners.includes(callback)) {
      this.listeners.push(callback);
    }
  }

  public removeListener(callback: (event: MessageEvent) => void) {
    this.listeners = this.listeners.filter(l => l !== callback);
  }

  public disconnect() {
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.ws) {
      this.ws.onclose = null; // Prevent reconnection
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.isReconnecting = false;
    this.reconnectAttempts = 0;
    console.log("WebSocket Manager: Disconnected by client");
  }

  public getConnectionState(): string {
    if (!this.ws) return 'DISCONNECTED';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING';
      case WebSocket.OPEN: return 'CONNECTED';
      case WebSocket.CLOSING: return 'CLOSING';
      case WebSocket.CLOSED: return 'DISCONNECTED';
      default: return 'UNKNOWN';
    }
  }
}

export const webSocketManager = new WebSocketManager();