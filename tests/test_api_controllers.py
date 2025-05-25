import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

from app.api.controllers import ChatController
from app.database.models import (
    GeneralConversation,
    PropertyConversation,
)
from app.api.routes import Role


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
def chat_controller():
    """Create a ChatController instance with mocked dependencies."""
    # Create the controller
    controller = ChatController()

    # Mock the session manager
    mock_session_manager = MagicMock()
    mock_session_manager.is_session_valid = MagicMock(return_value=True)
    mock_session_manager.is_property_session_valid = MagicMock(return_value=True)
    mock_session_manager.refresh_session = AsyncMock()

    # Mock the message router
    controller.message_router = AsyncMock()
    controller.message_router.route_message.return_value = {
        "response": "Test response",
        "intent": "test_intent",
    }

    # Mock the seller buyer communication module
    controller.seller_buyer_communication = AsyncMock()

    # Set the mocked session manager
    controller.session_manager = mock_session_manager

    return controller


@pytest.mark.asyncio
async def test_handle_general_chat_new_conversation(db_session, chat_controller):
    """Test handling a general chat message for a new conversation."""
    # Mock message router response
    chat_controller.message_router.route_message.return_value = {
        "response": "Hello! How can I help you today?",
        "intent": "greeting",
    }

    # Create a mock conversation with proper datetime
    mock_conversation = MagicMock(spec=GeneralConversation)
    mock_conversation.id = 1
    mock_conversation.session_id = "test_session"
    mock_conversation.messages = []
    mock_conversation.context = {}
    mock_conversation.user_id = "test_user"
    mock_conversation.is_logged_in = False
    mock_conversation.last_message_at = datetime.utcnow()  # Use real datetime

    # Mock database query
    db_session.query.return_value.filter.return_value.first.return_value = (
        mock_conversation
    )

    # Test parameters
    message = "Hi there!"
    session_id = "test_session"
    user_id = "test_user"

    # Call the handler
    response = await chat_controller.handle_general_chat(
        message=message, session_id=session_id, user_id=user_id, db=db_session
    )

    # Verify response
    assert response.conversation_id == 1
    assert response.session_id == "test_session"
    assert response.intent == "greeting"


@pytest.mark.asyncio
async def test_handle_general_chat_existing_conversation(db_session, chat_controller):
    """Test handling a general chat message for an existing conversation."""
    # Create existing conversation with proper datetime
    existing_conv = MagicMock(spec=GeneralConversation)
    existing_conv.id = 1
    existing_conv.session_id = "test_session"
    existing_conv.user_id = "test_user"
    existing_conv.is_logged_in = False
    existing_conv.started_at = datetime.utcnow()
    existing_conv.last_message_at = datetime.utcnow()
    existing_conv.context = {}
    existing_conv.messages = []

    # Mock database query
    db_session.query.return_value.filter.return_value.first.return_value = existing_conv

    # Mock message router response
    chat_controller.message_router.route_message.return_value = {
        "response": "I understand you're asking about that.",
        "intent": "inquiry",
    }

    # Test parameters
    message = "What about this?"
    session_id = "test_session"
    user_id = "test_user"

    # Call the handler
    response = await chat_controller.handle_general_chat(
        message=message, session_id=session_id, user_id=user_id, db=db_session
    )

    # Verify response
    assert response.message == "I understand you're asking about that."
    assert response.intent == "inquiry"
    assert response.session_id == session_id


