import logging
import re
import hashlib
from src.graph.state import AgentState
from src.scraper.core import fetch_voz_thread
from src.scraper.voz_parser import format_voz_thread
from src.rag.chunker import chunk_document
from src.rag.core import upsert_document, query_vector_db

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

def scraper_node(state: AgentState) -> dict:
    """Scrapes Voz thread from URL in state/question, chunks, indexes, and returns context.
    
    If no URL is found or if scraping fails, falls back to RAG database retrieval.
    """
    url = state.get("url") or extract_url_from_text(state["question"])
    
    if not url:
        logger.warning("No URL found in state or question. Falling back to local database retrieval.")
        results = query_vector_db(state["question"])
        context = "\n\n".join([r["content"] for r in results])
        return {"retrieved_context": context}
        
    try:
        html = fetch_voz_thread(url)
        formatted_text = format_voz_thread(html)
        
        # Save to database
        doc_id = get_url_id(url)
        metadata = {"url": url, "id": doc_id}
        
        chunks = chunk_document(formatted_text, metadata)
        logger.info("Splitting thread into %d chunks for indexing.", len(chunks))
        for chunk in chunks:
            upsert_document(chunk["content"], chunk["metadata"])
            
        return {"retrieved_context": formatted_text}
    except Exception as e:
        logger.error("Scraper node failed to scrape URL %s: %s. Falling back to database retrieval.", url, e)
        results = query_vector_db(state["question"])
        context = "\n\n".join([r["content"] for r in results])
        return {"retrieved_context": context}
