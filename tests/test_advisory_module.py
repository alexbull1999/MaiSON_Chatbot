import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.modules.advisory.advisory_module import AdvisoryModule
from app.modules.property_context.property_context_module import Property
from app.modules.data_integration.property_data_service import (
    PropertyPrice,
    AreaAmenity,
    TransportLink,
    AreaInsights
)

@pytest.fixture
def advisory_module():
    return AdvisoryModule()

@pytest.fixture
def mock_property_data_service():
    with patch('app.modules.data_integration.property_data_service.PropertyDataService') as mock:
        mock_instance = AsyncMock()
        # Set up mock area insights
        mock_instance.get_area_insights.return_value = AreaInsights(
            property_prices=PropertyPrice(
                average_price=350000.0,
                price_change_1y=5.2,
                price_change_5y=15.0,
                number_of_sales=120,
                last_updated=datetime.utcnow()
            ),
            amenities=[
                AreaAmenity(
                    name="Test Restaurant",
                    type="restaurant",
                    distance=100.0,
                    rating=4.5
                )
            ],
            transport_links=[
                TransportLink(
                    name="Test Station",
                    type="station",
                    distance=200.0,
                    frequency="10 mins"
                )
            ],
            schools=[{
                "name": "Test School",
                "type": "primary",
                "distance": 300.0,
                "rating": "Good"
            }],
            crime_rate=5.2,
            demographics={
                "population": 100000,
                "median_age": 35
            },
            last_updated=datetime.utcnow()
        )
        yield mock_instance

@pytest.fixture
def mock_llm_client():
    with patch('app.modules.llm.llm_client.LLMClient') as mock:
        mock_instance = AsyncMock()
        mock_instance.generate_response.return_value = "This is a test LLM response"
        yield mock_instance

def test_advisory_module_initialization():
    advisory = AdvisoryModule()
    assert isinstance(advisory.recommendations, dict)
    assert advisory.data_service is not None
    assert advisory.llm_client is not None

@pytest.mark.asyncio
async def test_get_area_insights(advisory_module, mock_property_data_service, mock_llm_client):
    """Test getting area insights with mocked data service."""
    advisory_module.data_service = mock_property_data_service
    advisory_module.llm_client = mock_llm_client
    
    insights = await advisory_module.get_area_insights("London")
    
    assert isinstance(insights, dict)
    assert "property_prices" in insights
    assert insights["property_prices"]["average_price"] == 350000.0
    assert insights["property_prices"]["price_change_1y"] == 5.2
    assert len(insights["amenities"]) == 1
    assert len(insights["transport_links"]) == 1
    assert insights["crime_rate"] == 5.2
    assert "analysis" in insights
    assert isinstance(insights["last_updated"], str)

@pytest.mark.asyncio
async def test_handle_general_inquiry_with_location(advisory_module, mock_property_data_service, mock_llm_client):
    """Test handling a general inquiry that includes a location."""
    advisory_module.data_service = mock_property_data_service
    advisory_module.llm_client = mock_llm_client
    
    # Mock location extraction
    advisory_module._extract_location = AsyncMock(return_value="London")
    
    response = await advisory_module.handle_general_inquiry(
        "What's it like to live in London?"
    )
    
    assert isinstance(response, str)
    assert len(response) > 0
    mock_property_data_service.get_area_insights.assert_called_once_with("London")

@pytest.mark.asyncio
async def test_handle_general_inquiry_without_location(advisory_module, mock_llm_client):
    """Test handling a general inquiry without a location."""
    advisory_module.llm_client = mock_llm_client
    
    # Mock location extraction to return None
    advisory_module._extract_location = AsyncMock(return_value=None)
    
    response = await advisory_module.handle_general_inquiry(
        "What makes a good investment property?"
    )
    
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_generate_area_analysis(advisory_module, mock_llm_client):
    """Test generating area analysis with LLM."""
    advisory_module.llm_client = mock_llm_client
    
    area_data = AreaInsights(
        property_prices=PropertyPrice(
            average_price=350000.0,
            price_change_1y=5.2,
            price_change_5y=15.0,
            number_of_sales=120,
            last_updated=datetime.utcnow()
        ),
        amenities=[],
        transport_links=[],
        schools=[],
        crime_rate=5.2,
        demographics={},
        last_updated=datetime.utcnow()
    )
    
    analysis = await advisory_module._generate_area_analysis("London", area_data)
    assert isinstance(analysis, str)
    assert len(analysis) > 0

def test_get_property_recommendations():
    advisory = AdvisoryModule()
    user_preferences = {
        "type": "Apartment",
        "location": "Test Location",
        "max_price": 1000
    }
    recommendations = advisory.get_property_recommendations(user_preferences)
    assert isinstance(recommendations, list)

def test_generate_property_insights():
    advisory = AdvisoryModule()
    test_property = Property(
        id="123",
        name="Test Property",
        type="Apartment",
        location="Test Location"
    )
    insights = advisory.generate_property_insights(test_property)
    assert isinstance(insights, list)
    assert len(insights) > 0
    assert any("Property Type: Apartment" in insight for insight in insights)
    assert any("Location: Test Location" in insight for insight in insights)

def test_get_market_analysis():
    advisory = AdvisoryModule()
    analysis = advisory.get_market_analysis("Test Location")
    assert isinstance(analysis, dict)
    assert "market_trend" in analysis
    assert "average_price" in analysis
    assert "demand_level" in analysis 