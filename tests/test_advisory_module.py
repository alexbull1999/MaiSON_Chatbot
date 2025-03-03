import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.modules.advisory.advisory_module import AdvisoryModule
from app.modules.property_context.property_context_module import Property
from app.models.property_data import PropertyPrice, AreaProfile, AreaInsights


@pytest.fixture
def advisory_module():
    return AdvisoryModule()


@pytest.fixture
def mock_property_data_service():
    with patch(
        "app.modules.data_integration.property_data_service.PropertyDataService"
    ) as _:
        mock_instance = AsyncMock()
        # Set up mock area insights
        mock_instance.get_area_insights.return_value = AreaInsights(
            market_overview=PropertyPrice(
                average_price=350000.0,
                price_change_1y=5.2,
                property_types=["apartments", "houses", "condos"],
                number_of_sales=120,
                last_updated=datetime.utcnow(),
            ),
            area_profile=AreaProfile(
                demographics={},
                crime_rate=5.2,
                amenities_summary={"restaurants": 15, "shops": 10},
                transport_summary={"stations": {"count": 5, "average_distance": 0.5}},
                education={"primary_schools": {"count": 3, "average_distance": 0.3}},
            ),
        )
        yield mock_instance


@pytest.fixture
def mock_llm_client():
    with patch("app.modules.llm.llm_client.LLMClient") as _:
        mock_instance = AsyncMock()
        mock_instance.generate_response.return_value = "This is a test LLM response"
        yield mock_instance


def test_advisory_module_initialization():
    advisory = AdvisoryModule()
    assert isinstance(advisory.recommendations, dict)
    assert advisory.data_service is not None
    assert advisory.llm_client is not None


@pytest.mark.asyncio
async def test_get_area_insights(
    advisory_module, mock_property_data_service, mock_llm_client
):
    """Test getting area insights with mocked data service."""
    advisory_module.data_service = mock_property_data_service
    advisory_module.llm_client = mock_llm_client

    # Mock the _generate_area_analysis method
    advisory_module._generate_area_analysis = AsyncMock(return_value="Test analysis")

    insights = await advisory_module.get_area_insights("London")

    assert isinstance(insights, dict)
    assert "market_overview" in insights
    assert insights["market_overview"]["average_price"] == 350000.0
    assert insights["market_overview"]["price_change_1y"] == 5.2
    assert "area_profile" in insights
    assert insights["area_profile"]["crime_rate"] == 5.2
    assert "analysis" in insights
    assert insights["analysis"] == "Test analysis"
    assert isinstance(insights["last_updated"], str)


@pytest.mark.asyncio
async def test_handle_general_inquiry_with_location(
    advisory_module, mock_property_data_service, mock_llm_client
):
    """Test handling a general inquiry that includes a location."""
    advisory_module.data_service = mock_property_data_service
    advisory_module.llm_client = mock_llm_client

    # Mock location extraction and area-within-city check
    advisory_module._extract_locations = AsyncMock(return_value=["London"])
    advisory_module._is_asking_for_areas_within_city = AsyncMock(return_value=None)

    response = await advisory_module.handle_general_inquiry(
        "What's it like to live in London?"
    )

    assert isinstance(response, str)
    assert len(response) > 0
    mock_property_data_service.get_area_insights.assert_called_once()
    
    # Verify LLM client was called the expected number of times
    # 1. extract_locations
    # 2. is_asking_for_areas_within_city
    # 3. generate_area_analysis
    # 4. final response
    assert mock_llm_client.generate_response.call_count == 2
    
    # Verify all calls used the correct module_name
    call_args_list = mock_llm_client.generate_response.call_args_list
    for call_args in call_args_list:
        assert call_args[1].get('module_name') == 'advisory'


