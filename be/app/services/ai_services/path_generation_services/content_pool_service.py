"""
AI Services - Content Pool Service
==================================

This module contains the business logic for the third node in the learning path
generation graph. It handles the creation of content pools by fetching content
from various platforms using the generated platform-specific queries.

The content pool service:
1. Determines when a new content pool is needed
2. Fetches content from all supported platforms using platform queries
3. Creates a unified content pool from all platform results
4. Manages content pool state transitions
5. Handles platform API failures gracefully
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime

from app.core.logger import get_logger
from app.core.config import settings
from app.schemas.path_generation_schemas.path_generation_state_schema import (
    PathGenerationState,
    StateManager,
    GenerationStage
)
from app.services.integrations.google_books_service import search_google_books
from app.services.integrations.youtube_service import search_youtube_videos
from app.services.integrations.spotify_service import search_spotify_audiobooks
from app.services.integrations.research_papers_service import search_semantic_scholar

logger = get_logger(__name__)

# Maximum number of results to fetch per platform
MAX_RESULTS = settings.max_number_of_modules


class ContentPoolService:
    """
    Service responsible for creating comprehensive content pools from all platforms.

    This service orchestrates the third critical step in learning path generation:
    fetching and aggregating content from multiple educational platforms to create
    a rich pool of resources for module generation.

    Key Responsibilities:
    1. Determine when a new content pool is needed
    2. Fetch content from supported platforms using generated queries
    3. Create unified content pool from all platform results
    4. Handle platform failures gracefully
    5. Update state with content pool results
    6. Manage content pool lifecycle and transitions
    """

    def __init__(self, db_session=None):
        """
        Initialize the content pool service.

        Args:
            db_session: Optional database session for any lookups
        """
        self.logger = get_logger(f"{__name__}.ContentPoolService")
        self.state_manager = StateManager()
        self.db = db_session

        # Platform name mapping (query generation service -> platform services)
        self.platform_mapping = {
            'youtube': 'YouTube',
            'spotify': 'Spotify',
            'google books': 'Google Books',
            'research papers': 'Semantic Scholar',
            'semantic scholar': 'Semantic Scholar',
            'codeforces': 'Codeforces',
        }

        # Supported platforms (platforms we can actually fetch content from)
        self.supported_platforms = [
            "youtube", "spotify", "google books", "semantic scholar", "research papers", 'codeforces'
        ]

        self.logger.info("ContentPoolService initialized")

    async def create_content_pool(self, state: PathGenerationState) -> Dict[str, Any]:
        """
        Main entry point for content pool creation.

        This is the LangGraph node function that:
        1. Determines the current difficulty level for content generation
        2. Checks if a new content pool is needed
        3. Fetches content from all platforms for the current difficulty
        4. Creates unified content pool
        5. Updates state with results
        6. Handles errors and retries

        Args:
            state: Current PathGenerationState

        Returns:
            Dict[str, Any]: State updates to apply
        """
        try:
            self.logger.info(
                f"Starting content pool creation for user {state['user_id']}, "
                f"current module index: {state.get('current_module_index', 1)}"
            )

            # Validate prerequisites
            validation_errors = self._validate_content_pool_prerequisites(state)
            if validation_errors:
                raise ValueError(f"Content pool prerequisites not met: {'; '.join(validation_errors)}")

            # Record stage start time
            stage_start_time = datetime.now()

            # Determine current difficulty for content generation
            current_difficulty = self._determine_current_difficulty(state)

            # Check if we need to generate a new content pool
            needs_new_pool = self._needs_new_content_pool(state, current_difficulty)

            if not needs_new_pool:
                self.logger.info("Content pool is still valid, skipping content generation")
                # Move to module generation stage
                next_stage_updates = self.state_manager.update_stage(
                    state,
                    GenerationStage.MODULES,
                    stage_data={"content_pool_reused_at": datetime.now()}
                )
                return next_stage_updates

            self.logger.info(f"Creating new content pool for difficulty: {current_difficulty}")

            # Get platform queries for current difficulty
            platform_queries = state["platform_queries"][current_difficulty]

            preferred_platforms = state.get("preferred_platforms", [])
            preferred_platforms_lower = [p.lower() for p in preferred_platforms]

            # Filter platform queries to only include preferred platforms
            filtered_platform_queries = {}
            for platform, query in platform_queries.items():
                platform_lower = platform.lower()
                if platform_lower in preferred_platforms_lower:
                    filtered_platform_queries[platform] = query
                    self.logger.debug(f"Including {platform} (user preference): {query}")
                else:
                    self.logger.debug(f"Skipping {platform} (not in user preferences: {preferred_platforms})")

            if not filtered_platform_queries:
                self.logger.warning(
                    f"No platform queries found for user's preferred platforms: {preferred_platforms}. "
                    f"Available platforms in queries: {list(platform_queries.keys())}"
                )
                # Fallback: use all available queries with warning
                filtered_platform_queries = platform_queries
                self.logger.warning("Using all available platforms as fallback")

            self.logger.info(
                f"Creating content pool using {len(filtered_platform_queries)} preferred platforms: "
                f"{list(filtered_platform_queries.keys())}"
            )

            # Create comprehensive content pool using only preferred platforms
            content_pool = await self._create_comprehensive_content_pool(filtered_platform_queries)

            # Calculate performance metrics
            generation_time = (datetime.now() - stage_start_time).total_seconds()
            performance_metrics = state.get("performance_metrics", {})
            performance_metrics.update({
                "content_pool_generation_time_seconds": generation_time,
                "content_items_fetched": len(content_pool),
                "platforms_queried": len(filtered_platform_queries),  # Updated to reflect filtered count
                "platforms_used": list(filtered_platform_queries.keys()),  # Show which platforms were used
                "platforms_skipped": [p for p in platform_queries.keys() if p not in filtered_platform_queries],
                "current_difficulty": current_difficulty,
                "content_pool_generation_timestamp": datetime.now().isoformat()
            })

            # Prepare state updates
            state_updates = {
                "content_pool": content_pool,
                "current_difficulty": current_difficulty,
                "performance_metrics": performance_metrics
            }

            # Transition to module generation stage
            next_stage_updates = self.state_manager.update_stage(
                state,
                GenerationStage.MODULES,
                stage_data={"content_pool_created_at": datetime.now()}
            )
            state_updates.update(next_stage_updates)

            self.logger.info(
                f"Content pool creation completed successfully. "
                f"Generated {len(content_pool)} content items for difficulty '{current_difficulty}' "
                f"from {len(filtered_platform_queries)} preferred platforms"
            )

            return state_updates

        except Exception as e:
            self.logger.error(f"Content pool creation failed: {str(e)}")

            # Add error to state
            error_updates = self.state_manager.add_error(
                state,
                error_type="content_pool_creation_error",
                message=str(e)
            )

            # Increment retry count
            retry_updates = self.state_manager.increment_retry(state)

            # Combine all updates
            state_updates = {**error_updates, **retry_updates}

            # Check if we should retry or fail
            if self.state_manager.should_retry(state):
                self.logger.info(
                    f"Will retry content pool creation. "
                    f"Attempt {state['retry_count'] + 1}/{state['max_retries']}"
                )
            else:
                self.logger.error(
                    f"Content pool creation failed after {state['max_retries']} attempts"
                )

            return state_updates

    def _validate_content_pool_prerequisites(self, state: PathGenerationState) -> List[str]:
        """
        Validate that all required data for content pool creation is present.

        Args:
            state: Current PathGenerationState

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []

        # Check query stage completion
        if GenerationStage.QUERY not in state.get("stages_completed", []):
            errors.append("Query stage not completed")

        # Check required query outputs
        if not state.get("platform_queries"):
            errors.append("Platform queries missing")
        elif not isinstance(state["platform_queries"], dict):
            errors.append("Platform queries must be a dictionary")

        # Check module difficulty mapping
        if not state.get("module_difficulty_map"):
            errors.append("Module difficulty mapping missing")

        # Validate preferred platforms
        if not state.get("preferred_platforms"):
            errors.append("Preferred platforms missing from user preferences")
        elif not isinstance(state["preferred_platforms"], list):
            errors.append("Preferred platforms must be a list")
        elif len(state["preferred_platforms"]) == 0:
            errors.append("At least one preferred platform must be specified")

        # Check current module index
        current_module_index = state.get("current_module_index")
        if current_module_index is None or current_module_index < 1:
            errors.append("Invalid current module index")

        total_modules = state.get("total_modules")
        if total_modules and current_module_index > total_modules:
            errors.append("Current module index exceeds total modules")

        return errors

    def _determine_current_difficulty(self, state: PathGenerationState) -> str:
        """
        Determine the current difficulty level based on current module index.

        Args:
            state: Current PathGenerationState

        Returns:
            str: Current difficulty level
        """
        current_module_index = state["current_module_index"]
        module_difficulty_map = state["module_difficulty_map"]

        # Get difficulty for current module
        current_difficulty = module_difficulty_map.get(current_module_index)

        if not current_difficulty:
            # Fallback: use first available difficulty
            available_difficulties = list(module_difficulty_map.values())
            current_difficulty = available_difficulties[0] if available_difficulties else "intermediate"

            self.logger.warning(
                f"No difficulty found for module {current_module_index}, "
                f"using fallback: {current_difficulty}"
            )

        self.logger.debug(f"Current difficulty for module {current_module_index}: {current_difficulty}")

        return current_difficulty

    def _needs_new_content_pool(self, state: PathGenerationState, current_difficulty: str) -> bool:
        """
        Determine if a new content pool needs to be created.

        A new content pool is needed if:
        1. No content pool exists
        2. Current difficulty is different from previous difficulty

        Args:
            state: Current PathGenerationState
            current_difficulty: Current difficulty level

        Returns:
            bool: True if new content pool is needed
        """
        # Check if content pool is empty
        content_pool = state.get("content_pool")
        if not content_pool or len(content_pool) == 0:
            self.logger.debug("Content pool is empty, new pool needed")
            return True

        # Check if difficulty changed
        previous_difficulty = state.get("current_difficulty")
        if previous_difficulty != current_difficulty:
            self.logger.debug(
                f"Difficulty changed from '{previous_difficulty}' to '{current_difficulty}', "
                f"new pool needed"
            )
            return True

        self.logger.debug("Content pool is still valid for current difficulty")
        return False

    async def _create_comprehensive_content_pool(
            self,
            platform_queries: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Create a comprehensive content pool from all available platforms.

        Args:
            platform_queries: Dictionary with platform names as keys and search queries as values

        Returns:
            List[Dict[str, Any]]: Unified content pool from all platforms
        """
        content_pool = []

        self.logger.info(f"Fetching content from {len(platform_queries)} platforms")

        # Fetch content from each platform concurrently
        fetch_tasks = []
        for platform_key, query in platform_queries.items():
            task = self._fetch_platform_content_safe(platform_key, query)
            fetch_tasks.append(task)

        # Wait for all platform fetches to complete
        platform_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

        # Process results and build unified content pool
        for i, (platform_key, query) in enumerate(platform_queries.items()):
            result = platform_results[i]

            if isinstance(result, Exception):
                self.logger.error(f"Failed to fetch from {platform_key}: {str(result)}")
                continue

            if isinstance(result, list) and len(result) > 0:
                content_pool.extend(result)
                self.logger.info(f"Added {len(result)} items from {platform_key}")
            else:
                self.logger.warning(f"No content fetched from {platform_key}")

        self.logger.info(f"Created content pool with {len(content_pool)} total items")

        return content_pool

    async def _fetch_platform_content_safe(
            self,
            platform_key: str,
            query: str
    ) -> List[Dict[str, Any]]:
        """
        Safely fetch content from a specific platform with error handling.

        Args:
            platform_key: Platform identifier
            query: Search query for the platform

        Returns:
            List[Dict[str, Any]]: Content items from the platform
        """
        try:
            # Normalize platform name
            platform_normalized = platform_key.lower()

            # Map to internal platform name
            internal_platform = self.platform_mapping.get(platform_normalized, platform_key)

            # Check if platform is supported
            if platform_normalized not in self.supported_platforms:
                self.logger.warning(f"Platform '{platform_key}' not supported yet")
                return []

            # Fetch content for this platform
            content_items = await self._fetch_platform_content(internal_platform, query)

            self.logger.debug(f"Fetched {len(content_items)} items from {internal_platform}")

            return content_items

        except Exception as e:
            self.logger.error(f"Error fetching from {platform_key}: {str(e)}")
            return []  # Return empty list to continue with other platforms

    async def _fetch_platform_content(
            self,
            platform: str,
            query: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch content from a specific platform using the appropriate service.

        Args:
            platform: Platform name (normalized)
            query: Search query

        Returns:
            List[Dict[str, Any]]: Content items from the platform
        """
        platform_lower = platform.lower()

        try:
            if platform_lower == "youtube":
                content = await search_youtube_videos(query, MAX_RESULTS)
            elif platform_lower == "spotify":
                content = await search_spotify_audiobooks(query, MAX_RESULTS)
            elif platform_lower == "google books":
                content = await search_google_books(query, MAX_RESULTS)
            elif platform_lower == "semantic scholar":
                content = await search_semantic_scholar(query, MAX_RESULTS)
            else:
                self.logger.warning(f"Platform {platform} not yet supported")
                content = []

        except Exception as e:
            self.logger.error(f"Error fetching from {platform}: {str(e)}")
            content = []

        return content if content else []

    def get_supported_platforms(self) -> List[str]:
        """
        Get list of currently supported platforms.

        Returns:
            List[str]: List of supported platform names
        """
        return self.supported_platforms.copy()

    def add_platform_support(self, platform_name: str, fetch_function) -> None:
        """
        Add support for a new platform (for future extensibility).

        Args:
            platform_name: Name of the platform
            fetch_function: Async function to fetch content from the platform
        """
        platform_normalized = platform_name.lower()
        if platform_normalized not in self.supported_platforms:
            self.supported_platforms.append(platform_normalized)
            # In a real implementation, you'd register the fetch function
            self.logger.info(f"Added support for platform: {platform_name}")


# =============================================================================
# UTILITY FUNCTIONS FOR CONTENT POOL MANAGEMENT
# =============================================================================

def validate_content_pool_inputs(state: PathGenerationState) -> List[str]:
    """
    Validate that all required inputs are present for content pool creation.

    Args:
        state: PathGenerationState to validate

    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    errors = []

    # Check content pool prerequisites
    service = ContentPoolService()
    content_pool_errors = service._validate_content_pool_prerequisites(state)
    errors.extend(content_pool_errors)

    return errors


def analyze_content_pool_quality(content_pool: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the quality and characteristics of a content pool.

    Args:
        content_pool: List of content items

    Returns:
        Dict[str, Any]: Analysis results
    """
    if not content_pool:
        return {
            "total_items": 0,
            "platform_distribution": {},
            "quality_metrics": {},
            "issues": ["Content pool is empty"]
        }

    analysis = {
        "total_items": len(content_pool),
        "platform_distribution": {},
        "quality_metrics": {},
        "issues": []
    }

    # Analyze platform distribution
    for item in content_pool:
        platform = item.get("platform", "Unknown")
        analysis["platform_distribution"][platform] = analysis["platform_distribution"].get(platform, 0) + 1

    # Analyze content quality
    items_with_description = sum(
        1 for item in content_pool if item.get("description") and len(item["description"]) > 50)
    items_with_duration = sum(1 for item in content_pool if item.get("duration"))
    items_with_valid_links = sum(1 for item in content_pool if item.get("link") and item["link"] != "#")

    analysis["quality_metrics"] = {
        "items_with_description": items_with_description,
        "items_with_duration": items_with_duration,
        "items_with_valid_links": items_with_valid_links,
        "description_coverage": (items_with_description / len(content_pool)) * 100,
        "duration_coverage": (items_with_duration / len(content_pool)) * 100,
        "link_coverage": (items_with_valid_links / len(content_pool)) * 100
    }

    # Identify potential issues
    if len(content_pool) < 5:
        analysis["issues"].append("Content pool may be too small for effective module generation")

    if analysis["quality_metrics"]["description_coverage"] < 50:
        analysis["issues"].append("Many content items lack detailed descriptions")

    if analysis["quality_metrics"]["link_coverage"] < 90:
        analysis["issues"].append("Some content items have invalid or missing links")

    if len(analysis["platform_distribution"]) == 1:
        analysis["issues"].append("Content pool lacks platform diversity")

    return analysis


def filter_content_pool_by_criteria(
        content_pool: List[Dict[str, Any]],
        criteria: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Filter content pool based on specific criteria.

    Args:
        content_pool: List of content items
        criteria: Filtering criteria (platform, duration_min, duration_max, etc.)

    Returns:
        List[Dict[str, Any]]: Filtered content pool
    """
    if not content_pool:
        return []

    filtered_pool = content_pool.copy()

    # Filter by platform
    if criteria.get("platform"):
        target_platform = criteria["platform"].lower()
        filtered_pool = [
            item for item in filtered_pool
            if item.get("platform", "").lower() == target_platform
        ]

    # Filter by minimum duration
    if criteria.get("duration_min"):
        min_duration = criteria["duration_min"]
        filtered_pool = [
            item for item in filtered_pool
            if item.get("duration") and item["duration"] >= min_duration
        ]

    # Filter by maximum duration
    if criteria.get("duration_max"):
        max_duration = criteria["duration_max"]
        filtered_pool = [
            item for item in filtered_pool
            if item.get("duration") and item["duration"] <= max_duration
        ]

    # Filter by content quality (has description)
    if criteria.get("require_description"):
        filtered_pool = [
            item for item in filtered_pool
            if item.get("description") and len(item["description"]) > 20
        ]

    # Filter by valid links
    if criteria.get("require_valid_link"):
        filtered_pool = [
            item for item in filtered_pool
            if item.get("link") and item["link"] != "#" and item["link"].startswith("http")
        ]

    return filtered_pool


def create_fallback_content_pool(
        state: PathGenerationState,
        current_difficulty: str
) -> List[Dict[str, Any]]:
    """
    Create a fallback content pool if platform fetching fails completely.

    This ensures module generation can continue even if all platform APIs fail.

    Args:
        state: Current PathGenerationState
        current_difficulty: Current difficulty level

    Returns:
        List[Dict[str, Any]]: Fallback content pool
    """
    logger.info("Creating fallback content pool")

    subject = state["subject"]

    # Create basic fallback content items
    fallback_content = [
        {
            "title": f"{subject} {current_difficulty} Tutorial",
            "description": f"Learn {subject} concepts at {current_difficulty} level through comprehensive tutorials and practical examples.",
            "link": "#",
            "platform": "Fallback",
            "duration": 30,
            "authors": ["System Generated"],
            "content_type": "tutorial"
        },
        {
            "title": f"{subject} {current_difficulty} Guide",
            "description": f"Step-by-step guide covering essential {subject} topics for {current_difficulty} learners.",
            "link": "#",
            "platform": "Fallback",
            "duration": 45,
            "authors": ["System Generated"],
            "content_type": "guide"
        },
        {
            "title": f"{subject} {current_difficulty} Practice",
            "description": f"Hands-on practice exercises and projects to reinforce {subject} knowledge at {current_difficulty} level.",
            "link": "#",
            "platform": "Fallback",
            "duration": 60,
            "authors": ["System Generated"],
            "content_type": "practice"
        },
        {
            "title": f"{subject} {current_difficulty} Reference",
            "description": f"Comprehensive reference material covering key {subject} concepts for {current_difficulty} learners.",
            "link": "#",
            "platform": "Fallback",
            "duration": 20,
            "authors": ["System Generated"],
            "content_type": "reference"
        },
        {
            "title": f"{subject} {current_difficulty} Examples",
            "description": f"Real-world examples and case studies demonstrating {subject} applications at {current_difficulty} level.",
            "link": "#",
            "platform": "Fallback",
            "duration": 40,
            "authors": ["System Generated"],
            "content_type": "examples"
        }
    ]

    logger.info(f"Fallback content pool created with {len(fallback_content)} items")

    return fallback_content


def merge_content_pools(
        existing_pool: List[Dict[str, Any]],
        new_pool: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge two content pools, removing duplicates based on title and platform.

    Args:
        existing_pool: Existing content pool
        new_pool: New content pool to merge

    Returns:
        List[Dict[str, Any]]: Merged content pool
    """
    if not existing_pool:
        return new_pool.copy()

    if not new_pool:
        return existing_pool.copy()

    merged_pool = existing_pool.copy()

    # Create a set of existing items for duplicate detection
    existing_items = set()
    for item in existing_pool:
        key = (item.get("title", ""), item.get("platform", ""))
        existing_items.add(key)

    # Add new items that don't already exist
    added_count = 0
    for item in new_pool:
        key = (item.get("title", ""), item.get("platform", ""))
        if key not in existing_items:
            merged_pool.append(item)
            existing_items.add(key)
            added_count += 1

    logger.debug(f"Merged content pools: {added_count} new items added, {len(merged_pool)} total items")

    return merged_pool


def sort_content_pool_by_relevance(
        content_pool: List[Dict[str, Any]],
        subject: str,
        difficulty: str
) -> List[Dict[str, Any]]:
    """
    Sort content pool by relevance to the subject and difficulty.

    Args:
        content_pool: Content pool to sort
        subject: Learning subject
        difficulty: Difficulty level

    Returns:
        List[Dict[str, Any]]: Sorted content pool
    """
    if not content_pool:
        return []

    def calculate_relevance_score(item: Dict[str, Any]) -> float:
        """Calculate relevance score for a content item."""
        score = 0.0

        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        subject_lower = subject.lower()
        difficulty_lower = difficulty.lower()

        # Title relevance (weighted heavily)
        if subject_lower in title:
            score += 3.0
        if difficulty_lower in title:
            score += 2.0

        # Description relevance
        if subject_lower in description:
            score += 1.5
        if difficulty_lower in description:
            score += 1.0

        # Platform preference (YouTube and academic sources score higher)
        platform = item.get("platform", "").lower()
        if platform == "youtube":
            score += 1.0
        elif platform in ["semantic scholar", "google books"]:
            score += 0.8
        elif platform == "spotify":
            score += 0.6

        # Duration preference (prefer moderate lengths)
        duration = item.get("duration")
        if duration:
            if isinstance(duration, dict):
                duration_mins = duration.get("duration_minutes", 0)
            else:
                duration_mins = duration

            if 10 <= duration_mins <= 60:  # Prefer 10-60 minute content
                score += 0.5
            elif duration_mins > 120:  # Penalize very long content
                score -= 0.3

        # Content quality indicators
        if item.get("description") and len(item["description"]) > 100:
            score += 0.3

        if item.get("authors") and len(item["authors"]) > 0:
            score += 0.2

        if item.get("view_count") and item["view_count"] > 1000:
            score += 0.2

        return score

    # Sort by relevance score (descending)
    sorted_pool = sorted(
        content_pool,
        key=calculate_relevance_score,
        reverse=True
    )

    logger.debug(f"Sorted content pool by relevance: {len(sorted_pool)} items")

    return sorted_pool


def get_content_pool_statistics(content_pool: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comprehensive statistics about a content pool.

    Args:
        content_pool: Content pool to analyze

    Returns:
        Dict[str, Any]: Statistics and metrics
    """
    if not content_pool:
        return {
            "total_items": 0,
            "platforms": {},
            "duration_stats": {},
            "content_types": {},
            "quality_metrics": {}
        }

    stats = {
        "total_items": len(content_pool),
        "platforms": {},
        "duration_stats": {
            "total_duration": 0,
            "average_duration": 0,
            "min_duration": float('inf'),
            "max_duration": 0,
            "items_with_duration": 0
        },
        "content_types": {},
        "quality_metrics": {
            "items_with_description": 0,
            "items_with_authors": 0,
            "items_with_valid_links": 0,
            "average_description_length": 0
        }
    }

    total_description_length = 0
    durations = []

    for item in content_pool:
        # Platform distribution
        platform = item.get("platform", "Unknown")
        stats["platforms"][platform] = stats["platforms"].get(platform, 0) + 1

        # Duration analysis
        duration = item.get("duration")
        if duration:
            if isinstance(duration, dict):
                duration_mins = duration.get("duration_minutes", 0)
            else:
                duration_mins = duration

            if duration_mins > 0:
                durations.append(duration_mins)
                stats["duration_stats"]["total_duration"] += duration_mins
                stats["duration_stats"]["items_with_duration"] += 1
                stats["duration_stats"]["min_duration"] = min(
                    stats["duration_stats"]["min_duration"], duration_mins
                )
                stats["duration_stats"]["max_duration"] = max(
                    stats["duration_stats"]["max_duration"], duration_mins
                )

        # Content type distribution
        content_type = item.get("content_type", "unknown")
        stats["content_types"][content_type] = stats["content_types"].get(content_type, 0) + 1

        # Quality metrics
        if item.get("description"):
            stats["quality_metrics"]["items_with_description"] += 1
            total_description_length += len(item["description"])

        if item.get("authors") and len(item["authors"]) > 0:
            stats["quality_metrics"]["items_with_authors"] += 1

        if item.get("link") and item["link"] != "#" and item["link"].startswith("http"):
            stats["quality_metrics"]["items_with_valid_links"] += 1

    # Calculate averages
    if durations:
        stats["duration_stats"]["average_duration"] = sum(durations) / len(durations)
    else:
        stats["duration_stats"]["min_duration"] = 0

    if stats["quality_metrics"]["items_with_description"] > 0:
        stats["quality_metrics"]["average_description_length"] = (
                total_description_length / stats["quality_metrics"]["items_with_description"]
        )

    return stats
