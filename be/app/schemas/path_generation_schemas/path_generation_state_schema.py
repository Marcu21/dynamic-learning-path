"""
Path Generation State
===================================

This module defines the state that flows through the LangGraph nodes during
learning path generation. The state maintains all necessary information
across the graph execution, including metadata, module specifications,
team context, and error handling.

State Structure:
- Path metadata (title, description, estimated_days)
- Module configuration (number, difficulty mapping)
- Team context for notifications and sharing
- Error tracking and validation results
- Progress tracking through generation steps
"""

from typing import Dict, List, Optional, TypedDict, Any
from datetime import datetime

from app.models.enums import DifficultyLevel, ExperienceLevel, LearningStyle
from app.core.logger import get_logger
from dataclasses import dataclass
from enum import Enum

logger = get_logger(__name__)


class GenerationStage(str, Enum):
    """Enumeration of generation stages for tracking progress."""
    BLUEPRINT = "blueprint"
    QUERY = "query"
    CONTENT_POOL = "content_pool"
    MODULES = "modules"
    FINALIZATION = "finalization"
    COMPLETED = "completed"

class StreamEventType(str, Enum):
    """Types of streaming events emitted during path generation."""
    LEARNING_PATH_INFO = "learning_path_info"
    MODULE_INFO = "module_info"
    GENERATION_PROGRESS = "generation_progress"
    GENERATION_COMPLETE = "generation_complete"
    ERROR_EVENT = "error_event"
    STAGE_COMPLETE = "stage_complete"

@dataclass
class StreamEvent:
    """
    Represents a single streaming event during path generation.

    Attributes:
        event_type: Type of the streaming event
        data: Event payload data
        timestamp: When the event occurred
        stage: Current generation stage
        progress_percentage: Overall progress (0-100)
        metadata: Additional metadata about the event
    """
    event_type: StreamEventType
    data: Dict[str, Any]
    timestamp: datetime
    stage: GenerationStage
    progress_percentage: float
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert stream event to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "stage": self.stage.value,
            "progress_percentage": self.progress_percentage,
            "metadata": self.metadata or {}
        }


