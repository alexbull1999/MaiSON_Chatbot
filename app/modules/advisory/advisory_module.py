from typing import List, Dict, Optional
from datetime import datetime
from app.modules.property_context.property_context_module import Property
from ..llm import LLMClient
from ..data_integration.property_data_service import PropertyDataService

class AdvisoryModule:
    def __init__(self):
        self.llm_client = LLMClient()
        self.data_service = PropertyDataService()
        self.recommendations: Dict[str, List[str]] = {}
        self.zoopla_api_key = None  # To be configured from environment variables

    async def get_area_insights(self, location: str, context: Optional[Dict] = None) -> Dict[str, any]:
        """
        Get comprehensive area insights combining multiple data sources and LLM analysis.
        
        Args:
            location: The location to analyze
            context: Optional context dictionary that may contain property_id or other relevant info
        """
        try:
            # Determine if we're looking at a specific property or a broad area
            is_property_specific = bool(context and context.get('property_id'))
            
            if is_property_specific:
                # Get property details first
                property_id = context['property_id']
                # TODO: Implement get_property_details to fetch property info including postcode
                property_details = await self._get_property_details(property_id)
                
                if not property_details or 'postcode' not in property_details:
                    raise ValueError(f"Could not find postcode for property {property_id}")
                
                # Get property-specific insights
                insights = await self.data_service.get_area_insights(
                    property_details['postcode'],
                    is_broad_area=False
                )
                
                # Add property-specific analysis
                analysis = await self._generate_property_analysis(
                    location,
                    insights.model_dump(),
                    property_details
                )
            else:
                # Get broad area insights
                insights = await self.data_service.get_area_insights(location, is_broad_area=True)
                
                # Add area-level analysis
                analysis = await self._generate_area_analysis(location, insights.model_dump())
            
            # Convert Pydantic model to dict and add analysis
            insights_dict = insights.model_dump()
            insights_dict['analysis'] = analysis
            insights_dict['last_updated'] = datetime.utcnow().isoformat()
            
            return insights_dict
            
        except Exception as e:
            print(f"Error getting area insights: {str(e)}")
            return {}

    async def _get_property_details(self, property_id: str) -> Optional[Dict]:
        """Get property details from the database or external service."""
        # TODO: Implement property details retrieval
        # This should return at minimum: postcode, type, price
        return None

    async def _generate_property_analysis(
        self,
        location: str,
        insights: Dict,
        property_details: Dict
    ) -> str:
        """Generate natural language analysis for a specific property's area."""
        prompt = (
            f"Analyze this specific property and its immediate area in {location}.\n\n"
            f"Property Details:\n"
            f"- Type: {property_details.get('type', 'Unknown')}\n"
            f"- Price: {property_details.get('price', 'Unknown')}\n\n"
            f"Local Market Data:\n"
            f"- Average Price: {insights.get('property_market', {}).get('average_price')}\n"
            f"- Price Trend: {insights.get('property_market', {}).get('price_trend')}%\n"
            f"- Rental Yield: {insights.get('property_market', {}).get('rental_yield')}%\n\n"
            f"Location Highlights:\n"
            f"- Nearest Amenities: {len(insights.get('location_highlights', {}).get('nearest_amenities', []))}\n"
            f"- Nearest Stations: {len(insights.get('location_highlights', {}).get('nearest_stations', []))}\n"
            f"- Nearest Schools: {len(insights.get('location_highlights', {}).get('nearest_schools', []))}\n\n"
            f"Please provide a detailed analysis focusing on:\n"
            f"1. How this property compares to the local market\n"
            f"2. The immediate area's strengths and weaknesses\n"
            f"3. Transport and connectivity\n"
            f"4. Local amenities and facilities\n"
            f"5. Investment potential"
        )
        
        response = await self.llm_client.generate_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response

    async def _generate_area_analysis(self, location: str, insights: Dict) -> str:
        """Generate a natural language analysis of an area based on insights."""
        try:
            prompt = (
                f"Analyze this area ({location}) based on the following data.\n\n"
                f"Market Overview:\n"
                f"- Average Price: {insights.get('market_data', {}).get('average_price')}\n"
                f"- Annual Change: {insights.get('market_data', {}).get('annual_change')}%\n"
                f"- Five Year Change: {insights.get('market_data', {}).get('five_year_change')}%\n"
                f"- Market Activity: {insights.get('market_data', {}).get('sales_volume')} sales\n\n"
                f"Area Profile:\n"
                f"- Demographics: {insights.get('demographics', {})}\n"
                f"- Crime Rate: {insights.get('crime_rate')}\n"
                f"- Amenities: {insights.get('amenities', {})}\n"
                f"- Transport: {insights.get('transport', {})}\n"
                f"- Education: {insights.get('education', {})}\n\n"
                "Please provide a comprehensive analysis focusing on:\n"
                "1. Overall area characteristics and lifestyle\n"
                "2. Property market trends and investment potential\n"
                "3. Transport and connectivity\n"
                "4. Local amenities and facilities\n"
                "5. Demographics and community\n"
                "6. Education options\n"
                "7. Safety and security"
            )

            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                module_name="advisory"
            )
            return response

        except Exception as e:
            print(f"Error generating area analysis: {str(e)}")
            return "I apologize, but I couldn't generate an analysis for this area at the moment."

    async def handle_general_inquiry(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle general inquiries about real estate and the market."""
        try:
            # Try to extract location from the message
            location = await self._extract_location(message)
            
            # If we found a location, get area insights
            area_insights = {}
            if location:
                area_insights = await self.get_area_insights(location)
            
            # Prepare the prompt with area insights if available
            prompt = f"User question: {message}\n"
            if area_insights:
                prompt += f"\nArea Information:\n{area_insights}\n"
            prompt += "\nPlease provide a detailed response about the inquiry."
            
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                module_name="advisory"
            )
            return response
            
        except Exception as e:
            print(f"Error in advisory module: {str(e)}")
            return "I apologize, but I encountered an error processing your inquiry. Please try again."

    async def _extract_location(self, message: str) -> Optional[str]:
        """Extract location information from a message using LLM."""
        try:
            prompt = (
                "Extract the location or area mentioned in this message. "
                "Return ONLY the location name, or 'None' if no location is mentioned.\n\n"
                f"Message: {message}"
            )
            
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                module_name="advisory"
            )
            
            return response.strip() if response.lower() != "none" else None

        except Exception as e:
            print(f"Error extracting location: {str(e)}")
            return None

    def get_property_recommendations(self, user_preferences: dict) -> List[Dict]:
        """Get property recommendations based on user preferences and market data."""
        # TODO: Implement property recommendations using PropertyDataService
        return []

    def get_market_analysis(self, location: str) -> Dict[str, str]:
        """Get market analysis for a specific location."""
        # TODO: Implement market analysis using PropertyDataService
        return {
            "market_trend": "Stable",
            "average_price": "Contact for details",
            "demand_level": "Moderate"
        }

    def generate_property_insights(self, property: Property) -> List[str]:
        """Generate insights about a specific property."""
        insights = [
            f"Property Type: {property.type}",
            f"Location: {property.location}",
            "Additional insights will be generated based on property data"
        ]
        return insights 