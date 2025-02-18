import pytest
from unittest.mock import AsyncMock
from datetime import datetime
from app.models.property_data import (
    PropertyPrice,
    AreaInsights,
    PropertySpecificInsights,
    LocationHighlights
)
from app.modules.data_integration.property_data_service import PropertyDataService

@pytest.fixture
def property_service():
    return PropertyDataService()

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    mock = AsyncMock()
    mock.generate_response.return_value = """```json
{
    "average_price": "£350,000",
    "price_trend": "5.2%",
    "property_types": ["apartments", "houses", "condos"]
}
```"""
    return mock

@pytest.fixture
def mock_nominatim_response():
    return [{"lat": "51.5074", "lon": "-0.1278"}]

@pytest.fixture
def mock_osm_response():
    return {
        "elements": [
            {
                "type": "node",
                "tags": {
                    "amenity": "restaurant",
                    "name": "Test Restaurant"
                },
                "lat": 51.5074,
                "lon": -0.1278
            },
            {
                "type": "node",
                "tags": {
                    "public_transport": "station",
                    "name": "Test Station"
                },
                "lat": 51.5074,
                "lon": -0.1278
            },
            {
                "type": "node",
                "tags": {
                    "amenity": "school",
                    "name": "Test School",
                    "school:level": "primary"
                },
                "lat": 51.5074,
                "lon": -0.1278
            }
        ]
    }

@pytest.mark.asyncio
async def test_get_area_insights_broad_area(property_service, mock_llm_client, mock_nominatim_response, mock_osm_response):
    """Test getting broad area insights."""
    # Mock the session
    mock_session = AsyncMock()
    mock_session.get = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.status = 200
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(side_effect=[
        mock_nominatim_response,  # For location lookup
        mock_osm_response,        # For amenities and transport
        mock_osm_response        # For schools
    ])
    
    property_service.session = mock_session
    property_service.llm_client = mock_llm_client
    
    insights = await property_service.get_area_insights("London", is_broad_area=True)
    
    assert isinstance(insights, AreaInsights)
    assert insights.market_overview is not None
    assert insights.market_overview.average_price == 350000.0
    assert insights.market_overview.price_change_1y == 5.2
    assert isinstance(insights.area_profile.amenities_summary, dict)
    assert isinstance(insights.area_profile.transport_summary, dict)
    assert isinstance(insights.area_profile.education, dict)
    assert len(insights.area_profile.amenities_summary) > 0
    assert "stations" in insights.area_profile.transport_summary

@pytest.mark.asyncio
async def test_get_area_insights_property_specific(property_service, mock_llm_client, mock_nominatim_response, mock_osm_response):
    """Test getting property-specific insights."""
    # Mock the session
    mock_session = AsyncMock()
    mock_session.get = AsyncMock()
    mock_session.get.return_value.__aenter__.return_value.status = 200
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(side_effect=[
        mock_nominatim_response,  # For location lookup
        mock_osm_response,        # For amenities and transport
        mock_osm_response        # For schools
    ])
    
    property_service.session = mock_session
    property_service.llm_client = mock_llm_client
    
    insights = await property_service.get_area_insights("SW1A 1AA", is_broad_area=False)
    
    assert isinstance(insights, PropertySpecificInsights)
    assert insights.market_overview is not None
    assert insights.market_overview.average_price == 350000.0
    assert insights.market_overview.price_change_1y == 5.2
    assert isinstance(insights.location_highlights, LocationHighlights)
    assert len(insights.location_highlights.nearest_amenities) > 0
    assert len(insights.location_highlights.nearest_stations) > 0
    assert len(insights.location_highlights.nearest_schools) > 0

@pytest.mark.asyncio
async def test_get_market_data(property_service, mock_llm_client):
    """Test fetching market data from LLM."""
    property_service.llm_client = mock_llm_client
    
    market_data = await property_service._get_market_data("London")
    
    assert isinstance(market_data, PropertyPrice)
    assert market_data.average_price == 350000.0
    assert market_data.price_change_1y == 5.2
    assert isinstance(market_data.last_updated, datetime)
    assert market_data.number_of_sales == 0  # We don't have this data