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
                insights_dict = insights.model_dump() if insights else {}
                
                # Check if we have any meaningful data before generating analysis
                has_data = False
                
                # Check market overview
                market_overview = insights_dict.get('market_overview', {})
                if market_overview and any(v is not None and v != 0 and v != "" for v in market_overview.values()):
                    has_data = True
                
                # Check area profile
                if not has_data:
                    area_profile = insights_dict.get('area_profile', {})
                    if area_profile:
                        # Check direct values
                        if any(v is not None and v != 0 and v != "" for v in area_profile.values() if not isinstance(v, dict)):
                            has_data = True
                        
                        # Check nested dictionaries
                        if not has_data:
                            for key, value in area_profile.items():
                                if isinstance(value, dict) and any(v is not None and v != 0 and v != "" for v in value.values()):
                                    has_data = True
                                    break
                
                # Generate analysis based on available data
                analysis = await self._generate_area_analysis(location, insights_dict)
                
                # If we don't have meaningful data, mark the insights as empty
                if not has_data:
                    insights_dict = {}
            
            # Convert Pydantic model to dict and add analysis
            insights_dict = insights.model_dump() if insights else {}
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
            # Clean up insights to remove None values and empty dictionaries
            clean_insights = {}
            
            # Process market overview
            market_data = insights.get('market_overview', {})
            if market_data and any(v is not None and v != 0 and v != "" for v in market_data.values()):
                clean_insights['market_overview'] = market_data
            
            # Process area profile
            area_profile = insights.get('area_profile', {})
            if area_profile:
                clean_area_profile = {}
                
                # Process demographics
                demographics = area_profile.get('demographics', {})
                if demographics and any(v for v in demographics.values() if v):
                    clean_area_profile['demographics'] = demographics
                
                # Process crime rate
                crime_rate = area_profile.get('crime_rate')
                if crime_rate is not None:
                    clean_area_profile['crime_rate'] = crime_rate
                
                # Process amenities
                amenities = area_profile.get('amenities_summary', {})
                if amenities and any(v for v in amenities.values() if v):
                    clean_area_profile['amenities'] = amenities
                
                # Process transport
                transport = area_profile.get('transport_summary', {})
                if transport and any(v for v in transport.values() if v):
                    clean_area_profile['transport'] = transport
                
                # Process education
                education = area_profile.get('education', {})
                if education and any(v for v in education.values() if v):
                    clean_area_profile['education'] = education
                
                if clean_area_profile:
                    clean_insights['area_profile'] = clean_area_profile
            
            # Create a prompt that focuses on available data and encourages the LLM to use its knowledge
            prompt = (
                f"Analyze this area ({location}) based on the following data.\n\n"
            )
            
            # Add market overview if available
            if 'market_overview' in clean_insights:
                market = clean_insights['market_overview']
                prompt += "Market Overview:\n"
                if market.get('average_price') is not None:
                    prompt += f"- Average Price: {market.get('average_price')}\n"
                if market.get('price_change_1y') is not None:
                    prompt += f"- Annual Change: {market.get('price_change_1y')}%\n"
                if market.get('number_of_sales') is not None:
                    prompt += f"- Market Activity: {market.get('number_of_sales')} sales\n"
                prompt += "\n"
            
            # Add area profile if available
            if 'area_profile' in clean_insights:
                area = clean_insights['area_profile']
                prompt += "Area Profile:\n"
                
                if 'demographics' in area:
                    prompt += f"- Demographics: {area['demographics']}\n"
                
                if 'crime_rate' in area:
                    prompt += f"- Crime Rate: {area['crime_rate']}\n"
                
                if 'amenities' in area:
                    prompt += f"- Amenities: {area['amenities']}\n"
                
                if 'transport' in area:
                    prompt += f"- Transport: {area['transport']}\n"
                
                if 'education' in area:
                    prompt += f"- Education: {area['education']}\n"
                
                prompt += "\n"
            
            # Add instructions for analysis
            prompt += (
                "Please provide a comprehensive analysis of this area. For any aspects where specific data is not provided above, "
                "use your general knowledge about this location to fill in the gaps. DO NOT mention any lack of data in your response.\n\n"
                "Focus your analysis on:\n"
                "1. Overall area characteristics and lifestyle\n"
                "2. Property market trends and investment potential\n"
                "3. Transport and connectivity\n"
                "4. Local amenities and facilities\n"
                "5. Demographics and community\n"
                "6. Education options\n"
                "7. Safety and security\n\n"
                "Be specific, informative, and confident in your analysis."
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
            print(f"Extracted location: {location}")
            
            # If we found a location, get area insights
            area_insights = {}
            if location:
                area_insights = await self.get_area_insights(location)
                print(f"Got area insights for {location}: {area_insights.keys() if area_insights else 'None'}")
            
            # Check if area_insights contains useful data
            has_useful_data = False
            if area_insights:
                # More thorough check for useful data in nested structures
                market_overview = area_insights.get('market_overview', {})
                area_profile = area_insights.get('area_profile', {})
                
                print(f"Market overview: {market_overview}")
                print(f"Area profile: {area_profile}")
                
                # Check market_overview for useful data
                if market_overview and isinstance(market_overview, dict):
                    market_has_data = any(v is not None and v != 0 and v != "" for v in market_overview.values())
                    print(f"Market overview has useful data: {market_has_data}")
                    if market_has_data:
                        has_useful_data = True
                
                # Check area_profile for useful data
                if not has_useful_data and area_profile and isinstance(area_profile, dict):
                    # Check direct values in area_profile
                    direct_has_data = any(v is not None and v != 0 and v != "" for v in area_profile.values() if not isinstance(v, dict))
                    print(f"Area profile direct values have useful data: {direct_has_data}")
                    if direct_has_data:
                        has_useful_data = True
                    
                    # Check nested dictionaries in area_profile
                    for key, value in area_profile.items():
                        if isinstance(value, dict):
                            nested_has_data = any(v is not None and v != 0 and v != "" for v in value.values())
                            print(f"Area profile nested dict '{key}' has useful data: {nested_has_data}")
                            if nested_has_data:
                                has_useful_data = True
                                break
            
            print(f"Final has_useful_data determination: {has_useful_data}")
            
            # Prepare the prompt based on whether we have useful data
            if has_useful_data:
                # Use the area insights in the prompt
                prompt = f"User question: {message}\n"
                prompt += f"\nArea Information:\n{area_insights}\n"
                prompt += "\nPlease provide a detailed response about the inquiry."
                print("Using area insights in prompt")
            else:
                # Fall back to using the LLM's own knowledge with explicit instructions
                prompt = (
                    f"User question: {message}\n\n"
                    f"Please provide a detailed and helpful response about this real estate inquiry using ONLY your own knowledge. "
                    f"If the question is about a specific location (like {location if location else 'a city or neighborhood'}), "
                    f"provide specific information about that location such as property market trends, "
                    f"typical prices, neighborhood characteristics, transport links, and amenities. "
                    f"DO NOT mention any lack of data or information in your response. "
                    f"DO NOT say phrases like 'I don't have specific data' or 'without specific data'. "
                    f"Instead, confidently provide information based on your general knowledge about real estate and locations. "
                    f"Be specific, helpful, and informative in your response."
                )
                print("Using fallback prompt with LLM knowledge")
            
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
        """Extract location information from a message using LLM and pattern matching."""
        try:
            # First try with simple pattern matching for common UK locations
            common_uk_locations = [
                "North London", "South London", "East London", "West London", "London", "Manchester", 
                "Birmingham", "Liverpool", "Leeds", "Glasgow", "Edinburgh",
                "Bristol", "Sheffield", "Newcastle", "Nottingham", "Cardiff", "Belfast", "Oxford",
                "Cambridge", "York", "Brighton", "Southampton", "Portsmouth", "Leicester", "Coventry",
                "Peckham", "Brixton", "Hackney", "Shoreditch", "Islington", "Camden", "Kensington",
                "Chelsea", "Westminster", "Mayfair", "Soho", "Covent Garden", "Notting Hill"
            ]
            
            # Check if any common location is in the message
            for location in common_uk_locations:
                if location.lower() in message.lower():
                    return location
            
            # If no common location found, use LLM for more complex extraction
            prompt = (
                "Extract the location or area mentioned in this message. "
                "Focus on identifying UK cities, towns, neighborhoods, or boroughs. "
                "Return ONLY the location name without any additional text, or 'None' if no location is mentioned.\n\n"
                f"Message: {message}"
            )
            
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                module_name="advisory"
            )
            
            # Clean up the response
            location = response.strip()
            if location.lower() == "none" or not location:
                return None
                
            # Remove any quotes or extra punctuation
            location = location.strip('"\'.,;:()[]{}')
            
            return location

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