import pytest
from src.observability import get_langfuse_callback

def test_get_langfuse_callback_disabled(mocker):
    # Mock settings to have empty keys
    mock_settings = mocker.patch("src.observability.settings")
    mock_settings.langfuse_public_key = ""
    mock_settings.langfuse_secret_key = ""
    
    # Reset internal singleton cache for clean test
    mocker.patch("src.observability._callback_handler", None)
    
    handler = get_langfuse_callback()
    assert handler is None

def test_get_langfuse_callback_enabled(mocker):
    # Mock settings to have valid keys
    mock_settings = mocker.patch("src.observability.settings")
    mock_settings.langfuse_public_key = "pk-lf-12345"
    mock_settings.langfuse_secret_key = "sk-lf-67890"
    mock_settings.langfuse_host = "https://cloud.langfuse.com"
    
    # Reset internal singleton cache
    mocker.patch("src.observability._callback_handler", None)
    
    # Mock CallbackHandler to prevent network calls during testing
    mock_handler_class = mocker.patch("src.observability.CallbackHandler")
    mock_handler_instance = mock_handler_class.return_value
    
    handler = get_langfuse_callback()
    
    # Assert CallbackHandler was instantiated with correct keys
    mock_handler_class.assert_called_once_with(
        public_key="pk-lf-12345",
        secret_key="sk-lf-67890",
        host="https://cloud.langfuse.com"
    )
    assert handler == mock_handler_instance
