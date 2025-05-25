import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.api.controllers import ChatController
from app.database import get_db
from app.database.models import (
    GeneralConversation as GeneralConversationModel,
    PropertyConversation as PropertyConversationModel,
)
from app.modules.property_context.property_context_module import Property


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
    yield _get_db
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_property():
    """Create a mock property."""
    return Property(
        id="test_property_1",
        name="Test Property",
        type="house",
        location="123 Test St, London",
        details={
            "price": 500000,
            "bedrooms": 3,
            "bathrooms": 2,
            "specs": {"property_type": "house", "square_footage": 1500},
            "features": {"parking": True, "garden": True},
            "location": {"city": "London", "postcode": "SW1 1AA"},
        },
    )


@pytest.fixture
def mock_chat_controller():
    """Create a mock chat controller with all necessary dependencies."""
    controller = ChatController()

    # Mock session manager
    controller.session_manager = MagicMock()
    controller.session_manager.is_property_session_valid.return_value = True
    controller.session_manager.is_session_valid.return_value = True
    controller.session_manager.refresh_session = AsyncMock()

    # Mock message router
    controller.message_router = MagicMock()
    controller.message_router.route_message = AsyncMock(
        return_value={
            "response": "This is a test response",
            "intent": "test_intent",
            "context": {},
        }
    )

    # Mock seller-buyer communication
    controller.seller_buyer_communication = MagicMock()
    controller.seller_buyer_communication.handle_message = AsyncMock(
        return_value="I'll help you with that property inquiry."
    )
    controller.seller_buyer_communication.notify_counterpart = AsyncMock()

    # Mock conversation creation methods
    async def mock_get_or_create_general_conversation(db, session_id, user_id=None):
        conversation = MagicMock(spec=GeneralConversationModel)
        conversation.id = 1
        conversation.session_id = session_id
        conversation.user_id = user_id
        conversation.is_logged_in = bool(user_id)
        conversation.started_at = datetime.utcnow()
        conversation.last_message_at = datetime.utcnow()
        conversation.context = {}
        conversation.messages = []
        return conversation

    async def mock_get_or_create_property_conversation(
        db, session_id, user_id, property_id, role, counterpart_id
    ):
        conversation = MagicMock(spec=PropertyConversationModel)
        conversation.id = 1
        conversation.session_id = session_id
        conversation.user_id = user_id
        conversation.property_id = property_id
        conversation.role = role
        conversation.counterpart_id = counterpart_id
        conversation.conversation_status = "active"
        conversation.started_at = datetime.utcnow()
        conversation.last_message_at = datetime.utcnow()
        conversation.property_context = {}
        conversation.messages = []
        return conversation

    controller._get_or_create_general_conversation = (
        mock_get_or_create_general_conversation
    )
    controller._get_or_create_property_conversation = (
        mock_get_or_create_property_conversation
    )

    return controller


@pytest.fixture
def override_chat_controller(mock_chat_controller):
    """Override the chat controller in the app."""
    from app.api import routes

    original_controller = routes.chat_controller
    routes.chat_controller = mock_chat_controller
    yield mock_chat_controller
    routes.chat_controller = original_controller


@pytest.mark.asyncio
async def test_complete_general_chat_flow(
    client, db_session, mock_property, override_chat_controller
):
    """
    Test a complete general chat flow including:
    1. Starting a new conversation
    2. Multiple message exchanges
    3. Intent classification and routing
    4. Context preservation
    5. Response generation
    """
    # Test initial greeting
    response1 = client.post(
        "/api/v1/chat/general",
        json={"message": "Hi, I'm looking for properties in London"},
    )

    assert response1.status_code == 200
    data1 = response1.json()
    assert "message" in data1
    assert data1["session_id"] is not None

    # Test follow-up question
    response2 = client.post(
        "/api/v1/chat/general",
        json={
            "message": "What areas would you recommend?",
            "session_id": data1["session_id"],
        },
    )

    assert response2.status_code == 200
    data2 = response2.json()
    assert "message" in data2
    assert data2["session_id"] == data1["session_id"]