@pytest.mark.asyncio
async def test_handle_general_inquiry_without_location(
    advisory_module, mock_llm_client
):
    """Test handling a general inquiry without a location."""
    advisory_module.llm_client = mock_llm_client

    # Mock location extraction to return empty list and area-within-city check to return None
    advisory_module._extract_locations = AsyncMock(return_value=[])
    advisory_module._is_asking_for_areas_within_city = AsyncMock(return_value=None)

    response = await advisory_module.handle_general_inquiry(
        "What makes a good investment property?"
    )

    assert isinstance(response, str)
    assert len(response) > 0
    
    # Verify LLM client was called the expected number of times
    # 1. extract_locations
    # 2. final response
    assert mock_llm_client.generate_response.call_count == 1
    
    # Verify module_name parameter
    call_args_list = mock_llm_client.generate_response.call_args_list
    for call_args in call_args_list:
        assert call_args[1].get('module_name') == 'advisory'


@pytest.mark.asyncio
async def test_generate_area_analysis(advisory_module, mock_llm_client):
    """Test generating area analysis with LLM."""
    advisory_module.llm_client = mock_llm_client

    insights = AreaInsights(
        market_overview=PropertyPrice(
            average_price=350000.0,
            price_change_1y=5.2,
            property_types=["apartments", "houses", "condos"],
            number_of_sales=120,
            last_updated=datetime.utcnow(),
        ),
        area_profile=AreaProfile(
            demographics={},
            crime_rate=5.2,
            amenities_summary={"restaurants": 15, "shops": 10},
            transport_summary={"stations": {"count": 5, "average_distance": 0.5}},
            education={"primary_schools": {"count": 3, "average_distance": 0.3}},
        ),
    )

    analysis = await advisory_module._generate_area_analysis(
        "London", insights.model_dump()
    )
    assert isinstance(analysis, str)
    assert len(analysis) > 0


def test_get_property_recommendations():
    advisory = AdvisoryModule()
    user_preferences = {
        "type": "Apartment",
        "location": "Test Location",
        "max_price": 1000,
    }
    recommendations = advisory.get_property_recommendations(user_preferences)
    assert isinstance(recommendations, list)


def test_generate_property_insights():
    advisory = AdvisoryModule()
    test_property = Property(
        id="123", name="Test Property", type="Apartment", location="Test Location"
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


@pytest.mark.asyncio
async def test_location_extraction(advisory_module):
    """Test location extraction from queries."""
    # Mock LLM client for location extraction
    advisory_module.llm_client.generate_response = AsyncMock()
    
    # Test with postcode
    advisory_module.llm_client.generate_response.return_value = "SW1A 1AA"
    locations = await advisory_module._extract_locations(
        "What's the property market like in SW1A 1AA?"
    )
    assert locations == ["SW1A 1AA"]

    # Test with city name
    advisory_module.llm_client.generate_response.return_value = "Manchester"
    locations = await advisory_module._extract_locations(
        "Tell me about properties in Manchester"
    )
    assert locations == ["Manchester"]

    # Test with area name
    advisory_module.llm_client.generate_response.return_value = "North London"
    locations = await advisory_module._extract_locations(
        "What's the market like in North London?"
    )
    assert locations == ["North London"]

    # Verify module_name parameter was used
    for call_args in advisory_module.llm_client.generate_response.call_args_list:
        assert call_args[1].get('module_name') == 'advisory'


@pytest.mark.asyncio
async def test_is_asking_for_areas_within_city(advisory_module):
    """Test detection of queries asking about areas within a city."""
    # Mock LLM client
    advisory_module.llm_client.generate_response = AsyncMock()
    
    # Test positive case
    advisory_module.llm_client.generate_response.return_value = "Manchester"
    result = await advisory_module._is_asking_for_areas_within_city(
        "What are good areas to live in Manchester?",
        ["Manchester"]
    )
    assert result == "Manchester"
    
    # Test negative case
    advisory_module.llm_client.generate_response.return_value = "No"
    result = await advisory_module._is_asking_for_areas_within_city(
        "Is Manchester a good place to invest?",
        ["Manchester"]
    )
    assert result is None
    
    # Test with no locations
    result = await advisory_module._is_asking_for_areas_within_city(
        "What makes a good investment property?",
        []
    )
    assert result is None
    
    # Verify module_name parameter was used
    for call_args in advisory_module.llm_client.generate_response.call_args_list:
        assert call_args[1].get('module_name') == 'advisory'
