import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import settings

logger = logging.getLogger(__name__)

_embeddings_client = None

def _get_embeddings_client() -> GoogleGenerativeAIEmbeddings:
    """Lazy-initialize and return the GoogleGenerativeAIEmbeddings client singleton."""
    global _embeddings_client
    if _embeddings_client is None:
        _embeddings_client = GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=settings.gemini_api_key,
        )
        logger.info("Initialized GoogleGenerativeAIEmbeddings client with model: %s", 
                    settings.gemini_embedding_model)
    return _embeddings_client

def get_embedding(text: str) -> list[float]:
    """Generate a vector embedding using Gemini API for the given text."""
    client = _get_embeddings_client()
    return client.embed_query(text)
