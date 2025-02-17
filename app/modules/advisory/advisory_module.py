from typing import List, Dict, Optional
import aiohttp
from datetime import datetime
from app.modules.property_context.property_context_module import Property
from ..llm import LLMClient, LLMProvider
from ..data_integration.property_data_service import PropertyDataService
from app.models.property_data import AreaInsights, PropertySpecificInsights

class AdvisoryModule:
    def __init__(self):
        self.llm_client = LLMClient(provider=LLMProvider.GEMINI)
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
                    insights,
                    property_details
                )
            else:
                # Get broad area insights
                insights = await self.data_service.get_area_insights(location, is_broad_area=True)
                
                # Add area-level analysis
                analysis = await self._generate_area_analysis(location, insights)
            
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
        """Generate natural language analysis for a broad area."""
        prompt = (
            f"Analyze this area ({location}) based on the following data.\n\n"
            f"Market Overview:\n"
            f"- Average Price: {insights.get('market_overview', {}).get('average_price')}\n"
            f"- Annual Change: {insights.get('market_overview', {}).get('annual_change')}%\n"
            f"- Five Year Change: {insights.get('market_overview', {}).get('five_year_change')}%\n"
            f"- Market Activity: {insights.get('market_overview', {}).get('market_activity')} sales\n\n"
            f"Area Profile:\n"
            f"- Demographics: {insights.get('area_profile', {}).get('demographics', {})}\n"
            f"- Crime Rate: {insights.get('area_profile', {}).get('crime_rate')}\n"
            f"- Amenities: {insights.get('area_profile', {}).get('amenities_summary', {})}\n"
            f"- Transport: {insights.get('area_profile', {}).get('transport_summary', {})}\n"
            f"- Education: {insights.get('area_profile', {}).get('education', {})}\n\n"
            f"Please provide a comprehensive analysis focusing on:\n"
            f"1. Overall area characteristics and lifestyle\n"
            f"2. Property market trends and investment potential\n"
            f"3. Transport and connectivity\n"
            f"4. Local amenities and facilities\n"
            f"5. Demographics and community\n"
            f"6. Education options\n"
            f"7. Safety and security"
        )
        
        response = await self.llm_client.generate_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response

    async def handle_general_inquiry(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle general real estate inquiries with data-backed responses."""
        try:
            # Extract location from message using LLM
            location = await self._extract_location(message)
            
            if location:
                # Get area insights
                insights = await self.get_area_insights(location)
                
                # Generate comprehensive response
                prompt = (
                    f"User question: {message}\n"
                    f"Area insights: {insights}\n\n"
                    "Please provide a helpful response that addresses the user's question "
                    "using the area insights and your general knowledge. Include specific "
                    "data points where available, and provide balanced, practical advice."
                )
                
                response = await self.llm_client.generate_response(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                return response
            else:
                # Handle general questions without location context
                return await self.llm_client.generate_response(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a knowledgeable real estate advisor. Provide helpful, "
                                     "specific advice based on your general knowledge."
                        },
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7
                )
                
        except Exception as e:
            print(f"Error handling general inquiry: {str(e)}")
            return (
                "I apologize, but I'm having trouble processing your inquiry. "
                "Could you please rephrase your question?"
            )

    async def _extract_location(self, message: str) -> Optional[str]:
        """Extract location information from user message using LLM."""
        prompt = (
            "Extract the location or area mentioned in this message. "
            "Return ONLY the location name, or 'None' if no location is mentioned.\n\n"
            f"Message: {message}"
        )
        
        response = await self.llm_client.generate_response(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3  # Lower temperature for more precise extraction
        )
        
        return response if response.lower() != "none" else None

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