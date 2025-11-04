from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any
from app.core.config import settings
import asyncio
import math


async def search_google_books(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Searches Google Books for ebooks based on a query.

    Args:
        query (str): The search term.
        max_results (int): The maximum number of results to return.

    Returns:
        list: A list of dictionaries, where each dictionary contains book
              details including ratings. Returns an empty list if an error occurs.
    """
    API_SERVICE_NAME = "books"
    API_VERSION = "v1"

    try:
        # Build the Google Books service object.
        books_service = build(API_SERVICE_NAME, API_VERSION, developerKey=settings.youtube_api_key)

        # Call the volumes.list method to retrieve results.
        search_response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: books_service.volumes().list(
                q=query,
                maxResults=max_results,
                orderBy="relevance"
            ).execute()
        )

        books = []
        for item in search_response.get("items", []):
            volume_info = item.get("volumeInfo", {})
            
            page_count = volume_info.get("pageCount", 0)
            categories = volume_info.get("categories", [])
            reading_speed = get_reading_speed_by_difficulty(categories, page_count)
            book_info = {
                "title": volume_info.get("title", "N/A"),
                "authors": volume_info.get("authors", ["N/A"]),
                "description": volume_info.get("description", "No description available."),
                "link": volume_info.get("infoLink", "#"),
                "platform": "Google Books",
                "average_rating": volume_info.get("averageRating", 0.0),
                "ratings_count": volume_info.get("ratingsCount", 0),
                "maturity_rating": volume_info.get("maturityRating", "N/A"),
                "categories": categories,
                "duration": calculate_reading_duration(page_count, reading_speed)
            }
            books.append(book_info)

        return books

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def calculate_reading_duration(page_count: int, words_per_page: int = 250, words_per_minute: int = 100) -> int:
    """
    Calculate reading duration based on page count.
    
    Args:
        page_count (int): Number of pages in the book
        words_per_page (int): Average words per page (default: 250)
        words_per_minute (int): Average reading speed (default: 200 WPM)
    
    Returns:
        int: Estimated reading duration in minutes
    """
    if page_count <= 0:
        return 0
        
    # Calculate total words and reading time
    estimated_words = page_count * words_per_page
    duration_minutes = math.ceil(estimated_words / words_per_minute)
    
    return duration_minutes

def get_reading_speed_by_difficulty(categories: list = None, page_count: int = 0) -> int:
    """
    Adjust reading speed based on book difficulty/category.
    
    Args:
        categories (list): Book categories from Google Books
        page_count (int): Number of pages
    
    Returns:
        int: Adjusted words per minute
    """
    base_speed = 200  # Average reading speed
    
    if not categories:
        return base_speed
    
    # Technical/complex categories - slower reading
    technical_categories = [
        "computers", "technology", "programming", "science", 
        "mathematics", "engineering", "medical", "law", "philosophy"
    ]
    
    # Light reading categories - faster reading
    light_categories = [
        "fiction", "romance", "mystery", "adventure", 
        "young adult", "children", "humor"
    ]
    
    categories_text = " ".join(categories).lower()
    
    # Adjust speed based on content type
    if any(cat in categories_text for cat in technical_categories):
        return 150  # Slower for technical content
    elif any(cat in categories_text for cat in light_categories):
        return 250  # Faster for light reading
    elif page_count > 500:
        return 175  # Slower for very long books (likely complex)
    
    return base_speed