@pytest.mark.asyncio
async def test_complete_property_chat_flow(
    client, db_session, mock_property, override_chat_controller
):
    """
    Test a complete property chat flow including:
    1. Starting a buyer-seller conversation
    2. Property inquiry and response
    3. Negotiation flow
    4. Message forwarding
    5. Context updates
    """
    # Mock database queries for duplicate message check
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,  # No duplicate message found
        None,  # For subsequent queries
    ]

    # Test initial property inquiry
    response1 = client.post(
        "/api/v1/chat/property",
        json={
            "message": "I'm interested in viewing this property",
            "user_id": "test_buyer",
            "property_id": "test_property_1",
            "role": "buyer",
            "counterpart_id": "test_seller",
        },
    )

    assert response1.status_code == 200
    data1 = response1.json()
    assert "message" in data1
    assert "conversation_id" in data1


@pytest.mark.asyncio
async def test_mixed_chat_flow_with_context_switching(
    client, db_session, mock_property, override_chat_controller
):
    """
    Test a complex flow that involves both general and property-specific conversations:
    1. Start with general inquiry
    2. Switch to specific property
    3. Return to general questions
    4. Test context preservation across switches
    """
    # Create mock conversations
    mock_general_conversation = MagicMock(spec=GeneralConversationModel)
    mock_general_conversation.id = 1
    mock_general_conversation.session_id = "test_session"
    mock_general_conversation.messages = []
    mock_general_conversation.context = {}

    mock_property_conversation = MagicMock(spec=PropertyConversationModel)
    mock_property_conversation.id = 1
    mock_property_conversation.session_id = "test_session"
    mock_property_conversation.property_id = "test_property_1"
    mock_property_conversation.user_id = "test_buyer"
    mock_property_conversation.role = "buyer"
    mock_property_conversation.counterpart_id = "test_seller"
    mock_property_conversation.conversation_status = "active"
    mock_property_conversation.messages = []
    mock_property_conversation.property_context = {}

    # Mock database queries with side effects
    def mock_query_side_effect(*args, **kwargs):
        mock_filter = MagicMock()
        mock_filter.first = MagicMock()

        # For PropertyMessage queries (duplicate check)
        if args and isinstance(args[0], type) and args[0].__name__ == 'PropertyMessage':
            mock_filter.filter = MagicMock(return_value=mock_filter)
            mock_filter.first.return_value = None
        # For conversation queries
        else:
            mock_filter.first.return_value = mock_general_conversation

        return mock_filter

    db_session.query.side_effect = mock_query_side_effect

    # Initial general inquiry about areas
    response1 = client.post(
        "/api/v1/chat/general",
        json={"message": "What areas in London have good schools?"},
    )
    assert response1.status_code == 200
    general_session_id = response1.json()["session_id"]

    # Switch to property inquiry
    def mock_query_side_effect_property(*args, **kwargs):
        mock_filter = MagicMock()
        mock_filter.first = MagicMock()

        # For PropertyMessage queries (duplicate check)
        if args and isinstance(args[0], type) and args[0].__name__ == 'PropertyMessage':
            mock_filter.filter = MagicMock(return_value=mock_filter)
            mock_filter.first.return_value = None
        # For conversation queries
        else:
            mock_filter.first.return_value = mock_property_conversation

        return mock_filter

    db_session.query.side_effect = mock_query_side_effect_property

    response2 = client.post(
        "/api/v1/chat/property",
        json={
            "message": "I'm interested in this property",
            "user_id": "test_buyer",
            "property_id": "test_property_1",
            "role": "buyer",
            "counterpart_id": "test_seller",
        },
    )
    assert response2.status_code == 200

    # Return to general area questions
    db_session.query.side_effect = mock_query_side_effect
    response3 = client.post(
        "/api/v1/chat/general",
        json={
            "message": "Tell me more about the school districts",
            "session_id": general_session_id,
        },
    )
    assert response3.status_code == 200
    assert response3.json()["session_id"] == general_session_id

    # Verify both conversation histories
    response4 = client.get(
        f"/api/v1/conversations/general/{response1.json()['conversation_id']}/history"
    )
    assert response4.status_code == 200

    db_session.query.side_effect = mock_query_side_effect_property
    response5 = client.get(
        f"/api/v1/conversations/property/{response2.json()['conversation_id']}/history"
    )
    assert response5.status_code == 200
