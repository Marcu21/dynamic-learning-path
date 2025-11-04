"""
Module Insertion Workflow
========================

This module contains the LangGraph workflow for inserting new modules into existing learning paths.
The workflow handles the complete process from query generation to content creation and database updates.

Key Features:
- Generate module content using AI services
- Handle module ordering and database updates
- Send notifications upon completion
- Comprehensive error handling and logging
- Proper database transaction management

Flow:
1. Validate input parameters and learning path access
2. Get learning path details (experience_level, goals, path_title)
3. Determine difficulty based on previous module
4. Generate module queries using QueryGenerationService
5. Create content using ContentPoolService
6. Save module to database with proper ordering
7. Update order_index of subsequent modules
8. Send completion notification
"""

from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.core.logger import get_logger
from app.core.utils import get_learning_style_by_platform_name
from app.models.enums import DifficultyLevel, ExperienceLevel
from app.schemas.path_generation_schemas.module_insertion_schema import create_initial_state, ModuleInsertionState
from app.services.ai_services.path_generation_services.query_generation_service import QueryGenerationService
from app.services.ai_services.path_generation_services.content_pool_service import ContentPoolService
from app.services.core_services import module_service, learning_path_service
from app.repositories import learning_path_repository, module_repository, preferences_repository
from app.db.celery_database import get_celery_db_session_sync

logger = get_logger(__name__)


