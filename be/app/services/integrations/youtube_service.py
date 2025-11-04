import asyncio
from typing import List, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings
import re
import math
from app.core.logger import get_logger


logger = get_logger(__name__)

async def search_youtube_videos(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Searches YouTube for videos based on a query and returns the top results,
    including duration, view count, like count, and comment count.

    Args:
        query (str): The search term.
        max_results (int): The maximum number of results to return.

    Returns:
        list: A list of dictionaries, where each dictionary contains the
              title, description, link, platform, duration, and statistics
              (views, likes, comments) of a video. Returns an empty list
              if an error occurs.
    """
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    try:
        youtube = build(API_SERVICE_NAME, API_VERSION, developerKey=settings.youtube_api_key)

        # Search for videos to get their IDs and basic snippet data.
        search_response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: youtube.search().list(
                q=query,
                part="snippet",
                maxResults=max_results,
                type="video",
                videoDuration="long",
                order="relevance"
            ).execute()
        )

        video_ids = []
        videos_data = {}
        for search_result in search_response.get("items", []):
            video_id = search_result["id"]["videoId"]
            video_ids.append(video_id)
            
            # Store snippet data temporarily, using the video_id as the key.
            videos_data[video_id] = {
                "title": search_result["snippet"]["title"],
                "description": search_result["snippet"]["description"],
                "link": f"https://www.youtube.com/watch?v={video_id}",
                "platform": "YouTube"
            }

        if not video_ids:
            return []

        # Use the collected video IDs to get their contentDetails, which includes duration.
        video_details_response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: youtube.videos().list(
                id=",".join(video_ids),
                part="contentDetails,statistics" # Get both duration and stats
            ).execute()
        )

        # Merge the duration and statistics into our existing video data.
        for item in video_details_response.get("items", []):
            video_id = item["id"]
            if video_id in videos_data:
                # Get the statistics object
                stats = item.get('statistics', {})
                
                duration = parse_youtube_duration(item.get('contentDetails', {}).get('duration', 'N/A'))
                
                # Add view, like, and comment counts. Convert to int, defaulting to 0.
                videos_data[video_id]['view_count'] = int(stats.get('viewCount', 0))
                videos_data[video_id]['like_count'] = int(stats.get('likeCount', 0))
                videos_data[video_id]['comment_count'] = int(stats.get('commentCount', 0))
                videos_data[video_id]['duration'] = duration
                
        logger.info(f"Found {len(videos_data)} videos for query: {query}")

        # Return a list of the video data dictionaries.
        return list(videos_data.values())

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def parse_youtube_duration(duration_str: str) -> int:
    """
    Parse YouTube's ISO 8601 duration format (e.g. "PT4M13S") and return the duration in minutes,
    rounded up to the nearest minute.
    
    Args:
        duration_str (str): YouTube duration string like "PT4M13S"
        
    Returns:
        int: Duration in minutes, rounded up
    """
    if not duration_str or duration_str == 'N/A':
        return 0

    # Parse ISO 8601 duration format PT#H#M#S
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    total_seconds = hours * 3600 + minutes * 60 + seconds

    return math.ceil(total_seconds / 60)
