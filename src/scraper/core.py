import logging
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_exponential

from .exceptions import ForumBlockedException

logger = logging.getLogger(__name__)

# Identify the tool honestly so site operators can see and contact it
USER_AGENT = "rag-scrape/0.1 (+https://github.com/Lolavine777/rag-scrape)"

# Minimum seconds between two requests to the same host
MIN_REQUEST_INTERVAL = 2.0

# Title of Cloudflare challenge pages; body markers like "challenge-platform" also appear on normal pages
CHALLENGE_TITLE = "<title>Just a moment...</title>"

_last_request_at: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser] = {}

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


def _throttle(host: str) -> None:
    wait = _last_request_at.get(host, 0.0) + MIN_REQUEST_INTERVAL - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_request_at[host] = time.monotonic()


def _http_get(url: str, timeout: float = 15) -> tuple[int, str]:
    """GET a URL with the tool's User-Agent and rate limit; return (status, body)."""
    _throttle(urlsplit(url).netloc)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.status, response.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def _allowed_by_robots(url: str) -> bool:
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    parser = _robots.get(origin)
    if parser is None:
        parser = urllib.robotparser.RobotFileParser()
        status, body = _http_get(f"{origin}/robots.txt")
        if status in (401, 403):
            parser.disallow_all = True
        elif status == 200:
            parser.parse(body.splitlines())
        else:
            parser.allow_all = True  # no robots.txt means no stated restrictions
        _robots[origin] = parser
    return parser.can_fetch(USER_AGENT, url)


def load_saved_thread(path: str) -> tuple[str, str | None]:
    """Read a thread page saved from a browser; return its HTML and canonical URL, if any."""
    html = Path(path).read_text(encoding="utf-8", errors="replace")
    link = BeautifulSoup(html, "html.parser").select_one('link[rel="canonical"]')
    return html, (link.get("href") if link else None)


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
    # Only transient network and server errors are retried; a refusal stays a refusal
    retry=retry_if_not_exception_type((ForumBlockedException, ValueError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def fetch_voz_thread(url: str) -> str:
    """Fetch a forum thread politely: honest User-Agent, robots.txt, per-host rate limit.

    Anti-bot challenges are never solved or bypassed. When a site refuses
    automated access, save the page from a browser and use `main.py ingest`.
    """
    logger.info("Fetching thread: %s", url)
    if not _allowed_by_robots(url):
        raise ForumBlockedException(f"robots.txt disallows fetching {url}")

    status, html = _http_get(url)
    if status in (401, 403, 429) or CHALLENGE_TITLE in html:
        raise ForumBlockedException(
            f"{urlsplit(url).netloc} refused automated access (HTTP {status}). "
            "Save the thread page from your browser and run: main.py ingest <file>"
        )
    if status >= 500:
        raise ConnectionError(f"Server error {status} for {url}")
    if status != 200:
        raise ValueError(f"HTTP {status} for {url}")
    return html

