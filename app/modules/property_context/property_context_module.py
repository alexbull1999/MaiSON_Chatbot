from typing import Dict, Optional, List
import aiohttp
from ..llm import LLMClient, LLMProvider
from ..data_integration.cache import cache_property_data

class Property:
    """Class representing a property with its details."""
    def __init__(self, id: str, name: str, type: str, location: str, details: Optional[Dict] = None):
        self.id = id
        self.name = name
        self.type = type
        self.location = location
        self.details = details or {}

class PropertyContextModule:
    """Module for handling property-specific queries and context."""
    
    def __init__(self):
        self.current_property: Optional[Property] = None
        self.llm_client = LLMClient(provider=LLMProvider.GEMINI)
        self.listings_api_url = "https://maison-api.jollybush-a62cec71.uksouth.azurecontainerapps.io"

    @cache_property_data
    async def _fetch_property_details(self, property_id: str) -> Optional[Dict]:
        """Fetch property details from the listings API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.listings_api_url}/api/properties/{property_id}"
                headers = {"Content-Type": "application/json", "Accept": "application/json"}
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        return None
                    if response.status != 200:
                        raise Exception(f"Failed to fetch property details: {response.status}")
                    return await response.json()
        except Exception as e:
            print(f"Error fetching property details: {str(e)}")
            return None

    async def get_or_fetch_property(self, property_id: str) -> Optional[Property]:
        """Get property details from cache or fetch from API."""
        try:
            property_data = await self._fetch_property_details(property_id)
            if not property_data:
                return None

            # Create Property instance from API response
            property_instance = Property(
                id=property_data["id"],  # Now using UUID from API
                name=f"{property_data['address']['street']}, {property_data['address']['city']}",
                type=property_data['specs']['property_type'],
                location=property_data['address']['city'],
                details={
                    **property_data,
                    'formatted_price': f"£{property_data['price']:,}",
                    'formatted_address': f"{property_data['address']['street']}, {property_data['address']['city']}, {property_data['address']['postcode']}"  # NOQA: E501
                }
            )
            self.current_property = property_instance
            return property_instance

        except Exception as e:
            print(f"Error in get_or_fetch_property: {str(e)}")
            return None

    async def handle_inquiry(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Handle property-specific inquiries with comprehensive property and area analysis.
        Combines data from:
        - Property details from listings API
        - Similar properties in the area
        - Local area insights (schools, transport, amenities)
        - Crime statistics and safety information
        - Market trends and neighborhood characteristics
        """
        try:
            if not context or "property_id" not in context:
                return "I need a property ID to provide specific information. Please try again with a property selected."

            property = await self.get_or_fetch_property(context["property_id"])
            if not property:
                return "I couldn't find information about this property. Please try again later."

            # Get similar properties for comparison
            similar_properties = await self._fetch_similar_properties(
                location=property.details.get("location", {}).get("city", ""),
                property_type=property.details.get("specs", {}).get("property_type", "Unknown"),
                bedrooms=property.details.get("bedrooms", 0),
                price_range=None  # Don't limit by price for general inquiries
            )

            # Get area insights using AdvisoryModule's functionality
            area_insights = await self._get_area_insights(property.details.get("location", {}))

            # Prepare comprehensive property and area analysis
            analysis_data = {
                "property_details": {
                    "basic_info": {
                        "name": property.name,
                        "type": property.type,
                        "bedrooms": property.details.get("bedrooms"),
                        "bathrooms": property.details.get("bathrooms"),
                        "square_footage": property.details.get("specs", {}).get("square_footage")
                    },
                    "location": property.details.get("location", {}),
                    "features": property.details.get("features", {}),
                    "specifications": property.details.get("specs", {}),
                    "media": property.details.get("media", [])
                },
                "similar_properties": {
                    "count": len(similar_properties),
                    "summary": self._summarize_similar_properties(similar_properties),
                    "unique_features": self._identify_unique_features(property.details, similar_properties)
                },
                "area_insights": {
                    "location_highlights": area_insights.get("location_highlights", {}),
                    "transport": {
                        "nearby_stations": area_insights.get("transport", {}).get("stations", []),
                        "connectivity_score": area_insights.get("transport", {}).get("connectivity_score")
                    },
                    "education": {
                        "schools": area_insights.get("education", {}).get("schools", []),
                        "school_ratings": area_insights.get("education", {}).get("ratings", {})
                    },
                    "amenities": area_insights.get("amenities", {}),
                    "safety": {
                        "crime_rate": area_insights.get("safety", {}).get("crime_rate"),
                        "safety_score": area_insights.get("safety", {}).get("safety_score")
                    }
                }
            }

            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert real estate agent with deep knowledge of properties and local areas. "
                            "Analyze the provided property details and area insights to give comprehensive, "
                            "informative responses. Consider:\n"
                            "1. Property features and unique selling points\n"
                            "2. How it compares to similar properties\n"
                            "3. Local area characteristics and amenities\n"
                            "4. Transport links and connectivity\n"
                            "5. Schools and education options\n"
                            "6. Safety and community aspects\n\n"
                            "Provide specific, factual information when available, and use your general knowledge "
                            "to give context and insights about the area and property type. Be engaging but professional."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Property and Area Analysis:\n{analysis_data}\n\nUser Question: {message}"
                    }
                ],
                temperature=0.7
            )

            return response

        except Exception as e:
            print(f"Error in property inquiry handler: {str(e)}")
            return "I apologize, but I'm having trouble accessing the property information. Please try again later."

    async def _get_area_insights(self, location: Dict) -> Dict:
        """Get comprehensive area insights using AdvisoryModule's functionality."""
        try:
            from ..advisory import AdvisoryModule
            advisory = AdvisoryModule()
            
            # Use postcode or city for area insights
            location_query = location.get("postcode") or location.get("city")
            if not location_query:
                return {}

            insights = await advisory.get_area_insights(
                location=location_query,
                context={"is_property_specific": True}
            )
            return insights if isinstance(insights, dict) else {}

        except Exception as e:
            print(f"Error getting area insights: {str(e)}")
            return {}

    def _summarize_similar_properties(self, properties: List[Dict]) -> Dict:
        """Generate a summary of similar properties."""
        if not properties:
            return {}

        avg_price = sum(p.get("price", 0) for p in properties) / len(properties)
        avg_size = sum(p.get("specs", {}).get("square_footage", 0) for p in properties) / len(properties)
        
        return {
            "average_price": avg_price,
            "average_size": avg_size,
            "price_range": self._get_price_range(properties),
            "common_features": self._get_common_features(properties)
        }

    def _get_common_features(self, properties: List[Dict]) -> Dict[str, int]:
        """Identify common features among similar properties."""
        feature_counts = {}
        for property in properties:
            features = property.get("features", {})
            for feature, value in features.items():
                if value:  # Only count features that are present (True)
                    feature_counts[feature] = feature_counts.get(feature, 0) + 1
        return feature_counts

    def _identify_unique_features(self, property_details: Dict, similar_properties: List[Dict]) -> List[str]:
        """Identify features that make this property unique compared to similar ones."""
        unique_features = []
        property_features = property_details.get("features", {})
        
        # Compare with similar properties
        for feature, value in property_features.items():
            if not value:  # Skip if feature is not present
                continue
                
            # Count how many similar properties have this feature
            similar_count = sum(
                1 for p in similar_properties
                if p.get("features", {}).get(feature)
            )
            
            # If less than 30% of similar properties have this feature, consider it unique
            if similar_count / len(similar_properties) < 0.3 if similar_properties else True:
                unique_features.append(feature)
        
        return unique_features

    async def handle_booking(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle property viewing and booking requests."""
        try:
            if not context or "property_id" not in context:
                return "I need a property ID to handle viewing requests. Please try again with a property selected."

            property = await self.get_or_fetch_property(context["property_id"])
            if not property:
                return "I couldn't find information about this property. Please try again later."

            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful booking assistant. Guide users through the "
                            "property viewing process. Explain the next steps and what "
                            "information is needed to schedule a viewing."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Property: {property.name} in {property.location}\n\nUser request: {message}"
                    }
                ],
                temperature=0.7
            )

            return response

        except Exception as e:
            print(f"Error in booking handler: {str(e)}")
            return "I apologize, but I'm having trouble with the booking request. Please try again later."

    async def handle_pricing(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Handle property pricing inquiries with advanced market analysis and negotiation advice.
        Provides insights on:
        - Current asking price and its position in the market
        - Historical price trends for similar properties
        - Negotiation strategy based on market conditions
        - Potential starting offer recommendations
        """
        try:
            if not context or "property_id" not in context:
                return "I need a property ID to provide pricing information. Please try again with a property selected."

            property = await self.get_or_fetch_property(context["property_id"])
            if not property:
                return "I couldn't find information about this property. Please try again later."

            # Extract core property information
            price = property.details.get("price", "Price on request")
            location = property.details.get("location", {})
            property_type = property.details.get("specs", {}).get("property_type", "Unknown")
            square_footage = property.details.get("specs", {}).get("square_footage", 0)
            bedrooms = property.details.get("bedrooms", 0)
            bathrooms = property.details.get("bathrooms", 0)

            # Get market context for similar properties
            similar_properties = await self._fetch_similar_properties(
                location=location.get("city", ""),
                property_type=property_type,
                bedrooms=bedrooms,
                price_range=[float(price) * 0.8, float(price) * 1.2] if isinstance(price, (int, float)) else None
            )

            # Prepare market analysis
            market_analysis = {
                "property_details": {
                    "asking_price": price,
                    "price_per_sqft": float(price) / square_footage if isinstance(price, (int, float)) and square_footage else None,
                    "location": location,
                    "property_type": property_type,
                    "square_footage": square_footage,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms
                },
                "market_context": {
                    "similar_properties": similar_properties,
                    "avg_price_per_sqft": self._calculate_avg_price_per_sqft(similar_properties),
                    "price_range": self._get_price_range(similar_properties),
                    "time_on_market": property.details.get("days_on_market", "Unknown"),
                    "market_conditions": self._analyze_market_conditions(similar_properties)
                }
            }

            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert real estate pricing analyst and negotiation advisor. "
                            "Analyze the property details and market data to provide:\n"
                            "1. Analysis of the current asking price relative to similar properties\n"
                            "2. Insights on price per square foot compared to market averages\n"
                            "3. Strategic negotiation advice based on market conditions\n"
                            "4. Recommended starting offer range with justification\n"
                            "5. Key factors that could influence negotiation\n\n"
                            "Be data-driven in your analysis but explain insights in a clear, actionable way."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Property Analysis Request:\n"
                            f"Market Data: {market_analysis}\n\n"
                            f"User Question: {message}"
                        )
                    }
                ],
                temperature=0.7
            )

            return response

        except Exception as e:
            print(f"Error in pricing handler: {str(e)}")
            return "I apologize, but I'm having trouble retrieving pricing information. Please try again later."

    async def _fetch_similar_properties(
        self,
        location: str,
        property_type: str,
        bedrooms: int,
        price_range: Optional[List[float]] = None
    ) -> List[Dict]:
        """Fetch similar properties from the listings API."""
        try:
            params = {
                'property_type': property_type.lower(),
                'min_bedrooms': bedrooms,
                'city': location
            }
            if price_range:
                params['min_price'] = price_range[0]
                params['max_price'] = price_range[1]

            async with aiohttp.ClientSession() as session:
                url = f"{self.listings_api_url}/api/properties"
                headers = {"Content-Type": "application/json", "Accept": "application/json"}
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch similar properties: {response.status}")
                    data = await response.json()
                    return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error fetching similar properties: {str(e)}")
            return []

    def _calculate_avg_price_per_sqft(self, properties: List[Dict]) -> Optional[float]:
        """Calculate average price per square foot from similar properties."""
        if not properties:
            return None
        
        valid_properties = [
            p for p in properties
            if p.get("price") and p.get("specs", {}).get("square_footage")
        ]
        
        if not valid_properties:
            return None
        
        total = sum(
            p["price"] / p["specs"]["square_footage"]
            for p in valid_properties
        )
        return total / len(valid_properties)

    def _get_price_range(self, properties: List[Dict]) -> Dict[str, Optional[float]]:
        """Get price range statistics from similar properties."""
        if not properties:
            return {"min": None, "max": None, "median": None}
        
        prices = [p["price"] for p in properties if p.get("price")]
        if not prices:
            return {"min": None, "max": None, "median": None}
        
        return {
            "min": min(prices),
            "max": max(prices),
            "median": sorted(prices)[len(prices) // 2]
        }

    def _analyze_market_conditions(self, properties: List[Dict]) -> Dict[str, any]:
        """Analyze market conditions based on similar properties."""
        if not properties:
            return {
                "market_speed": "Unknown",
                "price_trend": "Unknown",
                "competition_level": "Unknown"
            }
        
        # Calculate average days on market
        days_on_market = [
            p.get("days_on_market", 0)
            for p in properties
            if p.get("days_on_market") is not None
        ]
        avg_days = sum(days_on_market) / len(days_on_market) if days_on_market else None
        
        # Determine market speed
        market_speed = (
            "Fast" if avg_days and avg_days <= 30
            else "Moderate" if avg_days and avg_days <= 90
            else "Slow" if avg_days
            else "Unknown"
        )
        
        # Count active listings
        active_listings = len(properties)
        competition_level = (
            "High" if active_listings > 10
            else "Moderate" if active_listings > 5
            else "Low" if active_listings > 0
            else "Unknown"
        )
        
        return {
            "market_speed": market_speed,
            "avg_days_on_market": avg_days,
            "active_similar_listings": active_listings,
            "competition_level": competition_level
        } 