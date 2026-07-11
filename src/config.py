import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Project-wide configuration loaded from environment variables.

    Uses pydantic-settings to automatically read from .env file and
    environment variables. This gives us type validation, defaults,
    and a single source of truth for all config.
    """

    # ChromaDB
    chroma_persist_directory: str = "./chroma_data"
    chroma_collection_name: str = "forum_documents"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # LangFuse
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"


    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
logger.info(
    "Config loaded: Chroma dir=%s, Collection=%s",
    settings.chroma_persist_directory,
    settings.chroma_collection_name,
)
