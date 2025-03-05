import pytest
from unittest.mock import AsyncMock, patch
from app.modules.property_context.property_context_module import (
    PropertyContextModule,
)


@pytest.fixture
def property_module():
    """Create a PropertyContextModule instance with mocked dependencies."""
    module = PropertyContextModule()
    module.llm_client = AsyncMock()
    return module


@pytest.fixture
def mock_property_data():
    """Create mock property data matching the listings API format."""
    return {
        "property_id": "2b6d45e8-8e61-416a-a8f1-f52d002f9a3c",
        "address": {
            "street": "Sample Street",
            "city": "London",
            "postcode": "SW1 1AA",
            "latitude": None,
            "longitude": None
        },
        "price": 450000,
        "bedrooms": 3,
        "bathrooms": 2,
        "specs": {
            "property_type": "semi-detached",
            "square_footage": 1200.0,
            "bedrooms": 3,
            "bathrooms": 2,
            "reception_rooms": 1,
            "epc_rating": "B"
        },
        "features": {
            "has_garden": False,
            "garden_size": None,
            "has_garage": False,
            "parking_spaces": 0
        },
        "main_image_url": "https://maisonblobstorage.blob.core.windows.net/property-images/test.jpg",
        "image_urls": ["https://maisonblobstorage.blob.core.windows.net/property-images/test.jpg"],
        "floorplan_url": None,
        "created_at": "2025-02-23T22:11:18.776394+00:00",
        "last_updated": "2025-02-23T22:11:17.592427+00:00",
        "owner_id": 1,
        "details": {
            "description": None,
            "construction_year": None,
            "heating_type": None,
            "parking_spaces": None
        }
    }


@pytest.fixture
def mock_similar_properties():
    """Create mock similar properties data."""
    return [
        {
            "id": "ef4b18ae-499b-476c-9ed3-53c3bda7fb02",
            "address": {
                "street": "Similar Street",
                "city": "London",
                "postcode": "SW1 1AB"
            },
            "price": 400000,
            "bedrooms": 3,
            "bathrooms": 2,
            "specs": {
                "property_type": "semi-detached",
                "square_footage": 1100.0
            },
            "features": {
                "parking": True,
                "garden": True,
                "central_heating": True
            },
            "days_on_market": 45,
            "main_image_url": "https://maisonblobstorage.blob.core.windows.net/property-images/similar1.jpg"
        },
        {
            "id": "17d18993-b68c-4349-96ee-86eafa1747f0",
            "address": {
                "street": "Another Street",
                "city": "London",
                "postcode": "SW1 1AC"
            },
            "price": 500000,
            "bedrooms": 3,
            "bathrooms": 2,
            "specs": {
                "property_type": "semi-detached",
                "square_footage": 1300.0
            },
            "features": {
                "parking": True,
                "garden": True,
                "central_heating": True
            },
            "days_on_market": 15,
            "main_image_url": "https://maisonblobstorage.blob.core.windows.net/property-images/similar2.jpg"
        }
    ]


@pytest.fixture
def mock_area_insights():
    """Create mock area insights data."""
    return {
        "location_highlights": {"description": "Vibrant area with excellent amenities"},
        "transport": {
            "stations": [
                {"name": "Victoria", "distance": 0.5},
                {"name": "St James's Park", "distance": 0.7},
            ],
            "connectivity_score": 8.5,
        },
        "education": {
            "schools": [
                {"name": "Test Primary", "type": "primary", "rating": "Outstanding"},
                {"name": "Test Secondary", "type": "secondary", "rating": "Good"},
            ],
            "ratings": {"primary": 4.5, "secondary": 4.0},
        },
        "amenities": {"restaurants": 15, "shops": 25, "parks": 3},
        "safety": {"crime_rate": "Low", "safety_score": 8.0},
    }


