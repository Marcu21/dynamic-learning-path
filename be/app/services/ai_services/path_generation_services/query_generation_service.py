"""
AI Services - Query Generation Service
=====================================

This service handles the generation of platform-specific search queries
based on the difficulty levels determined in the blueprint stage.

The query generation service:
1. Analyzes the module difficulty mapping from the blueprint
2. Generates targeted search queries for each difficulty level
3. Creates platform-specific variations for each preferred platform
4. Optimizes queries for content discovery on each platform
5. Stores queries in the state for subsequent content retrieval
"""

import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from openai import AsyncOpenAI

from app.core.logger import get_logger
from app.core.config import settings
from app.schemas.path_generation_schemas.path_generation_state_schema import (
    PathGenerationState,
    StateManager,
    GenerationStage
)
from app.schemas.path_generation_schemas.query_generation_schema import QueryResponse

logger = get_logger(__name__)


class QueryGenerationService:
    """
    Service responsible for generating platform-specific search queries using AI/LLM.

    This service orchestrates the second critical step in learning path generation:
    creating targeted search queries that will be used to find relevant content
    for each difficulty level on each preferred platform.

    Key Responsibilities:
    1. Extract unique difficulty levels from the module difficulty mapping
    2. Generate platform-specific search queries for each difficulty
    3. Optimize queries for each platform's search characteristics
    4. Validate query structure and completeness
    5. Update state with generated queries
    6. Handle retries and error scenarios
    """

    def __init__(self, db_session=None):
        """
        Initialize the query generation service.

        Args:
            db_session: Database session for repository access
        """
        self.logger = get_logger(f"{__name__}.QueryGenerationService")
        self.db = db_session

        # Initialize OpenAI client
        self.llm_client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_url
        )

        # Generation configuration
        self.generation_config = {
            "model": settings.llm_model,
            "max_tokens": 2000,
            "timeout": 30
        }

        # Platform-specific guidelines for query optimization
        self.platform_guidelines = {
            "youtube": {
                "max_length": 100,
                "focus": "video tutorials, educational content",
                "keywords": ["tutorial", "guide", "how to", "explained"],
                "avoid": ["music", "entertainment", "gaming"]
            },
            "spotify": {
                "max_length": 80,
                "focus": "podcasts, audiobooks, educational audio",
                "keywords": ["podcast", "audiobook", "interview", "discussion"],
                "avoid": ["music", "playlist", "album"]
            },
            "google books": {
                "max_length": 120,
                "focus": "educational books, textbooks, reference materials",
                "keywords": ["book", "textbook", "guide", "reference"],
                "avoid": ["fiction", "novel", "entertainment"]
            },
            "coursera": {
                "max_length": 100,
                "focus": "structured courses, professional education",
                "keywords": ["course", "professional", "certificate", "specialization"],
                "avoid": ["audit", "verified", "free"]
            },
            "edx": {
                "max_length": 100,
                "focus": "academic courses, professional education",
                "keywords": ["course", "professional", "certificate", "MicroMasters"],
                "avoid": ["audit", "verified", "free"]
            },
            "udemy": {
                "max_length": 100,
                "focus": "practical courses, hands-on learning, skill development",
                "keywords": ["course", "practical", "hands-on", "complete"],
                "avoid": ["free", "preview", "demo"]
            },
            "pluralsight": {
                "max_length": 90,
                "focus": "technology skills, professional development",
                "keywords": ["path", "skill", "assessment", "hands-on"],
                "avoid": ["trial", "free", "demo"]
            },
            "linkedin_learning": {
                "max_length": 110,
                "focus": "professional skills, career development",
                "keywords": ["course", "skill", "professional", "career"],
                "avoid": ["free", "preview", "intro"]
            },
            "khan_academy": {
                "max_length": 90,
                "focus": "foundational concepts, step-by-step learning",
                "keywords": ["lesson", "exercise", "practice", "basics"],
                "avoid": ["advanced", "professional", "certification"]
            }
        }

        self.logger.info("QueryGenerationService initialized")

    async def generate_queries(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Main entry point for platform query generation.

        This is the LangGraph node function that:
        1. Validates input state from blueprint stage
        2. Extracts unique difficulty levels needed
        3. Determines target platforms from preferred_platforms
        4. Generates platform-specific queries using AI
        5. Validates and structures the query results
        6. Updates state with generated queries
        7. Handles retries and fallback scenarios

        Args:
            state: Current PathGenerationState

        Returns:
            Dict[str, Any]: State updates to apply
        """
        try:
            # Validate prerequisites
            validation_errors = self._validate_query_prerequisites(state)
            if validation_errors:
                raise ValueError(f"Query prerequisites not met: {'; '.join(validation_errors)}")

            self.logger.info(f"Starting query generation for user {state['user_id']}, subject: '{state['subject']}'")

            # Extract difficulty levels from module mapping
            difficulty_levels = self._extract_difficulty_levels(state)

            # Use preferred_platforms directly instead of always fetching from user preferences
            platforms = self._determine_target_platforms(state)

            self.logger.info(f"Generating queries for {len(difficulty_levels)} difficulty levels across {len(platforms)} platforms: {platforms}")

            # Generate queries using AI
            try:
                query_result = await self._generate_queries_with_ai(state, difficulty_levels, platforms)
            except Exception as ai_error:
                self.logger.warning(f"AI query generation failed: {str(ai_error)}")
                # Fallback to template-based queries
                query_result = self._create_fallback_queries(state, difficulty_levels, platforms)

            # Validate final structure
            self._validate_query_structure(
                query_result["platform_queries"],
                difficulty_levels,
                platforms
            )

            # Prepare state updates
            state_updates = {
                "platform_queries": query_result["platform_queries"]
            }

            # Update performance metrics
            if "performance_metrics" not in state:
                state["performance_metrics"] = {}

            state["performance_metrics"].update({
                "query_generation_completed_at": datetime.now().isoformat(),
                "difficulties_processed": len(difficulty_levels),
                "platforms_targeted": len(platforms),
                "total_queries_generated": len(difficulty_levels) * len(platforms)
            })

            # Transition to content pool stage
            if state.get("total_modules", 0) > 1:
                # This is full path generation - transition to content pool stage
                state_manager = StateManager()
                next_stage_updates = state_manager.update_stage(
                    state,
                    GenerationStage.CONTENT_POOL,
                    stage_data={"queries_generated_at": datetime.now()}
                )
                state_updates.update(next_stage_updates)

            self.logger.info(
                f"Query generation completed successfully for {len(difficulty_levels)} "
                f"difficulty levels across {len(platforms)} platforms"
            )

            return state_updates

        except Exception as e:
            self.logger.error(f"Query generation failed: {str(e)}")

            # Update error tracking
            errors = state.get("errors", [])
            errors.append({
                "stage": "query_generation",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

            return {
                "errors": errors,
                "current_stage": "error",
                "error_message": f"Query generation failed: {str(e)}"
            }

    def _determine_target_platforms(self, state: PathGenerationState) -> List[str]:
        """
        Determine which platforms to generate queries for.

        Now properly respects the preferred_platforms in state, whether it's:
        - Single platform (module insertion): ["YouTube"]
        - Multiple platforms (path generation): ["YouTube", "Coursera", "Udemy"]

        Args:
            state: Current PathGenerationState

        Returns:
            List[str]: Target platforms for query generation (normalized to lowercase)
        """
        # First, check if preferred_platforms is explicitly set in state
        if state.get("preferred_platforms"):
            platforms = state["preferred_platforms"]
            # Normalize platform names to lowercase to match our system
            normalized_platforms = [platform.lower() for platform in platforms]
            self.logger.info(f"Using platforms from state (normalized): {normalized_platforms}")
            return normalized_platforms

        # Final fallback: default platforms
        default_platforms = ["youtube"]
        self.logger.warning(f"No preferred platforms found, using defaults: {default_platforms}")
        return default_platforms

    def _validate_query_prerequisites(self, state: PathGenerationState) -> List[str]:
        """
        Validate that all required data for query generation is present.

        Args:
            state: Current PathGenerationState

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []

        # Check required basic fields
        if not state.get("subject"):
            errors.append("Subject missing")

        if not state.get("user_id"):
            errors.append("User ID missing")

        # Check module difficulty mapping
        if not state.get("module_difficulty_map"):
            errors.append("Module difficulty mapping missing from blueprint stage")
        elif not isinstance(state["module_difficulty_map"], dict):
            errors.append("Module difficulty mapping must be a dictionary")
        elif len(state["module_difficulty_map"]) == 0:
            errors.append("Module difficulty mapping cannot be empty")

        # Check that we can determine target platforms somehow
        has_platforms = (
            state.get("preferred_platforms") or
            (self.db and state.get("user_id"))  # Can fetch from user preferences
        )

        if not has_platforms:
            errors.append("No way to determine target platforms (no preferred_platforms in state and no user_id for preferences lookup)")

        return errors

    def _extract_difficulty_levels(self, state: PathGenerationState) -> List[str]:
        """
        Extract unique difficulty levels from the module difficulty mapping.

        Args:
            state: Current PathGenerationState

        Returns:
            List[str]: Sorted list of unique difficulty levels
        """
        difficulty_map = state["module_difficulty_map"]
        unique_difficulties = set(difficulty_map.values())

        # Sort difficulties by complexity (beginner -> expert)
        difficulty_order = ["beginner", "intermediate", "advanced", "expert"]
        sorted_difficulties = [d for d in difficulty_order if d in unique_difficulties]

        self.logger.debug(f"Extracted difficulty levels: {sorted_difficulties}")

        return sorted_difficulties

    async def _generate_queries_with_ai(
            self,
            state: PathGenerationState,
            difficulty_levels: List[str],
            platforms: List[str]
    ) -> Dict[str, Any]:
        """
        Generate platform-specific queries using OpenAI API.

        This method:
        1. Constructs a comprehensive prompt with context
        2. Makes async API call to OpenAI
        3. Parses and validates the response
        4. Returns structured query data

        Args:
            state: Current PathGenerationState
            difficulty_levels: List of difficulty levels to generate queries for
            platforms: List of platforms to generate queries for

        Returns:
            Dict[str, Any]: Query data organized by difficulty and platform
        """
        try:
            # Construct the generation prompt
            prompt = self._build_query_prompt(state, difficulty_levels, platforms)

            self.logger.debug("Making LLM API call for query generation")

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
                    max_completion_tokens=self.generation_config["max_tokens"]
                ),
                timeout=self.generation_config["timeout"]
            )

            # Extract response content
            response_content = response.choices[0].message.content.strip()

            # Clean up response - remove Markdown formatting if present
            if response_content.startswith("```json"):
                response_content = response_content[7:]
            if response_content.endswith("```"):
                response_content = response_content[:-3]
            response_content = response_content.strip()

            # Handle cases where AI might wrap JSON in other text
            if not response_content.startswith("{"):
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
                query_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {str(e)}")
                self.logger.error(f"Problematic content: {response_content[:500]}")
                raise ValueError(f"Invalid JSON response from AI: {str(e)}")

            # Validate response using Pydantic model
            try:
                validated_queries = QueryResponse(**query_data)
            except Exception as e:
                self.logger.error(f"Validation error: {str(e)}")
                self.logger.error(f"Query data: {query_data}")
                raise ValueError(f"AI response validation failed: {str(e)}")

            # Additional validation of query structure
            self._validate_query_structure(
                validated_queries.platform_queries,
                difficulty_levels,
                platforms
            )

            # Convert to state updates
            query_updates = {
                "platform_queries": validated_queries.platform_queries
            }

            self.logger.info(
                f"Queries generated successfully for {len(difficulty_levels)} difficulty levels "
                f"across {len(platforms)} platforms"
            )

            return query_updates

        except asyncio.TimeoutError:
            raise ValueError(f"AI API call timed out after {self.generation_config['timeout']} seconds")
        except Exception as e:
            self.logger.error(f"AI query generation failed: {str(e)}")
            raise

    def _build_query_prompt(
            self,
            state: PathGenerationState,
            difficulty_levels: List[str],
            platforms: List[str]
    ) -> str:
        """
        Build a comprehensive prompt for AI query generation.

        The prompt includes:
        - Subject and learning context
        - Difficulty level specifications
        - Platform-specific guidelines
        - Query optimization requirements
        - Expected output format

        Args:
            state: Current PathGenerationState
            difficulty_levels: List of difficulty levels
            platforms: List of platforms

        Returns:
            str: Formatted prompt for AI generation
        """
        # Build platform guidelines section
        platform_guidelines_text = ""
        for platform in platforms:
            if platform in self.platform_guidelines:
                guidelines = self.platform_guidelines[platform]
                platform_guidelines_text += f"""
{platform.upper()}:
- Focus: {guidelines['focus']}
- Max query length: {guidelines['max_length']} characters
- Recommended keywords: {', '.join(guidelines['keywords'])}
- Avoid: {', '.join(guidelines['avoid'])}
"""

        # Build difficulty specifications
        difficulty_specs = {
            "beginner": "Foundational concepts, basic terminology, introductory tutorials, step-by-step guides",
            "intermediate": "Practical applications, real-world examples, connecting concepts, hands-on projects",
            "advanced": "Complex topics, advanced techniques, specialized knowledge, expert-level content",
            "expert": "Cutting-edge concepts, research-level content, mastery-focused material, innovation"
        }

        difficulty_descriptions = ""
        for level in difficulty_levels:
            if level in difficulty_specs:
                difficulty_descriptions += f"- {level}: {difficulty_specs[level]}\n"

        # Build the comprehensive prompt
        prompt = f"""
PLATFORM-SPECIFIC QUERY GENERATION REQUEST

LEARNING CONTEXT:
- Subject: {state["subject"]}
- Experience Level: {state["experience_level"].value if hasattr(state.get("experience_level"), 'value') else state.get("experience_level", "intermediate")}
- Learning Goals: {state.get("goals", f"Learn {state['subject']}")}
- Path Title: {state.get("path_title", "N/A")}

DIFFICULTY LEVELS TO GENERATE QUERIES FOR:
{difficulty_descriptions}

PLATFORMS TO GENERATE QUERIES FOR:
{', '.join(platforms)}

PLATFORM-SPECIFIC GUIDELINES:
{platform_guidelines_text}

REQUIREMENTS:
1. Generate one targeted search query for each difficulty level on each platform
2. Queries must be optimized for the specific platform's search algorithm and content type
3. Consider the subject "{state["subject"]}" and tailor queries appropriately
4. Ensure queries will find relevant, high-quality educational content
5. Match the difficulty level expectations (beginner content for beginners, etc.)
6. Follow platform-specific guidelines for keywords and length limits
7. Avoid generic queries - make them specific and actionable

QUERY OPTIMIZATION PRINCIPLES:
- Use platform-appropriate terminology and keywords
- Include skill level indicators when relevant
- Consider the platform's content format (video, audio, course, etc.)
- Balance specificity with discoverability
- Include context that helps filter out irrelevant content

RESPONSE FORMAT:
You must respond with a valid JSON object containing exactly these fields:
{{
    "platform_queries": {{
        "difficulty_level_1": {{
            "platform_1": "optimized search query",
            "platform_2": "optimized search query"
        }},
        "difficulty_level_2": {{
            "platform_1": "optimized search query", 
            "platform_2": "optimized search query"
        }}
    }}
}}

EXAMPLE OUTPUT:
{{
    "platform_queries": {{
        "beginner": {{
            "youtube": "Python for beginners tutorial",
            "coursera": "Introduction to Python programming course"
        }},
        "intermediate": {{
            "youtube": "Python development projects tutorial",
            "coursera": "Python data structures course"
        }}
    }}
}}

IMPORTANT: Only generate queries for the exact platforms and difficulty levels specified above. Do not include platforms or difficulty levels that are not in the requirements.

Please generate platform-specific queries following these specifications exactly.
"""

        return prompt.strip()

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt that defines the AI's role for query generation.

        Returns:
            str: System prompt for the AI assistant
        """
        return """
