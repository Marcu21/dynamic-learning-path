import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any
import math
import ssl
import certifi

async def search_semantic_scholar(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Searches Semantic Scholar for scientific articles based on a query.

    Args:
        query (str): The search term.
        max_results (int): The maximum number of results to return.

    Returns:
        list: A list of dictionaries, where each dictionary contains article
              details. Returns an empty list if an error occurs.
    """
    base_url = 'https://api.semanticscholar.org/graph/v1/paper/search'
    encoded_query = urllib.parse.quote(query)
    # Request specific fields to get all the necessary information
    fields = "title,authors,abstract,url,citationCount,publicationVenue,tldr"
    request_url = f'{base_url}?query={encoded_query}&limit={max_results}&fields={fields}'

    try:
        # Create an SSL context that uses the certifi certificate bundle to avoid SSL errors.
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        # Perform the API request with the custom SSL context
        with urllib.request.urlopen(request_url, context=ssl_context) as url:
            response = json.loads(url.read().decode())

        articles = []
        for item in response.get("data", []):
            # Extract author names from the list of author objects
            authors = [author.get("name", "N/A") for author in item.get("authors", [])]
            
            # Use abstract for description and word count calculation
            description = item.get("abstract", "No description available.")
            word_count = len(description.split()) if description else 0

            article_info = {
                "title": item.get("title", "N/A"),
                "authors": authors,
                "description": description,
                "link": item.get("url", "#"),
                "platform": "Semantic Scholar",
                "average_rating": None,  # Semantic Scholar doesn't have user ratings
                "ratings_count": item.get("citationCount", 0), # Using citation count as a proxy for rating
                "maturity_rating": "N/A",
                "categories": [item.get("publicationVenue", {}).get("name", "N/A")] if item.get("publicationVenue") else [],
                "duration": calculate_reading_duration(word_count),
                "tldr": item.get("tldr", {}).get("text") if item.get("tldr") else "N/A"
            }
            articles.append(article_info)

        return articles

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def calculate_reading_duration(word_count: int, words_per_minute: int = 180) -> dict:
    """
    Calculate reading duration based on word count.
    
    Args:
        word_count (int): Estimated number of words in the article summary.
        words_per_minute (int): Average reading speed for scientific papers.
    
    Returns:
        dict: A dictionary containing the estimated reading duration in minutes,
              a formatted string, the estimated words, and the reading speed.
    """
    if word_count <= 0:
        return {
            "duration_minutes": 0,
            "duration_formatted": "N/A",
            "estimated_words": 0,
            "reading_speed_wpm": words_per_minute
        }
        
    duration_minutes = math.ceil(word_count / words_per_minute)
    
    return {
        "duration_minutes": duration_minutes,
        "duration_formatted": f"{duration_minutes} min",
        "estimated_words": word_count,
        "reading_speed_wpm": words_per_minute
    }
## EXAMPLE USAGE
# async def main():
#     """Main function to run the Semantic Scholar search from the command line."""
#     parser = argparse.ArgumentParser(description="Search for articles on Semantic Scholar.")
#     parser.add_argument("query", type=str, help="The search term.")
#     parser.add_argument(
#         "--max_results", 
#         type=int, 
#         default=3, 
#         help="The maximum number of results to return."
#     )
#     args = parser.parse_args()

#     print(f"Searching for '{args.query}' on Semantic Scholar...")
#     results = await search_semantic_scholar(args.query, args.max_results)
#     print(results[0])


# if __name__ == "__main__":
#     # To run the search, provide a query from the command line:
#     # python <your_script_name>.py "your query here"
#     #
#     # To run the unit tests, use the unittest module:
#     # python -m unittest <your_script_name>.py
#     asyncio.run(main())
