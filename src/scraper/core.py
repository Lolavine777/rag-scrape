import logging
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from scrapling import StealthyFetcher

from .exceptions import ForumBlockedException

logger = logging.getLogger(__name__)

# Minimum character length for a comment to be considered "real content"
MIN_CONTENT_LENGTH = 10

# CSS classes/tags to exclude entirely
NOISE_SELECTORS = [".signature", "script", "style", "nav", "footer", "header"]

# CSS selectors to try for content extraction, ordered by specificity
CONTENT_SELECTORS = [
    ".op",
    ".message-body",
    ".comment",
    ".post-content",
    ".bbWrapper",
    "article",
    "[class*='content']",
    "[class*='body']",
    "[class*='post']",
]


def _do_fetch(url: str) -> str:
    return ""


def fetch_forum_page(url: str) -> str:
    html = _do_fetch(url)
    if "Cloudflare" in html or "Access Denied" in html:
        raise ForumBlockedException("Blocked by Anti-bot")
    return html


def parse_forum_html(html: str) -> str:
    """Parse forum HTML and extract meaningful content, filtering noise.

    Strategy:
    1. Remove known noise elements (signatures, scripts, etc.)
    2. Try each CSS selector in CONTENT_SELECTORS to find content blocks
    3. Filter out short text (likely spam: "Chấm", "Upp", "Hóng")
    4. Fallback: extract all text from <body> if no selectors matched
    """
    soup = BeautifulSoup(html, "html.parser")

    # Step 1: Remove noise elements before any content extraction
    for selector in NOISE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()

    # Step 2: Try each content selector to find content blocks
    # We track matched elements to avoid double-counting when a broad
    # selector (e.g. [class*='post']) matches a parent of an already-matched
    # child (e.g. .op inside .post).
    content_parts: list[str] = []
    matched_elements: list = []

    for selector in CONTENT_SELECTORS:
        for element in soup.select(selector):
            # Skip if this element is an ancestor of an already-matched element
            is_ancestor = any(
                element in matched.parents for matched in matched_elements
            )
            # Skip if this element is a descendant of an already-matched element
            is_descendant = any(
                matched in element.parents for matched in matched_elements
            )
            if is_ancestor or is_descendant:
                continue

            text = element.get_text(strip=True)
            if len(text) >= MIN_CONTENT_LENGTH:
                content_parts.append(text)
                matched_elements.append(element)

    # Step 3: Fallback - if no selectors matched, extract all text from body
    if not content_parts:
        body = soup.find("body") or soup
        text = body.get_text(strip=True)
        if len(text) >= MIN_CONTENT_LENGTH:
            content_parts.append(text)

    result = "\n\n".join(content_parts)
    logger.info("Parsed HTML: extracted %d content blocks", len(content_parts))
    return result


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def fetch_voz_thread(url: str) -> str:
    """Fetch a Voz forum thread page using StealthyFetcher with retries."""
    logger.info("Fetching Voz thread: %s", url)
    try:
        fetcher = StealthyFetcher()
        # Solve cloudflare, set a 15-second timeout (15000 ms)
        response = fetcher.fetch(url, timeout=15000, solve_cloudflare=True)
        
        # Check HTTP status code
        if response.status != 200:
            logger.warning("Fetched page returned status code %d", response.status)
            
        html = response.text
        
        # Check for Cloudflare block or Access Denied
        if "Cloudflare" in html or "Access Denied" in html or response.status == 403:
            raise ForumBlockedException(f"Blocked by Anti-bot (Status: {response.status})")
            
        return html
    except Exception as e:
        logger.error("Failed to fetch Voz thread %s: %s", url, e)
        raise

