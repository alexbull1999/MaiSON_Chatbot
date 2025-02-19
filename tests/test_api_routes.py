import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api.controllers import chat_controller
from app.database import get_db
from app.database.schemas import GeneralChatResponse, PropertyChatResponse

# Create a test client
client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    session.commit = MagicMock()
    session.add = MagicMock()
    session.refresh = MagicMock()
    session.rollback = MagicMock()
    return session


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency."""

    def _get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    return _get_db


@pytest.fixture
def mock_chat_controller():
    """Create a mock chat controller."""
    original_controller = chat_controller
    chat_controller.handle_general_chat = AsyncMock()
    chat_controller.handle_property_chat = AsyncMock()
    yield chat_controller
    # Restore original controller after tests
    app.chat_controller = original_controller


def test_general_chat_endpoint_success(override_get_db, mock_chat_controller):
    """Test successful general chat endpoint."""
    # Mock the chat controller response
    mock_response = GeneralChatResponse(
        message="Hello! How can I help you today?",
        conversation_id=1,
        session_id="test_session",
        intent="greeting",
        context={},
    )
    mock_chat_controller.handle_general_chat.return_value = mock_response

    # Test request data
    request_data = {
        "message": "Hi there!",
        "session_id": "test_session",
        "user_id": "test_user",
    }

    # Make request to the endpoint
    response = client.post("/api/v1/chat/general", json=request_data)

    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Hello! How can I help you today?"
    assert response_data["conversation_id"] == 1
    assert response_data["session_id"] == "test_session"
    assert response_data["intent"] == "greeting"
    assert isinstance(response_data["context"], dict)


def test_general_chat_endpoint_missing_session_id(
    override_get_db, mock_chat_controller
):
    """Test general chat endpoint with missing session ID - should generate one."""
    # Mock the chat controller response with a generated session ID
    mock_response = GeneralChatResponse(
        message="Hello! How can I help you today?",
        conversation_id=1,
        session_id="generated_session_id",  # This would be a UUID in practice
        intent="greeting",
        context={},
    )
    mock_chat_controller.handle_general_chat.return_value = mock_response

    # Test request data without session_id
    request_data = {"message": "Hi there!", "user_id": "test_user"}

    # Make request to the endpoint
    response = client.post("/api/v1/chat/general", json=request_data)

    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert "session_id" in response_data  # Should have a generated session ID
    assert response_data["conversation_id"] == 1
    assert response_data["message"] == "Hello! How can I help you today?"

    # Verify that handle_general_chat was called with a generated session ID
    mock_chat_controller.handle_general_chat.assert_called_once()
    call_kwargs = mock_chat_controller.handle_general_chat.call_args.kwargs
    assert "session_id" in call_kwargs
    assert isinstance(call_kwargs["session_id"], str)


def test_property_chat_endpoint_success(override_get_db, mock_chat_controller):
    """Test successful property chat endpoint."""
    # Mock the chat controller response
    mock_response = PropertyChatResponse(
        message="I can help you with information about this property.",
        conversation_id=1,
        session_id="test_session",
        intent="property_info",
        property_context={},
    )
    mock_chat_controller.handle_property_chat.return_value = mock_response

    # Test request data
    request_data = {
        "message": "Tell me about this property",
        "session_id": "test_session",
        "user_id": "test_user",
        "property_id": "test_property",
        "seller_id": "test_seller",
    }

    # Make request to the endpoint
    response = client.post("/api/v1/chat/property", json=request_data)

    # Verify response
    assert response.status_code == 200
    response_data = response.json()
    assert (
        response_data["message"]
        == "I can help you with information about this property."
    )
    assert response_data["intent"] == "property_info"
    assert response_data["session_id"] == "test_session"
    assert "property_context" in response_data
    assert isinstance(response_data["property_context"], dict)


def test_property_chat_endpoint_missing_required_fields(override_get_db):
    """Test property chat endpoint with missing required fields."""
    request_data = {
        "message": "Tell me about this property",
        "session_id": "test_session",
        # Missing user_id, property_id, and seller_id
    }

    response = client.post("/api/v1/chat/property", json=request_data)

    assert response.status_code == 422  # Validation error


def test_general_chat_endpoint_error_handling(override_get_db, mock_chat_controller):
    """Test error handling in general chat endpoint."""
    # Mock the chat controller to raise an exception
    mock_chat_controller.handle_general_chat.side_effect = Exception(
        "Internal server error"
    )

    request_data = {
        "message": "Hi there!",
        "session_id": "test_session",
        "user_id": "test_user",
    }

    response = client.post("/api/v1/chat/general", json=request_data)

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_property_chat_endpoint_error_handling(override_get_db, mock_chat_controller):
    """Test error handling in property chat endpoint."""
    # Mock the chat controller to raise an exception
    mock_chat_controller.handle_property_chat.side_effect = Exception(
        "Internal server error"
    )

    request_data = {
        "message": "Tell me about this property",
        "session_id": "test_session",
        "user_id": "test_user",
        "property_id": "test_property",
        "seller_id": "test_seller",
    }

    response = client.post("/api/v1/chat/property", json=request_data)

    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]
