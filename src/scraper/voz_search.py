import logging
import urllib.parse
from bs4 import BeautifulSoup
from scrapling import StealthyFetcher

# Expose Fetcher for testing / typing check if needed
from scrapling import Fetcher

logger = logging.getLogger(__name__)

def parse_search_results(html: str) -> list[dict]:
    """Parse Google Search results HTML and extract Voz thread titles and URLs."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        
        # Look for Voz thread patterns
        if "voz.vn/t/" in href or "voz.vn/threads/" in href:
            # Handle Google redirect wrappers (/url?q=...)
            if href.startswith("/url?q="):
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                if "q" in parsed:
                    href = parsed["q"][0]
                    
            # Clean up query params from the thread URL
            if "&" in href:
                href = href.split("&")[0]
                
            title = a.get_text(strip=True)
            # Filter out navigation noise, empty titles, or raw links
            if title and not title.startswith("http") and len(title) > 5:
                results.append({
                    "title": title,
                    "url": href
                })
                
    # Deduplicate results by URL
    seen = set()
    unique_results = []
    for r in results:
        url = r["url"]
        if url not in seen:
            seen.add(url)
            unique_results.append(r)
            
    logger.info("Extracted %d unique Voz thread results from Google search page", len(unique_results))
    return unique_results


def search_voz_threads(keyword: str) -> list[dict]:
    """Search for Voz forum threads about a keyword using Google Search."""
    query = f"site:voz.vn {keyword}"
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded_query}"
    
    logger.info("Searching Google for Voz threads: %s", query)
    try:
        # Fetch the search page using StealthyFetcher to bypass blocks
        fetcher = StealthyFetcher()
        response = fetcher.fetch(search_url, timeout=15000, solve_cloudflare=True)
        
        # Fallback to GET CSRF token GET search page structure in test mocks if needed
        # We also check if status is success
        if response.status != 200:
            logger.warning("Google search returned status code %d", response.status)
            
        return parse_search_results(response.html_content)
    except Exception as e:
        logger.error("Failed to perform Google search for Voz threads: %s", e)
        return []
