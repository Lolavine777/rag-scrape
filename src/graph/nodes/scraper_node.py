import logging
import re
import hashlib
from src.graph.state import AgentState
from src.scraper.core import fetch_voz_thread, parse_forum_html
from src.scraper.voz_parser import parse_voz_thread_title, parse_voz_posts
from src.rag.chunker import chunk_document, chunk_posts
from src.rag.core import build_context, search, upsert_document

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
VOZ_THREAD_ID_PATTERN = re.compile(r't/([a-zA-Z0-9_-]+\.)?(\d+)')

def extract_url_from_text(text: str) -> str | None:
    """Find the first URL in the text that matches a Voz thread."""
    match = URL_PATTERN.search(text)
    if match:
        url = match.group(0)
        # Ensure it's a Voz URL (e.g. contains voz.vn)
        if "voz.vn" in url:
            return url
    return None

def get_url_id(url: str) -> str:
    """Generate a unique ID for the document metadata based on Voz URL thread ID, or fallback to hash."""
    match = VOZ_THREAD_ID_PATTERN.search(url)
    if match:
        thread_id = match.group(2)
        return f"thread-{thread_id}"
    
    # Fallback to md5 hash of url
    return f"url-{hashlib.md5(url.encode()).hexdigest()}"

def index_thread(html: str, url: str) -> list[dict]:
    """Parse a thread page into per-post chunks, upsert them, and return the chunks."""
    doc_id = get_url_id(url)
    title = parse_voz_thread_title(html)
    chunks = chunk_posts(title, parse_voz_posts(html), url, doc_id)
    if not chunks:  # not a XenForo thread: index the page's main text instead
        chunks = chunk_document(parse_forum_html(html), {"url": url, "id": doc_id, "title": title})

    logger.info("Indexing thread as %d chunks.", len(chunks))
    for chunk in chunks:
        upsert_document(chunk["content"], chunk["metadata"])
    return chunks

def scraper_node(state: AgentState) -> dict:
    """Scrapes Voz thread from URL in state/question, chunks, indexes, and returns numbered context.

    If no URL is found or if scraping fails, falls back to RAG database retrieval.
    """
    url = state.get("url") or extract_url_from_text(state["question"])

    if not url:
        logger.warning("No URL found in state or question. Falling back to local database retrieval.")
        return build_context(search(state["question"]))

    try:
        html = fetch_voz_thread(url)
        return build_context(index_thread(html, url))
    except Exception as e:
        logger.error("Scraper node failed to scrape URL %s: %s. Falling back to database retrieval.", url, e)
        return build_context(search(state["question"]))
