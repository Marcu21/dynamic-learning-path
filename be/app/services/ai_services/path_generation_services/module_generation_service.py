"""
AI Services - Module Generation Service
=======================================

This module contains the business logic for the fourth node in the learning path
generation graph. It handles the generation of individual learning modules by
creating metadata and selecting the best content from the content pool.

The module generation service:
1. Generates module metadata (title, description, learning_objectives) using AI
2. Ranks and selects the best content from the content pool
3. Ensures no content is reused across modules
4. Updates the current module index and tracks used content
5. Creates comprehensive module specifications
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import AsyncOpenAI

from app.core.logger import get_logger
from app.core.config import settings
from app.core.utils import convert_difficulty_to_enum, get_platform_id, get_learning_style_by_platform_name
from app.repositories import module_repository
from app.schemas.core_schemas.module_schema import ModuleCreate
from app.schemas.path_generation_schemas.path_generation_state_schema import (
    PathGenerationState,
    StateManager,
    GenerationStage
)
from app.schemas.path_generation_schemas.module_generation_schema import ModuleResponse

logger = get_logger(__name__)


class ModuleGenerationService:
    """
    Service responsible for generating individual learning modules using AI/LLM.

    This service orchestrates the fourth critical step in learning path generation:
    creating detailed module specifications by generating metadata and selecting
    the most appropriate content from the available content pool.

    Key Responsibilities:
    1. Generate module metadata using AI (title, description, objectives)
    2. Rank content from content pool based on relevance and quality
    3. Select best content while avoiding reuse
    4. Update module index and track used content
    5. Create comprehensive module specifications
    6. Handle content exhaustion and fallback scenarios
    """

    def __init__(self, db_session=None):
        """
        Initialize the module generation service.

        Args:
            db_session: Optional database session for any lookups
        """
        self.logger = get_logger(f"{__name__}.ModuleGenerationService")
        self.state_manager = StateManager()
        self.db = db_session

        # Initialize OpenAI client
        self.llm_client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url,
        )

        # Configuration for module generation
        self.generation_config = {
            "model": settings.llm_model,
            "max_tokens": getattr(settings, "module_max_tokens", 1000),
            "timeout": settings.llm_request_timeout,
        }

        self.logger.info("ModuleGenerationService initialized")

    # Update the generate_module method in ModuleGenerationService class
    async def generate_module(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Main entry point for module generation with database persistence.

        This is the LangGraph node function that:
        1. Validates prerequisites from content pool stage
        2. Filters out already used content from content pool
        3. Ranks remaining content by relevance and quality
        4. Generates module metadata using AI
        5. Creates module specification and saves to database
        6. Updates state with results including created module
        7. Handles iterative progression through all modules

        Args:
            state: Current PathGenerationState

        Returns:
            Dict[str, Any]: State updates to apply
        """
        try:
            self.logger.info(
                f"Starting module generation for module {state.get('current_module_index', 1)}"
            )

            # Record stage start time
            stage_start_time = datetime.now()

            # Validate prerequisites
            validation_errors = self._validate_module_prerequisites(state)
            if validation_errors:
                raise ValueError(f"Module generation prerequisites not met: {validation_errors}")

            # Get current module context
            current_module_index = state.get("current_module_index", 1)
            total_modules = state.get("total_modules", 0)
            module_difficulty = state["module_difficulty_map"].get(current_module_index)

            self.logger.info(
                f"Generating module {current_module_index}/{total_modules} "
                f"with difficulty: {module_difficulty}"
            )

            # Get available content (filtering out used content)
            available_content = self._get_available_content(state)

            if not available_content:
                # Handle case where no content is available
                return await self._handle_no_content_available(state)

            # Rank content by relevance for this module
            ranked_content = self._rank_content_by_relevance(available_content, state, module_difficulty)

            if not ranked_content:
                # Handle case where no content is available
                return await self._handle_no_content_available(state)

            # Generate module using AI
            module_result = await self._generate_module_with_ai(
                state, ranked_content, current_module_index, module_difficulty
            )

            # Create module specification
            module_spec = self._create_module_specification(
                module_result, current_module_index, module_difficulty, ranked_content
            )

            # Database persistence - Save module to database
            created_module_id = None
            if self.db and state.get("learning_path_id"):
                try:
                    created_module_id = await self._persist_module_to_database(
                        state, module_spec
                    )
                    self.logger.info(f"Created module with ID: {created_module_id}")
                except Exception as db_error:
                    self.logger.error(f"Database persistence failed: {str(db_error)}")
                    # Continue with module generation even if DB persistence fails
                    # This ensures the workflow can continue

            # Update state with new module
            state_updates = self._update_state_with_module(state, module_spec, module_result, created_module_id)

            # Add created module ID to state if persistence was successful
            if created_module_id:
                created_modules = state.get("created_modules")
                if created_modules is None:
                    created_modules = []
                elif not isinstance(created_modules, list):
                    self.logger.warning(f"created_modules is not a list: {type(created_modules)}, creating new list")
                    created_modules = []
                else:
                    created_modules = created_modules.copy()

                created_modules.append(created_module_id)
                state_updates["created_modules"] = created_modules

                self.logger.debug(f"Added module {created_module_id} to created_modules: {created_modules}")

            # Calculate performance metrics
            generation_time = (datetime.now() - stage_start_time).total_seconds()
            performance_metrics = state.get("performance_metrics", {})
            performance_metrics.update({
                f"module_{current_module_index}_generation_time_seconds": generation_time,
                f"module_{current_module_index}_content_pool_size": len(available_content),
                f"module_{current_module_index}_generation_timestamp": datetime.now().isoformat(),
                f"module_{current_module_index}_database_persistence_success": created_module_id is not None
            })
            state_updates["performance_metrics"] = performance_metrics

            # Determine next stage transition
            next_module_index = current_module_index + 1
            if next_module_index <= total_modules:
                # Continue to next module - check if content pool refresh needed
                next_module_difficulty = state["module_difficulty_map"].get(next_module_index)
                if next_module_difficulty != module_difficulty:
                    # Difficulty changes, need new content pool
                    next_stage_updates = self.state_manager.update_stage(
                        state,
                        GenerationStage.CONTENT_POOL,
                        stage_data={
                            "module_completed_at": datetime.now(),
                            "transitioning_to_difficulty": next_module_difficulty
                        }
                    )
                else:
                    # Same difficulty, continue with module generation
                    next_stage_updates = {"current_module_index": next_module_index}
            else:
                # All modules generated, move to finalization
                next_stage_updates = self.state_manager.update_stage(
                    state,
                    GenerationStage.FINALIZATION,
                    stage_data={"all_modules_completed_at": datetime.now()}
                )

            state_updates.update(next_stage_updates)

            self.logger.info(
                f"Module {current_module_index} generation completed successfully: "
                f"'{module_spec['title']}'"
                f"{f' (Module ID: {created_module_id})' if created_module_id else ' (DB persistence failed)'}"
            )

            return state_updates

        except Exception as e:
            self.logger.error(f"Module generation failed: {str(e)}")

            # Add error to state
            error_updates = self.state_manager.add_error(
                state,
                error_type="module_generation_error",
                message=str(e)
            )

            # Increment retry count
            retry_updates = self.state_manager.increment_retry(state)

            # Combine all updates
            state_updates = {**error_updates, **retry_updates}

            # Check if we should retry or fail
            if self.state_manager.should_retry(state):
                self.logger.info(
                    f"Will retry module generation. "
                    f"Attempt {state['retry_count'] + 1}/{state['max_retries']}"
                )
            else:
                self.logger.error(
                    f"Module generation failed after {state['max_retries']} attempts"
                )

            return state_updates

    def _validate_module_prerequisites(self, state: PathGenerationState) -> List[str]:
        """
        Validate that all prerequisites for module generation are met.

        Args:
            state: Current PathGenerationState

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []

        # Check content pool stage completion
        content_pool = state.get("content_pool")
        if content_pool is None:
            errors.append("Content pool is missing from state")
        elif not isinstance(content_pool, list):
            errors.append(f"Content pool is not a list, got type: {type(content_pool)}")
        elif len(content_pool) == 0:
            errors.append("Content pool is empty")

        # Check module difficulty mapping
        module_difficulty_map = state.get("module_difficulty_map")
        if not module_difficulty_map:
            errors.append("Module difficulty map missing from blueprint stage")

        # Check current module index
        current_module_index = state.get("current_module_index")
        if current_module_index is None:
            errors.append("Current module index is missing")
        else:
            total_modules = state.get("total_modules", 0)
            if current_module_index > total_modules:
                errors.append(f"Current module index ({current_module_index}) exceeds total modules ({total_modules})")

        # Check subject
        subject = state.get("subject")
        if not subject:
            errors.append("Subject is missing from state")

        return errors

    def _get_current_module_difficulty(self, state: PathGenerationState) -> str:
        """
        Get the difficulty level for the current module.

        Args:
            state: Current PathGenerationState

        Returns:
            str: Difficulty level for current module
        """
        current_module_index = state["current_module_index"]
        module_difficulty_map = state["module_difficulty_map"]

        difficulty = module_difficulty_map.get(current_module_index)

        if not difficulty:
            # Fallback to intermediate if not found
            difficulty = "intermediate"
            self.logger.warning(
                f"No difficulty found for module {current_module_index}, using fallback: {difficulty}"
            )

        return difficulty

    def _get_available_content(self, state: PathGenerationState) -> List[Dict[str, Any]]:
        """
        Get available content from content pool (excluding already used content).

        Args:
            state: Current PathGenerationState

        Returns:
            List[Dict[str, Any]]: Available content pool (unused content)
        """
        # Safely get content pool with null check
        content_pool = state.get("content_pool")
        if content_pool is None:
            self.logger.error("Content pool is None in state")
            return []

        if not isinstance(content_pool, list):
            self.logger.error(f"Content pool is not a list, got type: {type(content_pool)}")
            return []

        used_content_links = set(state.get("used_content_links", []))

        # Filter out used content
        available_content = []
        for content_item in content_pool:
            if content_item is None:
                self.logger.warning("Found None content item in content pool")
                continue

            content_link = content_item.get("link", "")
            if content_link not in used_content_links:
                available_content.append(content_item)

        self.logger.debug(
            f"Available content: {len(available_content)} items "
            f"(filtered from {len(content_pool)} total, {len(used_content_links)} used)"
        )

        return available_content

    def _rank_content_by_relevance(
            self,
            content_pool: List[Dict[str, Any]],
            state: PathGenerationState,
            module_difficulty: str
    ) -> List[Dict[str, Any]]:
        """
        Rank content by relevance to the current module requirements.

        Args:
            content_pool: Available content to rank
            state: Current PathGenerationState
            module_difficulty: Difficulty level for current module

        Returns:
            List[Dict[str, Any]]: Content ranked by relevance (the best first)
        """
        if not content_pool:
            self.logger.debug("Content pool is empty, returning empty list")
            return []

        self.logger.debug(f"Content pool type: {type(state.get('content_pool'))}")
        self.logger.debug(f"Content pool contents: {state.get('content_pool')[:3] if state.get('content_pool') else 'None'}")

        # Safely get subject with null checks
        subject = state.get("subject", "")
        if subject is None:
            subject = ""
        subject = subject.lower()

        current_module_index = state.get("current_module_index", 1)

        def calculate_relevance_score(content_item: Dict[str, Any]) -> float:
            """Calculate relevance score for content item."""
            if content_item is None:
                return 0.0

            score = 0.0

            # Safely get fields with null checks
            title = content_item.get("title")
            title = title.lower() if title is not None else ""

            description = content_item.get("description")
            description = description.lower() if description is not None else ""

            platform = content_item.get("platform")
            platform = platform.lower() if platform is not None else ""

            # Subject relevance (high weight)
            if subject and subject in title:
                score += 5.0
            elif subject and subject in description:
                score += 3.0

            # Difficulty relevance
            if module_difficulty:
                difficulty_lower = module_difficulty.lower()
                if difficulty_lower in title:
                    score += 3.0
                elif difficulty_lower in description:
                    score += 2.0

            # Platform preferences (educational platforms score higher)
            platform_scores = {
                "youtube": 4.0,
                "semantic scholar": 3.5,
                "google books": 3.5,
                "spotify": 3.0,
                "fallback": 0.0
            }
            score += platform_scores.get(platform, 2.0)

            # Content quality indicators
            if description and len(description) > 100:
                score += 1.0

            authors = content_item.get("authors")
            if authors and len(authors) > 0:
                score += 0.5

            # Duration preferences (prefer moderate durations)
            duration = content_item.get("duration")
            if duration:
                if isinstance(duration, dict):
                    duration_mins = duration.get("duration_minutes", 0)
                else:
                    duration_mins = duration

                if 15 <= duration_mins <= 90:  # Prefer 15-90 minute content
                    score += 1.5
                elif duration_mins > 180:  # Penalize very long content
                    score -= 1.0

            # Engagement metrics (if available)
            view_count = content_item.get("view_count")
            if view_count and view_count > 5000:
                score += 1.0

            like_count = content_item.get("like_count")
            if like_count and like_count > 100:
                score += 0.5

            # Citation count for academic content
            ratings_count = content_item.get("ratings_count")
            if ratings_count and ratings_count > 10:
                score += 0.8

            return score

        # Filter out None items before sorting
        valid_content = [item for item in content_pool if item is not None]

        # Sort by relevance score (descending)
        try:
            ranked_content = sorted(
                valid_content,
                key=calculate_relevance_score,
                reverse=True
            )
        except Exception as e:
            self.logger.error(f"Error ranking content: {str(e)}")
            return valid_content  # Return unranked but valid content

        self.logger.debug(
            f"Ranked {len(ranked_content)} content items by relevance for module {current_module_index}"
        )

        return ranked_content

    async def _generate_module_with_ai(
            self,
            state: PathGenerationState,
            ranked_content: List[Dict[str, Any]],
            module_index: int,
            module_difficulty: str
    ) -> Dict[str, Any]:
        """
        Generate module metadata and select content using OpenAI API.

        This method:
        1. Prepares top-ranked content for AI consideration
        2. Makes async API call to generate module metadata
        3. Parses and validates the response
        4. Returns module data with selected content

        Args:
            state: Current PathGenerationState
            ranked_content: Content ranked by relevance
            module_index: Current module index
            module_difficulty: Module difficulty level

        Returns:
            Dict[str, Any]: Generated module data including selected content
        """
        try:
            # Prepare content for AI (top 5 most relevant items)
            top_content = ranked_content[:5]

            # Build generation prompt
            prompt = self._build_module_prompt(state, top_content, module_index, module_difficulty)

            self.logger.debug("Making LLM call for module generation")

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
                    ]
                ),
                timeout=self.generation_config["timeout"]
            )

            # Extract and parse response content
            response_content = response.choices[0].message.content

            self.logger.debug("Received AI response for module generation")
            self.logger.debug(f"Raw AI response length: {len(response_content) if response_content else 0}")
            self.logger.debug(f"Raw AI response: {response_content[:500]}...")

            # Check if response is empty or None
            if not response_content or response_content.strip() == "":
                raise ValueError("AI returned empty response")

            # Handle Markdown code blocks and extract JSON
            response_content = response_content.strip()

            # Remove Markdown code blocks if present
            if response_content.startswith('```'):
                # Find the start of JSON (after ```json or ```)
                lines = response_content.split('\n')
                start_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('```'):
                        start_index = i + 1
                        break

                # Find the end of JSON (before closing ```)
                end_index = len(lines)
                for i in range(start_index, len(lines)):
                    if lines[i].strip() == '```':
                        end_index = i
                        break

                # Extract JSON content
                json_lines = lines[start_index:end_index]
                response_content = '\n'.join(json_lines).strip()
                self.logger.debug(f"Extracted JSON from markdown: {response_content[:200]}...")

            # If response still doesn't start with {, try regex extraction
            if not response_content.startswith('{'):
                import re
                json_match = re.search(r'\{.*}', response_content, re.DOTALL)
                if json_match:
                    response_content = json_match.group(0)
                    self.logger.debug(f"Extracted JSON with regex: {response_content[:200]}...")
                else:
                    raise ValueError(f"No JSON found in AI response: {response_content[:200]}...")

            self.logger.debug("Received AI response, parsing and validating")

            # Parse JSON response
            try:
                module_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {str(e)}")
                self.logger.error(f"Problematic content: {response_content[:500]}")
                raise ValueError(f"Invalid JSON response from AI: {str(e)}")

            # Validate response using Pydantic model
            try:
                validated_module = ModuleResponse(**module_data)
            except Exception as e:
                self.logger.error(f"Validation error: {str(e)}")
                self.logger.error(f"Module data: {module_data}")
                raise ValueError(f"AI response validation failed: {str(e)}")

            # Validate selected content index
            if validated_module.selected_content_index >= len(top_content):
                raise ValueError(f"Selected content index {validated_module.selected_content_index} out of range")

            # Get selected content
            selected_content = top_content[validated_module.selected_content_index]

            # Create module specification
            module_spec = {
                "module_title": validated_module.module_title,
                "module_description": validated_module.module_description,
                "learning_objectives": validated_module.learning_objectives,
                "selected_content": selected_content,
                "content_url": selected_content.get("url", ""),
                "platform": selected_content.get("platform", ""),
                "duration": selected_content.get("duration", 0),
                "module_index": module_index,
                "difficulty": module_difficulty
            }

            self.logger.info(
                f"Module {module_index} generated successfully: "
                f"'{validated_module.module_title}' using content from {selected_content.get('platform', 'unknown')}"
            )

            return module_spec

        except asyncio.TimeoutError:
            raise ValueError(f"AI API call timed out after {self.generation_config['timeout']} seconds")
        except Exception as e:
            self.logger.error(f"AI module generation failed: {str(e)}")
            raise

    def _build_module_prompt(
            self,
            state: PathGenerationState,
            content_options: List[Dict[str, Any]],
            module_index: int,
            module_difficulty: str
    ) -> str:
        """
        Build a comprehensive prompt for AI module generation.

        Args:
            state: Current PathGenerationState
            content_options: Top content options to choose from
            module_index: Current module index
            module_difficulty: Module difficulty level

        Returns:
            str: Formatted prompt for AI generation
        """
        # Format content options for the prompt
        content_descriptions = []
        for i, content in enumerate(content_options):
            content_desc = f"""
