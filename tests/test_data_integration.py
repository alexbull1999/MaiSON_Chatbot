import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from app.modules.data_integration.property_data_service import (
    PropertyDataService,
    PropertyPrice,
    AreaAmenity,
    TransportLink,
    AreaInsights,
    WebScrapingError
)

@pytest.fixture
def property_service():
    return PropertyDataService()

@pytest.fixture
def mock_aiohttp_session():
    class MockResponse:
        def __init__(self, status, json_data=None, text_data=None):
            self.status = status
            self._json = json_data
            self._text = text_data

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def json(self):
            return self._json

        async def text(self):
            return self._text

    class MockSession:
        def __init__(self):
            self.closed = False

        def get(self, url, **kwargs):
            if "nominatim" in url:
                return MockResponse(200, json_data=[{"lat": "51.5074", "lon": "-0.1278"}])
            elif "rightmove" in url:
                return MockResponse(200, text_data='<div data-test="average-price">£350,000</div><div data-test="price-change">5.2</div><div data-test="number-of-sales">120</div>')
            elif "overpass-api" in url:
                return MockResponse(200, json_data={"elements": [
                    {
                        "type": "node",
                        "lat": 51.5074,
                        "lon": -0.1278,
                        "tags": {
                            "amenity": "restaurant",
                            "name": "Test Restaurant",
                            "rating": "4.5"
                        }
                    }
                ]})
            elif "police.uk" in url:
                return MockResponse(200, json_data=[{"category": "violent-crime"}, {"category": "burglary"}])
            elif "ons.gov.uk" in url:
                return MockResponse(200, json_data={"population": 100000, "median_age": 35})
            elif "robots.txt" in url:
                return MockResponse(200, text_data="User-agent: *\nAllow: /")
            return MockResponse(404)

        async def close(self):
            self.closed = True

    return MockSession()

@pytest.mark.asyncio
async def test_get_area_insights(property_service, mock_aiohttp_session):
    """Test getting area insights with all data sources."""
    property_service.session = mock_aiohttp_session
    
    # Mock robots.txt check to always return True
    property_service._check_robots_txt = AsyncMock(return_value=True)
    
    insights = await property_service.get_area_insights("London")
    
    assert isinstance(insights, AreaInsights)
    assert insights.property_prices.average_price == 350000.0
    assert insights.property_prices.price_change_1y == 5.2
    assert len(insights.amenities) > 0
    assert insights.crime_rate is not None
    assert isinstance(insights.demographics, dict)

@pytest.mark.asyncio
async def test_scraping_error_handling(property_service):
    """Test error handling when scraping fails."""
    class MockResponse:
        def __init__(self, status, json_data=None, text_data=None):
            self.status = status
            self._json = json_data
            self._text = text_data

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def json(self):
            return self._json

        async def text(self):
            if self.status != 200:
                raise ConnectionError("Failed to connect to server")
            return self._text

    # Mock the _get_session method to return a session that will fail
    async def mock_get_session():
        class FailingSession:
            closed = False
            def get(self, url, *args, **kwargs):
                if "nominatim" in url:
                    # Return valid coordinates for location lookup
                    return MockResponse(200, json_data=[{"lat": "51.5074", "lon": "-0.1278"}])
                elif "robots.txt" in url:
                    # Allow scraping
                    return MockResponse(200, text_data="User-agent: *\nAllow: /")
                else:
                    # All other requests should fail
                    return MockResponse(404)
            async def close(self):
                self.closed = True
        return FailingSession()

    # Apply the mock
    property_service._get_session = mock_get_session
    property_service._check_robots_txt = AsyncMock(return_value=True)

    # Test that get_area_insights handles errors gracefully by returning default values
    insights = await property_service.get_area_insights("London")
    
    # Verify that we got default values due to the failures
    assert isinstance(insights, AreaInsights)
    assert insights.property_prices.average_price == 0.0
    assert insights.property_prices.price_change_1y == 0.0
    assert len(insights.amenities) == 0
    assert len(insights.transport_links) == 0
    assert insights.crime_rate is None
    assert insights.demographics == {}

@pytest.mark.asyncio
async def test_rate_limiting(property_service):
    """Test rate limiting functionality."""
    import time
    import asyncio
    
    # Override the sleep function to make tests faster
    real_sleep = asyncio.sleep
    asyncio.sleep = AsyncMock()
    
    try:
        start_time = time.time()
        await property_service._respect_rate_limits("rightmove.co.uk")
        first_call = time.time() - start_time
        assert first_call < 0.1
        
        await property_service._respect_rate_limits("rightmove.co.uk")
        assert asyncio.sleep.called
        assert round(asyncio.sleep.call_args[0][0], 2) == 5.0  # Should try to sleep for 5 seconds
    finally:
        # Restore the real sleep function
        asyncio.sleep = real_sleep

@pytest.mark.asyncio
async def test_distance_calculation(property_service):
    """Test the Haversine distance calculation."""
    # London to Paris (approximate)
    distance = property_service._calculate_distance(
        51.5074, -0.1278,  # London
        48.8566, 2.3522    # Paris
    )
    assert 300000 < distance < 350000  # Should be around 344 km 