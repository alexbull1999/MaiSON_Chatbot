import pytest
from unittest.mock import AsyncMock
from app.modules.message_router import MessageRouter
from app.modules.intent_classification.intent_classifier import Intent
from app.modules.property_context.property_context_module import Property


def test_message_router_initialization():
    router = MessageRouter()
    assert router.intent_classifier is not None
    assert router.context_manager is not None
    assert router.property_context is not None
    assert router.advisory_module is not None
    assert router.communication_module is not None


@pytest.fixture
def message_router():
    router = MessageRouter()
    router.intent_classifier = AsyncMock()
    router.property_context = AsyncMock()
    router.advisory_module = AsyncMock()
    router.communication_module = AsyncMock()
    router.seller_buyer_communication = AsyncMock()
    router.context_manager = AsyncMock()
    return router


@pytest.mark.asyncio
async def test_process_message():
    router = MessageRouter()
    message = "Tell me about this property"
    response = await router.process_message(message)
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_route_intent_property_inquiry():
    router = MessageRouter()

    # Mock property context module methods
    router.property_context.get_or_fetch_property = AsyncMock()
    router.property_context._fetch_similar_properties = AsyncMock(return_value=[])
    router.property_context._get_area_insights = AsyncMock(return_value={})
    router.property_context.llm_client.generate_response = AsyncMock(
        return_value="This is a beautiful 2-bedroom apartment in Test Location."
    )

    # Create mock property data
    mock_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location",
        details={
            "bedrooms": 2,
            "bathrooms": 1,
            "specs": {"property_type": "apartment", "square_footage": 1000},
            "features": {"parking": True},
            "location": {"city": "Test City"},
        },
    )
    router.property_context.get_or_fetch_property.return_value = mock_property

    # Test with property context
    response = await router._route_intent(
        Intent.PROPERTY_INQUIRY, "Tell me about this property", {"property_id": "123"}
    )

    assert isinstance(response, str)
    assert "beautiful" in response
    assert "apartment" in response
    assert "Test Location" in response

    # Test without property context
    response = await router._route_intent(
        Intent.PROPERTY_INQUIRY, "Tell me about this property", {}
    )
    assert "need a property ID" in response


@pytest.mark.asyncio
async def test_route_intent_price_inquiry():
    router = MessageRouter()

    # Mock property context module methods
    router.property_context.get_or_fetch_property = AsyncMock()
    router.property_context._fetch_similar_properties = AsyncMock(return_value=[])
    router.property_context.llm_client.generate_response = AsyncMock(
        return_value="The property is priced at £500,000."
    )

    # Create mock property data
    mock_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location",
        details={
            "price": 500000,
            "specs": {"property_type": "apartment", "square_footage": 1000},
            "location": {"city": "Test City"},
            "days_on_market": 30,
        },
    )
    router.property_context.get_or_fetch_property.return_value = mock_property

    # Test with property context
    response = await router._route_intent(
        Intent.PRICE_INQUIRY, "How much does it cost?", {"property_id": "123"}
    )

    assert isinstance(response, str)
    assert "£500,000" in response

    # Test without property context
    response = await router._route_intent(
        Intent.PRICE_INQUIRY, "How much does it cost?", {}
    )
    assert "need a property ID" in response


@pytest.mark.asyncio
async def test_route_property_inquiry(message_router):
    """Test routing of property inquiry messages."""
    message_router.intent_classifier.classify.return_value = Intent.PROPERTY_INQUIRY
    message_router.property_context.handle_inquiry.return_value = (
        "Property details response"
    )

    response = await message_router.process_message("Tell me about this property")
    assert response == "Property details response"
    message_router.property_context.handle_inquiry.assert_called_once()


@pytest.mark.asyncio
async def test_route_availability_request(message_router):
    """Test routing of availability request messages."""
    message_router.intent_classifier.classify.return_value = (
        Intent.AVAILABILITY_AND_BOOKING_REQUEST
    )
    message_router.property_context.handle_booking.return_value = "Booking response"

    response = await message_router.process_message("When can I view the property?")
    assert response == "Booking response"
    message_router.property_context.handle_booking.assert_called_once()


@pytest.mark.asyncio
async def test_route_buyer_seller_communication(message_router):
    """Test routing of buyer-seller communication messages."""
    message_router.intent_classifier.classify.return_value = (
        Intent.BUYER_SELLER_COMMUNICATION
    )
    message_router.seller_buyer_communication.handle_message.return_value = (
        "Communication response"
    )

    context = {
        "user_id": "buyer123",
        "role": "buyer",
        "counterpart_id": "seller456",
        "property_id": "prop789",
    }

    response = await message_router.process_message(
        "Could you provide more details about the renovation?", context=context
    )
    assert response == "Communication response"
    message_router.seller_buyer_communication.handle_message.assert_called_once()


@pytest.mark.asyncio
async def test_route_negotiation(message_router):
    """Test routing of negotiation messages."""
    message_router.intent_classifier.classify.return_value = Intent.NEGOTIATION
    message_router.seller_buyer_communication.handle_message.return_value = (
        "Negotiation response"
    )

    context = {
        "user_id": "buyer123",
        "role": "buyer",
        "counterpart_id": "seller456",
        "property_id": "prop789",
    }

    response = await message_router.process_message(
        "I would like to make an offer of $450,000", context=context
    )
    assert response == "Negotiation response"
    message_router.seller_buyer_communication.handle_message.assert_called_once()


@pytest.mark.asyncio
async def test_route_general_chat(message_router):
    """Test routing of general chat messages."""
    message_router.intent_classifier.classify.return_value = Intent.GENERAL_QUESTION
    message_router.advisory_module.handle_general_inquiry.return_value = (
        "General response"
    )

    response = await message_router.process_message("What are good areas to live in?")
    assert response == "General response"
    message_router.advisory_module.handle_general_inquiry.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling(message_router):
    """Test error handling in message routing."""
    message_router.intent_classifier.classify.side_effect = Exception("Test error")

    response = await message_router.process_message("Test message")
    assert "apologize" in response.lower()
    assert "error" in response.lower()