Content Option {i}:
- Title: {content.get('title', 'N/A')}
- Platform: {content.get('platform', 'N/A')}
- Description: {content.get('description', 'No description available')[:200]}...
- Duration: {content.get('duration', 'N/A')}
- Authors: {', '.join(content.get('authors', [])) if content.get('authors') else 'N/A'}
"""
            content_descriptions.append(content_desc)

        content_options_text = "\n".join(content_descriptions)

        # Build the comprehensive prompt
        prompt = f"""
LEARNING MODULE GENERATION REQUEST

LEARNING PATH CONTEXT:
- Path Title: {state["path_title"]}
- Subject: {state["subject"]}
- Overall Learning Goals: {state["goals"]}
- Total Modules in Path: {state["total_modules"]}

CURRENT MODULE CONTEXT:
- Module Number: {module_index} of {state["total_modules"]}
- Module Difficulty: {module_difficulty}
- Learner Experience Level: {state["experience_level"].value}

AVAILABLE CONTENT OPTIONS:
{content_options_text}

REQUIREMENTS:
1. Create module metadata that fits logically into the overall learning path progression
2. Ensure the module difficulty matches the specified level: {module_difficulty}
3. Select the most appropriate content from the options provided
4. Create specific, measurable learning objectives
5. Ensure the module builds appropriately on previous modules

