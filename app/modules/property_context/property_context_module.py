from typing import Dict, Optional, List
import aiohttp
from ..llm import LLMClient
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
        self.llm_client = LLMClient()
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

            # Get the property ID from the response
            # The API returns 'property_id' field
            property_id_from_api = property_data.get('property_id')
            
            if not property_id_from_api:
                print(f"Warning: No property_id found in property data for {property_id}")
                # Use the requested property_id as a fallback
                property_id_from_api = property_id

            # Create Property instance from API response
            property_instance = Property(
                id=property_id_from_api,
                name=f"{property_data['address']['street']}, {property_data['address']['city']}",
                type=property_data['specs']['property_type'],
                location=property_data['address']['city'],
                details={
                    **property_data,
                    'formatted_price': f"£{property_data['price']:,}",
                    'formatted_address': f"{property_data['address']['street']}, {property_data['address']['city']}, {property_data['address']['postcode']}"
                }
            )
            self.current_property = property_instance
            return property_instance

        except Exception as e:
            print(f"Error in get_or_fetch_property: {str(e)}")
            return None

    async def handle_inquiry(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle property-specific inquiries."""
        try:
            if not context or 'property_id' not in context:
                return "I need a specific property to answer your question. Could you please provide a property ID?"

            property_data = await self.get_or_fetch_property(context['property_id'])
            if not property_data:
                return "I'm sorry, but I couldn't find that property in our database."

            # Get area insights
            area_insights = await self._get_area_insights(property_data.details.get('location', {}))
            
            # Get similar properties for context
            similar_properties = await self._fetch_similar_properties(
                property_data.location,
                property_data.type,
                property_data.details.get('bedrooms', 0)
            )
            
            # Prepare comprehensive prompt with all available information
            prompt = (
                f"Property Details:\n{property_data}\n\n"
                f"Area Information:\n{area_insights}\n\n"
                f"Similar Properties in the Area:\n{self._summarize_similar_properties(similar_properties)}\n\n"
                f"User Question: {message}\n\n"
                "Please provide a detailed response focusing specifically on answering the user's question. "
                "Include relevant information from the property details, area insights, and market context "
                "where it directly relates to their inquiry."
            )

            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                module_name="property_context"
            )
            return response

        except Exception as e:
            print(f"Error handling property inquiry: {str(e)}")
            return "I apologize, but I encountered an error processing your inquiry. Please try again."

    async def handle_pricing(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle pricing-related inquiries."""
        try:
            if not context or 'property_id' not in context:
                return "I need a specific property to discuss pricing. Could you please provide a property ID?"

            property_data = await self.get_or_fetch_property(context['property_id'])
            if not property_data:
                return "I'm sorry, but I couldn't find that property in our database."

            # Get similar properties for price comparison
            similar_properties = await self._fetch_similar_properties(
                property_data.location,
                property_data.type,
                property_data.details.get('bedrooms', 0)
            )

            # Get area insights for market context
            area_insights = await self._get_area_insights(property_data.details.get('location', {}))

            # Analyze market conditions
            market_analysis = self._analyze_market_conditions(similar_properties)
            price_stats = self._get_price_range(similar_properties)
            avg_price_sqft = self._calculate_avg_price_per_sqft(similar_properties)

            prompt = (
                f"Property Details:\n{property_data}\n\n"
                f"Market Analysis:\n"
                f"- Market Speed: {market_analysis.get('market_speed')}\n"
                f"- Competition Level: {market_analysis.get('competition_level')}\n"
                f"- Average Days on Market: {market_analysis.get('avg_days_on_market')}\n"
                f"- Price Range in Area: £{price_stats.get('min')} - £{price_stats.get('max')}\n"
                f"- Average Price per Sqft: £{avg_price_sqft}\n\n"
                f"Area Information:\n{area_insights}\n\n"
                f"Similar Properties Summary:\n{self._summarize_similar_properties(similar_properties)}\n\n"
                f"User Question: {message}\n\n"
                "Please provide a detailed response about the property's pricing, "
                "using the market analysis and comparable properties to support your answer. "
                "Focus specifically on answering the user's pricing question."
            )

            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                module_name="property_context"
            )
            return response

        except Exception as e:
            print(f"Error handling pricing inquiry: {str(e)}")
            return "I apologize, but I encountered an error processing your pricing inquiry. Please try again."

    async def handle_booking(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle booking and viewing requests."""
        try:
            if not context or 'property_id' not in context:
                return "I need a specific property to arrange a viewing. Could you please provide a property ID?"

            property_data = await self.get_or_fetch_property(context['property_id'])
            if not property_data:
                return "I'm sorry, but I couldn't find that property in our database."

            # Get area insights for context about the location
            area_insights = await self._get_area_insights(property_data.details.get('location', {}))

            prompt = (
                f"Property Details:\n{property_data}\n\n"
                f"Area Information:\n{area_insights}\n\n"
                f"User Request: {message}\n\n"
                "Please provide information about viewing options, emphasizing our digital services first "
                "(virtual tours, 3D walkthroughs, live video viewings). If the user specifically requires "
                "an in-person viewing, provide details about our streamlined digital booking process. "
                "Focus on how our platform makes the entire viewing process efficient and convenient."
            )

            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                module_name="property_context"
            )
            return response

        except Exception as e:
            print(f"Error handling booking request: {str(e)}")
            return "I apologize, but I encountered an error processing your booking request. Please try again."

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