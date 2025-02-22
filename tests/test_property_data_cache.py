import pytest
import asyncio
from app.modules.data_integration.cache import (
    PropertyDataCache,
    create_cache_decorators,
)
from app.config import settings


@pytest.fixture
def property_cache():
    cache = PropertyDataCache()
    yield cache
    cache.clear_all()  # Cleanup after each test


@pytest.fixture
def cache_decorators(property_cache):
    return create_cache_decorators(property_cache)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def test_cache_initialization(property_cache):
    """Test that cache is initialized with correct settings."""
    assert property_cache.property_cache.maxsize == settings.max_cache_items
    assert property_cache.property_cache.ttl == settings.cache_ttl
    assert property_cache.market_data_cache.ttl == settings.cache_ttl // 2


def test_property_cache_operations(property_cache):
    """Test basic property cache operations."""
    test_data = {"name": "Test Property", "price": 500000}

    # Test setting and getting
    property_cache.set_property("prop123", test_data)
    cached_data = property_cache.get_property("prop123")
    assert cached_data == test_data

    # Test invalidation
    property_cache.invalidate_property("prop123")
    assert property_cache.get_property("prop123") is None


def test_area_insights_cache_operations(property_cache):
    """Test area insights cache operations."""
    test_data = {
        "market_overview": {"average_price": 350000},
        "area_profile": {"crime_rate": 5.2},
    }

    # Test setting and getting for broad area
    property_cache.set_area_insights("London", True, test_data)
    cached_data = property_cache.get_area_insights("London", True)
    assert cached_data == test_data

    # Test setting and getting for specific area
    property_cache.set_area_insights("SW1A 1AA", False, test_data)
    cached_data = property_cache.get_area_insights("SW1A 1AA", False)
    assert cached_data == test_data

    # Test invalidation
    property_cache.invalidate_area_insights("London", True)
    assert property_cache.get_area_insights("London", True) is None


def test_market_data_cache_operations(property_cache):
    """Test market data cache operations."""
    test_data = {
        "average_price": 350000,
        "price_trend": "5.2%",
        "property_types": ["apartments", "houses"],
    }

    # Test setting and getting
    property_cache.set_market_data("London", test_data)
    cached_data = property_cache.get_market_data("London")
    assert cached_data == test_data

    # Test invalidation
    property_cache.invalidate_market_data("London")
    assert property_cache.get_market_data("London") is None


def test_cache_expiry():
    """Test that cached items expire after TTL."""
    # Create a new cache instance with a short TTL
    cache = PropertyDataCache(ttl=0.1, maxsize=100)  # 100ms TTL

    test_data = {"name": "Test Property"}

    # Set data
    cache.set_property("prop123", test_data)

    # Verify data is cached
    assert cache.get_property("prop123") == test_data

    # Wait for expiry
    asyncio.run(asyncio.sleep(0.2))

    # Verify data has expired
    assert cache.get_property("prop123") is None


@pytest.mark.asyncio
async def test_cache_property_data_decorator(cache_decorators):
    """Test the cache_property_data decorator."""
    cache_property_data = cache_decorators[0]

    class TestService:
        @cache_property_data
        async def fetch_property(self, property_id: str):
            return {"name": "Test Property", "id": property_id}

    service = TestService()

    # First call should fetch
    result1 = await service.fetch_property("prop123")
    assert result1["name"] == "Test Property"

    # Second call should use cache
    result2 = await service.fetch_property("prop123")
    assert result2 == result1


@pytest.mark.asyncio
async def test_cache_area_insights_decorator(cache_decorators):
    """Test the cache_area_insights decorator."""
    cache_area_insights = cache_decorators[1]

    class TestService:
        @cache_area_insights
        async def fetch_insights(self, location: str, is_broad_area: bool = False):
            return {"market_overview": {"average_price": 350000}}

    service = TestService()

    # First call should fetch
    result1 = await service.fetch_insights("London", True)
    assert result1["market_overview"]["average_price"] == 350000

    # Second call should use cache
    result2 = await service.fetch_insights("London", True)
    assert result2 == result1


@pytest.mark.asyncio
async def test_cache_market_data_decorator(cache_decorators):
    """Test the cache_market_data decorator."""
    cache_market_data = cache_decorators[2]

    class TestService:
        @cache_market_data
        async def fetch_market_data(self, location: str):
            return {"average_price": 350000, "price_trend": "5.2%"}

    service = TestService()

    # First call should fetch
    result1 = await service.fetch_market_data("London")
    assert result1["average_price"] == 350000

    # Second call should use cache
    result2 = await service.fetch_market_data("London")
    assert result2 == result1
