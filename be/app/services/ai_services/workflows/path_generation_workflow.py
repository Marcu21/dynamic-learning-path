"""
AI Services - Streaming Path Generation Workflow
===============================================

This module implements a streaming version of the learning path generation workflow.
Instead of returning final results all at once, it yields incremental updates as each
stage completes, allowing for real-time progress tracking and immediate user feedback.

Streaming Events:
- learning_path_info: Basic path metadata and structure
- module_N_info: Information about each generated module
- generation_complete: Final results and summary
- error_event: Error information if generation fails

Key Features:
- Real-time progress updates via async generator
- Incremental data delivery for better UX
- Comprehensive error handling with stream recovery
- Performance metrics for each streaming event
- Team notifications integrated with streaming
"""

from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.logger import get_logger
from app.models.enums import ExperienceLevel, LearningStyle
from app.schemas.path_generation_schemas.path_generation_state_schema import (
    PathGenerationState,
    StateManager,
    GenerationStage,
    StreamEventType,
    StreamEvent
)
from app.services.ai_services.path_generation_services.path_blueprint_service import PathBlueprintService
from app.services.ai_services.path_generation_services.query_generation_service import QueryGenerationService
from app.services.ai_services.path_generation_services.content_pool_service import ContentPoolService
from app.services.ai_services.path_generation_services.module_generation_service import ModuleGenerationService

logger = get_logger(__name__)


