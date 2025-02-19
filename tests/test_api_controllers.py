import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.api.controllers import ChatController
from app.database.models import (
    GeneralConversation, GeneralMessage,
    PropertyConversation, PropertyMessage
)

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
    controller = ChatController()
    controller.message_router = AsyncMock()
    return controller

@pytest.mark.asyncio
async def test_handle_general_chat_new_conversation(db_session, chat_controller):
    """Test handling a general chat message for a new conversation."""
    # Mock message router response
    chat_controller.message_router.route_message.return_value = {
        "response": "Hello! How can I help you today?",
        "intent": "greeting"
    }

    # Create a mock conversation
    mock_conversation = MagicMock(spec=GeneralConversation)
    mock_conversation.id = 1
    mock_conversation.session_id = "test_session"
    mock_conversation.messages = []
    mock_conversation.context = {}
    mock_conversation.user_id = "test_user"
    
    # Mock database query to return our mock conversation
    db_session.query.return_value.filter.return_value.first.return_value = mock_conversation

    # Test parameters
    message = "Hi there!"
    session_id = "test_session"
    user_id = "test_user"

    # Call the handler
    response = await chat_controller.handle_general_chat(
        message=message,
        session_id=session_id,
        user_id=user_id,
        db=db_session
    )

    # Verify response
    assert response.conversation_id == 1
    assert response.session_id == "test_session"
    assert response.intent == "greeting"

@pytest.mark.asyncio
async def test_handle_general_chat_existing_conversation(db_session, chat_controller):
    """Test handling a general chat message for an existing conversation."""
    # Create existing conversation
    existing_conv = GeneralConversation(
        id=1,
        session_id="test_session",
        user_id="test_user",
        started_at=datetime.utcnow(),
        last_message_at=datetime.utcnow(),
        context={}
    )
    existing_conv.messages = []
    
    # Mock database query
    db_session.query.return_value.filter.return_value.first.return_value = existing_conv
    
    # Mock message router response
    chat_controller.message_router.route_message.return_value = {
        "response": "I understand you're asking about that.",
        "intent": "inquiry"
    }
    
    # Test parameters
    message = "What about this?"
    session_id = "test_session"
    user_id = "test_user"
    
    # Call the handler
    response = await chat_controller.handle_general_chat(
        message=message,
        session_id=session_id,
        user_id=user_id,
        db=db_session
    )
    
    # Verify messages were added to existing conversation
    assert db_session.add.call_count == 2  # user message + assistant message
    
    # Verify the messages were created with correct types
    add_calls = db_session.add.call_args_list
    assert isinstance(add_calls[0].args[0], GeneralMessage)
    assert isinstance(add_calls[1].args[0], GeneralMessage)
    
    assert response.message == "I understand you're asking about that."
    assert response.intent == "inquiry"
    assert response.session_id == session_id

@pytest.mark.asyncio
async def test_handle_property_chat_new_conversation(db_session, chat_controller):
    """Test handling a property chat message for a new conversation."""
    # Mock message router response
    chat_controller.message_router.route_message.return_value = {
        "response": "I can help you with information about this property.",
        "intent": "property_info"
    }

    # Create a mock conversation
    mock_conversation = MagicMock(spec=PropertyConversation)
    mock_conversation.id = 1
    mock_conversation.session_id = "test_session"
    mock_conversation.messages = []
    mock_conversation.property_context = {}
    mock_conversation.user_id = "test_user"
    mock_conversation.property_id = "test_property"
    mock_conversation.seller_id = "test_seller"
    
    # Mock database query to return our mock conversation
    db_session.query.return_value.filter.return_value.first.return_value = mock_conversation

    # Test parameters
    message = "Tell me about this property"
    session_id = "test_session"
    user_id = "test_user"
    property_id = "test_property"
    seller_id = "test_seller"

    # Call the handler
    response = await chat_controller.handle_property_chat(
        message=message,
        user_id=user_id,
        property_id=property_id,
        seller_id=seller_id,
        session_id=session_id,
        db=db_session
    )

    # Verify response
    assert response.conversation_id == 1
    assert response.session_id == "test_session"
    assert response.intent == "property_info"

@pytest.mark.asyncio
async def test_handle_property_chat_existing_conversation(db_session, chat_controller):
    """Test handling a property chat message for an existing conversation."""
    # Create existing conversation
    existing_conv = PropertyConversation(
        id=1,
        session_id="test_session",
        user_id="test_user",
        property_id="test_property",
        seller_id="test_seller",
        started_at=datetime.utcnow(),
        last_message_at=datetime.utcnow(),
        property_context={}
    )
    existing_conv.messages = []
    
    # Mock database query
    db_session.query.return_value.filter.return_value.first.return_value = existing_conv
    
    # Mock message router response
    chat_controller.message_router.route_message.return_value = {
        "response": "The property has 3 bedrooms.",
        "intent": "property_details"
    }
    
    # Test parameters
    message = "How many bedrooms?"
    session_id = "test_session"
    user_id = "test_user"
    property_id = "test_property"
    seller_id = "test_seller"
    
    # Call the handler
    response = await chat_controller.handle_property_chat(
        message=message,
        user_id=user_id,
        property_id=property_id,
        seller_id=seller_id,
        session_id=session_id,
        db=db_session
    )
    
    # Verify messages were added to existing conversation
    assert db_session.add.call_count == 2  # user message + assistant message
    
    # Verify the messages were created with correct types
    add_calls = db_session.add.call_args_list
    assert isinstance(add_calls[0].args[0], PropertyMessage)
    assert isinstance(add_calls[1].args[0], PropertyMessage)
    
    assert response.message == "The property has 3 bedrooms."
    assert response.intent == "property_details"
    assert response.session_id == session_id

@pytest.mark.asyncio
async def test_handle_general_chat_error(db_session, chat_controller):
    """Test error handling in general chat."""
    # Mock database error
    db_session.commit.side_effect = Exception("Database error")
    
    # Test parameters
    message = "Hi there!"
    session_id = "test_session"
    user_id = "test_user"
    
    # Verify error handling
    with pytest.raises(HTTPException) as exc_info:
        await chat_controller.handle_general_chat(
            message=message,
            session_id=session_id,
            user_id=user_id,
            db=db_session
        )
    
    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)
    assert db_session.rollback.called

@pytest.mark.asyncio
async def test_handle_property_chat_error(db_session, chat_controller):
    """Test error handling in property chat."""
    # Mock database error
    db_session.commit.side_effect = Exception("Database error")
    
    # Test parameters
    message = "Hi there!"
    session_id = "test_session"
    user_id = "test_user"
    property_id = "test_property"
    seller_id = "test_seller"
    
    # Verify error handling
    with pytest.raises(HTTPException) as exc_info:
        await chat_controller.handle_property_chat(
            message=message,
            user_id=user_id,
            property_id=property_id,
            seller_id=seller_id,
            session_id=session_id,
            db=db_session
        )
    
    assert exc_info.value.status_code == 500
    assert "Database error" in str(exc_info.value.detail)
    assert db_session.rollback.called 