@pytest.mark.asyncio
async def test_handle_property_chat_new_conversation(db_session, chat_controller):
    """Test handling a new property chat conversation."""
    # Mock the message router to return a property inquiry intent
    chat_controller.message_router.route_message = AsyncMock(
        return_value={
            "intent": "property_inquiry",
            "response": None,
            "context": {}
        }
    )

    # Mock the property context module
    chat_controller.property_context.handle_inquiry = AsyncMock(
        return_value="This property is 1500 sq ft with 3 bedrooms and 2 bathrooms."
    )

    # Create a mock conversation
    mock_conversation = MagicMock(spec=PropertyConversation)
    mock_conversation.id = 1
    mock_conversation.session_id = "test_session"
    mock_conversation.messages = []
    mock_conversation.property_context = {}
    mock_conversation.user_id = "test_user"
    mock_conversation.property_id = "test_property"
    mock_conversation.role = Role.BUYER
    mock_conversation.counterpart_id = "test_seller"
    mock_conversation.conversation_status = "active"

    # Mock database queries
    db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_conversation,  # For conversation lookup
        None,  # For duplicate message check
    ]

    # Test data
    message = "Tell me about this property"
    user_id = "test_user"
    property_id = "test_property"
    role = Role.BUYER
    counterpart_id = "test_seller"
    session_id = "test_session"

    response = await chat_controller.handle_property_chat(
        message=message,
        user_id=user_id,
        property_id=property_id,
        role=role,
        counterpart_id=counterpart_id,
        session_id=session_id,
        db=db_session,
    )

    assert response.message == "This property is 1500 sq ft with 3 bedrooms and 2 bathrooms."
    assert response.conversation_id == 1
    assert response.session_id == "test_session"
    assert response.intent == "property_inquiry"


@pytest.mark.asyncio
async def test_handle_property_chat_existing_conversation(db_session, chat_controller):
    """Test handling an existing property chat conversation."""
    # Mock the message router to return a negotiation intent
    chat_controller.message_router.route_message = AsyncMock(
        return_value={
            "intent": "negotiation",
            "response": None,
            "context": {}
        }
    )

    # Mock the seller-buyer communication module
    chat_controller.seller_buyer_communication.handle_message = AsyncMock(
        return_value="Let me help you with your negotiation."
    )
    chat_controller.seller_buyer_communication.notify_counterpart = AsyncMock(
        return_value=True
    )

    # Create a mock existing conversation
    mock_conversation = MagicMock(spec=PropertyConversation)
    mock_conversation.id = 1
    mock_conversation.session_id = "test_session"
    mock_conversation.messages = []
    mock_conversation.property_context = {}
    mock_conversation.user_id = "test_user"
    mock_conversation.property_id = "test_property"
    mock_conversation.role = Role.SELLER
    mock_conversation.counterpart_id = "test_buyer"
    mock_conversation.conversation_status = "active"

    # Mock database queries
    db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_conversation,  # For conversation lookup
        None,  # For duplicate message check
    ]

    # Test data
    message = "I'd like to make a counter-offer"
    user_id = "test_user"
    property_id = "test_property"
    role = Role.SELLER
    counterpart_id = "test_buyer"
    session_id = "test_session"

    response = await chat_controller.handle_property_chat(
        message=message,
        user_id=user_id,
        property_id=property_id,
        role=role,
        counterpart_id=counterpart_id,
        session_id=session_id,
        db=db_session,
    )

    assert response.message == "Let me help you with your negotiation."
    assert response.conversation_id == 1
    assert response.session_id == "test_session"
    assert response.intent == "negotiation"
    chat_controller.seller_buyer_communication.notify_counterpart.assert_called_once()


@pytest.mark.asyncio
async def test_handle_property_chat_notification(db_session, chat_controller):
    """Test that notifications are sent during property chat."""
    # Mock the message router to return a buyer_seller_communication intent
    chat_controller.message_router.route_message = AsyncMock(
        return_value={
            "intent": "buyer_seller_communication",
            "response": None,
            "context": {}
        }
    )

    # Mock the seller-buyer communication module
    chat_controller.seller_buyer_communication.handle_message = AsyncMock(
        return_value="I'll forward your offer to the seller."
    )
    chat_controller.seller_buyer_communication.notify_counterpart = AsyncMock(
        return_value=True
    )

    # Create a mock existing conversation
    mock_conversation = MagicMock(spec=PropertyConversation)
    mock_conversation.id = 1
    mock_conversation.session_id = "test_session"
    mock_conversation.messages = []
    mock_conversation.property_context = {}
    mock_conversation.user_id = "test_buyer"
    mock_conversation.property_id = "test_property"
    mock_conversation.role = Role.BUYER
    mock_conversation.counterpart_id = "test_seller"
    mock_conversation.conversation_status = "active"

    # Mock database queries
    db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_conversation,  # For conversation lookup
        None,  # For duplicate message check
    ]

    # Test data
    message = "I'd like to make an offer of $450,000"
    user_id = "test_buyer"
    property_id = "test_property"
    role = Role.BUYER
    counterpart_id = "test_seller"
    session_id = "test_session"

    response = await chat_controller.handle_property_chat(
        message=message,
        user_id=user_id,
        property_id=property_id,
        role=role,
        counterpart_id=counterpart_id,
        session_id=session_id,
        db=db_session,
    )

    assert response.message == "I'll forward your offer to the seller."
    assert response.conversation_id == 1
    assert response.session_id == "test_session"
    assert response.intent == "buyer_seller_communication"
    chat_controller.seller_buyer_communication.notify_counterpart.assert_called_once()