class PathGenerationState(TypedDict):
    """
    State object that flows through the LangGraph nodes during learning path generation.

    This state maintains all necessary information across the graph execution,
    including path metadata, module specifications, team context, and progress tracking.

    Key Design Principles:
    - Immutable updates: Each node returns partial state updates
    - Comprehensive logging: All state changes are tracked
    - Error resilience: Validation errors are captured and handled
    - Team awareness: Full support for team-based path generation
    """

    # =============================================================================
    # INPUT PARAMETERS (Set at initialization)
    # =============================================================================

    user_id: str
    """ID of the user requesting the learning path generation."""

    team_id: Optional[str]
    """Optional team ID if generating for a team."""

    preferences_id: Optional[int]
    """ID of the preferences to use for generation."""

    subject: str
    """Subject/topic for the learning path."""

    experience_level: ExperienceLevel
    """Experience level of the learner(s)."""

    learning_styles: List[LearningStyle]
    """Preferred learning styles."""

    preferred_platforms: List[str]
    """List of preferred learning platforms."""

    study_time_minutes: int
    """Available daily study time in minutes."""

    goals: str
    """Learning goals and objectives."""

    # =============================================================================
    # GENERATION PROGRESS TRACKING
    # =============================================================================

    current_stage: GenerationStage
    """Current stage of the generation process."""

    stages_completed: List[GenerationStage]
    """List of completed generation stages."""

    generation_started_at: datetime
    """Timestamp when generation started."""

    stage_started_at: Optional[datetime]
    """Timestamp when current stage started."""

    # =============================================================================
    # PATH BLUEPRINT (Generated in first node)
    # =============================================================================

    path_title: Optional[str]
    """Generated title for the learning path."""

    path_description: Optional[str]
    """Generated description for the learning path."""

    estimated_days: Optional[int]
    """Estimated completion time in days."""

    total_modules: Optional[int]
    """Total number of modules to generate."""

    module_difficulty_map: Optional[Dict[int, str]]
    """
    Mapping of module order_index to difficulty level.
    Example: {1: "beginner", 2: "beginner", 3: "intermediate", 4: "advanced"}
    """

    learning_objectives: Optional[List[str]]
    """High-level learning objectives for the entire path."""

    # =============================================================================
    # PLATFORM QUERIES (Generated in query generation node)
    # =============================================================================

    platform_queries: Optional[Dict[str, Dict[str, str]]]
    """
    Platform-specific queries organized by difficulty level and platform.
    Structure: {
        "beginner": {
            "youtube": "query1",
            "spotify": "query2"
        },
        "intermediate": {
            "youtube": "query3", 
            "spotify": "query4"
        }
    }
    """

    # =============================================================================
    # CONTENT POOL (Generated in content pool node)
    # =============================================================================

    content_pool: Optional[List[Dict[str, Any]]]
    """
    Content pool containing all fetched content from various platforms.
    Each item is a dictionary with platform-specific content data including:
    title, description, link, platform, duration, etc.
    """

    current_difficulty: Optional[str]
    """Current difficulty level being processed for module generation."""

    current_module_index: Optional[int]
    """Current module index being generated (1-based)."""

    used_content_links: Optional[List[str]]
    """List of content links that have already been used in generated modules."""

    # =============================================================================
    # MODULE SPECIFICATIONS (Generated in subsequent nodes)
    # =============================================================================

    modules_spec: Optional[List[Dict[str, Any]]]
    """
    Detailed specifications for each generated module.
    Each dict contains: title, description, learning_objectives, content_url, 
    order_index, difficulty, duration, platform, etc.
    """

    # =============================================================================
    # TEAM CONTEXT AND NOTIFICATIONS
    # =============================================================================

    team_members: Optional[List[Dict[str, str]]]
    """
    List of team members who will receive the learning path.
    Each dict contains: user_id, username, full_name, email
    """

    team_lead_id: Optional[str]
    """ID of the team lead (for enhanced notifications)."""

    team_name: Optional[str]
    """Name of the team (for notification context)."""

    notification_recipients: Optional[List[str]]
    """List of user IDs who should receive notifications."""

    # =============================================================================
    # AI GENERATION CONTEXT
    # =============================================================================

    llm_context: Optional[Dict[str, Any]]
    """Context and parameters for LLM calls."""

    # =============================================================================
    # ERROR HANDLING AND VALIDATION
    # =============================================================================

    errors: List[Dict[str, Any]]
    """
    List of errors encountered during generation.
    Each dict contains: stage, error_type, message, timestamp
    """

    warnings: List[Dict[str, Any]]
    """
    List of warnings encountered during generation.
    Each dict contains: stage, warning_type, message, timestamp
    """

    validation_results: Optional[Dict[str, Any]]
    """Results of various validation steps."""

    retry_count: int
    """Number of retries attempted for the current stage."""

    max_retries: int
    """Maximum number of retries allowed per stage."""

    # =============================================================================
    # FINAL RESULTS
    # =============================================================================

    learning_path_id: Optional[int]
    """ID of the created learning path (set upon successful creation)."""

    created_modules: Optional[List[int]]
    """List of module IDs that were successfully created."""

    generation_summary: Optional[Dict[str, Any]]
    """Summary of the entire generation process."""

    # =============================================================================
    # METADATA AND DEBUGGING
    # =============================================================================

    generation_config: Optional[Dict[str, Any]]
    """Configuration used for this generation session."""

    debug_info: Optional[Dict[str, Any]]
    """Debug information for troubleshooting."""

    performance_metrics: Optional[Dict[str, Any]]
    """Performance metrics for each stage."""


