"""
Context retriever for location-aware chat assistant.

This module provides context retrieval based on user's current location in the application.
The chat assistant adapts its context based on where the user is:
- Personal dashboard: Context of user's last 5 learning paths
- Team dashboard: Context of team's last 5 learning paths (excluding personal ones)
- Learning path view: Context of specific learning path metadata and modules
- Module view: Context of specific module metadata and parent learning path
- Quiz attempt: Restricted responses with completion reminder
- Review answers: Context of quiz attempt with review answers
"""

import time
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.services.core_services import learning_path_service, module_service
from app.services.core_services.quiz_service import get_user_quiz_attempts_by_quiz
from app.services.caching_services.context_cache_service import ContextCacheService
from app.models.quiz import QuizStatus
from app.schemas.chat_assistant_schemas.chat_assistant_schema import UserContextLocation, UserLocation

logger = get_logger(__name__)


class ContextRetriever:
    """
    Location-aware context retriever for the chat assistant.

    Provides contextual information based on user's current location in the application,
    ensuring appropriate restrictions during quiz attempts.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_service = ContextCacheService()

    async def check_active_quiz_attempt(self, user_id: str, quiz_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Check if user has an active quiz attempt.

        Args:
            user_id: ID of the user
            quiz_id: Optional specific quiz ID to check

        Returns:
            Dict with quiz attempt details if active, None otherwise
        """
        try:
            if quiz_id:
                logger.debug(f"Checking active quiz attempt for user {user_id} on quiz {quiz_id}")
                attempts = await get_user_quiz_attempts_by_quiz(self.db, quiz_id, user_id)
                active_attempts = [a for a in attempts if getattr(a, 'status', None) == QuizStatus.ACTIVE]

                if active_attempts:
                    attempt = active_attempts[0]
                    logger.info(f"Found active quiz attempt for user {user_id}")
                    return {
                        "quiz_id": quiz_id,
                        "attempt_id": getattr(attempt, 'id', None),
                        "status": "in_progress",
                        "started_at": getattr(attempt, 'started_at', None).isoformat() if getattr(attempt, 'started_at', None) else None
                    }

            logger.debug(f"No active quiz attempt found for user {user_id}")
            return None

        except Exception as e:
            logger.error(f"Error checking active quiz attempt for user {user_id}: {str(e)}")
            return None

    async def get_scoped_learning_path_context(
            self,
            user_id: str,
            user_location: UserContextLocation,
            use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get learning path context scoped to user's current location.

        Retrieves different context based on location:
        - Dashboard: Last 5 learning paths (personal or team-scoped)
        - Learning path: Specific learning path details with modules
        - Module/Quiz: Parent learning path context

        Args:
            user_id: ID of the user
            user_location: Current user location context
            use_cache: Whether to use cached results

        Returns:
            Dict containing context data and metadata
        """
        start_time = time.time()

        # Check cache first
        if use_cache:
            cache_key_suffix = getattr(user_location, 'team_id', None) or "personal"
            cached_context = self.cache_service.get_learning_path_context(user_id, cache_key_suffix)
            if cached_context:
                # Validate cached data format to ensure it's compatible
                try:
                    learning_paths = cached_context.get("learning_paths", [])
                    # Check if cached data contains old LearningPathResponse objects
                    if learning_paths and hasattr(learning_paths[0], 'id') and not isinstance(learning_paths[0], dict):
                        logger.warning(f"Detected old cache format for user {user_id}, clearing cache")
                        self.cache_service.clear_learning_path_context(user_id, cache_key_suffix)
                        # Continue to fetch fresh data
                    else:
                        retrieval_time = int((time.time() - start_time) * 1000)
                        logger.debug(f"Retrieved learning path context from cache for user {user_id}")
                        return {"data": cached_context, "cache_hit": True, "retrieval_time_ms": retrieval_time}
                except Exception as cache_error:
                    logger.warning(f"Cache validation failed for user {user_id}, clearing cache: {str(cache_error)}")
                    self.cache_service.clear_learning_path_context(user_id, cache_key_suffix)
                    # Continue to fetch fresh data

        try:
            context_data = {}

            if getattr(user_location, 'location', None) == UserLocation.DASHBOARD:
                # Dashboard context: Last 5 learning paths
                context_data = await self._get_dashboard_context(user_id, getattr(user_location, 'team_id', None))

            elif getattr(user_location, 'learning_path_id', None):
                # Specific learning path context
                context_data = await self._get_specific_learning_path_context(
                    user_id, getattr(user_location, 'learning_path_id', None)
                )

            else:
                # Fallback to general dashboard context
                context_data = await self._get_dashboard_context(user_id, None)

            # Cache the result
            if use_cache and context_data and "error" not in context_data:
                cache_key_suffix = getattr(user_location, 'team_id', None) or "personal"
                self.cache_service.cache_learning_path_context(user_id, cache_key_suffix, context_data)

            retrieval_time = int((time.time() - start_time) * 1000)
            logger.info(
                f"Retrieved learning path context for user {user_id} in {retrieval_time}ms "
                f"(location: {getattr(user_location, 'location', None)}, team: {getattr(user_location, 'team_id', None)})"
            )

            return {"data": context_data, "cache_hit": False, "retrieval_time_ms": retrieval_time}

        except Exception as e:
            logger.error(f"Error retrieving learning path context for user {user_id}: {str(e)}")
            return {"data": {}, "cache_hit": False, "error": str(e)}

    async def _get_dashboard_context(self, user_id: str, team_id: Optional[str]) -> Dict[str, Any]:
        """
        Get dashboard context with last 5 learning paths.

        Args:
            user_id: ID of the user
            team_id: Optional team ID for team dashboard context

        Returns:
            Dict containing learning paths and metadata
        """
        try:
            if team_id:
                # Team dashboard: get team learning paths excluding personal ones
                logger.debug(f"Retrieving team dashboard context for user {user_id}, team {team_id}")
                all_paths = await learning_path_service.get_team_learning_paths(
                    self.db, team_id
                )
                # Filter for team paths only - use safe attribute access
                team_paths = [path for path in all_paths if getattr(path, 'team_id', None) == team_id]
                learning_paths = team_paths[:5]

            else:
                # Personal dashboard: get user's own learning paths
                logger.debug(f"Retrieving personal dashboard context for user {user_id}")
                all_paths = await learning_path_service.get_user_learning_paths(
                    self.db, user_id
                )
                # Filter for personal paths only (no team_id) - use safe attribute access
                personal_paths = [path for path in all_paths if not getattr(path, 'team_id', None)]
                learning_paths = personal_paths[:5]

            # Convert LearningPathResponse objects to dictionaries for proper serialization
            learning_paths_data = []
            for path in learning_paths:
                path_data = {
                    "id": getattr(path, 'id', None),
                    "title": getattr(path, 'title', 'Untitled'),
                    "description": getattr(path, 'description', ''),
                    "subject": getattr(path, 'subject', ''),
                    "estimated_days": getattr(path, 'estimated_days', None),
                    "total_modules": getattr(path, 'total_modules', 0),
                    "team_id": getattr(path, 'team_id', None),
                    "user_id": getattr(path, 'user_id', None),
                    "status": getattr(path, 'status', 'active'),
                    "created_at": getattr(path, 'created_at', None).isoformat() if getattr(path, 'created_at', None) else None,
                    "updated_at": getattr(path, 'updated_at', None).isoformat() if getattr(path, 'updated_at', None) else None,
                    "is_public": getattr(path, 'is_public', False),
                    "learning_objectives": getattr(path, 'learning_objectives', []),
                    "difficulty_progression": getattr(path, 'difficulty_progression', []),
                    "estimated_hours": getattr(path, 'estimated_hours', None),
                    "study_time_minutes": getattr(path, 'study_time_minutes', None),
                    "goals": getattr(path, 'goals', ''),
                    "preferred_platforms": getattr(path, 'preferred_platforms', []),
                    "experience_level": getattr(path, 'experience_level', None)
                }
                learning_paths_data.append(path_data)

            context_data = {
                "learning_paths": learning_paths_data,
                "context_type": "dashboard",
                "team_context": team_id is not None,
                "team_id": team_id,
                "total_paths": len(learning_paths_data)
            }

            logger.debug(
                f"Dashboard context prepared: {len(learning_paths_data)} paths "
                f"(team: {team_id is not None})"
            )
            return context_data

        except Exception as e:
            logger.error(f"Error getting dashboard context: {str(e)}")
            return {"error": str(e)}

    async def _get_specific_learning_path_context(self, user_id: str, learning_path_id: int) -> Dict[str, Any]:
        """
        Get specific learning path context with modules and metadata.

        Args:
            user_id: ID of the user
            learning_path_id: ID of the learning path

        Returns:
            Dict containing learning path details and modules
        """
        try:
            logger.debug(f"Retrieving specific learning path context: {learning_path_id} for user {user_id}")

            # Get learning path with user access validation
            learning_path = await learning_path_service.get_learning_path_by_id(
                self.db, learning_path_id, user_id
            )

            if not learning_path:
                logger.warning(f"Learning path {learning_path_id} not found or access denied for user {user_id}")
                return {"error": "Learning path not found or access denied"}

            # Get modules for this learning path
            modules = await module_service.get_modules_by_learning_path_id(self.db, learning_path_id)

            # Format modules data
            modules_data = []
            for module in modules:
                module_data = {
                    "id": getattr(module, 'id', None),
                    "title": getattr(module, 'title', 'Untitled'),
                    "description": getattr(module, 'description', ''),
                    "learning_objectives": getattr(module, 'learning_objectives', []) or [],
                    "duration": getattr(module, 'duration', None),
                    "order_index": getattr(module, 'order_index', 0),
                    "has_quiz": getattr(module, 'has_quiz', False),
                    "difficulty": getattr(module, 'difficulty', {}).value if hasattr(getattr(module, 'difficulty', {}), 'value') else getattr(module, 'difficulty', 'intermediate'),
                    "learning_style": getattr(module, 'learning_style', {}).value if hasattr(getattr(module, 'learning_style', {}), 'value') else getattr(module, 'learning_style', 'mixed')
                }
                modules_data.append(module_data)

            context_data = {
                "learning_path": {
                    "id": getattr(learning_path, 'id', None),
                    "title": getattr(learning_path, 'title', 'Untitled'),
                    "description": getattr(learning_path, 'description', ''),
                    "estimated_days": getattr(learning_path, 'estimated_days', None),
                    "total_modules": getattr(learning_path, 'total_modules', 0),
                    "team_id": getattr(learning_path, 'team_id', None),
                    "is_public": getattr(learning_path, 'is_public', False)
                },
                "modules": modules_data,
                "context_type": "learning_path",
                "total_modules": len(modules_data)
            }

            logger.debug(
                f"Learning path context prepared: {getattr(learning_path, 'title', 'Untitled')} with {len(modules_data)} modules"
            )
            return context_data

        except Exception as e:
            logger.error(f"Error getting specific learning path context: {str(e)}")
            return {"error": str(e)}

    async def get_scoped_module_context(
            self,
            user_id: str,
            user_location: UserContextLocation,
            entities: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get module-specific context.

        Args:
            user_id: ID of the user
            user_location: Current user location context
            entities: Additional context entities

        Returns:
            Dict containing module context data
        """
        start_time = time.time()

        try:
            if not getattr(user_location, 'module_id', None):
                logger.warning(f"Module context requested but no module_id provided for user {user_id}")
                return {"data": {}, "cache_hit": False, "error": "No module ID provided"}

            logger.debug(f"Retrieving module context: {getattr(user_location, 'module_id', None)} for user {user_id}")

            # Get module with user access validation
            module = await module_service.get_module_by_id(self.db, getattr(user_location, 'module_id', None))

            if not module:
                logger.warning(f"Module {getattr(user_location, 'module_id', None)} not found or access denied for user {user_id}")
                return {"data": {}, "cache_hit": False, "error": "Module not found or access denied"}

            # Get parent learning path context
            learning_path = await learning_path_service.get_learning_path_by_id(
                self.db, getattr(module, 'learning_path_id', None), user_id
            )

            context_data = {
                "module": {
                    "id": getattr(module, 'id', None),
                    "title": getattr(module, 'title', 'Untitled'),
                    "description": getattr(module, 'description', ''),
                    "learning_objectives": getattr(module, 'learning_objectives', []) or [],
                    "duration": getattr(module, 'duration', None),
                    "order_index": getattr(module, 'order_index', 0),
                    "content_url": getattr(module, 'content_url', ''),
                    "has_quiz": getattr(module, 'has_quiz', False),
                    "difficulty": getattr(module, 'difficulty', {}).value if hasattr(getattr(module, 'difficulty', {}), 'value') else getattr(module, 'difficulty', 'intermediate'),
                    "learning_style": getattr(module, 'learning_style', {}).value if hasattr(getattr(module, 'learning_style', {}), 'value') else getattr(module, 'learning_style', 'mixed')
                },
                "learning_path": {
                    "id": getattr(learning_path, 'id', None),
                    "title": getattr(learning_path, 'title', 'Untitled'),
                    "description": getattr(learning_path, 'description', '')
                } if learning_path else None,
                "context_type": "module"
            }

            retrieval_time = int((time.time() - start_time) * 1000)
            logger.info(f"Retrieved module context for user {user_id} in {retrieval_time}ms")

            return {"data": context_data, "cache_hit": False, "retrieval_time_ms": retrieval_time}

        except Exception as e:
            logger.error(f"Error retrieving module context for user {user_id}: {str(e)}")
            return {"data": {}, "cache_hit": False, "error": str(e)}

    async def get_scoped_quiz_context(
            self,
            user_id: str,
            user_location: UserContextLocation
    ) -> Dict[str, Any]:
        """
        Get quiz-specific context (restricted during active attempts).

        Args:
            user_id: ID of the user
            user_location: Current user location context

        Returns:
            Dict containing quiz context or restriction message
        """
        start_time = time.time()

        try:
            # Check for active quiz attempt
            active_attempt = await self.check_active_quiz_attempt(user_id, getattr(user_location, 'quiz_id', None))

            if active_attempt:
                logger.info(f"Quiz context restricted for user {user_id} due to active attempt")
                return {
                    "data": {
                        "restricted": True,
                        "restriction_reason": "active_quiz_attempt",
                        "message": "Sorry, please finish your quiz first before asking questions.",
                        "active_attempt": active_attempt
                    },
                    "cache_hit": False,
                    "retrieval_time_ms": int((time.time() - start_time) * 1000)
                }

            # If no active attempt, provide general quiz context
            context_data = {
                "context_type": "quiz",
                "quiz_id": getattr(user_location, 'quiz_id', None),
                "message": "Quiz context available",
                "restricted": False
            }

            retrieval_time = int((time.time() - start_time) * 1000)
            logger.debug(f"Retrieved quiz context for user {user_id} in {retrieval_time}ms")

            return {"data": context_data, "cache_hit": False, "retrieval_time_ms": retrieval_time}

        except Exception as e:
            logger.error(f"Error retrieving quiz context for user {user_id}: {str(e)}")
            return {"data": {}, "cache_hit": False, "error": str(e)}