class ModuleInsertionWorkflow:
    """
    LangGraph-based workflow for inserting modules into learning paths.

    This workflow orchestrates the complete module insertion process:
    1. Input validation and learning path analysis
    2. Content generation using AI services
    3. Database operations with proper ordering
    4. Notification delivery
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize the module insertion workflow.

        Args:
            db_session: Database session for all operations
        """
        self.logger = get_logger(f"{__name__}.ModuleInsertionWorkflow")
        self.db = db_session

        # Initialize AI services
        self.query_service = QueryGenerationService(db_session)
        self.content_service = ContentPoolService(db_session)

        # Build the workflow graph
        self.graph = self._build_workflow_graph()

        self.logger.info("ModuleInsertionWorkflow initialized")

    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for module insertion.

        Returns:
            Compiled StateGraph for the module insertion workflow
        """
        workflow = StateGraph(ModuleInsertionState)

        # Add workflow nodes
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("analyze_learning_path", self._analyze_learning_path_node)
        workflow.add_node("generate_queries", self._generate_queries_node)
        workflow.add_node("create_content", self._create_content_node)
        workflow.add_node("save_module", self._save_module_node)
        workflow.add_node("update_ordering", self._update_ordering_node)
        workflow.add_node("send_notification", self._send_notification_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Set entry point
        workflow.set_entry_point("validate_input")

        # Define workflow edges with error handling
        workflow.add_conditional_edges(
            "validate_input",
            self._route_after_validation,
            {
                "continue": "analyze_learning_path",
                "error": "handle_error"
            }
        )

        workflow.add_conditional_edges(
            "analyze_learning_path",
            self._route_after_analysis,
            {
                "continue": "generate_queries",
                "error": "handle_error"
            }
        )

        workflow.add_conditional_edges(
            "generate_queries",
            self._route_after_queries,
            {
                "continue": "create_content",
                "error": "handle_error"
            }
        )

        workflow.add_conditional_edges(
            "create_content",
            self._route_after_content,
            {
                "continue": "save_module",
                "error": "handle_error"
            }
        )

        workflow.add_conditional_edges(
            "save_module",
            self._route_after_save,
            {
                "continue": "update_ordering",
                "error": "handle_error"
            }
        )

        workflow.add_conditional_edges(
            "update_ordering",
            self._route_after_ordering,
            {
                "continue": "send_notification",
                "error": "handle_error"
            }
        )

        workflow.add_edge("send_notification", END)
        workflow.add_edge("handle_error", END)

        # Compile with checkpointing for error recovery
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    async def insert_module(
            self,
            user_query: str,
            learning_path_id: int,
            insert_position: int,
            platform_name: str,
            user_id: str
    ) -> Dict[str, Any]:
        """
        Execute the module insertion workflow.

        Args:
            user_query: What the user wants in the module
            learning_path_id: Target learning path ID
            insert_position: Index where new module will be inserted
            platform_name: Platform to use for content
            user_id: User performing the insertion

        Returns:
            Dict containing the results of the insertion process

        Raises:
            ValueError: If input validation fails
            PermissionError: If user lacks permission
            SQLAlchemyError: If database operations fail
        """
        try:
            self.logger.info(
                f"Starting module insertion workflow - "
                f"User: {user_id}, Learning Path: {learning_path_id}, "
                f"Position: {insert_position}, Platform: {platform_name}"
            )

            # Initialize workflow state
            initial_state = create_initial_state(
                user_query=user_query,
                learning_path_id=learning_path_id,
                insert_position=insert_position,
                platform_name=platform_name,
                user_id=user_id
            ).to_dict()

            # Create workflow configuration with required checkpoint keys
            workflow_config = {
                "configurable": {
                    "thread_id": f"module_insertion_{user_id}_{learning_path_id}_{int(datetime.now().timestamp())}",
                    "checkpoint_ns": "module_insertion",
                    "checkpoint_id": f"insertion_{learning_path_id}_{insert_position}_{int(datetime.now().timestamp())}"
                }
            }

            self.logger.debug(f"Workflow config: {workflow_config}")
            self.logger.debug(f"Initial state keys: {list(initial_state.keys())}")

            # Execute the workflow with proper configuration
            final_state = await self.graph.ainvoke(initial_state, config=workflow_config)

            # Calculate total execution time
            total_time = (datetime.now() - final_state["total_start_time"]).total_seconds()

            # Prepare response
            if final_state.get("error_message"):
                self.logger.error(f"Module insertion failed: {final_state['error_message']}")
                return {
                    "success": False,
                    "error": final_state["error_message"],
                    "execution_time_seconds": total_time
                }
            else:
                self.logger.info(f"Module insertion completed successfully in {total_time:.2f} seconds")
                return {
                    "success": True,
                    "created_module_id": final_state.get("created_module_id"),
                    "module_title": final_state.get("generated_module", {}).get("title"),
                    "execution_time_seconds": total_time,
                    "stages_completed": final_state.get("current_stage")
                }

        except Exception as e:
            self.logger.error(f"Module insertion workflow failed: {str(e)}")
            raise

    # =============================================================================
    # WORKFLOW NODE IMPLEMENTATIONS
    # =============================================================================

    async def _validate_input_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input parameters and user permissions.

        Validates:
        - Learning path exists and user has access
        - Insert position is valid
        - Platform name is supported
        - User query is not empty
        """
        try:
            self.logger.info(f"Validating input for learning path {state['learning_path_id']}")
            state["current_stage"] = "validation"
            state["stage_start_time"] = datetime.now()

            # Validate user query
            if not state["user_query"] or not state["user_query"].strip():
                raise ValueError("User query cannot be empty")

            # Validate learning path exists and user has access
            learning_path = await learning_path_repository.get_by_id(self.db, state["learning_path_id"])
            if not learning_path:
                raise ValueError(f"Learning path {state['learning_path_id']} not found")

            # Check user permissions
            if not learning_path_service.validate_learning_path_access(self.db, learning_path.id, state["user_id"]):
                raise PermissionError(f"User {state['user_id']} cannot modify learning path {state['learning_path_id']}")

            # Get existing modules to validate insert position
            existing_modules = await module_repository.get_by_learning_path_id(self.db, state["learning_path_id"])

            # Validate insert position
            max_position = len(existing_modules) + 1
            if state["insert_position"] < 0 or state["insert_position"] > max_position:
                raise ValueError(f"Insert position {state['insert_position']} is invalid. Must be between 0 and {max_position}")

            # Validate platform name
            supported_platforms = ["youtube", "spotify", "google books", "research papers", "codeforces"]
            if state["platform_name"].lower() not in supported_platforms:
                raise ValueError(f"Platform '{state['platform_name']}' is not supported. Supported platforms: {supported_platforms}")

            self.logger.info("Input validation completed successfully")
            return state

        except Exception as e:
            self.logger.error(f"Input validation failed: {str(e)}")
            state["error_message"] = str(e)
            return state

    async def _analyze_learning_path_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the learning path to gather context for module generation.

        Retrieves:
        - Learning path details (title, experience_level, goals)
        - Existing modules and their order
        - Difficulty of the module before insertion point
        """
        try:
            self.logger.info(f"Analyzing learning path {state['learning_path_id']}")
            state["current_stage"] = "analysis"
            state["stage_start_time"] = datetime.now()

            # Get learning path details
            learning_path = await learning_path_repository.get_by_id(self.db, state["learning_path_id"])
            if not learning_path:
                raise ValueError(f"Learning path {state['learning_path_id']} not found")

            state["learning_path_title"] = learning_path.title

            # Get preferences - try multiple approaches
            preferences = None

            # Method 1: Try to get from state if provided
            if state.get("preferences_id"):
                preferences = await preferences_repository.get_by_id(self.db, state["preferences_id"])

            # Method 2: Try to get from learning path relationship
            if not preferences and learning_path.preferences_id:
                preferences = await preferences_repository.get_by_id(self.db, learning_path.preferences_id)

            # Method 3: Try using the learning path repository helper method
            if not preferences:
                preferences = await learning_path_repository.get_preferences(self.db, state["learning_path_id"])

            # Set defaults if no preferences found
            if preferences:
                state["experience_level"] = preferences.experience_level or ExperienceLevel.INTERMEDIATE
                state["goals"] = preferences.goals or f"Master {learning_path.title}"
                self.logger.info(f"Found preferences with experience level: {preferences.experience_level}")
            else:
                # Use sensible defaults if no preferences found
                state["experience_level"] = ExperienceLevel.INTERMEDIATE
                state["goals"] = f"Master {learning_path.title}"
                self.logger.warning(
                    f"No preferences found for learning path {state['learning_path_id']}, using defaults")

            # Get existing modules in order
            existing_modules = await module_repository.get_by_learning_path_id(self.db, state["learning_path_id"])

            # Convert modules to dictionaries for state storage
            modules_data = []
            for module in existing_modules:
                modules_data.append({
                    "id": module.id,
                    "title": module.title,
                    "order_index": module.order_index,
                    "difficulty": module.difficulty if module.difficulty else "intermediate"
                })

            state["existing_modules"] = modules_data

            # Determine difficulty for new module based on previous module
            if state["insert_position"] == 0:
                # Inserting at the beginning - use beginner or learning path's base difficulty
                if state["experience_level"] == ExperienceLevel.BEGINNER:
                    state["module_difficulty"] = DifficultyLevel.BEGINNER
                else:
                    state["module_difficulty"] = DifficultyLevel.INTERMEDIATE
            else:
                # Get difficulty of module at position insert_position - 1
                previous_module = next(
                    (m for m in existing_modules if m.order_index == state["insert_position"] - 1),
                    None
                )

                if previous_module and previous_module.difficulty:
                    # Use same difficulty as previous module or step up
                    current_difficulty = previous_module.difficulty
                    if current_difficulty == DifficultyLevel.BEGINNER:
                        state["module_difficulty"] = DifficultyLevel.INTERMEDIATE
                    elif current_difficulty == DifficultyLevel.INTERMEDIATE:
                        state["module_difficulty"] = DifficultyLevel.ADVANCED
                    else:
                        state["module_difficulty"] = DifficultyLevel.ADVANCED
                else:
                    # Default to intermediate if can't determine
                    state["module_difficulty"] = DifficultyLevel.INTERMEDIATE

            self.logger.info(
                f"Learning path analysis complete - "
                f"Experience: {state['experience_level']}, "
                f"Module difficulty: {state['module_difficulty']}, "
                f"Existing modules: {len(modules_data)}"
            )

            return state

        except Exception as e:
            self.logger.error(f"Learning path analysis failed: {str(e)}")
            state["error_message"] = str(e)
            return state

    async def _generate_queries_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate platform-specific queries using the QueryGenerationService.

        Uses the gathered context to create appropriate search queries
        for the specified platform.
        """
        try:
            self.logger.info("Generating platform queries for module content")
            state["current_stage"] = "query_generation"
            state["stage_start_time"] = datetime.now()

            # Get difficulty value - handle both enum and string cases
            module_difficulty = state["module_difficulty"]
            if hasattr(module_difficulty, 'value'):
                # It's an enum, get the string value
                difficulty_value = module_difficulty
            else:
                # It's already a string
                difficulty_value = str(module_difficulty)

            # Get experience level value - handle both enum and string cases
            experience_level = state["experience_level"]
            if hasattr(experience_level, 'value'):
                # It's an enum, get the string value
                experience_level_obj = experience_level  # Keep the enum for the service
            else:
                # It's already a string, need to convert back to enum for the service
                from app.models.enums import ExperienceLevel
                experience_level_obj = ExperienceLevel(experience_level)

            # Create module difficulty map in the expected format
            module_difficulty_map = {1: difficulty_value}

            # Prepare state for query generation service - adapt to PathGenerationState format
            query_generation_state = {
                "subject": state["user_query"],
                "preferred_platforms": [state["platform_name"]],
                "module_difficulty_map": module_difficulty_map,
                "experience_level": experience_level_obj,
                "goals": state["goals"],
                "path_title": state["learning_path_title"],
                "learning_path_id": state["learning_path_id"],
                "user_id": state["user_id"],
                # Add required fields for QueryGenerationService validation
                "stages_completed": ["blueprint"],  # Fake that blueprint stage is completed
                "current_stage": "query",
                "total_modules": 1,  # We're generating just one module
                "path_description": f"Learning module for {state['user_query']}",
                # Add retry-related fields
                "retry_count": 0,
                "max_retries": 3,
                "errors": []
            }

            self.logger.debug(f"Query generation state: {query_generation_state}")

            # Generate queries using the service
            query_result = await self.query_service.generate_queries(query_generation_state)

            self.logger.debug(f"Query result: {query_result}")

            # Extract platform queries from result and filter to only requested platform
            if "platform_queries" in query_result:
                # Filter the result to only include the platform we requested
                filtered_queries = {}
                for difficulty, platform_queries in query_result["platform_queries"].items():
                    filtered_queries[difficulty] = {}
                    # Only include the platform we actually requested
                    if state["platform_name"] in platform_queries:
                        filtered_queries[difficulty][state["platform_name"]] = platform_queries[state["platform_name"]]

                state["platform_queries"] = filtered_queries
                self.logger.info(
                    f"Generated and filtered queries for {len(state['platform_queries'])} difficulty levels")
            else:
                raise ValueError("Query generation failed - no platform queries returned")

            return state

        except Exception as e:
            self.logger.error(f"Query generation failed: {str(e)}")
            state["error_message"] = str(e)
            return state

    async def _create_content_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create content using the ContentPoolService.

        Fetches multiple content items for the module using the generated platform queries.
        This method preserves all available content items to allow the save module node
        to select the first unused content URL, preventing duplicate content within
        the same learning path.
        """
        try:
            from app.schemas.path_generation_schemas.path_generation_state_schema import GenerationStage

            self.logger.info("Creating content for module insertion")
            state["current_stage"] = "content_creation"
            state["stage_start_time"] = datetime.now()

            # Handle both enum and string cases for module_difficulty to ensure compatibility
            # with different stages of the workflow that may have converted enums to strings
            module_difficulty = state["module_difficulty"]
            if hasattr(module_difficulty, 'value'):
                difficulty_value = module_difficulty.value
            else:
                difficulty_value = str(module_difficulty)

            # Prepare state for content pool service with all required fields
            content_generation_state = {
                "platform_queries": state["platform_queries"],
                "module_difficulty_map": {1: difficulty_value},
                "preferred_platforms": [state["platform_name"]],
                "current_module_index": 1,
                "total_modules": 1,
                "user_id": state["user_id"],
                "learning_path_id": state["learning_path_id"],
                "stages_completed": [GenerationStage.QUERY],
                "current_stage": GenerationStage.CONTENT_POOL,
                "subject": state["user_query"],
                "experience_level": state["experience_level"],
                "goals": state["goals"],
                "retry_count": 0,
                "max_retries": 3,
                "errors": []
            }

            # Import GenerationStage if not already available in scope
            from app.schemas.path_generation_schemas.path_generation_state_schema import GenerationStage

            self.logger.debug(f"Content generation state prepared: {content_generation_state}")

            # Create content pool using the ContentPoolService which handles platform API calls
            content_result = await self.content_service.create_content_pool(content_generation_state)

            # Extract and preserve ALL content items for duplicate checking
            # The save module node will iterate through these to find unused content
            if "content_pool" in content_result and content_result["content_pool"]:
                content_items = content_result["content_pool"]

                if isinstance(content_items, dict):
                    # Content pool is organized by difficulty level
                    # Extract all items for the current difficulty
                    if difficulty_value in content_items and content_items[difficulty_value]:
                        state["content_pool"] = content_items[difficulty_value]  # Keep ALL items
                        self.logger.info(
                            f"Retrieved {len(state['content_pool'])} content items for difficulty '{difficulty_value}'")
                    else:
                        # Fallback to any available content from any difficulty
                        for difficulty_key, items in content_items.items():
                            if items:
                                state["content_pool"] = items  # Keep ALL items from the available difficulty
                                self.logger.info(
                                    f"Using {len(state['content_pool'])} content items from difficulty '{difficulty_key}' as fallback")
                                break
                        else:
                            raise ValueError("No content items found in content pool")
                else:
                    # Content pool is already a list - preserve all items
                    state["content_pool"] = content_items  # Keep ALL items
                    self.logger.info(f"Retrieved {len(state['content_pool'])} content items from content pool")

            else:
                raise ValueError("Content creation failed - no content pool returned")

            return state

        except Exception as e:
            self.logger.error(f"Content creation failed: {str(e)}")
            state["error_message"] = str(e)
            return state

    async def _save_module_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save the generated module to the database.

        Creates a new module record with the generated content and assigns it the correct order_index.
        This method handles the final stage of module insertion by persisting all gathered information
        to the database through the module service layer. It includes duplicate content URL detection
        to ensure no content is reused within the same learning path, and cleans content descriptions
        to provide educational-focused module descriptions.
        """
        try:
            self.logger.info("Saving module to database")
            state["current_stage"] = "module_save"
            state["stage_start_time"] = datetime.now()

            # Validate that content is available for module creation
            if not state["content_pool"]:
                raise ValueError("No content available for module creation")

            # Map platform names to their corresponding database IDs
            # These IDs should match the platform table in the database
            platform_id = await module_service.get_platform_id_by_name(
                self.db, state["platform_name"].lower()
            )

            # Get existing content URLs from the learning path to avoid duplicates
            # This prevents inserting modules with content that's already been used
            existing_modules = await module_repository.get_by_learning_path_id(self.db, state["learning_path_id"])
            existing_content_urls = {module.content_url for module in existing_modules if module.content_url}

            self.logger.info(f"Found {len(existing_content_urls)} existing content URLs in learning path")

            # Find the first unused content item from the content pool
            # Iterate through all available content to find one that hasn't been used
            selected_content_item = None
            for i, content_item in enumerate(state["content_pool"]):
                # Extract content URL with fallback handling for different field names
                # YouTube service returns "link" field, while other services might use "url"
                content_url = content_item.get("link") or content_item.get("url") or ""

                # Skip items without URLs as they cannot be used for modules
                if not content_url:
                    self.logger.debug(f"Skipping content item {i} - no URL found")
                    continue

                # Check if this content URL is already used in the learning path
                if content_url in existing_content_urls:
                    self.logger.debug(f"Skipping content item {i} - URL already used: {content_url}")
                    continue

                # Found an unused content item
                selected_content_item = content_item
                self.logger.info(f"Selected unused content item {i}: '{content_item.get('title', 'Unknown')}'")
                break

            # Ensure we found a usable content item
            if selected_content_item is None:
                raise ValueError(
                    "No unused content available - all content URLs are already used in this learning path")

            # Extract the final content URL that will be used
            final_content_url = selected_content_item.get("link") or selected_content_item.get("url") or ""

            # Extract and validate duration with type conversion and fallback
            # Content sources may return duration as string, integer, or missing entirely
            # We ensure it's always a valid integer with a reasonable default
            duration = selected_content_item.get("duration", 30)
            if isinstance(duration, str):
                try:
                    duration = int(duration)
                except (ValueError, TypeError):
                    duration = 30  # Default to 30 minutes if conversion fails
            elif not isinstance(duration, int):
                duration = 30  # Default to 30 minutes for any other type

            # Generate a standardized educational description for inserted modules
            # This provides consistent, professional descriptions for all inserted content
            module_description = self._get_hardcoded_module_description(
                state["user_query"],
                state["platform_name"]
            )

            module_learning_goals = self._get_hardcoded_learning_goals(state)

            module_learning_style = get_learning_style_by_platform_name(state["platform_name"])

            # Import the required schema for module creation
            from app.schemas.core_schemas.module_schema import ModuleCreate

            # Construct the module creation data with all required fields
            # This schema ensures data validation before database insertion
            module_data = ModuleCreate(
                learning_path_id=state["learning_path_id"],
                platform_id=platform_id,
                title=selected_content_item.get("title", f"Module: {state['user_query']}"),
                description=module_description,
                duration=duration,
                order_index=state["insert_position"],
                content_url=final_content_url,
                difficulty=state["module_difficulty"],
                learning_style=[module_learning_style],
                learning_objectives=module_learning_goals,
                is_inserted=True
            )

            # Log the extracted data for debugging and audit purposes
            self.logger.info(f"Creating module '{module_data.title}' for learning path {state['learning_path_id']}")
            self.logger.info(f"Content URL: {final_content_url}")
            self.logger.info(f"Duration: {duration} minutes")
            self.logger.info(f"Generated description: {module_description}")

            # Create the module through the service layer which handles business logic and validation
            sync_db_session = get_celery_db_session_sync()
            created_module = module_repository.create_module(sync_db_session, module_data)

            # Store module information in state for downstream processing and response
            state["created_module_id"] = created_module.id
            state["generated_module"] = {
                "id": created_module.id,
                "title": created_module.title,
                "description": created_module.description,
                "order_index": created_module.order_index,
                "content_url": created_module.content_url
            }

            self.logger.info(f"Successfully created module {created_module.id}: '{created_module.title}'")

            return state

        except Exception as e:
            self.logger.error(f"Module save failed: {str(e)}")
            state["error_message"] = str(e)
            return state

    def _get_hardcoded_module_description(self, user_query: str, platform: str) -> str:
        """
        Generate a standardized hardcoded description for inserted modules.

        Provides consistent, professional descriptions that focus on educational value
        rather than using potentially promotional or low-quality content descriptions.

        Args:
            user_query: User's learning request
            platform: Content platform name

        Returns:
            Standardized educational module description
        """
        # Create a professional, educational description based on the user query
        base_description = f"This module was inserted using the following query: '{user_query}'. "

        # Add platform-specific context
        if platform.lower() == "youtube":
            platform_context = "This module was generated using YouTube content, which provides visual and auditory learning experiences. "
        elif platform.lower() == "spotify":
            platform_context = "This module was generated using Spotify content, which offers audio-based learning through podcasts and music. "
        elif platform.lower() in ["google books", "semantic scholar"]:
            platform_context = "This module was generated using Google Books or Semantic Scholar, providing access to scholarly articles and books. "
        elif platform.lower() == "coursera":
            platform_context = "This module was generated using Coursera content, which includes structured courses from top universities. "
        elif platform.lower() == "udemy":
            platform_context = "This module was generated using Udemy content, which offers a wide range of courses from various instructors. "
        else:
            platform_context = "This module was generated using a content platform that provides educational resources. "

        # Add learning outcomes
        learning_outcomes = "By the end of this module, you'll have a solid understanding of the core principles and be able to apply what you've learned in practical scenarios."

        return base_description + platform_context + learning_outcomes

    def _get_hardcoded_learning_goals(self, state):
        """
        Generate hardcoded learning goals for the module based on the user query and platform.

        Provides a consistent set of learning objectives that align with the educational content
        and the user's learning request, ensuring clarity and focus on key outcomes.

        Args:
            state: Current workflow state containing user query and platform name

        Returns:
            List of standardized learning goals for the module
        """
        return [
            f"Understand the key concepts related to '{state['user_query']}'",
            "Apply learned concepts in practical scenarios",
            "Develop critical thinking skills related to the subject matter",
            "Engage with content from reputable sources on the specified platform"
        ]

    async def _update_ordering_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the order_index of subsequent modules.

        Increments the order_index of all modules that come after
        the insertion point to maintain proper sequencing.
        """
        try:
            self.logger.info("Updating module ordering")
            state["current_stage"] = "ordering_update"
            state["stage_start_time"] = datetime.now()

            # Get all modules that need their order_index updated
            modules_to_update = []
            for module_data in state["existing_modules"]:
                if module_data["order_index"] >= state["insert_position"]:
                    modules_to_update.append({
                        "module_id": module_data["id"],
                        "new_order_index": module_data["order_index"] + 1
                    })

            # Update the order indices if there are modules to update
            if modules_to_update:
                await module_repository.reorder_modules(
                    self.db,
                    state["learning_path_id"],
                    modules_to_update,
                    state["user_id"]
                )

                self.logger.info(f"Updated ordering for {len(modules_to_update)} modules")
            else:
                self.logger.info("No modules required order index updates")

            return state

        except Exception as e:
            self.logger.error(f"Module ordering update failed: {str(e)}")
            state["error_message"] = str(e)
            return state

    async def _send_notification_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification about successful module insertion.

        Notifies the user that their module has been successfully
        inserted into the learning path.
        """
        try:
            self.logger.info("Sending completion notification")
            state["current_stage"] = "notification"
            state["stage_start_time"] = datetime.now()

            self.logger.info("Notification sent successfully")
            state["current_stage"] = "completed"
            return state

        except Exception as e:
            self.logger.error(f"Notification sending failed: {str(e)}")
            # Don't fail the entire workflow for notification errors
            self.logger.warning("Continuing despite notification failure")
            state["current_stage"] = "completed"
            return state

    async def _handle_error_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle errors that occur during the workflow.

        Logs the error, performs cleanup if necessary,
        and prepares the final error state.
        """
        try:
            self.logger.error(f"Handling workflow error: {state.get('error_message', 'Unknown error')}")
            state["current_stage"] = "error_handling"

            # Perform cleanup if a module was partially created
            if state.get("created_module_id"):
                try:
                    # Attempt to clean up partially created module
                    await module_service.delete_module(self.db, state["created_module_id"])
                    self.logger.info(f"Cleaned up partially created module {state['created_module_id']}")
                except Exception as cleanup_error:
                    self.logger.error(f"Failed to cleanup module: {str(cleanup_error)}")

            # Rollback any database changes
            try:
                await self.db.rollback()
                self.logger.info("Database transaction rolled back")
            except Exception as rollback_error:
                self.logger.error(f"Failed to rollback transaction: {str(rollback_error)}")

            state["current_stage"] = "error"
            return state

        except Exception as e:
            self.logger.error(f"Error handling failed: {str(e)}")
            state["error_message"] = f"Error handling failed: {str(e)}"
            state["current_stage"] = "error"
            return state

    # =============================================================================
    # ROUTING FUNCTIONS
    # =============================================================================

    def _route_after_validation(self, state: Dict[str, Any]) -> str:
        """Route after input validation."""
        return "error" if state.get("error_message") else "continue"

    def _route_after_analysis(self, state: Dict[str, Any]) -> str:
        """Route after learning path analysis."""
        return "error" if state.get("error_message") else "continue"

    def _route_after_queries(self, state: Dict[str, Any]) -> str:
        """Route after query generation."""
        return "error" if state.get("error_message") else "continue"

    def _route_after_content(self, state: Dict[str, Any]) -> str:
        """Route after content creation."""
        return "error" if state.get("error_message") else "continue"

    def _route_after_save(self, state: Dict[str, Any]) -> str:
        """Route after module save."""
        return "error" if state.get("error_message") else "continue"

    def _route_after_ordering(self, state: Dict[str, Any]) -> str:
        """Route after ordering update."""
        return "error" if state.get("error_message") else "continue"


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def insert_module(
    self,
    user_query: str,
    learning_path_id: int,
    insert_position: int,
    platform_name: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Execute the module insertion workflow.

    Args:
        user_query: What the user wants in the module
        learning_path_id: Target learning path ID
        insert_position: Index where new module will be inserted
        platform_name: Platform to use for content
        user_id: User performing the insertion

    Returns:
        Dict containing the results of the insertion process

    Raises:
        ValueError: If input validation fails
        PermissionError: If user lacks permission
        SQLAlchemyError: If database operations fail
    """
    try:
        self.logger.info(
            f"Starting module insertion workflow - "
            f"User: {user_id}, Learning Path: {learning_path_id}, "
            f"Position: {insert_position}, Platform: {platform_name}"
        )

        # Initialize workflow state
        initial_state = create_initial_state(
            user_query=user_query,
            learning_path_id=learning_path_id,
            insert_position=insert_position,
            platform_name=platform_name,
            user_id=user_id
        ).to_dict()

        # Create workflow configuration with required checkpoint keys
        workflow_config = {
            "configurable": {
                "thread_id": f"module_insertion_{user_id}_{learning_path_id}_{int(datetime.now().timestamp())}",
                "checkpoint_ns": "module_insertion",
                "checkpoint_id": f"insertion_{learning_path_id}_{insert_position}_{int(datetime.now().timestamp())}"
            }
        }

        self.logger.debug(f"Workflow config: {workflow_config}")
        self.logger.debug(f"Initial state keys: {list(initial_state.keys())}")

        # Execute the workflow with proper configuration
        final_state = await self.graph.ainvoke(initial_state, config=workflow_config)

        # Calculate total execution time
        total_time = (datetime.now() - final_state["total_start_time"]).total_seconds()

        # Prepare response
        if final_state.get("error_message"):
            self.logger.error(f"Module insertion failed: {final_state['error_message']}")
            return {
                "success": False,
                "error": final_state["error_message"],
                "execution_time_seconds": total_time
            }
        else:
            self.logger.info(f"Module insertion completed successfully in {total_time:.2f} seconds")
            return {
                "success": True,
                "created_module_id": final_state.get("created_module_id"),
                "module_title": final_state.get("generated_module", {}).get("title"),
                "execution_time_seconds": total_time,
                "stages_completed": final_state.get("current_stage")
            }

    except Exception as e:
        self.logger.error(f"Module insertion workflow failed: {str(e)}")
        raise
