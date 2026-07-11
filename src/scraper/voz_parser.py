import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MIN_CONTENT_LENGTH = 10

def parse_voz_thread_title(html: str) -> str:
    """Extract the thread title from Voz/XenForo thread HTML."""
    soup = BeautifulSoup(html, "html.parser")
    # XenForo title selectors
    title_elem = soup.select_one("h1.p-title-value") or soup.select_one("div.p-title")
    if title_elem:
        return title_elem.get_text(strip=True)
    return "Unknown Thread Title"

def parse_voz_posts(html: str) -> list[dict]:
    """Parse posts in the Voz/XenForo HTML thread and return a list of dicts.
    
    Each dict contains:
    - id (str): The unique post ID (from data-content).
    - author (str): The username of the poster.
    - timestamp (str): The ISO/formatted string representing post time.
    - content (str): Cleaned text of the post.
    """
    soup = BeautifulSoup(html, "html.parser")
    posts = []
    
    # XenForo posts are contained in <article class="message message--post ...">
    post_elements = soup.select("article.message--post") or soup.select("article.message")
    
    for element in post_elements:
        # Extract post ID
        post_id = element.get("data-content") or ""
        
        # Extract author
        author_elem = element.select_one(".message-name .username") or element.select_one(".username")
        author = author_elem.get_text(strip=True) if author_elem else "Unknown User"
        
        # Extract timestamp
        time_elem = element.select_one("time.u-dt")
        timestamp = ""
        if time_elem:
            timestamp = time_elem.get("datetime") or time_elem.get("data-time") or time_elem.get_text(strip=True)
            
        # Extract content (inside .bbWrapper)
        content_elem = element.select_one("div.bbWrapper")
        if not content_elem:
            continue
            
        # Clean up quotes (e.g. if one post quotes another, it contains blockquote elements)
        # For simplicity, we can keep the text but we should clean up spacing
        content = content_elem.get_text(strip=True)
        
        # Skip short/spam posts (e.g. "Chấm", "Upp")
        if len(content) < MIN_CONTENT_LENGTH:
            logger.info("Filtered short post ID %s (length %d)", post_id, len(content))
            continue
            
        posts.append({
            "id": post_id,
            "author": author,
            "timestamp": timestamp,
            "content": content
        })
        
    logger.info("Parsed %d valid posts out of %d elements", len(posts), len(post_elements))
    return posts

def format_voz_thread(html: str) -> str:
    """Format thread title and parsed posts into a single clean text representation."""
    title = parse_voz_thread_title(html)
    posts = parse_voz_posts(html)
    
    formatted_parts = [f"Thread Title: {title}"]
    for post in posts:
        header = f"[Post #{post['id']} by {post['author']} at {post['timestamp']}]"
        formatted_parts.append(f"{header}\n{post['content']}")
        
    return "\n\n".join(formatted_parts)
