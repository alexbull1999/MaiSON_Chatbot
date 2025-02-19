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
                "id": 1,
                "lat": 51.5074,
                "lon": -0.1278,
                "tags": {
                    "amenity": "restaurant",
                    "name": "Test Restaurant"
                }
            },
            {
                "type": "node",
                "id": 2,
                "lat": 51.5075,
                "lon": -0.1279,
                "tags": {
                    "amenity": "cafe",
                    "name": "Test Cafe"
                }
            },
            {
                "type": "node",
                "id": 3,
                "lat": 51.5076,
                "lon": -0.1280,
                "tags": {
                    "amenity": "pub",
                    "name": "Test Pub"
                }
            },
            {
                "type": "node",
                "id": 4,
                "lat": 51.5077,
                "lon": -0.1281,
                "tags": {
                    "public_transport": "station",
                    "name": "Test Station"
                }
            },
            {
                "type": "node",
                "id": 5,
                "lat": 51.5078,
                "lon": -0.1282,
                "tags": {
                    "amenity": "school",
                    "name": "Test School",
                    "school:level": "primary"
                }
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

    # Enhanced mock OSM response with more detailed school data
    enhanced_osm_response = {
        'elements': [
            {
                'type': 'node',
                'id': 1,
                'lat': 51.5074,
                'lon': -0.1278,
                'tags': {
                    'amenity': 'school',
                    'name': 'Test Primary School',
                    'school:level': 'primary'
                }
            },
            {
                'type': 'node',
                'id': 2,
                'lat': 51.5075,
                'lon': -0.1279,
                'tags': {
                    'amenity': 'school',
                    'name': 'Test Secondary School',
                    'school:level': 'secondary'
                }
            }
        ]
    }

    # Create a list of responses for each API call
    api_responses = [
        mock_nominatim_response,    # For location lookup
        mock_osm_response,          # For amenities and transport
        [],                         # For crime data
        enhanced_osm_response       # For schools - using enhanced response
    ]

    # Set up the mock to return each response in sequence
    mock_session.get.return_value.__aenter__.return_value.json = AsyncMock(side_effect=api_responses)

    property_service.session = mock_session
    property_service.llm_client = mock_llm_client

    try:
        insights = await property_service.get_area_insights("London", is_broad_area=True)

        # Debug output
        print("Debug: Amenities summary:", insights.area_profile.amenities_summary)
        print("Debug: Transport summary:", insights.area_profile.transport_summary)
        print("Debug: Education summary:", insights.area_profile.education)
        print("Debug: Mock responses:", api_responses)
        print("Debug: OSM Response elements:", enhanced_osm_response['elements'])

        # Basic type assertions
        assert isinstance(insights, AreaInsights), "Result should be an AreaInsights instance"
        assert insights.market_overview is not None, "Market overview should not be None"
        assert isinstance(insights.area_profile.amenities_summary, dict), "Amenities summary should be a dict"
        assert isinstance(insights.area_profile.transport_summary, dict), "Transport summary should be a dict"
        assert isinstance(insights.area_profile.education, dict), "Education should be a dict"

        # Specific value assertions
        assert insights.market_overview.average_price == 350000.0, "Incorrect average price"
        assert insights.market_overview.price_change_1y == 5.2, "Incorrect price change"

        # Check amenities
        amenities = insights.area_profile.amenities_summary
        assert amenities, "Amenities summary should not be empty"
        assert sum(amenities.values()) >= 1, f"Expected at least 1 amenity, got {sum(amenities.values())}"

        # Check transport
        transport = insights.area_profile.transport_summary
        assert transport["stations"]["count"] >= 0, "Should have station count"

        # Check education with more specific assertions
        education = insights.area_profile.education
        assert education, "Education summary should not be empty"
        
        # Check for either the new or old education data structure
        if "schools" in education:
            # New structure
            assert isinstance(education["schools"], list), "Schools should be a list"
            assert len(education["schools"]) > 0, "Should have at least one school"
            school = education["schools"][0]
            assert "name" in school, "School should have a name"
            assert "type" in school, "School should have a type"
            assert "distance" in school, "School should have a distance"
        else:
            # Current structure
            assert any(key in education for key in ["Unknown", "primary", "secondary"]), "Should have school categories"
            category = next(iter(education))
            assert "count" in education[category], "Should have school count"
            assert "average_distance" in education[category], "Should have average distance"
            assert education[category]["count"] > 0, "Should have at least one school"

    except Exception as e:
        print("Debug: Test failed with error:", str(e))
        print("Debug: Mock responses:", api_responses)
        print("Debug: OSM Response elements:", enhanced_osm_response['elements'])
        raise

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