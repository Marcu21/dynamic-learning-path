"""
AI Services - Path Blueprint Service
====================================

This module contains the business logic for the first node in the learning path
generation graph. It handles the creation of learning path blueprints using
AI/LLM calls to generate metadata and module structure.

The blueprint service:
1. Analyzes user preferences and requirements
2. Generates path metadata (title, description, estimated_days)
3. Determines optimal module count and difficulty progression
4. Creates module difficulty mapping for subsequent nodes
5. Handles team context and notification preparation
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import AsyncOpenAI

from app.core.logger import get_logger
from app.core.config import settings
from app.models.enums import DifficultyLevel
from app.repositories import team_repository, user_repository, preferences_repository
from app.schemas.core_schemas.learning_path_schema import LearningPathCreate
from app.schemas.core_schemas.preference_schema import PreferencesCreate
from app.schemas.path_generation_schemas.path_generation_state_schema import (
    PathGenerationState,
    StateManager,
    GenerationStage
)
from app.schemas.path_generation_schemas.path_blueprint_schema import BlueprintResponse

logger = get_logger(__name__)


class PathBlueprintService:
    """
    Service responsible for generating learning path blueprints using AI/LLM.

    This service orchestrates the first critical step in learning path generation:
    creating a comprehensive blueprint that guides all subsequent generation steps.
    """

    def __init__(self, db_session=None):
        """
        Initialize the blueprint service.

        Args:
            db_session: Optional database session for team/user lookups
        """
        self.logger = get_logger(f"{__name__}.PathBlueprintService")
        self.state_manager = StateManager()
        self.db = db_session

        # Initialize OpenAI client
        self.llm_client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
        )

        self.generation_config = {
            "model": settings.llm_model,
            "max_tokens": getattr(settings, "blueprint_max_tokens", 1000),
            "timeout": settings.llm_request_timeout,
        }

        self.logger.info("PathBlueprintService initialized")

    async def generate_blueprint(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Main entry point for blueprint generation with database persistence.

        This is the LangGraph node function that:
        1. Validates input state
        2. Prepares team context if applicable
        3. Generates blueprint using AI
        4. Creates preferences and learning path in database
        5. Updates state with results including learning_path_id
        6. Handles errors and retries

        Args:
            state: Current PathGenerationState

        Returns:
            Dict[str, Any]: State updates to apply
        """
        try:
            self.logger.info(
                f"Starting blueprint generation for user {state['user_id']}, "
                f"subject: '{state['subject']}'"
            )

            # Record stage start time
            stage_start_time = datetime.now()

            # Prepare team context if generating for a team
            team_context_updates = {}
            if state.get("team_id"):
                team_context_updates = await self._prepare_team_context(state)

            # Generate the blueprint using AI - this includes ALL validation
            blueprint_result = await self._generate_blueprint_with_ai(state)

            # Only persist to database AFTER all validations pass
            learning_path_id = None
            if self.db:
                try:
                    # Check if learning_path_id already exists (avoid duplicates in retries)
                    existing_learning_path_id = state.get("learning_path_id")
                    if existing_learning_path_id:
                        self.logger.info(f"Using existing learning path ID: {existing_learning_path_id}")
                        learning_path_id = existing_learning_path_id
                    else:
                        # Create new learning path only if blueprint generation was successful
                        learning_path_id = await self._persist_preferences_and_learning_path(
                            state, blueprint_result
                        )
                        self.logger.info(f"Created learning path with ID: {learning_path_id}")

                except Exception as db_error:
                    self.logger.error(f"Database persistence failed: {str(db_error)}")

            # Calculate performance metrics
            generation_time = (datetime.now() - stage_start_time).total_seconds()
            performance_metrics = {
                "blueprint_generation_time_seconds": generation_time,
                "llm_model_used": self.generation_config["model"],
                "generation_timestamp": datetime.now().isoformat(),
                "database_persistence_success": learning_path_id is not None
            }

            # Prepare state updates
            state_updates = {
                **team_context_updates,
                **blueprint_result,
                "performance_metrics": performance_metrics
            }

            # Add learning_path_id to state if persistence was successful
            if learning_path_id:
                state_updates["learning_path_id"] = learning_path_id

            # Transition to next stage
            next_stage_updates = self.state_manager.update_stage(
                state,
                GenerationStage.QUERY,
                stage_data={"blueprint_completed_at": datetime.now()}
            )
            state_updates.update(next_stage_updates)

            self.logger.info(
                f"Blueprint generation completed successfully. "
                f"Generated path: '{blueprint_result.get('path_title')}' "
                f"with {blueprint_result.get('total_modules')} modules"
                f"{f' (Learning Path ID: {learning_path_id})' if learning_path_id else ' (DB persistence failed)'}"
            )

            return state_updates

        except Exception as e:
            self.logger.error(f"Blueprint generation failed: {str(e)}")

            existing_learning_path_id = state.get("learning_path_id")
            if existing_learning_path_id and self.db:
                try:
                    await self._cleanup_failed_learning_path(existing_learning_path_id)
                    self.logger.info(f"Cleaned up failed learning path {existing_learning_path_id}")
                except Exception as cleanup_error:
                    self.logger.error(
                        f"Failed to cleanup learning path {existing_learning_path_id}: {str(cleanup_error)}")

            # Add error to state
            error_updates = self.state_manager.add_error(
                state,
                error_type="blueprint_generation_error",
                message=str(e)
            )

            # Increment retry count
            retry_updates = self.state_manager.increment_retry(state)

            # Combine all updates
            state_updates = {**error_updates, **retry_updates}

            # Check if we should retry or fail
            if self.state_manager.should_retry(state):
                self.logger.info("Will retry blueprint generation.")
                return state_updates
            else:
                self.logger.error("Maximum retries exceeded for blueprint generation")
                return state_updates

    async def _cleanup_failed_learning_path(self, learning_path_id: int) -> None:
        """
        Clean up a learning path that was created but whose blueprint generation failed.

        Args:
            learning_path_id: ID of the learning path to clean up
        """
        try:
            from app.repositories.learning_path_repository import delete_with_cascade

            # Delete the learning path and any associated data
            await delete_with_cascade(self.db, learning_path_id)
            self.logger.info(f"Successfully cleaned up failed learning path {learning_path_id}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup learning path {learning_path_id}: {str(e)}")

    async def _prepare_team_context(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Prepare team context for team-based learning path generation.

        This method gathers team information needed for:
        - Understanding team composition and skills
        - Preparing notification recipients
        - Customizing content for team dynamics

        Args:
            state: Current PathGenerationState

        Returns:
            Dict[str, Any]: Team context updates for state
        """
        try:
            self.logger.info(f"Preparing team context for team {state['team_id']}")

            if not self.db:
                self.logger.warning("No database session available for team context")
                return {}

            team_id = state["team_id"]

            # Get team information
            team = await team_repository.get_by_id(self.db, team_id)
            if not team:
                raise ValueError(f"Team {team_id} not found")

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
                f"Team context prepared: {len(formatted_members)} members, "
                f"team lead: {team.team_lead_id}"
            )

            return team_context

        except Exception as e:
            self.logger.error(f"Failed to prepare team context: {str(e)}")
            # Return empty context rather than failing the entire generation
            return {}

    async def _generate_blueprint_with_ai(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Generate learning path blueprint using OpenAI API.

        This method:
        1. Constructs a comprehensive prompt with user context
        2. Makes async API call to OpenAI
        3. Parses and validates the response
        4. Returns structured blueprint data

        Args:
            state: Current PathGenerationState

        Returns:
            Dict[str, Any]: Blueprint data including title, description, modules, etc.
        """
        try:
            # Construct the generation prompt
            prompt = self._build_blueprint_prompt(state)

            self.logger.debug("Making LLM call for blueprint generation")
            self.logger.debug(f"Using model: {self.generation_config['model']}")
            self.logger.debug(f"Prompt length: {len(prompt)} characters")

            # Make async API call
            response = await asyncio.wait_for(
                self.llm_client.chat.completions.create(
                    model=self.generation_config["model"],
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                ),
                timeout=self.generation_config["timeout"]
            )

            # Extract and parse response content
            response_content = response.choices[0].message.content

            self.logger.debug("Received AI response for blueprint generation")
            self.logger.debug(f"Raw AI response length: {len(response_content) if response_content else 0}")
            self.logger.debug(f"Raw AI response: {response_content[:500]}...")  # Log first 500 chars

            # Check if response is empty or None
            if not response_content or response_content.strip() == "":
                raise ValueError("AI returned empty response")

            # Try to find JSON in the response if it's mixed with other text
            response_content = response_content.strip()

            # If response doesn't start with {, try to extract JSON
            if not response_content.startswith('{'):
                # Look for JSON block in the response
                import re
                json_match = re.search(r'\{.*}', response_content, re.DOTALL)
                if json_match:
                    response_content = json_match.group(0)
                    self.logger.debug(f"Extracted JSON from response: {response_content[:200]}...")
                else:
                    raise ValueError(f"No JSON found in AI response: {response_content[:200]}...")

            self.logger.debug("Received AI response, parsing and validating")

            # Parse JSON response
            try:
                blueprint_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {str(e)}")
                self.logger.error(f"Problematic content: {response_content[:500]}")
                raise ValueError(f"Invalid JSON response from AI: {str(e)}")

            # Validate response using Pydantic model
            try:
                validated_blueprint = BlueprintResponse(**blueprint_data)
            except Exception as e:
                self.logger.error(f"Validation error: {str(e)}")
                self.logger.error(f"Blueprint data: {blueprint_data}")
                raise ValueError(f"AI response validation failed: {str(e)}")

            # Validate difficulty mapping
            self._validate_difficulty_mapping(validated_blueprint.module_difficulty_map)

            # Convert to state updates
            blueprint_updates = {
                "path_title": validated_blueprint.path_title,
                "path_description": validated_blueprint.path_description,
                "estimated_days": validated_blueprint.estimated_days,
                "total_modules": validated_blueprint.total_modules,
                "module_difficulty_map": validated_blueprint.module_difficulty_map,
                "learning_objectives": validated_blueprint.learning_objectives
            }

            self.logger.info(
                f"Blueprint generated successfully: "
                f"'{validated_blueprint.path_title}' with {validated_blueprint.total_modules} modules"
            )

            return blueprint_updates

        except asyncio.TimeoutError:
            raise ValueError(f"AI API call timed out after {self.generation_config['timeout']} seconds")
        except Exception as e:
            self.logger.error(f"AI blueprint generation failed: {str(e)}")
            raise

    def _build_blueprint_prompt(self, state: PathGenerationState) -> str:
        """
        Build a comprehensive prompt for AI blueprint generation.

        The prompt includes:
        - User/team context and requirements
        - Subject and learning goals
        - Experience level and learning preferences
        - Specific format requirements
        - Examples and guidelines

        Args:
            state: Current PathGenerationState

        Returns:
            str: Formatted prompt for AI generation
        """
        # Determine if this is for a team
        is_team_path = state["team_id"] is not None
        team_context = ""

        if is_team_path:
            team_members = state.get("team_members", [])
            # Handle case where team_members might be None
            team_members_count = len(team_members) if team_members is not None else 0
            team_name = state.get("team_name", "Unknown")

            team_context = f"""
TEAM CONTEXT:
- This learning path is being created for a team of {team_members_count} members
- Team name: {team_name}
- Consider collaborative learning opportunities and team-based activities
- Ensure content is suitable for team discussion and knowledge sharing
"""

        # Build the comprehensive prompt
        prompt = f"""
LEARNING PATH BLUEPRINT GENERATION REQUEST

LEARNER PROFILE:
- Subject: {state["subject"]}
- Experience Level: {state["experience_level"].value}
- Daily Study Time: {state["study_time_minutes"]} minutes
- Learning Goals: {state["goals"]}

{team_context}

REQUIREMENT:
Create a comprehensive learning path blueprint for the subject "{state["subject"]}"

BLUEPRINT SPECIFICATIONS:
- Path Title: Create an engaging, clear title (5-255 characters)
- Path Description: Comprehensive overview of what learners will achieve (50-1000 characters)
- Estimated Days: Realistic completion timeline (1-30 days)
- Total Modules: Optimal number of learning modules ({settings.min_number_of_modules}-{settings.max_number_of_modules} modules)
- Module Difficulty Progression: Based on user experience level and goals, with logical progression
- Learning Objectives: 2-5 high-level objectives for the entire path
- You do not need to go through all the difficulty levels, just the ones that are relevant to the user experience and goals (e.g. if the user is advanced, you can skip beginner and intermediate levels or if the user doesn't have high goals, you can skip advanced and expert levels)

DIFFICULTY LEVELS AVAILABLE:
- beginner: Foundational concepts, basic terminology, introductory skills
- intermediate: Building on basics, practical applications, connecting concepts
- advanced: Complex topics, advanced techniques, specialized knowledge
- expert: Cutting-edge concepts, research-level understanding, mastery

MODULE DIFFICULTY MAPPING FORMAT:
The module_difficulty_map should be a dictionary where:
- Keys are module order indices (starting from 1)
- Values are difficulty levels (beginner, intermediate, advanced, expert)
- Example: {{"1": "beginner", "2": "beginner", "3": "intermediate", "4": "advanced"}}

DESIGN PRINCIPLES:
1. Start based on the user's experience level
2. Gradually increase complexity (logical progression)
3. Ensure each module builds on previous knowledge
4. Consider the learner's experience level for appropriate starting point
5. Balance challenge with achievability
6. Include practical applications and real-world examples
7. Design for the specified daily time commitment

RESPONSE FORMAT:
You must respond with a valid JSON object containing exactly these fields:
{{
    "path_title": "string",
    "path_description": "string", 
    "estimated_days": integer,
    "total_modules": integer,
    "module_difficulty_map": {{"1": "difficulty_level", "2": "difficulty_level", ...}},
    "learning_objectives": ["objective1", "objective2", ...]
}}

EXAMPLE INPUT:
{{
    "SUBJECT": "Python Programming",
    "EXPERIENCE_LEVEL": "BEGINNER",
    "DAILY_STUDY_TIME": 60,
    "LEARNING_GOALS": "HIGH"
}}

EXAMPLE OUTPUT:
{{
    "path_title": "Complete Python Programming Mastery",
    "path_description": "Master Python programming from basic syntax to advanced applications including web development, data analysis, and automation. Build real projects and develop professional-level coding skills.",
    "estimated_days": 10,
    "total_modules": 7,
    "module_difficulty_map": {{"1": "beginner", "2": "beginner", "3": "intermediate", "4": "intermediate", "5": "intermediate", "6": "advanced", "7": "advanced"}},
    "learning_objectives": [
        "Master Python syntax and core programming concepts",
        "Build practical applications using Python libraries",
        "Implement data structures and algorithms efficiently",
        "Develop web applications using Python frameworks",
        "Apply Python for data analysis and automation"
    ]
}}

Please generate a learning path blueprint following these specifications exactly.
"""

        return prompt.strip()

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that defines the AI's role and behavior.

        Returns:
            str: System prompt for the AI assistant
        """
        return """
You are an expert learning path architect and instructional designer with deep knowledge of:
- Curriculum development and pedagogical principles
- Adult learning theory and cognitive science
- Technology-enhanced learning platforms
- Skills assessment and competency mapping
- Team-based and collaborative learning

Your role is to create comprehensive, well-structured learning path blueprints that:
1. Follow sound educational principles and learning progressions
2. Are tailored to the learner's experience level and preferences
3. Consider practical constraints like time availability
4. Incorporate modern learning platforms and resources
5. Design for measurable learning outcomes

Key Design Principles:
- Scaffold learning from simple to complex concepts
- Ensure prerequisite knowledge is covered before advanced topics
- Balance theoretical knowledge with practical application
- Consider different learning styles and modalities
- Design for retention and long-term skill development
- Include opportunities for practice and reinforcement

You must always respond with valid JSON that exactly matches the specified format.
Be precise, educational, and focused on creating effective learning experiences.
"""

    def _validate_difficulty_mapping(self, difficulty_map: Dict[int, str]) -> None:
        """
        Validate the module difficulty mapping for consistency and logic.

        This ensures:
        1. All difficulty levels are valid
        2. Module indices are sequential starting from 1
        3. Progression follows logical learning principles

        Args:
            difficulty_map: Dictionary mapping module order to difficulty

        Raises:
            ValueError: If validation fails
        """
        try:
            # Check if difficulty_map is None or empty
            if difficulty_map is None:
                raise ValueError("Module difficulty mapping cannot be None")
            
            if not difficulty_map:
                raise ValueError("Module difficulty mapping cannot be empty")

            # Check that all difficulty values are valid
            valid_difficulties = {d.value for d in DifficultyLevel}
            for order_idx, difficulty in difficulty_map.items():
                if difficulty not in valid_difficulties:
                    raise ValueError(f"Invalid difficulty level '{difficulty}' for module {order_idx}")

            # Check that indices are sequential starting from 1
            expected_indices = set(range(1, len(difficulty_map) + 1))
            actual_indices = set(difficulty_map.keys())

            if actual_indices != expected_indices:
                raise ValueError(
                    f"Module indices must be sequential starting from 1. "
                    f"Expected: {sorted(expected_indices)}, Got: {sorted(actual_indices)}"
                )

            # Validate logical progression (no major difficulty jumps)
            difficulty_levels = ["beginner", "intermediate", "advanced", "expert"]
            difficulty_values = [difficulty_levels.index(difficulty_map[i]) for i in sorted(difficulty_map.keys())]

            # Check for unreasonable difficulty jumps (skipping more than 1 level)
            for i in range(1, len(difficulty_values)):
                jump = difficulty_values[i] - difficulty_values[i - 1]
                if jump > 2:  # Skipping more than 2 levels is unreasonable
                    self.logger.warning(
                        f"Large difficulty jump detected between modules {i} and {i + 1}: "
                        f"{difficulty_levels[difficulty_values[i - 1]]} -> {difficulty_levels[difficulty_values[i]]}"
                    )

            self.logger.debug("Module difficulty mapping validation passed")

        except Exception as e:
            self.logger.error(f"Difficulty mapping validation failed: {str(e)}")
            raise ValueError(f"Invalid module difficulty mapping: {str(e)}")

    def get_generation_config(self) -> Dict[str, Any]:
        """
        Get current generation configuration.

        Returns:
            Dict[str, Any]: Configuration settings for blueprint generation
        """
        return self.generation_config.copy()

    def update_generation_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update generation configuration settings.

        Args:
            config_updates: Dictionary of configuration updates
        """
        self.generation_config.update(config_updates)
        self.logger.info(f"Updated generation config: {config_updates}")

# =============================================================================
# UTILITY FUNCTIONS FOR BLUEPRINT GENERATION
# =============================================================================

    def validate_blueprint_inputs(state: PathGenerationState) -> List[str]:
        """
        Validate that all required inputs are present for blueprint generation.

        Args:
            state: PathGenerationState to validate

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        required_fields = [
            "user_id", "subject", "experience_level", "learning_styles",
            "preferred_platforms", "study_time_minutes", "goals"
        ]

        for field in required_fields:
            if not state.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate field types and values
        if state.get("study_time_minutes") and state["study_time_minutes"] <= 0:
            errors.append("Study time must be greater than 0")

        if state.get("learning_styles") and not isinstance(state["learning_styles"], list):
            errors.append("Learning styles must be a list")

        if state.get("preferred_platforms") and not isinstance(state["preferred_platforms"], list):
            errors.append("Preferred platforms must be a list")

        return errors


    def create_fallback_blueprint(state: PathGenerationState) -> Dict[str, Any]:
        """
        Create a fallback blueprint if AI generation fails completely.

        This ensures the system can continue functioning even if external AI fails.

        Args:
            state: Current PathGenerationState

        Returns:
            Dict[str, Any]: Fallback blueprint data
        """
        logger.info("Creating fallback blueprint")

        # Calculate basic parameters
        total_modules = 5

        # Create simple difficulty progression
        difficulty_map = {}
        for i in range(1, total_modules + 1):
            if i <= total_modules * 0.4:  # First 40% are beginner
                difficulty_map[i] = "beginner"
            elif i <= total_modules * 0.8:  # Next 40% are intermediate
                difficulty_map[i] = "intermediate"
            else:  # Last 20% are advanced
                difficulty_map[i] = "advanced"

        # Estimate completion time
        estimated_days = max(7, min(90, total_modules * 3))  # 3 days per module on average

        fallback_blueprint = {
            "path_title": f"Complete {state['subject']} Learning Path",
            "path_description": f"A comprehensive learning journey covering essential {state['subject']} concepts and skills. Progress from foundational knowledge to practical application through structured modules designed for {state['experience_level'].value} learners.",
            "estimated_days": estimated_days,
            "total_modules": total_modules,
            "module_difficulty_map": difficulty_map,
            "learning_objectives": [
                f"Understand fundamental {state['subject']} concepts",
                f"Apply {state['subject']} knowledge to practical problems",
                f"Develop proficiency in {state['subject']} best practices",
                f"Build confidence in {state['subject']} skills"
            ]
        }

        logger.info(f"Fallback blueprint created: {total_modules} modules over {estimated_days} days")

        return fallback_blueprint

    async def _persist_preferences_and_learning_path(
            self,
            state: PathGenerationState,
            blueprint_result: Dict[str, Any]
    ) -> Optional[int]:
        """
        Create preferences and learning path in database.

        Args:
            state: Current PathGenerationState
            blueprint_result: Blueprint data from AI generation

        Returns:
            Optional[int]: Learning path ID if successful, None if failed
        """
        try:
            self.logger.info("Creating preferences and learning path in database")

            # Step 1: Create or use existing preferences
            preferences_id = state.get("preferences_id")

            if not preferences_id:
                # Create new preferences
                preferences_create_data = PreferencesCreate(
                    subject=state.get("subject"),
                    experience_level=state.get("experience_level"),
                    learning_styles=state.get("learning_styles"),
                    preferred_platforms=state.get("preferred_platforms"),
                    study_time_minutes=state.get("study_time_minutes"),
                    goals=state.get("goals")
                )

                preferences_response = preferences_repository.create_preferences(
                    self.db, preferences_create_data
                )
                preferences_id = preferences_response.id
                self.logger.info(f"Created preferences with ID: {preferences_id}")
            else:
                self.logger.info(f"Using existing preferences ID: {preferences_id}")

            # Step 2: Create learning path
            path_create_data = LearningPathCreate(
                title=blueprint_result["path_title"],
                description=blueprint_result["path_description"],
                estimated_days=blueprint_result["estimated_days"],
                user_id=state.get("user_id"),
                team_id=state.get("team_id"),
                preferences_id=preferences_id
            )

            from app.repositories.learning_path_repository import create_learning_path

            learning_path = create_learning_path(
                self.db, path_create_data
            )

            self.logger.info(
                f"Successfully created learning path {learning_path.id}: "
                f"'{learning_path.title}' for user {state.get('user_id')}"
            )

            return learning_path.id

        except Exception as e:
            self.logger.error(f"Failed to persist preferences and learning path: {str(e)}")
            # Rollback any partial changes
            if self.db:
                self.db.rollback()
            raise  # Re-raise to be handled by calling method
