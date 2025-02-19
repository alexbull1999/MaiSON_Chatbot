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
            "location": {"city": "Test City"}
        }
    )
    router.property_context.get_or_fetch_property.return_value = mock_property

    # Test with property context
    response = await router._route_intent(
        Intent.PROPERTY_INQUIRY,
        "Tell me about this property",
        {"property_id": "123"}
    )
    
    assert isinstance(response, str)
    assert "beautiful" in response
    assert "apartment" in response
    assert "Test Location" in response

    # Test without property context
    response = await router._route_intent(
        Intent.PROPERTY_INQUIRY,
        "Tell me about this property",
        {}
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
            "days_on_market": 30
        }
    )
    router.property_context.get_or_fetch_property.return_value = mock_property

    # Test with property context
    response = await router._route_intent(
        Intent.PRICE_INQUIRY,
        "How much does it cost?",
        {"property_id": "123"}
    )
    
    assert isinstance(response, str)
    assert "£500,000" in response

    # Test without property context
    response = await router._route_intent(
        Intent.PRICE_INQUIRY,
        "How much does it cost?",
        {}
    )
    assert "need a property ID" in response