MODULE GENERATION GUIDELINES:
- Module Title: Clear, engaging, and descriptive (5-200 characters)
- Module Description: Comprehensive overview of what learners will achieve (50-1000 characters)
- Learning Objectives: 2-5 specific, measurable objectives using action verbs
- Content Selection: Choose content that best matches the module requirements
- Consider content quality, relevance, platform credibility, and duration

DIFFICULTY LEVEL EXPECTATIONS:
- beginner: Basic concepts, foundational knowledge, step-by-step guidance
- intermediate: Practical applications, connecting concepts, hands-on experience
- advanced: Complex topics, specialized knowledge, expert-level understanding
- expert: Cutting-edge concepts, research-level content, mastery-focused

RESPONSE FORMAT:
You must respond with a valid JSON object containing exactly these fields:
{{
    "module_title": "string",
    "module_description": "string",
    "learning_objectives": ["objective1", "objective2", "objective3"],
    "selected_content_index": integer
}}

EXAMPLE OUTPUT:
{{
    "module_title": "Introduction to Python Variables and Data Types",
    "module_description": "Learn the fundamental building blocks of Python programming by mastering variables and basic data types. This module covers variable declaration, naming conventions, and working with strings, numbers, and booleans through practical examples and exercises.",
    "learning_objectives": [
        "Declare and initialize variables using proper Python syntax",
        "Identify and work with basic data types: strings, integers, floats, and booleans",
        "Apply Python naming conventions and best practices for variables",
        "Perform basic operations and type conversions between different data types"
    ],
    "selected_content_index": 2
}}

