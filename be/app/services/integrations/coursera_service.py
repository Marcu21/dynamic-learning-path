import asyncio
import requests
from typing import List, Dict, Any, Optional
import base64
from app.core.config import settings
import re

async def search_coursera_courses(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search Coursera courses using API Key authentication.
    
    Args:
        query (str): Search term
        max_results (int): Maximum number of results
        
    Returns:
        List[Dict[str, Any]]: List of course information
    """
    # Use API Key authentication instead of OAuth
    search_url = "https://api.coursera.com/api/courses.v1"
    
    headers = {
        "Authorization": f"Bearer {settings.coursera_api_key}",
        "Content-Type": "application/json"
    }
    
    params = {
        "q": "search",
        "query": query,
        "limit": max_results,
        "fields": "id,name,description,photoUrl,workload,averageRating,ratingCount,enrollmentCount,startDate,duration,difficultyLevel,categories,instructors,partners,slug"
    }

    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.get(search_url, headers=headers, params=params, timeout=10)
        )
        
        print(f"[Coursera] API Response Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"[Coursera] API Response: {resp.text}")
            
        resp.raise_for_status()
        data = resp.json()

        courses = []
        
        for item in data.get("elements", []):
            # Calculate duration in minutes
            duration_info = calculate_coursera_duration(item)
            
            course_info = {
                "title": item.get("name", "N/A"),
                "description": item.get("description", "No description available."),
                "link": f"https://www.coursera.org/learn/{item.get('slug', item.get('id', ''))}",
                "platform": "Coursera",
                
                # Duration information
                "duration": duration_info["duration_minutes"],
                "workload": item.get("workload", "N/A"),
                
                # Course metadata
                "difficulty_level": item.get("difficultyLevel", "N/A"),
                "average_rating": item.get("averageRating", 0.0),
                "rating_count": item.get("ratingCount", 0),
                "enrollment_count": item.get("enrollmentCount", 0),
                
                # Additional info
                "categories": item.get("categories", []),
                "instructors": extract_instructor_names(item.get("instructors", [])),
                "partners": extract_partner_names(item.get("partners", [])),
                "photo_url": item.get("photoUrl", "")
            }
            courses.append(course_info)

        return courses

    except requests.exceptions.RequestException as e:
        print(f"[Coursera] Search error: {e}")
        return []
    except Exception as e:
        print(f"[Coursera] Unexpected error: {e}")
        return []
    
async def get_coursera_access_token(client_id: str, client_secret: str) -> Optional[str]:
    """
    Obtain an OAuth 2.0 access token from Coursera using client credentials flow.
    
    Args:
        client_id (str): Coursera API Key (acts as client_id)
        client_secret (str): Coursera Secret Key
        
    Returns:
        str | None: Access token if successful, None if failed
    """
    auth_url = "https://api.coursera.com/oauth2/client_credentials/token"
    
    # Create Basic Auth header (Base64 encode "key:secret")
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }
    
    data = {"grant_type": "client_credentials"}
    
    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None,
            lambda: requests.post(auth_url, headers=headers, data=data, timeout=10)
        )
        
        if resp.status_code == 200:
            token_data = resp.json()
            print(f"[Coursera] ✅ OAuth token obtained successfully")
            return token_data.get("access_token")
        else:
            print(f"[Coursera] ❌ OAuth failed ({resp.status_code}): {resp.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[Coursera] ❌ OAuth error: {e}")
        return None

def calculate_coursera_duration(course_data: dict) -> dict:
    """
    Calculate course duration from Coursera course data.
    
    Args:
        course_data (dict): Course information from Coursera API
        
    Returns:
        dict: Duration information in minutes and formatted
    """
    # Coursera provides duration in different formats
    duration_weeks = course_data.get("duration", 0)  # Usually in weeks
    workload = course_data.get("workload", "")  # e.g., "4-6 hours/week"
    
    # Try to extract hours per week from workload string
    hours_per_week = extract_hours_from_workload(workload)
    
    # Calculate total duration in minutes
    if duration_weeks and hours_per_week:
        total_hours = duration_weeks * hours_per_week
        total_minutes = int(total_hours * 60)
    else:
        # Fallback: estimate based on typical Coursera course
        total_minutes = 240  # 4 hours default
    
    # Format duration
    if total_minutes >= 60:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if minutes > 0:
            formatted = f"{hours}h {minutes}m"
        else:
            formatted = f"{hours}h"
    else:
        formatted = f"{total_minutes}m"
    
    return {
        "duration_minutes": total_minutes,
        "duration_formatted": formatted,
        "estimated_weeks": duration_weeks,
        "hours_per_week": hours_per_week
    }

def extract_hours_from_workload(workload: str) -> float:
    """
    Extract hours per week from workload string.
    
    Args:
        workload (str): Workload string like "4-6 hours/week"
        
    Returns:
        float: Average hours per week
    """
    if not workload or not isinstance(workload, str):
        return 4.0  # Default 4 hours per week
    
    # Pattern to match "X-Y hours" or "X hours"
    pattern = r'(\d+)(?:-(\d+))?\s*hours?'
    match = re.search(pattern, workload.lower())
    
    if match:
        min_hours = int(match.group(1))
        max_hours = int(match.group(2)) if match.group(2) else min_hours
        return (min_hours + max_hours) / 2
    
    return 4.0  # Default fallback

def extract_instructor_names(instructors: list) -> list:
    """
    Extract instructor names from instructor objects.
    
    Args:
        instructors (list): List of instructor objects
        
    Returns:
        list: List of instructor names
    """
    if not instructors:
        return ["N/A"]
    
    names = []
    for instructor in instructors:
        if isinstance(instructor, dict):
            name = instructor.get("fullName") or instructor.get("name", "Unknown Instructor")
            names.append(name)
        elif isinstance(instructor, str):
            names.append(instructor)
    
    return names if names else ["N/A"]

def extract_partner_names(partners: list) -> list:
    """
    Extract partner/university names from partner objects.
    
    Args:
        partners (list): List of partner objects
        
    Returns:
        list: List of partner names
    """
    if not partners:
        return ["N/A"]
    
    names = []
    for partner in partners:
        if isinstance(partner, dict):
            name = partner.get("name", "Unknown Partner")
            names.append(name)
        elif isinstance(partner, str):
            names.append(partner)
    
    return names if names else ["N/A"]


async def main():
    """
    Main function to run the Coursera search test.
    """
    print("🚀 Starting Coursera course search test...")
    
    if settings.coursera_api_key == "YOUR_COURSERA_API_KEY":
        print("⚠️  Warning: Please replace 'YOUR_COURSERA_API_KEY' in the script with your actual key.")
        return

    search_query = "python programming"
    num_results = 5
    
    print(f"🔍 Searching for '{search_query}' (limit: {num_results} results)\n")
    
    courses = await search_coursera_courses(query=search_query, max_results=num_results)
    
    if courses:
        print(f"\n✅ Found {len(courses)} courses:")
        for i, course in enumerate(courses, 1):
            print("-" * 40)
            print(f"Course #{i}")
            print(f"  Title: {course.get('title')}")
            print(f"  Partner(s): {', '.join(course.get('partners', []))}")
            print(f"  Link: {course.get('link')}")
            print(f"  Difficulty: {course.get('difficulty_level')}")
            print(f"  Rating: {course.get('average_rating')} ({course.get('rating_count')} ratings)")
            print(f"  Workload: {course.get('workload')}")
        print("-" * 40)
    else:
        print("\n❌ No courses found or an error occurred. Check the logs above.")

if __name__ == "__main__":
    # This runs the async main function
    asyncio.run(main())
