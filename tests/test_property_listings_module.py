import pytest
from unittest.mock import MagicMock, AsyncMock
from app.modules.property_listings import PropertyListingsModule
from app.modules.property_listings.api_client import PropertyListingsAPIClient


@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    client = MagicMock(spec=PropertyListingsAPIClient)
    
    # Mock property data
    mock_properties = [
        {
            "property_id": "123e4567-e89b-12d3-a456-426614174000",
            "price": 350000,
            "bedrooms": 3,
            "bathrooms": 2,
            "main_image_url": "https://example.com/main.jpg",
            "address": {
                "city": "London",
                "postcode": "SW1 1AA",
                "street": "Sample Street"
            },
            "specs": {
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "semi-detached"
            },
            "details": {
                "description": "Beautiful family home"
            }
        },
        {
            "property_id": "223e4567-e89b-12d3-a456-426614174001",
            "price": 450000,
            "bedrooms": 4,
            "bathrooms": 3,
            "main_image_url": "https://example.com/main2.jpg",
            "address": {
                "city": "Manchester",
                "postcode": "M1 1AA",
                "street": "Another Street"
            },
            "specs": {
                "bedrooms": 4,
                "bathrooms": 3,
                "property_type": "detached"
            },
            "details": {
                "description": "Spacious modern house"
            }
        }
    ]
    
    # Mock user dashboard
    mock_dashboard = {
        "user": {
            "user_id": "user123",
            "first_name": "John",
            "last_name": "Doe"
        },
        "saved_properties": [
            {
                "property_id": "123e4567-e89b-12d3-a456-426614174000",
                "price": 350000,
                "main_image_url": "https://example.com/main.jpg",
                "address": {
                    "city": "London",
                    "postcode": "SW1 1AA"
                },
                "specs": {
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "property_type": "semi-detached"
                },
                "notes": "Great location"
            }
        ],
        "total_saved_properties": 1
    }
    
    # Set up return values with AsyncMock
    client.get_all_properties = AsyncMock(return_value=mock_properties)
    client.get_user_dashboard = AsyncMock(return_value=mock_dashboard)
    client.get_property_details = AsyncMock(return_value=mock_properties[0])
    
    return client


@pytest.fixture
def property_listings_module(mock_api_client):
    """Create a PropertyListingsModule with mocked dependencies."""
    module = PropertyListingsModule()
    module.api_client = mock_api_client
    
    # Create a proper mock for the LLM client with AsyncMock
    llm_client = MagicMock()
    llm_client.generate_response = AsyncMock(return_value="Here are some properties that match your criteria...")
    
    module.llm_client = llm_client
    return module


@pytest.mark.asyncio
async def test_handle_inquiry_anonymous_user(property_listings_module):
    """Test handling a property listings inquiry from an anonymous user."""
    # Test parameters
    message = "Show me 3-bedroom houses in London"
    context = {"session_id": "test_session"}
    
    # Call the handler
    response = await property_listings_module.handle_inquiry(message, context)
    
    # Verify API calls
    property_listings_module.api_client.get_all_properties.assert_called_once()
    property_listings_module.api_client.get_user_dashboard.assert_not_called()
    
    # Verify LLM call
    property_listings_module.llm_client.generate_response.assert_called_once()
    
    # Verify response
    assert response == "Here are some properties that match your criteria..."


@pytest.mark.asyncio
async def test_handle_inquiry_authenticated_user(property_listings_module):
    """Test handling a property listings inquiry from an authenticated user."""
    # Test parameters
    message = "Show me properties similar to my saved ones"
    context = {"session_id": "test_session"}
    user_id = "user123"
    
    # Call the handler
    response = await property_listings_module.handle_inquiry(message, context, user_id)
    
    # Verify API calls
    property_listings_module.api_client.get_all_properties.assert_called_once()
    property_listings_module.api_client.get_user_dashboard.assert_called_once_with(user_id)
    
    # Verify LLM call
    property_listings_module.llm_client.generate_response.assert_called_once()
    
    # Verify response
    assert response == "Here are some properties that match your criteria..."


@pytest.mark.asyncio
async def test_handle_inquiry_api_error(property_listings_module):
    """Test handling API errors gracefully."""
    # Mock API error
    property_listings_module.api_client.get_all_properties.side_effect = Exception("API error")
    
    # Test parameters
    message = "Show me houses in London"
    context = {"session_id": "test_session"}
    
    # Call the handler
    response = await property_listings_module.handle_inquiry(message, context)
    
    # Verify error handling
    assert "I'm sorry, I couldn't retrieve property listings" in response 