Please generate a module that fits perfectly into the learning path progression and selects the most appropriate content.
"""

        return prompt.strip()

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that defines the AI's role for module generation.

        Returns:
            str: System prompt for the AI assistant
        """
        return """
You are an expert instructional designer and curriculum developer with deep expertise in:
- Learning path design and module sequencing
- Pedagogical best practices and learning theory
- Content evaluation and selection criteria
- Learning objective development and assessment
- Educational content curation across multiple platforms

Your role is to create well-structured learning modules that:
1. Fit logically into the overall learning path progression
2. Match the specified difficulty level and learner needs
3. Select the most appropriate content from available options
4. Include clear, measurable learning objectives
5. Provide comprehensive yet focused learning experiences

Key Design Principles:
- Ensure proper learning progression and scaffolding
- Select content based on quality, relevance, and pedagogical value
- Create specific, actionable learning objectives using Bloom's taxonomy
- Consider different learning styles and modalities
- Balance theoretical knowledge with practical application
- Maintain consistency with the overall path theme and goals

Content Selection Criteria:
- Relevance to the module topic and difficulty level
- Content quality and credibility of the source
- Appropriate duration and engagement level
- Clear explanations and pedagogical structure
- Availability and accessibility of the content

You must always respond with valid JSON that exactly matches the specified format.
Be precise, educational, and focused on creating effective learning experiences.
"""

    def _create_module_specification(
            self,
            module_result: Dict[str, Any],
            module_index: int,
            module_difficulty: str,
            available_content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a comprehensive module specification from AI results.

        Args:
            module_result: AI-generated module data
            module_index: Module order index
            module_difficulty: Module difficulty level
            available_content: Available content pool

        Returns:
            Dict[str, Any]: Complete module specification
        """
        selected_content = module_result["selected_content"]

        # Extract duration from selected content
        duration = selected_content.get("duration", 0)
        if isinstance(duration, dict):
            duration_mins = duration.get("duration_minutes", 0)
        else:
            duration_mins = duration

        # Get platform name
        platform = selected_content.get("platform", "")

        # Get learning style based on platform
        learning_style = get_learning_style_by_platform_name(platform)

        module_spec = {
            "title": module_result["module_title"],
            "description": module_result["module_description"],
            "learning_objectives": module_result["learning_objectives"],
            "order_index": module_index,
            "difficulty": module_difficulty,
            "duration": duration_mins,
            "content_url": selected_content.get("link", ""),
            "content_title": selected_content.get("title", ""),
            "content_description": selected_content.get("description", ""),
            "platform": platform,
            "learning_style": learning_style,
            "content_authors": selected_content.get("authors", []),
            "created_at": datetime.now().isoformat()
        }

        # Add platform-specific metadata
        if selected_content.get("view_count"):
            module_spec["view_count"] = selected_content["view_count"]

        if selected_content.get("like_count"):
            module_spec["like_count"] = selected_content["like_count"]

        if selected_content.get("ratings_count"):
            module_spec["citation_count"] = selected_content["ratings_count"]

        return module_spec

    def _update_state_with_module(
            self,
            state: PathGenerationState,
            module_spec: Dict[str, Any],
            module_result: Dict[str, Any],
            created_module_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update state with the newly generated module.

        Args:
            state: Current PathGenerationState
            module_spec: Complete module specification
            module_result: AI generation results

        Returns:
            Dict[str, Any]: State updates to apply
        """
        # Inject module_id into spec if available
        module_spec["module_id"] = created_module_id

        # Update modules list
        modules_spec = state.get("modules_spec", []).copy()
        modules_spec.append(module_spec)

        # Update used content links
        used_content_links = state.get("used_content_links", []).copy()
        selected_content_link = module_result["selected_content"].get("link", "")
        if selected_content_link and selected_content_link not in used_content_links:
            used_content_links.append(selected_content_link)

        # Increment module index
        current_module_index = state.get("current_module_index", 1)
        new_module_index = current_module_index + 1

        state_updates = {
            "modules_spec": modules_spec,
            "used_content_links": used_content_links,
            "current_module_index": new_module_index
        }

        self.logger.debug(
            f"Updated state: {len(modules_spec)} modules, "
            f"{len(used_content_links)} used content items, "
            f"next module index: {new_module_index}"
        )

        return state_updates

    async def _handle_no_content_available(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Handle the case where no content is available for module generation.

        This could happen if all content has been used or content pool is empty.

        Args:
            state: Current PathGenerationState

        Returns:
            Dict[str, Any]: State updates to apply
        """
        current_module_index = state.get("current_module_index", 1)

        self.logger.warning(f"No content available for module {current_module_index}")

        # Check if we can request a new content pool
        current_difficulty = self._get_current_module_difficulty(state)

        # Add warning to state
        warning_updates = self.state_manager.add_warning(
            state,
            warning_type="no_content_available",
            message=f"No content available for module {current_module_index} at {current_difficulty} difficulty"
        )

        # Transition back to content pool stage to get fresh content
        next_stage_updates = self.state_manager.update_stage(
            state,
            GenerationStage.CONTENT_POOL,
            stage_data={
                "content_exhausted_at": datetime.now(),
                "requesting_fresh_content": True
            }
        )

        state_updates = {**warning_updates, **next_stage_updates}

        return state_updates

    def get_generation_config(self) -> Dict[str, Any]:
        """
        Get current generation configuration.

        Returns:
            Dict[str, Any]: Configuration settings for module generation
        """
        return self.generation_config.copy()

    def update_generation_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update generation configuration settings.

        Args:
            config_updates: Dictionary of configuration updates
        """
        self.generation_config.update(config_updates)
        self.logger.info(f"Updated module generation config: {config_updates}")


    async def _persist_module_to_database(
            self,
            state: PathGenerationState,
            module_spec: Dict[str, Any]
    ) -> Optional[int]:
        """
        Save the generated module to the database.

        Args:
            state: Current PathGenerationState
            module_spec: Module specification from AI generation

        Returns:
            Optional[int]: Module ID if successful, None if failed
        """
        try:
            self.logger.info("Creating module in database")

            # Get learning path ID from state
            learning_path_id = state.get("learning_path_id")
            if not learning_path_id:
                raise ValueError("No learning_path_id found in state")

            # Convert difficulty string to enum
            difficulty_enum = convert_difficulty_to_enum(module_spec.get("difficulty"))

            # Get platform ID
            platform_id = get_platform_id(module_spec["platform"], self.db)
            if not platform_id:
                raise ValueError(f"Platform '{module_spec['platform']}' not found")

            # Get learning style based on platform
            learning_style = [get_learning_style_by_platform_name(module_spec["platform"])]

            # Create ModuleCreate schema
            module_create_data = ModuleCreate(
                learning_path_id=learning_path_id,
                platform_id=platform_id,
                title=module_spec["title"],
                description=module_spec["description"],
                duration=module_spec["duration"],
                order_index=module_spec["order_index"],
                content_url=module_spec["content_url"],
                difficulty=difficulty_enum,  # Now properly converted to enum
                learning_style=learning_style,
                learning_objectives=module_spec.get("learning_objectives", [])
            )

            # Create module using service layer
            created_module = module_repository.create_module(self.db, module_create_data)

            self.logger.info(
                f"Successfully created module {created_module.id}: "
                f"'{created_module.title}' for learning path {learning_path_id}"
            )

            return created_module.id

        except Exception as e:
            self.logger.error(f"Failed to persist module to database: {str(e)}")
            # Rollback any partial changes
            if self.db:
                self.db.rollback()
            raise  # Re-raise to be handled by calling method
