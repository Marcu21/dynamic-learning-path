"""
Platform search functionality.
Separated to avoid circular imports with the main service.
"""

import asyncio
from typing import Dict, List, Tuple
from app.core.logger import get_logger
from app.schemas.core_schemas.preference_schema import PreferencesCreate
from app.services.integrations.youtube_service import search_youtube_videos
from app.services.integrations.spotify_service import search_spotify_audiobooks
from app.services.integrations.google_books_service import search_google_books
from app.services.integrations.coursera_service import search_coursera_courses
from app.services.integrations.codeforces_service import search_codeforces_problems
from app.services.integrations.research_papers_service import search_semantic_scholar


logger = get_logger(__name__)

class PlatformSearchService:
    """Handle platform searching without dependencies on main learning service"""
    
    @staticmethod
    async def search_single_platform(platform: str, search_query: str, max_results: int = 10) -> Tuple[str, List[Dict]]:
        """Search a single platform and return results with platform name"""
        try:
            platform_lower = platform.lower()
            logger.debug(f"Searching {platform} for: '{search_query}'")
            
            if platform_lower == "youtube":
                content = await search_youtube_videos(search_query, max_results)
                
            elif platform_lower == "spotify":
                content = await search_spotify_audiobooks(search_query, max_results)
                
            elif platform_lower == "google books":
                content = await search_google_books(search_query, max_results)
                
            elif platform_lower == "coursera":
                content = await search_coursera_courses(search_query, max_results)
                
            elif platform_lower == "codeforces":
                content = await search_codeforces_problems(query=search_query, max_results=max_results)
                
            elif platform_lower == "research papers":
                content = await search_semantic_scholar(search_query, max_results=max_results)
                
            else:
                logger.warning(f"Platform '{platform}' not supported")
                return platform, []
            
            # Add platform info to each content item
            for item in content:
                item['source_platform'] = platform_lower
            
            logger.debug(f"{platform} returned {len(content)} results")
            return platform, content
            
        except Exception as e:
            logger.error(f"Error searching {platform}: {str(e)}")
            return platform, []
    
    @staticmethod
    async def parallel_platform_search(
        preferences: PreferencesCreate,
        platform_queries: Dict[str, str],
        max_results_per_platform: int = 10
    ) -> List[Dict]:
        """
        Search platforms in parallel using platform-specific queries.
        
        Args:
            preferences: User preferences (contains preferred platforms)
            platform_queries: Dict mapping platform names to their specific queries
            max_results_per_platform: Maximum results per platform
            
        Returns:
            List of all content found across platforms
        """
        
        tasks = []
        
        for platform in preferences.preferred_platforms:
            if platform in platform_queries:
                query = platform_queries[platform]
                
                if platform.lower() == "youtube":
                    task = PlatformSearchService.search_single_platform("YouTube", query, max_results_per_platform)
                elif platform.lower() == "spotify":
                    task = PlatformSearchService.search_single_platform("Spotify", query, max_results_per_platform)
                elif platform.lower() == "google books":
                    task = PlatformSearchService.search_single_platform("Google Books", query, max_results_per_platform)
                elif platform.lower() == "codeforces":
                    task = PlatformSearchService.search_single_platform("Codeforces", query, max_results_per_platform)
                elif platform.lower() == "coursera":
                    task = PlatformSearchService.search_single_platform("Coursera", query, max_results_per_platform)
                elif platform.lower() == "research papers":
                    task = PlatformSearchService.search_single_platform("Research Papers", query, max_results_per_platform)
                else:
                    continue
                
                tasks.append(task)
                logger.info(f"Queuing {platform} search with query: '{query}'")
        
        if not tasks:
            logger.warning("No valid platform search tasks created")
            return []
        
        # Execute all searches in parallel
        logger.info(f"Executing {len(tasks)} platform searches in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all results
        all_content = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Platform search {i} failed: {str(result)}")
                continue
            elif isinstance(result, list):
                all_content.extend(result)
                logger.info(f"Platform search {i} returned {len(result)} results")
            else:
                logger.warning(f"Platform search {i} returned unexpected result type: {type(result)}")
        
        logger.info(f"Total content found: {len(all_content)} items")
        return all_content
