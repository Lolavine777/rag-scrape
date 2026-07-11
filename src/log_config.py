import json
import logging
import os
import sys
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as structured JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Construct standard log payload
        log_payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno,
        }
        
        # Include exception trace if present
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_payload)


def setup_logging(verbose: bool = False) -> None:
    """Configure system-wide logging.
    
    If verbose is True, sets root logger level to DEBUG. Otherwise INFO.
    If environment variable LOG_FORMAT is set to 'json', outputs structured JSON logs.
    Otherwise, defaults to clean human-readable output.
    """
    root_logger = logging.getLogger()
    
    # Determine log level
    log_level = logging.DEBUG if verbose else logging.INFO
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        
    # Create stderr handler
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(log_level)
    
    # Select formatter based on LOG_FORMAT env var
    log_format_env = os.environ.get("LOG_FORMAT", "").lower()
    if log_format_env == "json":
        formatter = JsonFormatter()
    else:
        # Standard human-readable console format
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    
    # Quiet down noisy third-party loggers unless verbose is explicitly enabled
    if not verbose:
        for noisy_logger in [
            "chromadb",
            "urllib3",
            "httpcore",
            "httpx",
            "google",
            "langchain",
            "langfuse",
            "asyncio",
            "pymilvus"
        ]:
            logging.getLogger(noisy_logger).setLevel(logging.WARNING)
