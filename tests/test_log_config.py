import logging
import json
import pytest
from src.log_config import JsonFormatter, setup_logging

def test_json_formatter():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=10,
        msg="Hello %s!",
        args=("world",),
        exc_info=None
    )
    
    formatted_msg = formatter.format(record)
    
    # Assert output is valid JSON
    data = json.loads(formatted_msg)
    assert data["name"] == "test_logger"
    assert data["level"] == "INFO"
    assert data["message"] == "Hello world!"
    assert "timestamp" in data

def test_setup_logging_verbose(mocker):
    # Mock logging root configuration functions
    mock_get_logger = mocker.patch("logging.getLogger")
    mock_root = MagicMock()
    mock_get_logger.return_value = mock_root
    
    # We will test setup_logging directly on root logger level
    setup_logging(verbose=True)
    
    # Assert setLevel was called on mock root logger
    mock_root.setLevel.assert_called_with(logging.DEBUG)


def test_setup_logging_default():
    setup_logging(verbose=False)
    
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO

from unittest.mock import MagicMock