@pytest.mark.asyncio
async def test_handle_property_chat_error(db_session, chat_controller):
    """Test error handling in property chat."""
    # Mock an expired property conversation
    mock_conversation = MagicMock(spec=PropertyConversation)
    mock_conversation.conversation_status = "closed"  # Simulate expired/closed session
    mock_conversation.id = 1
    mock_conversation.session_id = "test_session"
    mock_conversation.messages = []
    mock_conversation.property_context = {}
    mock_conversation.user_id = "test_user"
    mock_conversation.property_id = "test_property"
    mock_conversation.role = Role.BUYER
    mock_conversation.counterpart_id = "test_seller"

    # Mock database to return the conversation
    db_session.query.return_value.filter.return_value.first.return_value = (
        mock_conversation
    )

    # Set session manager to indicate invalid session
    chat_controller.session_manager.is_property_session_valid.return_value = False

    # Test the chat handling with expired session
    with pytest.raises(HTTPException) as exc_info:
        await chat_controller.handle_property_chat(
            message="test message",
            user_id="test_user",
            property_id="test_property",
            role=Role.BUYER,
            counterpart_id="test_seller",
            session_id="test_session",
            db=db_session,
        )
    assert exc_info.value.status_code == 401
    assert "expired" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_handle_general_chat_error(db_session, chat_controller):
    """Test error handling in general chat."""
    # Mock an expired general conversation
    mock_conversation = MagicMock(spec=GeneralConversation)
    mock_conversation.is_logged_in = True  # Simulate authenticated user
    mock_conversation.last_message_at = datetime.utcnow()
    db_session.query.return_value.filter.return_value.first.return_value = (
        mock_conversation
    )

    # Mock database error
    db_session.commit.side_effect = Exception("Database error")

    # Test that it raises the correct exception
    with pytest.raises(HTTPException) as exc_info:
        await chat_controller.handle_general_chat(
            message="Test message",
            session_id="test_session",
            user_id="test_user",
            db=db_session,
        )

    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_handle_expired_anonymous_session(db_session, chat_controller):
    """Test handling of expired anonymous session."""
    # Create expired anonymous conversation
    expired_conv = MagicMock(spec=GeneralConversation)
    expired_conv.id = 1
    expired_conv.session_id = "old_session"
    expired_conv.user_id = None
    expired_conv.is_logged_in = False
    expired_conv.last_message_at = datetime.utcnow()
    expired_conv.messages = []
    expired_conv.context = {}

    # Create new conversation that will be created after expiry
    new_conv = MagicMock(spec=GeneralConversation)
    new_conv.id = 2
    new_conv.session_id = str(uuid.uuid4())  # Generate a new session ID
    new_conv.user_id = None
    new_conv.is_logged_in = False
    new_conv.last_message_at = datetime.utcnow()
    new_conv.messages = []
    new_conv.context = {}

    # Set up the database mock to return the expired conversation first
    db_session.query.return_value.filter.return_value.first.side_effect = [
        expired_conv,
        new_conv,
    ]

    # Set session manager to indicate expired session for the first call
    chat_controller.session_manager.is_session_valid.return_value = False

    # Test the chat handling with expired session
    response = await chat_controller.handle_general_chat(
        message="test message", session_id="old_session", user_id=None, db=db_session
    )

    # Verify that a new session was created
    assert response.session_id != "old_session"
    assert response.session_id == new_conv.session_id