You are an expert search query optimization specialist with deep knowledge of:
- Educational content discovery across multiple platforms
- Search engine optimization and algorithm behavior
- Platform-specific content characteristics and user behavior
- Learning progression and difficulty level mapping
- Educational content quality assessment

Your role is to create highly optimized search queries that:
1. Maximize the discovery of relevant, high-quality educational content
2. Are tailored to each platform's specific search algorithms and content types
3. Accurately target the appropriate difficulty level for learners
4. Use platform-specific terminology and formatting conventions
5. Balance specificity with broad enough appeal to return sufficient results

Key Optimization Principles:
- Understand each platform's content ecosystem and search behavior
- Use appropriate keywords that resonate with content creators on each platform
- Consider the format preferences (video tutorials vs podcasts vs courses)
- Include skill level indicators that help filter content appropriately
- Avoid over-specific queries that might return no results
- Avoid under-specific queries that return too much irrelevant content

Platform Expertise:
- YouTube: Optimize for tutorial discovery, educational channels, and instructional content
- Spotify: Focus on podcast discovery, educational audio, and interview content
- Udemy/Coursera/edX: Target structured course discovery and professional development
- LinkedIn Learning: Emphasize professional skills and career development
- Pluralsight: Focus on technology skills and hands-on learning paths

You must always respond with valid JSON that exactly matches the specified format.
Be precise, strategic, and focused on maximizing educational content discovery.
"""

    def _validate_query_structure(
            self,
            platform_queries: Dict[str, Dict[str, str]],
            expected_difficulties: List[str],
            expected_platforms: List[str]
    ) -> None:
        """
        Validate that the generated query structure matches expectations.

        This ensures:
        1. All expected difficulty levels are present
        2. All expected platforms are present for each difficulty
        3. All queries are non-empty strings
        4. Query lengths are within platform limits

        Args:
            platform_queries: Generated query structure
            expected_difficulties: List of difficulty levels that should be present
            expected_platforms: List of platforms that should be present

        Raises:
            ValueError: If validation fails
        """
        try:
            # Check that all expected difficulty levels are present
            for difficulty in expected_difficulties:
                if difficulty not in platform_queries:
                    raise ValueError(f"Missing queries for difficulty level: {difficulty}")

                # Check that all expected platforms are present for this difficulty
                difficulty_queries = platform_queries[difficulty]
                for platform in expected_platforms:
                    if platform not in difficulty_queries:
                        raise ValueError(
                            f"Missing query for platform '{platform}' at difficulty '{difficulty}'"
                        )

                    # Validate query content
                    query = difficulty_queries[platform]
                    if not isinstance(query, str) or not query.strip():
                        raise ValueError(
                            f"Empty or invalid query for {platform} at {difficulty} level"
                        )

                    # Check query length against platform limits
                    if platform in self.platform_guidelines:
                        max_length = self.platform_guidelines[platform]["max_length"]
                        if len(query) > max_length:
                            self.logger.warning(
                                f"Query for {platform} at {difficulty} level exceeds "
                                f"recommended length ({len(query)} > {max_length}): {query[:50]}..."
                            )

            # Check for unexpected difficulty levels
            unexpected_difficulties = set(platform_queries.keys()) - set(expected_difficulties)
            if unexpected_difficulties:
                self.logger.warning(f"Unexpected difficulty levels in response: {unexpected_difficulties}")

            self.logger.debug("Query structure validation passed")

        except Exception as e:
            self.logger.error(f"Query structure validation failed: {str(e)}")
            raise ValueError(f"Invalid query structure: {str(e)}")

    def _create_fallback_queries(
            self,
            state: PathGenerationState,
            difficulty_levels: List[str],
            platforms: List[str]
    ) -> Dict[str, Any]:
        """
        Create fallback queries when AI generation fails.

        This ensures the system can continue functioning even if external AI fails.

        Args:
            state: Current PathGenerationState
            difficulty_levels: List of difficulty levels
            platforms: List of platforms

        Returns:
            Dict[str, Any]: Fallback query data
        """
        self.logger.info("Creating fallback queries")

        subject = state["subject"]
        platform_queries = {}

        # Simple query templates by difficulty
        query_templates = {
            "beginner": {
                "youtube": f"{subject} tutorial for beginners",
                "spotify": f"learn {subject} podcast beginners",
                "udemy": f"{subject} course for beginners",
                "coursera": f"introduction to {subject}",
                "edx": f"{subject} fundamentals course",
                "pluralsight": f"{subject} getting started",
                "linkedin_learning": f"{subject} basics course",
                "khan_academy": f"{subject} lessons basics"
            },
            "intermediate": {
                "youtube": f"{subject} intermediate tutorial",
                "spotify": f"{subject} podcast intermediate",
                "udemy": f"{subject} practical course",
                "coursera": f"{subject} specialization",
                "edx": f"{subject} professional course",
                "pluralsight": f"{subject} skills path",
                "linkedin_learning": f"{subject} professional skills",
                "khan_academy": f"{subject} practice exercises"
            },
            "advanced": {
                "youtube": f"advanced {subject} tutorial",
                "spotify": f"advanced {subject} podcast",
                "udemy": f"master {subject} course",
                "coursera": f"advanced {subject} specialization",
                "edx": f"{subject} professional certificate",
                "pluralsight": f"advanced {subject} path",
                "linkedin_learning": f"advanced {subject} skills",
                "khan_academy": f"advanced {subject} concepts"
            },
            "expert": {
                "youtube": f"{subject} expert masterclass",
                "spotify": f"{subject} expert interview podcast",
                "udemy": f"{subject} mastery course",
                "coursera": f"{subject} expert specialization",
                "edx": f"{subject} professional certificate advanced",
                "pluralsight": f"{subject} expert skills",
                "linkedin_learning": f"{subject} leadership course",
                "khan_academy": f"{subject} advanced topics"
            }
        }

        # Generate queries for each difficulty and platform
        for difficulty in difficulty_levels:
            platform_queries[difficulty] = {}
            for platform in platforms:
                if difficulty in query_templates and platform in query_templates[difficulty]:
                    platform_queries[difficulty][platform] = query_templates[difficulty][platform]
                else:
                    # Generic fallback
                    platform_queries[difficulty][platform] = f"{subject} {difficulty} level"

        fallback_data = {
            "platform_queries": platform_queries,
            "llm_responses": {
                "query_response": "Fallback queries generated due to AI service unavailability",
                "query_strategy": "Simple template-based queries targeting basic discovery patterns for each platform and difficulty level"
            }
        }

        self.logger.info(
            f"Fallback queries created: {len(difficulty_levels)} difficulties "
            f"x {len(platforms)} platforms = {len(difficulty_levels) * len(platforms)} queries"
        )

        return fallback_data

    def get_generation_config(self) -> Dict[str, Any]:
        """
        Get current generation configuration.

        Returns:
            Dict[str, Any]: Current configuration settings
        """
        return self.generation_config.copy()