class StreamingPathGenerationWorkflow:
    """
    Streaming version of the learning path generation workflow.

    This workflow extends the original PathGenerationWorkflow to emit
    real-time streaming events as generation progresses, allowing clients
    to receive immediate feedback and display progress updates.

    Key Features:
    - Async generator interface for streaming events
    - Real-time progress tracking with percentage completion
    - Incremental data delivery (path info, then modules)
    - Comprehensive error handling with stream recovery
    - Performance metrics for each streaming event
    - Integration with existing LangGraph infrastructure
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize the streaming path generation workflow.

        Args:
            db_session: Database session for services (optional)
        """
        self.logger = get_logger(f"{__name__}.StreamingPathGenerationWorkflow")
        self.state_manager = StateManager()
        self.db = db_session

        # Initialize all generation services
        self.blueprint_service = PathBlueprintService(db_session)
        self.query_service = QueryGenerationService(db_session)
        self.content_pool_service = ContentPoolService(db_session)
        self.module_service = ModuleGenerationService(db_session)

        # Build the workflow graph with streaming support
        self.graph = self._build_streaming_workflow_graph()

        # Progress tracking
        self.current_progress = 0.0
        self.stage_weights = {
            GenerationStage.BLUEPRINT: 15.0,
            GenerationStage.QUERY: 10.0,
            GenerationStage.CONTENT_POOL: 15.0,
            GenerationStage.MODULES: 50.0,
            GenerationStage.FINALIZATION: 10.0
        }

        # Set to track streamed modules
        self.streamed_modules = set()

        self.learning_path_streamed = False

        self.logger.info("StreamingPathGenerationWorkflow initialized")

    async def generate_learning_path_stream(
            self,
            user_id: str,
            subject: str,
            experience_level: ExperienceLevel,
            learning_styles: List[LearningStyle],
            preferred_platforms: List[str],
            study_time_minutes: int,
            goals: str,
            team_id: Optional[str] = None,
            config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Generate a learning path with real-time streaming updates - SAFE VERSION.

        This method yields StreamEvent objects as generation progresses,
        allowing clients to receive immediate feedback and display progress.
        """
        try:
            # Create initial state with enhanced safety checks
            try:
                initial_state = self.state_manager.create_initial_state(
                    user_id=user_id,
                    subject=subject,
                    experience_level=experience_level,
                    learning_styles=learning_styles,
                    preferred_platforms=preferred_platforms,
                    study_time_minutes=study_time_minutes,
                    goals=goals,
                    team_id=team_id,
                )
            except Exception as e:
                self.logger.error(f"Failed to create initial state: {str(e)}")
                yield StreamEvent(
                    event_type=StreamEventType.ERROR_EVENT,
                    data={
                        "error": f"State initialization failed: {str(e)}",
                        "error_type": type(e).__name__,
                        "stage": "initialization",
                        "recoverable": False
                    },
                    timestamp=datetime.now(),
                    stage=GenerationStage.BLUEPRINT,
                    progress_percentage=0.0
                )
                return

            # Validate initial state
            if not isinstance(initial_state, dict):
                error_msg = f"Initial state is not a dict: {type(initial_state)}"
                self.logger.error(error_msg)
                yield StreamEvent(
                    event_type=StreamEventType.ERROR_EVENT,
                    data={
                        "error": error_msg,
                        "error_type": "StateValidationError",
                        "stage": "initialization",
                        "recoverable": False
                    },
                    timestamp=datetime.now(),
                    stage=GenerationStage.BLUEPRINT,
                    progress_percentage=0.0
                )
                return

            # Add configuration if provided
            if config and isinstance(config, dict):
                initial_state["generation_config"] = config

            self.logger.info(f"Starting streaming learning path generation for user {user_id}")

            # Validate that essential state fields are present and not None
            required_fields = ["user_id", "subject", "experience_level", "preferred_platforms"]
            missing_fields = []
            for field in required_fields:
                if field not in initial_state or initial_state[field] is None:
                    missing_fields.append(field)

            if missing_fields:
                error_msg = f"Missing required state fields: {missing_fields}"
                self.logger.error(error_msg)
                yield StreamEvent(
                    event_type=StreamEventType.ERROR_EVENT,
                    data={
                        "error": error_msg,
                        "error_type": "StateValidationError",
                        "stage": "initialization",
                        "recoverable": False
                    },
                    timestamp=datetime.now(),
                    stage=GenerationStage.BLUEPRINT,
                    progress_percentage=0.0
                )
                return

            # Reset progress tracking
            self.current_progress = 0.0
            self.streamed_modules = set()
            self.learning_path_streamed = False

            # Initialize team context early if team_id is provided
            if team_id and self.db:
                try:
                    team_context = await self._load_team_context_early(team_id)
                    initial_state.update(team_context)
                    self.logger.info(f"Loaded team context for team {team_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to load team context early: {str(e)}")
                    # Set default values to prevent None errors
                    initial_state.update({
                        "team_members": [],
                        "team_name": "Unknown Team",
                        "team_lead_id": None,
                        "notification_recipients": []
                    })

            # Emit initial progress event
            yield StreamEvent(
                event_type=StreamEventType.GENERATION_PROGRESS,
                data={
                    "message": "Initializing path generation...",
                    "stage": "initialization"
                },
                timestamp=datetime.now(),
                stage=GenerationStage.BLUEPRINT,
                progress_percentage=0.0,
                metadata={"user_id": user_id, "subject": subject}
            )

            # Execute the streaming workflow with enhanced error handling
            workflow_config = {"thread_id": f"stream_path_{user_id}_{datetime.now().timestamp()}"}

            try:
                # Debug initial state before streaming
                self.logger.debug(f"Initial state keys: {list(initial_state.keys())}")
                self.logger.debug(f"Initial state content_pool: {initial_state.get('content_pool')}")
                self.logger.debug(f"Initial state used_content_links: {initial_state.get('used_content_links')}")
                self.logger.debug(f"Initial state modules_spec: {initial_state.get('modules_spec')}")

                # Use astream to get incremental updates from LangGraph
                chunk_count = 0
                async for chunk in self.graph.astream(initial_state, config=workflow_config):
                    chunk_count += 1
                    self.logger.debug(f"Processing chunk {chunk_count}: {list(chunk.keys()) if chunk else 'None'}")

                    try:
                        # Process each chunk and emit appropriate stream events
                        async for event in self._process_workflow_chunk(chunk):
                            yield event
                    except Exception as chunk_error:
                        self.logger.error(f"Error processing chunk {chunk_count}: {str(chunk_error)}")
                        # Continue with next chunk instead of failing completely
                        yield StreamEvent(
                            event_type=StreamEventType.ERROR_EVENT,
                            data={
                                "error": f"Chunk {chunk_count} processing failed: {str(chunk_error)}",
                                "error_type": type(chunk_error).__name__,
                                "stage": "chunk_processing",
                                "recoverable": True,
                                "chunk_number": chunk_count
                            },
                            timestamp=datetime.now(),
                            stage=GenerationStage.BLUEPRINT,
                            progress_percentage=self.current_progress
                        )

                # Emit final completion event
                yield StreamEvent(
                    event_type=StreamEventType.GENERATION_COMPLETE,
                    data={
                        "success": True,
                        "message": "Learning path generation completed successfully",
                        "total_time_seconds": self._calculate_total_time(initial_state),
                        "chunks_processed": chunk_count,
                        "modules_streamed": len(self.streamed_modules)
                    },
                    timestamp=datetime.now(),
                    stage=GenerationStage.COMPLETED,
                    progress_percentage=100.0
                )

            except Exception as stream_error:
                self.logger.error(f"Streaming workflow execution failed: {str(stream_error)}")
                import traceback
                self.logger.error(f"Full traceback: {traceback.format_exc()}")

                # Emit error event
                yield StreamEvent(
                    event_type=StreamEventType.ERROR_EVENT,
                    data={
                        "error": f"Workflow streaming failed: {str(stream_error)}",
                        "error_type": type(stream_error).__name__,
                        "stage": "workflow_execution",
                        "recoverable": False
                    },
                    timestamp=datetime.now(),
                    stage=GenerationStage.COMPLETED,
                    progress_percentage=self.current_progress
                )

        except Exception as e:
            self.logger.error(f"Streaming learning path generation failed: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")

            # Emit error event
            yield StreamEvent(
                event_type=StreamEventType.ERROR_EVENT,
                data={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "stage": "workflow_execution",
                    "recoverable": False
                },
                timestamp=datetime.now(),
                stage=GenerationStage.COMPLETED,
                progress_percentage=self.current_progress
            )

    async def _process_workflow_chunk(self, chunk: Dict[str, Any]) -> AsyncGenerator[StreamEvent, None]:
        """
        Process a single chunk from the LangGraph workflow stream with enhanced safety.

        Args:
            chunk: State update chunk from LangGraph

        Yields:
            StreamEvent: Processed streaming events
        """
        try:
            self.logger.debug(f"Processing workflow chunk: {list(chunk.keys()) if chunk else 'None'}")

            if not chunk:
                self.logger.warning("Received empty chunk from workflow")
                return

            # Extract node name and state from chunk
            for node_name, node_state in chunk.items():
                if node_name == "__end__":
                    continue

                self.logger.debug(f"Processing node: {node_name}")

                # Safe state extraction with null checks
                if not isinstance(node_state, dict):
                    self.logger.warning(f"Node state is not a dict: {type(node_state)}")
                    continue

                current_stage = node_state.get("current_stage", GenerationStage.BLUEPRINT)
                if current_stage is None:
                    self.logger.warning("Current stage is None, defaulting to BLUEPRINT")
                    current_stage = GenerationStage.BLUEPRINT

                # Update progress based on stage
                try:
                    self._update_progress(current_stage, node_state)
                except Exception as e:
                    self.logger.error(f"Error updating progress: {str(e)}")

                # Process blueprint completion IMMEDIATELY when transitioning to query stage
                if not self.learning_path_streamed:
                    self.logger.info(f"Checking for learning path data in node: {node_name}")
                    async for event in self._process_blueprint_completion(node_state):
                        yield event
                try:
                    # Note: We process blueprint completion above for early streaming
                    if current_stage == GenerationStage.MODULES:
                        async for event in self._process_module_generation(node_state):
                            yield event

                except Exception as e:
                    self.logger.error(f"Error processing stage-specific events for {current_stage}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error processing workflow chunk: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")

            # Emit error event but don't stop the stream
            yield StreamEvent(
                event_type=StreamEventType.ERROR_EVENT,
                data={
                    "error": f"Chunk processing error: {str(e)}",
                    "error_type": type(e).__name__,
                    "stage": "chunk_processing",
                    "recoverable": True
                },
                timestamp=datetime.now(),
                stage=GenerationStage.BLUEPRINT,
                progress_percentage=self.current_progress
            )

    async def _process_blueprint_completion(self, state: PathGenerationState) -> AsyncGenerator[StreamEvent, None]:
        """
        Process blueprint completion and emit learning path info with safety checks.

        Args:
            state: Current workflow state

        Yields:
            StreamEvent: Learning path information event
        """
        try:
            if not isinstance(state, dict):
                self.logger.warning(f"Blueprint state is not a dict: {type(state)}")
                return

            # Safe extraction of blueprint data
            path_title = state.get("path_title")
            total_modules = state.get("total_modules")

            # Stream learning path info as soon as we have the data
            if path_title and total_modules and not self.learning_path_streamed:
                # Get the learning_path_id if it was created
                learning_path_id = state.get("learning_path_id")

                # Create comprehensive learning path data
                learning_path_data = {
                    # Core path information
                    "learning_path_id": learning_path_id,
                    "title": path_title,
                    "description": state.get("path_description", ""),
                    "estimated_days": state.get("estimated_days", 0),
                    "total_modules": total_modules,
                    "learning_objectives": state.get("learning_objectives", []),

                    # Module planning
                    "difficulty_progression": list(state.get("module_difficulty_map", {}).values()),
                    "module_difficulty_map": state.get("module_difficulty_map", {}),

                    # Time estimates
                    "estimated_hours": state.get("estimated_days", 0) * (state.get("study_time_minutes", 60) / 60),
                    "study_time_minutes": state.get("study_time_minutes", 0),

                    # User context
                    "subject": state.get("subject", ""),
                    "experience_level": (
                        state.get("experience_level", {}).get("value")
                        if isinstance(state.get("experience_level"), dict)
                        else str(state.get("experience_level", ""))
                    ),
                    "goals": state.get("goals", ""),
                    "preferred_platforms": state.get("preferred_platforms", []),

                    # Team/collaboration
                    "team_id": state.get("team_id"),
                    "user_id": state.get("user_id"),

                    # Status and timestamps
                    "status": "blueprint_complete",
                    "created_at": datetime.now().isoformat(),

                    # Database persistence status
                    "persisted_to_database": learning_path_id is not None,

                    # Team context if available
                    "team_name": state.get("team_name"),
                    "team_members_count": len(state.get("team_members", [])) if state.get("team_members") else None
                }

                yield StreamEvent(
                    event_type=StreamEventType.LEARNING_PATH_INFO,
                    data=learning_path_data,
                    timestamp=datetime.now(),
                    stage=GenerationStage.BLUEPRINT,
                    progress_percentage=self.current_progress,
                    metadata={
                        "modules_planned": total_modules,
                        "subject": state.get("subject", "Unknown"),
                        "learning_path_created": learning_path_id is not None,
                        "blueprint_completed": True,
                        "estimated_completion_time": f"{state.get('estimated_days', 0)} days"
                    }
                )

                # Mark as streamed to prevent duplicates
                self.learning_path_streamed = True

                self.logger.info(
                    f"Streamed learning path info: '{path_title}' with {total_modules} modules" +
                    (f" (ID: {learning_path_id})" if learning_path_id else " (not yet persisted)")
                )

        except Exception as e:
            self.logger.error(f"Error processing blueprint completion: {str(e)}")

    async def _process_module_generation(self, state: PathGenerationState) -> AsyncGenerator[StreamEvent, None]:
        """
        Process module generation and emit individual module info with safety checks.

        Args:
            state: Current workflow state

        Yields:
            StreamEvent: Module information events
        """
        try:
            if not isinstance(state, dict):
                self.logger.warning(f"Module state is not a dict: {type(state)}")
                return

            # Safe extraction of module data
            modules_spec = state.get("modules_spec", [])
            if not isinstance(modules_spec, list):
                self.logger.warning(f"modules_spec is not a list: {type(modules_spec)}")
                return

            current_module_index = state.get("current_module_index", 1)

            self.logger.debug(f"Processing modules: current_index={current_module_index}, modules_count={len(modules_spec)}, streamed={self.streamed_modules}")

            new_module_index = current_module_index - 1

            # Validate we have a valid module to process
            if new_module_index < 1:
                self.logger.debug(f"No valid module to stream. current_module_index: {current_module_index}")
                return

            # Check if this module has already been streamed
            if new_module_index in self.streamed_modules:
                self.logger.debug(f"Module {new_module_index} already streamed, skipping")
                return

            # Get the module that was just added (convert to 0-based array indexing)
            module_array_index = new_module_index - 1
            if module_array_index >= len(modules_spec) or module_array_index < 0:
                self.logger.warning(
                    f"Module array index {module_array_index} out of range for modules_spec length {len(modules_spec)}")
                return

            module = modules_spec[module_array_index]
            if not isinstance(module, dict):
                self.logger.warning(f"Module at index {module_array_index} is not a dict: {type(module)}")
                return

            module_data = {
                "module_id": module.get("module_id", f"module_{new_module_index}"),
                "title": module.get("title", "Unknown Module"),
                "description": module.get("description", ""),
                "learning_objectives": module.get("learning_objectives", []),
                "order_index": module.get("order_index", 0),
                "learning_style": module.get("learning_style", "Unknown"),
                "difficulty": module.get("difficulty", "intermediate"),
                "platform": module.get("platform", "Unknown"),
                "duration": module.get("duration", 0),
                "content_url": module.get("content_url", "")
            }

            # Handle learning_style if it's a list (convert to string)
            if isinstance(module_data["learning_style"], list):
                if len(module_data["learning_style"]) > 0:
                    module_data["learning_style"] = module_data["learning_style"][0]
                else:
                    module_data["learning_style"] = "visual"

            self.logger.info(f"Extracted module {new_module_index}: title='{module_data['title']}', platform={module_data['platform']}, order_index={module_data['order_index']}")

            yield StreamEvent(
                event_type=StreamEventType.MODULE_INFO,
                data=module_data,
                timestamp=datetime.now(),
                stage=GenerationStage.MODULES,
                progress_percentage=self.current_progress,
                metadata={
                    "module_index": new_module_index,
                    "total_modules": state.get("total_modules", len(modules_spec)),
                    "modules_completed": len(self.streamed_modules) + 1,
                    "current_module_index": current_module_index
                }
            )

            # Mark this module as streamed
            self.streamed_modules.add(new_module_index)

            self.logger.info(f"Successfully streamed module {new_module_index}: '{module_data['title']}'")

        except Exception as e:
            self.logger.error(f"Error processing module generation: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")

    def _update_progress(self, current_stage: GenerationStage, state: Dict[str, Any]) -> None:
        """
        Update progress percentage based on current stage with safety checks.

        Args:
            current_stage: Current generation stage
            state: Current state dictionary
        """
        try:
            if not isinstance(state, dict):
                self.logger.warning(f"State is not a dict in progress update: {type(state)}")
                return

            # Safe access to stage weights
            stage_weight = self.stage_weights.get(current_stage, 10.0)

            # Calculate base progress
            base_progress = sum(
                weight for stage, weight in self.stage_weights.items()
                if stage.value < current_stage.value
            ) if hasattr(current_stage, 'value') else 0.0

            # Add stage-specific progress
            stage_progress = 0.0
            if current_stage == GenerationStage.MODULES:
                # Calculate module-specific progress
                current_module = state.get("current_module_index", 1)
                total_modules = state.get("total_modules", 1)

                if total_modules and total_modules > 0:
                    module_progress = (current_module - 1) / total_modules
                    stage_progress = stage_weight * module_progress

            self.current_progress = min(100.0, base_progress + stage_progress)

        except Exception as e:
            self.logger.error(f"Error updating progress: {str(e)}")

    def _build_streaming_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow with streaming support.

        Returns:
            StateGraph: Compiled workflow graph optimized for streaming
        """
        # Create the state graph (same structure as original)
        workflow = StateGraph(PathGenerationState)

        # Add all workflow nodes (reusing existing node implementations)
        workflow.add_node("blueprint_generation", self._blueprint_node)
        workflow.add_node("query_generation", self._query_node)
        workflow.add_node("content_pool_creation", self._content_pool_node)
        workflow.add_node("module_generation", self._module_node)
        workflow.add_node("finalization", self._finalization_node)
        workflow.add_node("error_handler", self._error_handler_node)

        # Set entry point
        workflow.set_entry_point("blueprint_generation")

        # Define the workflow edges (same as original)
        workflow.add_conditional_edges(
            "blueprint_generation",
            self._route_after_blueprint,
            {
                "continue": "query_generation",
                "retry": "blueprint_generation",
                "error": "error_handler"
            }
        )

        workflow.add_conditional_edges(
            "query_generation",
            self._route_after_queries,
            {
                "continue": "content_pool_creation",
                "retry": "query_generation",
                "error": "error_handler"
            }
        )

        workflow.add_conditional_edges(
            "content_pool_creation",
            self._route_after_content_pool,
            {
                "continue": "module_generation",
                "retry": "content_pool_creation",
                "error": "error_handler"
            }
        )

        workflow.add_conditional_edges(
            "module_generation",
            self._route_after_module,
            {
                "next_module_same_difficulty": "module_generation",
                "next_module_new_difficulty": "content_pool_creation",
                "finalize": "finalization",
                "retry": "module_generation",
                "error": "error_handler"
            }
        )

        workflow.add_edge("finalization", END)
        workflow.add_edge("error_handler", END)

        # Compile with checkpointing
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    # Node implementations (reuse from original workflow)
    async def _blueprint_node(self, state: PathGenerationState) -> PathGenerationState:
        """Blueprint generation node."""
        self.logger.info("Executing streaming blueprint generation node")
        try:
            updates = await self.blueprint_service.generate_blueprint(state)
            return {**state, **updates}
        except Exception as e:
            self.logger.error(f"Blueprint node failed: {str(e)}")
            error_updates = self.state_manager.add_error(state, "blueprint_node_error", str(e))
            return {**state, **error_updates}

    async def _query_node(self, state: PathGenerationState) -> PathGenerationState:
        """Query generation node."""
        self.logger.info("Executing streaming query generation node")
        try:
            updates = await self.query_service.generate_queries(state)
            return {**state, **updates}
        except Exception as e:
            self.logger.error(f"Query node failed: {str(e)}")
            error_updates = self.state_manager.add_error(state, "query_node_error", str(e))
            return {**state, **error_updates}

    async def _content_pool_node(self, state: PathGenerationState) -> PathGenerationState:
        """Content pool creation node."""
        self.logger.info("Executing streaming content pool creation node")
        try:
            updates = await self.content_pool_service.create_content_pool(state)
            return {**state, **updates}
        except Exception as e:
            self.logger.error(f"Content pool node failed: {str(e)}")
            error_updates = self.state_manager.add_error(state, "content_pool_node_error", str(e))
            return {**state, **error_updates}

    async def _module_node(self, state: PathGenerationState) -> PathGenerationState:
        """Module generation node with enhanced debugging."""
        current_module = state.get("current_module_index", 1)
        total_modules = state.get("total_modules", 0)
        self.logger.info(f"Executing streaming module generation: {current_module}/{total_modules}")

        try:
            # Debug state before calling module service
            self.logger.debug(f"State keys: {list(state.keys())}")
            self.logger.debug(f"Content pool type: {type(state.get('content_pool'))}")
            self.logger.debug(f"Content pool value: {state.get('content_pool')}")
            self.logger.debug(f"Current stage: {state.get('current_stage')}")
            self.logger.debug(f"Subject: {state.get('subject')}")
            self.logger.debug(f"Module difficulty map: {state.get('module_difficulty_map')}")

            # Check for None values that might cause len() errors
            content_pool = state.get("content_pool")
            if content_pool is None:
                self.logger.error("Content pool is None - this will cause len() error")
                raise ValueError("Content pool is None")

            used_content_links = state.get("used_content_links")
            if used_content_links is None:
                self.logger.warning("used_content_links is None, setting to empty list")
                state["used_content_links"] = []

            modules_spec = state.get("modules_spec")
            if modules_spec is None:
                self.logger.warning("modules_spec is None, setting to empty list")
                state["modules_spec"] = []

            # Call the module service
            updates = await self.module_service.generate_module(state)
            return {**state, **updates}

        except Exception as e:
            self.logger.error(f"Module node failed: {str(e)}")
            self.logger.error(f"Exception type: {type(e)}")

            # Enhanced error logging
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")

            error_updates = self.state_manager.add_error(state, "module_node_error", str(e))
            return {**state, **error_updates}

    async def _finalization_node(self, state: PathGenerationState) -> PathGenerationState:
        """Finalization node."""
        self.logger.info("Executing streaming finalization node")
        try:
            # Create generation summary
            modules_spec = state.get("modules_spec", [])
            generation_summary = {
                "status": "completed",
                "modules_generated": len(modules_spec),
                "completion_time": datetime.now().isoformat(),
                "total_duration_hours": sum(m.get("duration", 0) for m in modules_spec) / 60
            }

            final_updates = self.state_manager.update_stage(
                state, GenerationStage.COMPLETED,
                stage_data={"generation_completed_at": datetime.now()}
            )
            final_updates["generation_summary"] = generation_summary

            return {**state, **final_updates}
        except Exception as e:
            self.logger.error(f"Finalization node failed: {str(e)}")
            error_updates = self.state_manager.add_error(state, "finalization_node_error", str(e))
            return {**state, **error_updates}

    async def _error_handler_node(self, state: PathGenerationState) -> PathGenerationState:
        """Error handler node."""
        self.logger.error("Executing streaming error handler node")
        errors = state.get("errors", [])

        error_summary = {
            "status": "failed",
            "total_errors": len(errors),
            "error_details": errors[-3:] if errors else [],
            "failure_time": datetime.now().isoformat()
        }

        final_updates = self.state_manager.update_stage(
            state, GenerationStage.COMPLETED,
            stage_data={"error_handling_completed_at": datetime.now()}
        )
        final_updates["generation_summary"] = error_summary

        return {**state, **final_updates}

    # Routing methods (reuse from original workflow)
    def _route_after_blueprint(self, state: PathGenerationState) -> str:
        """Route after blueprint generation."""
        errors = [e for e in state.get("errors", []) if e["stage"] == GenerationStage.BLUEPRINT]
        if errors:
            return "retry" if self.state_manager.should_retry(state) else "error"

        if (state.get("current_stage") == GenerationStage.QUERY and
                state.get("path_title") and state.get("module_difficulty_map")):
            return "continue"
        return "error"

    def _route_after_queries(self, state: PathGenerationState) -> str:
        """Route after query generation."""
        errors = [e for e in state.get("errors", []) if e["stage"] == GenerationStage.QUERY]
        if errors:
            return "retry" if self.state_manager.should_retry(state) else "error"

        if (state.get("current_stage") == GenerationStage.CONTENT_POOL and
                state.get("platform_queries")):
            return "continue"
        return "error"

    def _route_after_content_pool(self, state: PathGenerationState) -> str:
        """Route after content pool creation."""
        errors = [e for e in state.get("errors", []) if e["stage"] == GenerationStage.CONTENT_POOL]
        if errors:
            return "retry" if self.state_manager.should_retry(state) else "error"

        if (state.get("current_stage") == GenerationStage.MODULES and
                state.get("content_pool")):
            return "continue"
        return "error"

    def _route_after_module(self, state: PathGenerationState) -> str:
        """Route after module generation."""
        errors = [e for e in state.get("errors", []) if e["stage"] == GenerationStage.MODULES]
        if errors:
            return "retry" if self.state_manager.should_retry(state) else "error"

        if state.get("current_stage") == GenerationStage.FINALIZATION:
            return "finalize"

        if state.get("current_stage") == GenerationStage.CONTENT_POOL:
            return "next_module_new_difficulty"

        if state.get("current_stage") == GenerationStage.MODULES:
            current_module_index = state.get("current_module_index", 1)
            total_modules = state.get("total_modules", 0)

            if current_module_index > total_modules:
                return "finalize"
            return "next_module_same_difficulty"

        return "error"

    def _calculate_total_time(self, initial_state: PathGenerationState) -> float:
        """Calculate total generation time in seconds."""
        start_time = initial_state.get("generation_started_at")
        if start_time:
            return (datetime.now() - start_time).total_seconds()
        return 0.0

    async def _load_team_context_early(self, team_id: str) -> Dict[str, Any]:
        """
        Load team context early in the workflow to prevent None values.

        Args:
            team_id: Team ID to load context for

        Returns:
            Dict[str, Any]: Team context data
        """
        try:
            from app.repositories import team_repository, user_repository

            self.logger.info(f"Loading early team context for team {team_id}")

            # Get team information
            team = await team_repository.get_by_id(self.db, team_id)
            if not team:
                self.logger.warning(f"Team {team_id} not found during early context loading")
                return {
                    "team_members": [],
                    "team_name": "Unknown Team",
                    "team_lead_id": None,
                    "notification_recipients": []
                }

            # Get team members
            team_members = await team_repository.get_team_members(self.db, team_id)

            # Format team member information
            formatted_members = []
            notification_recipients = []

            for member in team_members:
                user = await user_repository.get_by_id(self.db, member.user_id)
                if user:
                    formatted_members.append({
                        "user_id": user.id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "email": user.email,
                        "role": member.role.value if hasattr(member, 'role') else "member"
                    })
                    notification_recipients.append(user.id)

            team_context = {
                "team_members": formatted_members,
                "team_lead_id": team.team_lead_id,
                "team_name": team.name,
                "notification_recipients": notification_recipients
            }

            self.logger.info(
                f"Early team context loaded: {len(formatted_members)} members, "
                f"team: '{team.name}', lead: {team.team_lead_id}"
            )

            return team_context

        except Exception as e:
            self.logger.error(f"Failed to load early team context: {str(e)}")
            # Return safe defaults instead of failing
            return {
                "team_members": [],
                "team_name": "Unknown Team",
                "team_lead_id": None,
                "notification_recipients": []
            }
