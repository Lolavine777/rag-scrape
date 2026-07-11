import logging
from typing import Optional
from langfuse.langchain import CallbackHandler
from src.config import settings

logger = logging.getLogger(__name__)

# Cache for the callback handler instance
_callback_handler: Optional[CallbackHandler] = None

def get_langfuse_callback() -> Optional[CallbackHandler]:
    """Lazy-initialize and return the LangFuse CallbackHandler singleton.
    
    If the public/secret keys are not configured, it returns None.
    If initialization fails, it catches the error and returns None to maintain robustness.
    """
    global _callback_handler
    
    if _callback_handler is not None:
        return _callback_handler
        
    # Check if required credentials are set
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        try:
            logger.info("Initializing LangFuse callback handler on host: %s", settings.langfuse_host)
            _callback_handler = CallbackHandler(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host
            )
            logger.info("LangFuse callback handler successfully initialized.")
        except Exception as e:
            logger.error("Failed to initialize LangFuse CallbackHandler: %s", e)
            _callback_handler = None
    else:
        logger.debug("LangFuse keys not configured. Tracing is disabled.")
        
    return _callback_handler
