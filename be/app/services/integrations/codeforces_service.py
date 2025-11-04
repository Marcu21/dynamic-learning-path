import aiohttp
from typing import List, Dict, Any, Optional
from app.core.logger import get_logger


logger = get_logger(__name__)

async def search_codeforces_problems(
    query: str,
    max_results: int = 10,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Searches Codeforces for problems based on tags and rating range.
    
    Args:
        max_results (int): Maximum number of problems to return
        min_rating (int, optional): Minimum problem rating
        max_rating (int, optional): Maximum problem rating
    
    Returns:
        List[Dict[str, Any]]: List of problem dictionaries containing
                             title, description, link, platform, rating, and tags
    """
    base_url = "https://codeforces.com/api/problemset.problems"
    
    try:
        params = {}
        if query and query.strip():
            # Convert comma-separated tags to semicolon-separated format for Codeforces API
            tags = [tag.strip() for tag in query.split(',') if tag.strip()]
            if tags:
                params['tags'] = ';'.join(tags)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"HTTP error {response.status} when fetching problems")
                    return []
                
                data = await response.json()
                
                if data.get('status') != 'OK':
                    logger.error(f"API error: {data.get('comment', 'Unknown error')}")
                    return []
                
                problems = data.get('result', {}).get('problems', [])
                problem_stats = data.get('result', {}).get('problemStatistics', [])
                
                # Create a mapping of problem stats for quick lookup
                stats_map = {}
                for stat in problem_stats:
                    key = (stat.get('contestId'), stat.get('index'))
                    stats_map[key] = stat
                
                processed_problems = []
                for problem in problems:
                    # Filter by rating if specified
                    problem_rating = problem.get('rating')
                    if min_rating is not None and (problem_rating is None or problem_rating < min_rating):
                        continue
                    if max_rating is not None and (problem_rating is None or problem_rating > max_rating):
                        continue
                    
                    contest_id = problem.get('contestId')
                    index = problem.get('index')
                    
                    # Get problem statistics
                    stats = stats_map.get((contest_id, index), {})
                    solved_count = stats.get('solvedCount', 0)
                    
                    # Build problem URL
                    if contest_id:
                        problem_url = f"https://codeforces.com/contest/{contest_id}/problem/{index}"
                    else:
                        problem_url = f"https://codeforces.com/problemset/problem/{problem.get('problemsetName', '')}/{index}"
                    
                    problem_data = {
                        'title': f"{index}. {problem.get('name', 'Unknown Problem')}",
                        'link': problem_url,
                        'platform': 'Codeforces',
                        'rating': problem_rating or 0,
                        'tags': problem.get('tags', []),
                        'solved_count': solved_count
                    }
                    
                    processed_problems.append(problem_data)
                
                # Sort by rating (ascending) and then by solved count (descending)
                processed_problems.sort(key=lambda x: (x['rating'], -x['solved_count']))
                
                # Limit results
                result = processed_problems[:max_results]
                
                logger.info(f"Found {len(result)} Codeforces problems")
                return result
                
    except aiohttp.ClientError as e:
        logger.error(f"Network error when fetching Codeforces problems: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error when fetching Codeforces problems: {e}")
        return []
