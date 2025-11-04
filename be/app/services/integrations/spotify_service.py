import base64
import requests
from app.core.config import settings
import asyncio


async def search_spotify_audiobooks(query: str, max_results: int = 10, market: str = "US") -> list[dict]:
    """
    Search Spotify's catalog for audiobooks and return a list with duration info.
    """
    access_token = await get_spotify_access_token(settings.spotify_client_id, settings.spotify_client_secret)
    if not access_token:
        return []

    search_url = "https://api.spotify.com/v1/search"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": query,
        "type": "audiobook",
        "limit": max_results,
        "market": market,
    }

    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.get(search_url, headers=headers, params=params, timeout=10)
        )
        resp.raise_for_status()
        data = resp.json()

        audiobooks: list[dict] = []
        
        # Process each audiobook
        for item in data.get("audiobooks", {}).get("items", []):
            audiobook_id = item.get("id")
            
            duration_info = 0
            
            if audiobook_id:
                chapters = await get_audiobook_chapters(audiobook_id, access_token)
                if chapters:
                    duration_info = calculate_audiobook_duration(chapters)
            
            # Fallback to page-based duration calculation if no chapters found
            if not duration_info:
                description = item.get("html_description") or ""
                total_pages = extract_pages_from_description(description)
                if total_pages:
                    duration_info = calculate_duration_from_pages(total_pages)
                else:
                    # Final fallback: estimate based on typical audiobook length
                    duration_info = 60  # Default to 60 minutes if no info available

            audiobook_data = {
                "title": item.get("name") or "N/A",
                "authors": [a["name"] for a in item.get("authors", [])] or ["N/A"],
                "description": item.get("html_description") or "No description available.",
                "link": item.get("external_urls", {}).get("spotify", "#"),
                "publisher": item.get("publisher", "N/A"),
                "cover_image": next(
                    (img.get("url") for img in item.get("images", []) if img.get("url")),
                    None,
                ),
                "platform": "Spotify",
                "duration": duration_info
            }
            
            audiobooks.append(audiobook_data)
            
        return audiobooks
    
    except requests.exceptions.RequestException as e:
        print(f"[Spotify] search error: {e}")
        return []
    except Exception as e:
        print(f"[Spotify] unexpected error: {e}")
        return []
    
async def get_audiobook_chapters(audiobook_id: str, access_token: str) -> list[dict]:
    """
    Get chapters for an audiobook to calculate total duration.
    """
    chapters_url = f"https://api.spotify.com/v1/audiobooks/{audiobook_id}/chapters"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 50}  # Spotify's max limit per request
    
    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.get(chapters_url, headers=headers, params=params, timeout=10)
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"[Spotify] chapters error: {e}")
        return []
    
def calculate_audiobook_duration(chapters: list[dict]) -> int:
    """
    Calculate total duration from chapters.
    """
    total_duration_ms = sum(chapter.get("duration_ms", 0) for chapter in chapters)
    total_seconds = total_duration_ms // 1000
    total_minutes = (total_seconds + 59) // 60  # Round up to nearest minute
    
    return total_minutes

def calculate_duration_from_pages(total_pages: int, average_reading_speed_wpm: int = 200) -> int:
    """
    Calculate estimated reading duration based on number of pages.

    Args:
        total_pages: Total number of pages in the book
        average_reading_speed_wpm: Average reading speed in words per minute (default: 200)

    Returns:
        Estimated duration in minutes
    """
    # Estimate words per page (typical range: 250-300 words per page)
    words_per_page = 275
    total_words = total_pages * words_per_page

    # Calculate reading time in minutes
    duration_minutes = total_words / average_reading_speed_wpm

    # Round up to nearest minute and ensure minimum of 1 minute
    return max(1, int(duration_minutes + 0.5))

def extract_pages_from_description(description: str) -> int:
    """
    Extract number of pages from book description.

    Args:
        description: Book description text

    Returns:
        Number of pages if found, 0 otherwise
    """
    import re

    # Look for patterns like "123 pages", "123 pp", etc.
    page_patterns = [
        r'(\d+)\s*pages?',
        r'(\d+)\s*pp\.?',
        r'(\d+)\s*p\.',
    ]

    for pattern in page_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return 0

async def get_spotify_access_token(client_id: str, client_secret: str) -> str | None:
    """
    Obtain an app-only (client-credentials) access token from the Spotify Accounts API.
    """
    auth_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}"}
    data = {"grant_type": "client_credentials"}

    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.post(auth_url, headers=headers, data=data, timeout=10)
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"[Spotify] token error: {e}")
        return None
