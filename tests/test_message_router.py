import pytest
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

def test_process_message():
    router = MessageRouter()
    message = "Tell me about this property"
    response = router.process_message(message)
    assert isinstance(response, str)
    assert len(response) > 0

def test_route_intent_property_inquiry():
    router = MessageRouter()
    # Set up a test property
    test_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location"
    )
    router.property_context.add_property(test_property)
    router.property_context.set_current_property("123")
    
    response = router._route_intent(
        Intent.PROPERTY_INQUIRY,
        "Tell me about this property",
        {}
    )
    assert isinstance(response, str)
    assert "Property Type: Apartment" in response
    assert "Location: Test Location" in response

def test_route_intent_price_inquiry():
    router = MessageRouter()
    # Set up a test property
    test_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location"
    )
    router.property_context.add_property(test_property)
    router.property_context.set_current_property("123")
    
    response = router._route_intent(
        Intent.PRICE_INQUIRY,
        "How much does it cost?",
        {}
    )
    assert isinstance(response, str)
    assert "Test Location" in response 