@pytest.mark.asyncio
async def test_fetch_property_details(property_module):
    """Test fetching property details from the listings API."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"id": "test_1", "name": "Test Property"}
        mock_get.return_value.__aenter__.return_value = mock_response

        result = await property_module._fetch_property_details("test_1")
        assert result == {"id": "test_1", "name": "Test Property"}


@pytest.mark.asyncio
async def test_get_or_fetch_property(property_module, mock_property_data):
    """Test fetching and creating a Property instance."""
    # Mock the _fetch_property_details method
    property_module._fetch_property_details = AsyncMock(return_value=mock_property_data)
    
    # Test fetching property
    property = await property_module.get_or_fetch_property("test-id")
    
    # Verify property instance
    assert property is not None
    assert property.id == mock_property_data["property_id"]
    assert property.name == f"{mock_property_data['address']['street']}, {mock_property_data['address']['city']}"
    assert property.type == mock_property_data["specs"]["property_type"]
    assert property.location == mock_property_data["address"]["city"]
    assert property.details["formatted_price"] == "£450,000"
    assert property.details["formatted_address"] == "Sample Street, London, SW1 1AA"


@pytest.mark.asyncio
async def test_handle_inquiry(
    property_module, mock_property_data, mock_similar_properties, mock_area_insights
):
    """Test handling a property inquiry."""
    # Mock required methods
    property_module._fetch_property_details = AsyncMock(return_value=mock_property_data)
    property_module._fetch_similar_properties = AsyncMock(return_value=mock_similar_properties)
    property_module._get_area_insights = AsyncMock(return_value=mock_area_insights)
    property_module.llm_client.generate_response = AsyncMock(
        return_value="This is a great semi-detached property in London with 3 bedrooms."
    )

    # Test inquiry handling
    response = await property_module.handle_inquiry(
        "Tell me about this property",
        {"property_id": "test-id"}
    )

    # Verify response
    assert "great" in response
    assert "semi-detached" in response
    assert "London" in response
    assert "3 bedrooms" in response
    
    # Verify LLM client call
    property_module.llm_client.generate_response.assert_called_once()
    call_args = property_module.llm_client.generate_response.call_args[1]
    assert call_args.get('module_name') == 'property_context'


@pytest.mark.asyncio
async def test_handle_pricing(
    property_module, mock_property_data, mock_similar_properties
):
    """Test handling a pricing inquiry."""
    # Mock required methods
    property_module._fetch_property_details = AsyncMock(return_value=mock_property_data)
    property_module._fetch_similar_properties = AsyncMock(return_value=mock_similar_properties)
    property_module.llm_client.generate_response = AsyncMock(
        return_value="The property is priced at £450,000 which is competitive for the area."
    )

    # Test pricing inquiry
    response = await property_module.handle_pricing(
        "How much does this property cost?",
        {"property_id": "test-id"}
    )

    # Verify response
    assert "£450,000" in response
    assert "competitive" in response
    
    # Verify LLM client call
    property_module.llm_client.generate_response.assert_called_once()
    call_args = property_module.llm_client.generate_response.call_args[1]
    assert call_args.get('module_name') == 'property_context'


@pytest.mark.asyncio
async def test_handle_booking(property_module, mock_property_data):
    """Test handling a booking inquiry."""
    # Mock required methods
    property_module._fetch_property_details = AsyncMock(return_value=mock_property_data)
    property_module.llm_client.generate_response = AsyncMock(
        return_value="You can schedule a viewing of this property at Sample Street, London."
    )

    # Test booking inquiry
    response = await property_module.handle_booking(
        "Can I view this property?",
        {"property_id": "test-id"}
    )

    # Verify response
    assert "schedule a viewing" in response
    assert "Sample Street" in response
    
    # Verify LLM client call
    property_module.llm_client.generate_response.assert_called_once()
    call_args = property_module.llm_client.generate_response.call_args[1]
    assert call_args.get('module_name') == 'property_context'


def test_summarize_similar_properties(property_module, mock_similar_properties):
    """Test summarizing similar properties."""
    summary = property_module._summarize_similar_properties(mock_similar_properties)

    assert isinstance(summary, dict)
    assert "average_price" in summary
    assert summary["average_price"] == 450000  # (400000 + 500000) / 2
    assert "average_size" in summary
    assert summary["average_size"] == 1200  # (1100 + 1300) / 2


def test_get_common_features(property_module, mock_similar_properties):
    """Test getting common features from similar properties."""
    features = property_module._get_common_features(mock_similar_properties)

    assert isinstance(features, dict)
    assert features["parking"] == 2  # Both properties have parking
    assert features["garden"] == 2  # Both properties have garden
    assert features["central_heating"] == 2  # Both properties have central heating


def test_identify_unique_features(
    property_module, mock_property_data, mock_similar_properties
):
    """Test identifying unique features of a property."""
    # Add elevator as a unique feature to the main property
    mock_property_data["features"] = {
        "parking": True,
        "garden": True,
        "elevator": True,
        "central_heating": True
    }
    
    unique_features = property_module._identify_unique_features(
        mock_property_data, mock_similar_properties
    )

    assert isinstance(unique_features, list)
    assert "elevator" in unique_features  # Only the main property has an elevator


def test_analyze_market_conditions(property_module, mock_similar_properties):
    """Test analyzing market conditions."""
    conditions = property_module._analyze_market_conditions(mock_similar_properties)

    assert isinstance(conditions, dict)
    assert conditions["market_speed"] == "Fast"  # Average days on market is 30
    assert conditions["competition_level"] == "Low"  # Only 2 similar properties
    assert conditions["avg_days_on_market"] == 30  # (45 + 15) / 2


@pytest.mark.asyncio
async def test_get_area_insights(property_module, mock_area_insights):
    """Test getting area insights."""
    with patch("app.modules.advisory.AdvisoryModule") as MockAdvisoryModule:
        mock_advisory = AsyncMock()
        mock_advisory.get_area_insights.return_value = mock_area_insights
        MockAdvisoryModule.return_value = mock_advisory

        insights = await property_module._get_area_insights({"postcode": "SW1A 1AA"})

        assert isinstance(insights, dict)
        assert "location_highlights" in insights
        assert "transport" in insights
        assert "education" in insights
        assert "safety" in insights


@pytest.mark.asyncio
async def test_fetch_similar_properties(property_module, mock_similar_properties):
    """Test fetching similar properties."""
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_similar_properties
        mock_get.return_value.__aenter__.return_value = mock_response

        properties = await property_module._fetch_similar_properties(
            location="London", property_type="apartment", bedrooms=2
        )

        assert isinstance(properties, list)
        assert len(properties) == 2
        assert properties[0]["id"] == "ef4b18ae-499b-476c-9ed3-53c3bda7fb02"  # Updated to match UUID format


@pytest.mark.asyncio
async def test_get_area_insights_property_specific(
    property_module, mock_area_insights
):
    """Test getting area insights for a specific property."""
    with patch("app.modules.advisory.AdvisoryModule") as MockAdvisoryModule:
        mock_advisory = AsyncMock()
        mock_advisory.get_area_insights.return_value = mock_area_insights
        MockAdvisoryModule.return_value = mock_advisory

        insights = await property_module._get_area_insights({"postcode": "SW1 1AA"})
        
        assert insights is not None
        assert "location_highlights" in insights
        assert "transport" in insights
        assert "education" in insights
        assert "amenities" in insights
        assert "safety" in insights
