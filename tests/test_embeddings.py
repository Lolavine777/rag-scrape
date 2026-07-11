import pytest
from unittest.mock import MagicMock
from src.rag.embeddings import get_embedding

def test_get_embedding_success(mocker):
    mock_client = MagicMock()
    # Return dummy vector
    mock_client.embed_query.return_value = [0.1, 0.2, 0.3]
    
    mock_class = mocker.patch("src.rag.embeddings.GoogleGenerativeAIEmbeddings")
    mock_class.return_value = mock_client
    
    vector = get_embedding("Hello world")
    
    assert vector == [0.1, 0.2, 0.3]
    mock_client.embed_query.assert_called_once_with("Hello world")