class StateManager:
    """
    Utility class for managing PathGenerationState updates and validations.

    This class provides helper methods for:
    - Safe state updates
    - State validation
    - Error and warning management
    - Progress tracking
    """

    def __init__(self):
        self.logger = get_logger(f"{__name__}.StateManager")

    def create_initial_state(
            self,
            user_id: str,
            subject: str,
            experience_level: ExperienceLevel,
            learning_styles: List[LearningStyle],
            preferred_platforms: List[str],
            study_time_minutes: int,
            goals: str,
            team_id: Optional[str] = None,
            max_retries: int = 3
    ) -> PathGenerationState:
        """
        Create initial state for learning path generation.

        Args:
            user_id: ID of the user requesting generation
            subject: Subject/topic for the learning path
            experience_level: Experience level of the learner(s)
            learning_styles: Preferred learning styles
            preferred_platforms: List of preferred platforms
            study_time_minutes: Available daily study time
            goals: Learning goals and objectives
            team_id: Optional team ID for team-based generation
            max_retries: Maximum retries per stage

        Returns:
            PathGenerationState: Initial state object
        """
        current_time = datetime.now()

        initial_state = PathGenerationState(
            # Input parameters
            user_id=user_id,
            team_id=team_id,
            preferences_id=None,
            subject=subject,
            experience_level=experience_level,
            learning_styles=learning_styles,
            preferred_platforms=preferred_platforms,
            study_time_minutes=study_time_minutes,
            goals=goals,

            # Progress tracking
            current_stage=GenerationStage.BLUEPRINT,
            stages_completed=[],
            generation_started_at=current_time,
            stage_started_at=current_time,

            # Blueprint results (to be populated)
            path_title=None,
            path_description=None,
            estimated_days=None,
            total_modules=None,
            module_difficulty_map=None,
            learning_objectives=None,

            # Platform queries (to be populated)
            platform_queries=None,

            # Content pool (to be populated)
            content_pool=None,
            current_difficulty=None,
            current_module_index=1,
            used_content_links=None,

            # Module specifications (to be populated)
            modules_spec=None,

            # Team context (to be populated if team_id provided)
            team_members=None,
            team_lead_id=None,
            team_name=None,
            notification_recipients=None,

            # AI context (to be populated)
            llm_context=None,

            # Error handling
            errors=[],
            warnings=[],
            validation_results=None,
            retry_count=0,
            max_retries=max_retries,

            # Final results (to be populated)
            learning_path_id=None,
            created_modules=None,
            generation_summary=None,

            # Metadata
            generation_config=None,
            debug_info=None,
            performance_metrics=None
        )

        self.logger.info(
            f"Created initial state for path generation: "
            f"user_id={user_id}, subject='{subject}', team_id={team_id}"
        )

        return initial_state

    def update_stage(
            self,
            state: PathGenerationState,
            new_stage: GenerationStage,
            stage_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update the current generation stage and track progress.

        Args:
            state: Current state
            new_stage: New stage to transition to
            stage_data: Optional data specific to the new stage

        Returns:
            Dict[str, Any]: State updates to apply
        """
        current_time = datetime.now()

        # Mark previous stage as completed
        stages_completed = state["stages_completed"].copy()
        if state["current_stage"] not in stages_completed:
            stages_completed.append(state["current_stage"])

        updates = {
            "current_stage": new_stage,
            "stages_completed": stages_completed,
            "stage_started_at": current_time,
            "retry_count": 0  # Reset retry count for new stage
        }

        # Add stage-specific data if provided
        if stage_data:
            updates.update(stage_data)

        self.logger.info(f"Transitioning from {state['current_stage']} to {new_stage}")

        return updates

    def add_error(
            self,
            state: PathGenerationState,
            error_type: str,
            message: str,
            stage: Optional[GenerationStage] = None
    ) -> Dict[str, Any]:
        """
        Add an error to the state.

        Args:
            state: Current state
            error_type: Type/category of the error
            message: Error message
            stage: Stage where error occurred (defaults to current stage)

        Returns:
            Dict[str, Any]: State updates to apply
        """
        error_entry = {
            "stage": stage or state["current_stage"],
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.now(),
            "retry_count": state["retry_count"]
        }

        errors = state["errors"].copy()
        errors.append(error_entry)

        self.logger.error(
            f"Error in stage {error_entry['stage']}: {error_type} - {message}"
        )

        return {"errors": errors}

    def add_warning(
            self,
            state: PathGenerationState,
            warning_type: str,
            message: str,
            stage: Optional[GenerationStage] = None
    ) -> Dict[str, Any]:
        """
        Add a warning to the state.

        Args:
            state: Current state
            warning_type: Type/category of the warning
            message: Warning message
            stage: Stage where warning occurred (defaults to current stage)

        Returns:
            Dict[str, Any]: State updates to apply
        """
        warning_entry = {
            "stage": stage or state["current_stage"],
            "warning_type": warning_type,
            "message": message,
            "timestamp": datetime.now()
        }

        warnings = state["warnings"].copy()
        warnings.append(warning_entry)

        self.logger.warning(
            f"Warning in stage {warning_entry['stage']}: {warning_type} - {message}"
        )

        return {"warnings": warnings}

    def increment_retry(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Increment the retry count for the current stage.

        Args:
            state: Current state

        Returns:
            Dict[str, Any]: State updates to apply
        """
        new_retry_count = state["retry_count"] + 1

        self.logger.info(
            f"Incrementing retry count for stage {state['current_stage']}: "
            f"{new_retry_count}/{state['max_retries']}"
        )

        return {"retry_count": new_retry_count}

    def should_retry(self, state: PathGenerationState) -> bool:
        """
        Check if the current stage should be retried.

        Args:
            state: Current state

        Returns:
            bool: True if retry should be attempted
        """
        return state["retry_count"] < state["max_retries"]

    def validate_state(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Validate the current state and return validation results.

        Args:
            state: Current state to validate

        Returns:
            Dict[str, Any]: Validation results
        """
        validation_results = {
            "is_valid": True,
            "validation_errors": [],
            "validation_warnings": [],
            "stage": state["current_stage"]
        }

        # Validate based on current stage
        if state["current_stage"] == GenerationStage.BLUEPRINT:
            validation_results.update(self._validate_blueprint_stage(state))
        elif state["current_stage"] == GenerationStage.QUERY:
            validation_results.update(self._validate_query_stage(state))
        elif state["current_stage"] == GenerationStage.CONTENT_POOL:
            validation_results.update(self._validate_content_pool_stage(state))
        elif state["current_stage"] == GenerationStage.MODULES:
            validation_results.update(self._validate_modules_stage(state))
        # Add more stage validations as needed

        return {"validation_results": validation_results}

    def _validate_blueprint_stage(self, state: PathGenerationState) -> Dict[str, Any]:
        """Validate the blueprint stage requirements."""
        errors = []
        warnings = []

        # Check required blueprint fields
        if not state.get("path_title"):
            errors.append("Missing path title")

        if not state.get("path_description"):
            errors.append("Missing path description")

        if not state.get("estimated_days"):
            errors.append("Missing estimated days")

        if not state.get("module_difficulty_map"):
            errors.append("Missing module difficulty mapping")

        # Validate difficulty mapping format
        if state.get("module_difficulty_map"):
            difficulty_map = state["module_difficulty_map"]
            if not isinstance(difficulty_map, dict):
                errors.append("Module difficulty map must be a dictionary")
            else:
                for order_idx, difficulty in difficulty_map.items():
                    if not isinstance(order_idx, int) or order_idx < 1:
                        errors.append(f"Invalid module order index: {order_idx}")
                    if difficulty not in [d.value for d in DifficultyLevel]:
                        errors.append(f"Invalid difficulty level: {difficulty}")

        return {
            "is_valid": len(errors) == 0,
            "validation_errors": errors,
            "validation_warnings": warnings
        }

    def _validate_query_stage(self, state: PathGenerationState) -> Dict[str, Any]:
        """Validate the query generation stage requirements."""
        errors = []
        warnings = []

        # Check that blueprint stage was completed
        if not state.get("module_difficulty_map"):
            errors.append("Module difficulty map missing from blueprint stage")

        if not state.get("preferred_platforms"):
            errors.append("Preferred platforms missing")

        # Check platform queries structure if present
        if state.get("platform_queries"):
            platform_queries = state["platform_queries"]
            if not isinstance(platform_queries, dict):
                errors.append("Platform queries must be a dictionary")
            else:
                # Validate structure
                expected_difficulties = set(state.get("module_difficulty_map", {}).values())
                expected_platforms = set(state.get("preferred_platforms", []))

                for difficulty in expected_difficulties:
                    if difficulty not in platform_queries:
                        errors.append(f"Missing queries for difficulty: {difficulty}")
                    else:
                        for platform in expected_platforms:
                            if platform not in platform_queries[difficulty]:
                                errors.append(f"Missing query for {platform} at {difficulty} level")

        return {
            "is_valid": len(errors) == 0,
            "validation_errors": errors,
            "validation_warnings": warnings
        }

    def _validate_content_pool_stage(self, state: PathGenerationState) -> Dict[str, Any]:
        """Validate the content pool stage requirements."""
        errors = []
        warnings = []

        # Check that query stage was completed
        if not state.get("platform_queries"):
            errors.append("Platform queries missing from query stage")

        if not state.get("current_difficulty"):
            errors.append("Current difficulty not set")

        # Check content pool structure if present
        if state.get("content_pool"):
            content_pool = state["content_pool"]
            if not isinstance(content_pool, list):
                errors.append("Content pool must be a list")
            elif len(content_pool) == 0:
                warnings.append("Content pool is empty")
            else:
                # Validate content structure
                for i, content_item in enumerate(content_pool):
                    if not isinstance(content_item, dict):
                        errors.append(f"Content pool item {i} must be a dictionary")
                    else:
                        required_fields = ["title", "platform", "link"]
                        for field in required_fields:
                            if field not in content_item:
                                errors.append(f"Content pool item {i} missing required field: {field}")

        return {
            "is_valid": len(errors) == 0,
            "validation_errors": errors,
            "validation_warnings": warnings
        }

    def _validate_modules_stage(self, state: PathGenerationState) -> Dict[str, Any]:
        """Validate the module generation stage requirements."""
        errors = []
        warnings = []

        # Check that content pool stage was completed
        if not state.get("content_pool"):
            errors.append("Content pool missing from content pool stage")

        if not state.get("current_difficulty"):
            errors.append("Current difficulty not set")

        if not state.get("current_module_index"):
            errors.append("Current module index not set")

        # Check module specifications structure if present
        if state.get("modules_spec"):
            modules_spec = state["modules_spec"]
            if not isinstance(modules_spec, list):
                errors.append("Module specifications must be a list")
            else:
                # Validate module structure
                for i, module in enumerate(modules_spec):
                    if not isinstance(module, dict):
                        errors.append(f"Module specification {i} must be a dictionary")
                    else:
                        required_fields = ["title", "description", "order_index", "difficulty"]
                        for field in required_fields:
                            if field not in module:
                                errors.append(f"Module {i} missing required field: {field}")

        return {
            "is_valid": len(errors) == 0,
            "validation_errors": errors,
            "validation_warnings": warnings
        }
