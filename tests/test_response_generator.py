import pytest
from app.modules.response_generator import ResponseGenerator

def test_response_generator_initialization():
    generator = ResponseGenerator()
    assert generator.communication_module is not None

def test_generate_response_with_greeting():
    generator = ResponseGenerator()
    response = generator.generate_response(
        intent="greeting",
        context={},
    )
    assert isinstance(response, str)
    assert len(response) > 0
    assert "Welcome" in response or "Hello" in response

def test_generate_response_with_property_data():
    generator = ResponseGenerator()
    property_data = {
        "name": "Test Property",
        "type": "Apartment",
        "location": "Test Location",
        "price": 1000
    }
    response = generator.generate_response(
        intent="property_inquiry",
        context={},
        property_data=property_data
    )
    assert isinstance(response, str)
    assert "Test Property" in response or "property" in response.lower()

def test_generate_response_with_market_data():
    generator = ResponseGenerator()
    market_data = {
        "market_trend": "Stable",
        "average_price": "$1,000",
        "demand_level": "High"
    }
    response = generator.generate_response(
        intent="market_inquiry",
        context={},
        market_data=market_data
    )
    assert isinstance(response, str)
    assert "market" in response.lower()

def test_generate_response_without_data():
    generator = ResponseGenerator()
    response = generator.generate_response(
        intent="general_inquiry",
        context={"conversation_history": ["previous message"]}
    )
    assert isinstance(response, str)
    assert len(response) > 0 