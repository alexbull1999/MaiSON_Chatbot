import pytest
from unittest.mock import AsyncMock, patch
from app.modules.property_context.property_context_module import (
    PropertyContextModule,
    Property,
)


@pytest.fixture
def property_module():
    """Create a PropertyContextModule instance with mocked dependencies."""
    module = PropertyContextModule()
    module.llm_client = AsyncMock()
    return module


@pytest.fixture
def mock_property_data():
    """Create mock property data."""
    return {
        "id": "test_property_1",
        "name": "Test Property",
        "type": "apartment",
        "location": {
            "city": "London",
            "postcode": "SW1A 1AA",
            "coordinates": {"lat": 51.5074, "lon": -0.1278},
        },
        "price": 500000,
        "bedrooms": 2,
        "bathrooms": 2,
        "specs": {
            "property_type": "apartment",
            "square_footage": 1000,
            "year_built": 2020,
        },
        "features": {
            "parking": True,
            "garden": False,
            "balcony": True,
            "elevator": True,
        },
        "media": [{"type": "image", "url": "http://example.com/image1.jpg"}],
        "days_on_market": 30,
    }


@pytest.fixture
def mock_similar_properties():
    """Create mock similar properties data."""
    return [
        {
            "id": "similar_1",
            "price": 480000,
            "specs": {"square_footage": 950},
            "features": {"parking": True, "garden": False},
            "days_on_market": 45,
        },
        {
            "id": "similar_2",
            "price": 520000,
            "specs": {"square_footage": 1050},
            "features": {"parking": True, "balcony": True},
            "days_on_market": 15,
        },
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
    """Test getting or fetching a property."""
    # Mock the fetch method
    property_module._fetch_property_details = AsyncMock(return_value=mock_property_data)

    # Test fetching new property
    property = await property_module.get_or_fetch_property("test_1")
    assert isinstance(property, Property)
    assert property.id == "test_1"
    assert property.name == "Test Property"

    # Test getting cached property
    cached_property = await property_module.get_or_fetch_property("test_1")
    assert cached_property is property


@pytest.mark.asyncio
async def test_handle_inquiry(
    property_module, mock_property_data, mock_similar_properties, mock_area_insights
):
    """Test handling a property inquiry."""
    # Mock dependencies
    property_module._fetch_property_details = AsyncMock(return_value=mock_property_data)
    property_module._fetch_similar_properties = AsyncMock(
        return_value=mock_similar_properties
    )
    property_module._get_area_insights = AsyncMock(return_value=mock_area_insights)
    property_module.llm_client.generate_response = AsyncMock(
        return_value="This is a great property in a prime location."
    )

    # Test with valid property ID
    response = await property_module.handle_inquiry(
        "Tell me about this property", {"property_id": "test_1"}
    )
    assert isinstance(response, str)
    assert "great property" in response

    # Test without property ID
    response = await property_module.handle_inquiry("Tell me about this property", {})
    assert "need a property ID" in response


@pytest.mark.asyncio
async def test_handle_pricing(
    property_module, mock_property_data, mock_similar_properties
):
    """Test handling a pricing inquiry."""
    # Mock dependencies
    property_module._fetch_property_details = AsyncMock(return_value=mock_property_data)
    property_module._fetch_similar_properties = AsyncMock(
        return_value=mock_similar_properties
    )
    property_module.llm_client.generate_response = AsyncMock(
        return_value="The property is priced competitively at £500,000."
    )

    # Test with valid property ID
    response = await property_module.handle_pricing(
        "What's the price of this property?", {"property_id": "test_1"}
    )
    assert isinstance(response, str)
    assert "£500,000" in response

    # Test without property ID
    response = await property_module.handle_pricing("What's the price?", {})
    assert "need a property ID" in response


@pytest.mark.asyncio
async def test_handle_booking(property_module, mock_property_data):
    """Test handling a booking request."""
    # Mock dependencies
    property_module._fetch_property_details = AsyncMock(return_value=mock_property_data)
    property_module.llm_client.generate_response = AsyncMock(
        return_value="I can help you schedule a viewing of this property."
    )

    # Test with valid property ID
    response = await property_module.handle_booking(
        "I'd like to view this property", {"property_id": "test_1"}
    )
    assert isinstance(response, str)
    assert "schedule a viewing" in response

    # Test without property ID
    response = await property_module.handle_booking(
        "I'd like to view this property", {}
    )
    assert "need a property ID" in response


def test_summarize_similar_properties(property_module, mock_similar_properties):
    """Test summarizing similar properties."""
    summary = property_module._summarize_similar_properties(mock_similar_properties)

    assert isinstance(summary, dict)
    assert "average_price" in summary
    assert summary["average_price"] == 500000  # (480000 + 520000) / 2
    assert "average_size" in summary
    assert summary["average_size"] == 1000  # (950 + 1050) / 2


def test_get_common_features(property_module, mock_similar_properties):
    """Test getting common features from similar properties."""
    features = property_module._get_common_features(mock_similar_properties)

    assert isinstance(features, dict)
    assert features["parking"] == 2  # Both properties have parking
    assert "balcony" in features
    assert features["balcony"] == 1  # Only one property has a balcony


def test_identify_unique_features(
    property_module, mock_property_data, mock_similar_properties
):
    """Test identifying unique features of a property."""
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
        assert properties[0]["id"] == "similar_1"
        assert properties[1]["id"] == "similar_2"
