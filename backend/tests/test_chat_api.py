import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.app.main import app

client = TestClient(app)

@patch('backend.app.routes.chat.rag_chain')
def test_chat_rag_endpoint(mock_rag_chain):
    # Arrange
    mock_rag_chain.invoke.return_value = "This is a mock RAG response."
    
    # Act
    response = client.post(
        "/api/v1/chat/rag",
        json={"message": "Hello", "user_id": "test_user"}
    )
    
    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["response"] == "This is a mock RAG response."
    mock_rag_chain.invoke.assert_called_once_with("Hello")
