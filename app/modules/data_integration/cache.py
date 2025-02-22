from typing import Any, Optional, TypeVar, Callable
from cachetools import TTLCache
from functools import wraps
from app.config import settings

# Type variable for generic cache key
KT = TypeVar('KT')
VT = TypeVar('VT')

class PropertyDataCache:
    """Cache manager for property data with TTL-based expiration."""
    
    def __init__(self, ttl: Optional[int] = None, maxsize: Optional[int] = None):
        self.ttl = ttl or settings.cache_ttl
        self.maxsize = maxsize or settings.max_cache_items
        
        self.property_cache = TTLCache(
            maxsize=self.maxsize,
            ttl=self.ttl
        )
        self.area_insights_cache = TTLCache(
            maxsize=self.maxsize,
            ttl=self.ttl
        )
        self.market_data_cache = TTLCache(
            maxsize=self.maxsize,
            ttl=self.ttl // 2  # Market data expires twice as fast
        )

    def get_property(self, property_id: str) -> Optional[dict]:
        """Get property data from cache."""
        return self.property_cache.get(property_id)

    def set_property(self, property_id: str, data: dict) -> None:
        """Store property data in cache."""
        self.property_cache[property_id] = data

    def get_area_insights(self, location: str, is_broad_area: bool) -> Optional[dict]:
        """Get area insights from cache."""
        cache_key = f"{location}:{'broad' if is_broad_area else 'specific'}"
        return self.area_insights_cache.get(cache_key)

    def set_area_insights(self, location: str, is_broad_area: bool, data: dict) -> None:
        """Store area insights in cache."""
        cache_key = f"{location}:{'broad' if is_broad_area else 'specific'}"
        self.area_insights_cache[cache_key] = data

    def get_market_data(self, location: str) -> Optional[dict]:
        """Get market data from cache."""
        return self.market_data_cache.get(location)

    def set_market_data(self, location: str, data: dict) -> None:
        """Store market data in cache."""
        self.market_data_cache[location] = data

    def invalidate_property(self, property_id: str) -> None:
        """Remove property data from cache."""
        self.property_cache.pop(property_id, None)

    def invalidate_area_insights(self, location: str, is_broad_area: bool) -> None:
        """Remove area insights from cache."""
        cache_key = f"{location}:{'broad' if is_broad_area else 'specific'}"
        self.area_insights_cache.pop(cache_key, None)

    def invalidate_market_data(self, location: str) -> None:
        """Remove market data from cache."""
        self.market_data_cache.pop(location, None)

    def clear_all(self) -> None:
        """Clear all caches."""
        self.property_cache.clear()
        self.area_insights_cache.clear()
        self.market_data_cache.clear()

def create_cache_decorators(cache_instance: PropertyDataCache):
    """Create cache decorators that use a specific cache instance."""
    
    def cache_property_data(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to cache property data."""
        @wraps(func)
        async def wrapper(self, property_id: str, *args, **kwargs):
            cached_data = cache_instance.get_property(property_id)
            if cached_data is not None:
                return cached_data

            data = await func(self, property_id, *args, **kwargs)
            if data is not None:
                cache_instance.set_property(property_id, data)
            return data
        return wrapper

    def cache_area_insights(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to cache area insights."""
        @wraps(func)
        async def wrapper(self, location: str, is_broad_area: bool = False, *args, **kwargs):
            cached_data = cache_instance.get_area_insights(location, is_broad_area)
            if cached_data is not None:
                return cached_data

            data = await func(self, location, is_broad_area, *args, **kwargs)
            if data is not None:
                cache_instance.set_area_insights(location, is_broad_area, data)
            return data
        return wrapper

    def cache_market_data(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator to cache market data."""
        @wraps(func)
        async def wrapper(self, location: str, *args, **kwargs):
            cached_data = cache_instance.get_market_data(location)
            if cached_data is not None:
                return cached_data

            data = await func(self, location, *args, **kwargs)
            if data is not None:
                cache_instance.set_market_data(location, data)
            return data
        return wrapper

    return cache_property_data, cache_area_insights, cache_market_data

# Create default cache instance and decorators for production use
default_cache = PropertyDataCache()
cache_property_data, cache_area_insights, cache_market_data = create_cache_decorators(default_cache) 