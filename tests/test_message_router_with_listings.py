import pytest
from unittest.mock import MagicMock, AsyncMock
from app.modules.message_router import MessageRouter
from app.modules.intent_classification import Intent


@pytest.fixture
def message_router():
    """Create a MessageRouter with mocked dependencies."""
    router = MessageRouter()
    
    # Mock all modules with AsyncMock for async methods
    router.intent_classifier = MagicMock()
    router.intent_classifier.classify = AsyncMock()
    router.intent_classifier.classify_general = AsyncMock()
    
    router.property_context = MagicMock()
    router.advisory_module = MagicMock()
    router.advisory_module.handle_general_inquiry = AsyncMock()
    
    router.communication_module = MagicMock()
    router.communication_module.handle_unclear_intent = AsyncMock()
    
    router.seller_buyer_communication = MagicMock()
    router.context_manager = MagicMock()
    
    router.greeting_module = MagicMock()
    router.greeting_module.handle_greeting = AsyncMock()
    
    router.website_info_module = MagicMock()
    router.website_info_module.handle_website_functionality = AsyncMock()
    router.website_info_module.handle_company_information = AsyncMock()
    
    router.property_listings_module = MagicMock()
    router.property_listings_module.handle_inquiry = AsyncMock()
    
    return router


@pytest.mark.asyncio
async def test_route_property_listings_inquiry_general_chat(message_router):
    """Test routing of property listings inquiries in general chat."""
    # Mock intent classification
    message_router.intent_classifier.classify_general.return_value = Intent.GENERAL_QUESTION
    message_router.intent_classifier.classify.return_value = Intent.PROPERTY_LISTINGS_INQUIRY
    
    # Mock module response
    message_router.property_listings_module.handle_inquiry.return_value = "Here are some properties that match your criteria..."
    
    # Test parameters
    message = "Show me 3-bedroom houses in London"
    context = {"session_id": "test_session", "user_id": "user123"}
    
    # Call the router
    response = await message_router.route_message(message, context, chat_type="general")
    
    # Verify intent classification
    message_router.intent_classifier.classify_general.assert_called_once_with(message)
    message_router.intent_classifier.classify.assert_called_once_with(message, {"session_id": "test_session", "user_id": "user123"})
    
    # Verify module call
    message_router.property_listings_module.handle_inquiry.assert_called_once()
    
    # Verify response
    assert response["response"] == "Here are some properties that match your criteria..."
    assert response["intent"] == "property_listings_inquiry"


@pytest.mark.asyncio
async def test_route_property_listings_inquiry_property_chat(message_router):
    """Test routing of property listings inquiries in property chat."""
    # Mock intent classification
    message_router.intent_classifier.classify.return_value = Intent.PROPERTY_LISTINGS_INQUIRY
    
    # Mock module response via _route_intent
    message_router.property_listings_module.handle_inquiry.return_value = "Here are some properties that match your criteria..."
    
    # Test parameters
    message = "Show me similar properties to this one"
    context = {
        "session_id": "test_session",
        "user_id": "user123",
        "property_id": "prop123",
        "role": "buyer"
    }
    
    # Call the router
    response = await message_router.route_message(message, context, chat_type="property")
    
    # Verify intent classification
    message_router.intent_classifier.classify.assert_called_once_with(message, {
        "session_id": "test_session",
        "user_id": "user123",
        "property_id": "prop123",
        "role": "buyer",
        "intent": "property_listings_inquiry"
    })
    
    # Verify response
    assert response["intent"] == "property_listings_inquiry"


@pytest.mark.asyncio
async def test_route_intent_with_property_listings(message_router):
    """Test _route_intent with property listings inquiry."""
    # Mock module response
    message_router.property_listings_module.handle_inquiry.return_value = "Here are some properties that match your criteria..."
    
    # Test parameters
    message = "Show me 3-bedroom houses in London"
    context = {"session_id": "test_session"}
    
    # Call _route_intent directly
    response = await message_router._route_intent(Intent.PROPERTY_LISTINGS_INQUIRY, message, context)
    
    # Verify module call
    message_router.property_listings_module.handle_inquiry.assert_called_once_with(message, context)
    
    # Verify response
    assert response == "Here are some properties that match your criteria..." 