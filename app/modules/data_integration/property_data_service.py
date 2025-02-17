from typing import Dict, List, Optional, Tuple, Any, Union
import aiohttp
from datetime import datetime
import logging
from ..llm import LLMClient, LLMProvider
import json
from app.models.property_data import (
    PropertyPrice,
    AreaProfile,
    LocationHighlights,
    AreaInsights,
    PropertySpecificInsights,
    Amenity,
    Station,
    School
)
from app.config import settings
import math

# Initialize logger
logger = logging.getLogger(__name__)

class DataSource:
    OPENSTREETMAP = "openstreetmap"
    POLICE_UK = "police_uk"
    LLM = "llm"

class PropertyDataService:
    def __init__(self):
        self.session = None
        self.last_request_time = {}
        self.settings = settings
        self.llm_client = LLMClient(provider=LLMProvider.GEMINI)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_area_insights(self, location: str, is_broad_area: bool = False) -> Union[AreaInsights, PropertySpecificInsights]:
        """Get insights for a location."""
        try:
            # Get OSM data
            logger.debug(f"Fetching OSM data for location: {location}")
            amenities, stations = await self._get_osm_data(location)
            
            # Get crime data
            logger.debug(f"Fetching crime data for location: {location}")
            crime_rate = await self._get_crime_data(location)
            
            # Get school data
            logger.debug(f"Fetching school data for location: {location}")
            schools = await self._get_school_data(location)
            
            # Get market data
            logger.debug(f"Fetching market data for {location} using LLM")
            market_data = await self._get_market_data(location)
            
            if is_broad_area:
                return AreaInsights(
                    market_overview=market_data,
                    area_profile=AreaProfile(
                        demographics={},  # Not implemented yet
                        crime_rate=crime_rate,
                        amenities_summary=self._summarize_amenities(amenities),
                        transport_summary=self._summarize_transport(stations),
                        education=self._summarize_schools(schools)
                    )
                )
            else:
                return PropertySpecificInsights(
                    market_overview=market_data,
                    location_highlights=LocationHighlights(
                        nearest_amenities=amenities,
                        nearest_stations=stations,
                        nearest_schools=schools
                    )
                )
                
        except Exception as e:
            logger.error(f"Error getting area insights for {location}: {str(e)}")
            if is_broad_area:
                return AreaInsights(
                    market_overview=None,
                    area_profile=AreaProfile(
                        demographics={},
                        crime_rate=None,
                        amenities_summary={},
                        transport_summary={},
                        education={}
                    )
                )
            else:
                return PropertySpecificInsights(
                    market_overview=None,
                    location_highlights=LocationHighlights(
                        nearest_amenities=[],
                        nearest_stations=[],
                        nearest_schools=[]
                    )
                )

    async def _get_market_data(self, location: str) -> Optional[PropertyPrice]:
        """Get market data from LLM."""
        prompt = f"""Provide specific property insights for {location} including:
1. Average property prices in the immediate area
2. Recent price trends (as a percentage)
3. Property types available
Return the response as a JSON object with these exact keys:
{{
    "average_price": "string with price",
    "price_trend": "string with percentage",
    "property_types": ["array of strings"]
}}"""

        try:
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            market_data = self._extract_json_from_response(response)
            
            if market_data:
                # Parse the price trend to extract just the number
                price_trend_str = market_data.get("price_trend", "0%")
                price_trend = float(''.join(c for c in price_trend_str if c.isdigit() or c == '.'))
                
                # Parse the average price
                price_str = market_data.get("average_price", "0")
                price = float(''.join(c for c in price_str if c.isdigit() or c == '.'))
                
                return PropertyPrice(
                    average_price=price,
                    price_change_1y=price_trend,
                    number_of_sales=0,  # We don't have this data
                    last_updated=datetime.now()
                )
            return None
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return None

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            # Find JSON content between triple backticks if present
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```JSON" in response:
                json_str = response.split("```JSON")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Failed to parse JSON from response: {str(e)}")
            return {}

    def _summarize_amenities(self, amenities: List[Amenity]) -> Dict:
        """Summarize amenities into categories with counts."""
        categories = {}
        for amenity in amenities:
            categories[amenity.type] = categories.get(amenity.type, 0) + 1
        return categories

    def _summarize_transport(self, stations: List[Station]) -> Dict:
        """Summarize transport links by average distance."""
        summary = {
            "stations": {
                "count": len(stations),
                "average_distance": sum(s.distance for s in stations) / len(stations) if stations else 0
            }
        }
        return summary

    def _summarize_schools(self, schools: List[School]) -> Dict:
        """Summarize schools by type and rating."""
        summary = {}
        for school in schools:
            school_type = school.type
            if school_type not in summary:
                summary[school_type] = {"count": 0, "average_distance": 0}
            summary[school_type]["count"] += 1
            summary[school_type]["average_distance"] += school.distance
        
        # Calculate averages
        for type_summary in summary.values():
            type_summary["average_distance"] /= type_summary["count"]
        
        return summary

    async def _get_osm_data(self, location: str) -> Tuple[List[Amenity], List[Station]]:
        """Fetch amenities and transport data from OpenStreetMap."""
        try:
            # Log the location for OSM data
            logger.debug(f"Fetching OSM data for location: {location}")
            session = await self._get_session()
            
            # First, get coordinates for the location using Nominatim
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": location,
                "format": "json",
                "limit": 1
            }
            
            async with session.get(nominatim_url, params=params) as response:
                if response.status != 200:
                    return [], []
                
                location_data = await response.json()
                if not location_data:
                    return [], []
                
                lat = float(location_data[0]["lat"])
                lon = float(location_data[0]["lon"])
            
            # Now query OpenStreetMap for amenities and transport
            overpass_url = "https://overpass-api.de/api/interpreter"
            radius = self.settings.default_search_radius
            
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"](around:{radius},{lat},{lon});
              way["amenity"](around:{radius},{lat},{lon});
              node["public_transport"="station"](around:{radius},{lat},{lon});
              way["public_transport"="station"](around:{radius},{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
            
            async with session.get(overpass_url, params={"data": query}) as response:
                if response.status != 200:
                    return [], []
                
                data = await response.json()
                amenities = []
                transport = []
                
                for element in data.get("elements", []):
                    tags = element.get("tags", {})
                    
                    # Process amenities
                    if "amenity" in tags and tags["amenity"] not in ["bus_station", "train_station"]:
                        amenities.append(Amenity(
                            name=tags.get("name", "Unknown"),
                            type=tags["amenity"],
                            distance=self._calculate_distance(lat, lon, element.get("lat"), element.get("lon"))
                        ))
                    
                    # Process transport
                    if tags.get("public_transport") == "station" or tags.get("amenity") in ["bus_station", "train_station"]:
                        transport.append(Station(
                            name=tags.get("name", "Unknown"),
                            distance=self._calculate_distance(lat, lon, element.get("lat"), element.get("lon")),
                            frequency=None  # We don't have frequency data from OSM
                        ))
                
                return (
                    sorted(amenities, key=lambda x: x.distance)[:10],  # Limit to 10 nearest amenities
                    sorted(transport, key=lambda x: x.distance)[:5]  # Limit to 5 nearest stations
                )
                
        except Exception as e:
            logger.error(f"Error fetching OSM data for {location}: {str(e)}")
            return [], []

    def _calculate_distance(self, lat1: float, lon1: float, lat2: Optional[float], lon2: Optional[float]) -> float:
        """Calculate distance between two points in meters using Haversine formula."""
        if lat2 is None or lon2 is None:
            return 0.0
        
        R = 6371000  # Earth's radius in meters
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

    async def _get_school_data(self, location: str) -> List[School]:
        """Fetch school data from OpenStreetMap."""
        try:
            # Log the location for school data
            logger.debug(f"Fetching school data for location: {location}")
            session = await self._get_session()
            
            # First, get coordinates for the location
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": location,
                "format": "json",
                "limit": 1
            }
            
            async with session.get(nominatim_url, params=params) as response:
                if response.status != 200:
                    return []
                
                location_data = await response.json()
                if not location_data:
                    return []
                
                lat = float(location_data[0]["lat"])
                lon = float(location_data[0]["lon"])
            
            # Query OpenStreetMap for schools
            overpass_url = "https://overpass-api.de/api/interpreter"
            radius = self.settings.default_search_radius
            
            query = f"""
            [out:json][timeout:25];
            (
              node["amenity"="school"](around:{radius},{lat},{lon});
              way["amenity"="school"](around:{radius},{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
            
            async with session.get(overpass_url, params={"data": query}) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                schools = []
                
                for element in data.get("elements", []):
                    tags = element.get("tags", {})
                    if tags.get("amenity") == "school":
                        schools.append(School(
                            name=tags.get("name", "Unknown School"),
                            type=tags.get("school:level", "Unknown"),
                            distance=self._calculate_distance(lat, lon, element.get("lat"), element.get("lon"))
                        ))
                
                return sorted(schools, key=lambda x: x.distance)[:5]  # Limit to 5 nearest schools
                
        except Exception as e:
            logger.error(f"Error fetching school data for {location}: {str(e)}")
            return []

    async def _get_crime_data(self, location: str) -> Optional[float]:
        """Fetch crime data from Police UK API."""
        try:
            # Log the location for crime data
            logger.debug(f"Fetching crime data for location: {location}")
            session = await self._get_session()
            
            # First, get coordinates for the location
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": location,
                "format": "json",
                "limit": 1
            }
            
            async with session.get(nominatim_url, params=params) as response:
                if response.status != 200:
                    return None
                
                location_data = await response.json()
                if not location_data:
                    return None
                
                lat = location_data[0]["lat"]
                lon = location_data[0]["lon"]
            
            # Get crime data from Police UK API
            url = f"{self.settings.police_uk_api_base_url}/crimes-street/all-crime"
            params = {
                "lat": lat,
                "lng": lon
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return None
                
                crimes = await response.json()
                if not crimes:
                    return 0.0
                
                # Calculate crime rate (crimes per 1000 people)
                # This is a simplified calculation
                return len(crimes) / 10  # Approximate rate per 1000 people
                
        except Exception as e:
            logger.error(f"Error fetching crime data for {location}: {str(e)}")
            return None

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close() 