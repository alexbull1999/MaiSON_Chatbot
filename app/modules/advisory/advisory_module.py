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
            is_property_specific = bool(context and context.get("property_id"))

            if is_property_specific:
                # Get property details first
                property_id = context["property_id"]
                # TODO: Implement get_property_details to fetch property info including postcode
                property_details = await self._get_property_details(property_id)

                if not property_details or "postcode" not in property_details:
                    raise ValueError(f"Could not find postcode for property {property_id}")

                # Get property-specific insights
                insights = await self.data_service.get_area_insights(property_details["postcode"], is_broad_area=False)

                # Add property-specific analysis
                analysis = await self._generate_property_analysis(location, insights.model_dump(), property_details)
            else:
                # Get broad area insights
                insights = await self.data_service.get_area_insights(location, is_broad_area=True)

                # Add area-level analysis
                insights_dict = insights.model_dump() if insights else {}

                # Check if we have any meaningful data before generating analysis
                has_data = False

                # Check market overview
                market_overview = insights_dict.get("market_overview", {})
                if market_overview and any(v is not None and v != 0 and v != "" for v in market_overview.values()):
                    has_data = True

                # Check area profile
                if not has_data:
                    area_profile = insights_dict.get("area_profile", {})
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
            insights_dict["analysis"] = analysis
            insights_dict["last_updated"] = datetime.utcnow().isoformat()

            return insights_dict

        except Exception as e:
            print(f"Error getting area insights: {str(e)}")
            return {}

    async def _get_property_details(self, property_id: str) -> Optional[Dict]:
        """Get property details from the database or external service."""
        # TODO: Implement property details retrieval
        # This should return at minimum: postcode, type, price
        return None

    async def _generate_property_analysis(self, location: str, insights: Dict, property_details: Dict) -> str:
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

        response = await self.llm_client.generate_response(messages=[{"role": "user", "content": prompt}], temperature=0.7)
        return response

    async def _generate_area_analysis(self, location: str, insights: Dict) -> str:
        """Generate a natural language analysis of an area based on insights."""
        try:
            # Clean up insights to remove None values and empty dictionaries
            clean_insights = {}

            # Process market overview
            market_data = insights.get("market_overview", {})
            if market_data and any(v is not None and v != 0 and v != "" for v in market_data.values()):
                clean_insights["market_overview"] = market_data

            # Process area profile
            area_profile = insights.get("area_profile", {})
            if area_profile:
                clean_area_profile = {}

                # Process demographics
                demographics = area_profile.get("demographics", {})
                if demographics and any(v for v in demographics.values() if v):
                    clean_area_profile["demographics"] = demographics

                # Process crime rate
                crime_rate = area_profile.get("crime_rate")
                if crime_rate is not None:
                    clean_area_profile["crime_rate"] = crime_rate

                # Process amenities
                amenities = area_profile.get("amenities_summary", {})
                if amenities and any(v for v in amenities.values() if v):
                    clean_area_profile["amenities"] = amenities

                # Process transport
                transport = area_profile.get("transport_summary", {})
                if transport and any(v for v in transport.values() if v):
                    clean_area_profile["transport"] = transport

                # Process education
                education = area_profile.get("education", {})
                if education and any(v for v in education.values() if v):
                    clean_area_profile["education"] = education

                if clean_area_profile:
                    clean_insights["area_profile"] = clean_area_profile

            # Create a prompt that focuses on available data and encourages the LLM to use its knowledge
            prompt = f"Analyze this area ({location}) based on the following data.\n\n"

            # Add market overview if available
            if "market_overview" in clean_insights:
                market = clean_insights["market_overview"]
                prompt += "Market Overview:\n"
                if market.get("average_price") is not None:
                    prompt += f"- Average Price: {market.get('average_price')}\n"
                if market.get("price_change_1y") is not None:
                    prompt += f"- Annual Change: {market.get('price_change_1y')}%\n"
                if market.get("number_of_sales") is not None:
                    prompt += f"- Market Activity: {market.get('number_of_sales')} sales\n"
                prompt += "\n"

            # Add area profile if available
            if "area_profile" in clean_insights:
                area = clean_insights["area_profile"]
                prompt += "Area Profile:\n"

                if "demographics" in area:
                    prompt += f"- Demographics: {area['demographics']}\n"

                if "crime_rate" in area:
                    prompt += f"- Crime Rate: {area['crime_rate']}\n"

                if "amenities" in area:
                    prompt += f"- Amenities: {area['amenities']}\n"

                if "transport" in area:
                    prompt += f"- Transport: {area['transport']}\n"

                if "education" in area:
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
                messages=[{"role": "user", "content": prompt}], temperature=0.7, module_name="advisory"
            )
            return response

        except Exception as e:
            print(f"Error generating area analysis: {str(e)}")
            return "I apologize, but I couldn't generate an analysis for this area at the moment."

    async def _extract_locations(self, message: str) -> List[str]:
        """Extract all locations mentioned in the message."""
        try:
            prompt = (
                f"Extract all location names (cities, towns, neighborhoods, boroughs, districts, etc.) mentioned in the following message. "
                f"Return ONLY the names as a comma-separated list. "
                f"If no locations are mentioned, return 'None'. "
                f"Message: {message}"
            )

            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}], temperature=0.1, module_name="advisory"
            )

            # Clean up the response
            locations_text = response.strip()
            if locations_text.lower() == "none" or not locations_text:
                return []

            # Split by commas and clean up each location
            locations = [loc.strip().strip("\"'.,;:()[]{}") for loc in locations_text.split(",")]
            # Filter out empty strings and "None"
            locations = [loc for loc in locations if loc and loc.lower() != "none"]

            print(f"Extracted locations: {locations}")
            return locations

        except Exception as e:
            print(f"Error extracting locations: {str(e)}")
            return []

    async def _is_asking_for_areas_within_city(self, message: str, locations: List[str]) -> Optional[str]:
        """
        Determine if the user is asking about areas/neighborhoods within a specific city.
        Returns the city name if the user is asking about areas within it, None otherwise.
        """
        if not locations:
            return None

        try:
            prompt = (
                f"Analyze this message: '{message}'\n\n"
                f"Is the user asking about specific areas, neighborhoods, or districts WITHIN a larger city or region? "
                f"If yes, identify which city or region they want areas within and return ONLY that city/region name. "
                f"If they're not asking about areas within a city, return 'No'.\n\n"
                f"For example:\n"
                f"- 'What are good areas to live in Manchester?' → 'Manchester'\n"
                f"- 'Is Birmingham a good place to invest?' → 'No'\n"
                f"- 'Compare London and Leeds property prices' → 'No'\n"
                f"- 'Which neighborhoods in Bristol are good for families?' → 'Bristol'"
            )

            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}], temperature=0.1, module_name="advisory"
            )

            response = response.strip()
            if response.lower() == "no":
                return None

            # Check if the response matches one of our extracted locations
            for location in locations:
                if location.lower() in response.lower() or response.lower() in location.lower():
                    print(f"User is asking about areas within: {location}")
                    return location

            return None
        except Exception as e:
            print(f"Error determining if asking about areas within city: {str(e)}")
            return None

    async def handle_general_inquiry(self, message: str, context: Optional[Dict] = None) -> str:
        """Handle general inquiries about real estate and the market."""
        try:
            # Extract all locations from the message
            locations = await self._extract_locations(message)
            print(f"All extracted locations: {locations}")

            # Check if the user is asking about areas within a specific city
            parent_city = await self._is_asking_for_areas_within_city(message, locations)

            # Get area insights for each location
            location_insights = {}
            for location in locations:
                insights = await self.get_area_insights(location)
                if insights:
                    # Check if insights contain useful data
                    has_data = self._check_insights_for_useful_data(insights)
                    if has_data:
                        location_insights[location] = insights
                        print(f"Got useful insights for {location}")
                    else:
                        print(f"No useful data in insights for {location}")

            # Prepare the prompt based on the available data
            if location_insights:
                # We have useful data for at least one location
                prompt = f"User question: {message}\n\n"
                prompt += "Area Information:\n"

                for location, insights in location_insights.items():
                    prompt += f"\n{location}:\n"

                    # Add market overview if available
                    market_overview = insights.get("market_overview", {})
                    if market_overview and any(v is not None and v != 0 and v != "" for v in market_overview.values()):
                        prompt += "Market Overview:\n"
                        if market_overview.get("average_price") is not None:
                            prompt += f"- Average Price: {market_overview.get('average_price')}\n"
                        if market_overview.get("price_change_1y") is not None:
                            prompt += f"- Annual Change: {market_overview.get('price_change_1y')}%\n"
                        if market_overview.get("number_of_sales") is not None:
                            prompt += f"- Market Activity: {market_overview.get('number_of_sales')} sales\n"

                    # Add area profile if available
                    area_profile = insights.get("area_profile", {})
                    if area_profile:
                        prompt += "Area Profile:\n"

                        # Add demographics if available
                        demographics = area_profile.get("demographics", {})
                        if demographics and any(v for v in demographics.values() if v):
                            prompt += f"- Demographics: {demographics}\n"

                        # Add crime rate if available
                        crime_rate = area_profile.get("crime_rate")
                        if crime_rate is not None:
                            prompt += f"- Crime Rate: {crime_rate}\n"

                        # Add amenities if available
                        amenities = area_profile.get("amenities_summary", {})
                        if amenities and any(v for v in amenities.values() if v):
                            prompt += f"- Amenities: {amenities}\n"

                        # Add transport if available
                        transport = area_profile.get("transport_summary", {})
                        if transport and any(v for v in transport.values() if v):
                            prompt += f"- Transport: {transport}\n"

                        # Add education if available
                        education = area_profile.get("education", {})
                        if education and any(v for v in education.values() if v):
                            prompt += f"- Education: {education}\n"

                if parent_city:
                    prompt += f"\nThe user is asking about specific areas or neighborhoods within {parent_city}. "
                    prompt += f"Please recommend at least 3-5 specific neighborhoods or districts within {parent_city} "
                    prompt += "that would be suitable based on their query. "
                    prompt += "For each recommended area, include details about:\n"
                    prompt += "1. The character and vibe of the neighborhood\n"
                    prompt += "2. Typical property prices and types\n"
                    prompt += "3. Transport connections\n"
                    prompt += "4. Local amenities\n"
                    prompt += "5. Who the area might be suitable for\n\n"

                prompt += "\nPlease provide a detailed response to the user's question using both the information above and your own knowledge. "
                prompt += "For any aspects where specific data is not provided, use your general knowledge to fill in the gaps. "
                prompt += "DO NOT mention any lack of data in your response. Be specific, helpful, and informative."
            else:
                # No useful data for any location, fall back to using the LLM's own knowledge
                if parent_city:
                    # User is asking about areas within a city but we don't have data
                    prompt = (
                        f"User question: {message}\n\n"
                        f"The user is asking about specific areas or neighborhoods within {parent_city}. "
                        f"Please recommend at least 3-5 specific neighborhoods or districts within {parent_city} "
                        f"that would be suitable based on their query. "
                        f"For each recommended area, include details about:\n"
                        f"1. The character and vibe of the neighborhood\n"
                        f"2. Typical property prices and types\n"
                        f"3. Transport connections\n"
                        f"4. Local amenities\n"
                        f"5. Who the area might be suitable for\n\n"
                        f"DO NOT mention any lack of data or information in your response. "
                        f"Use your knowledge to provide specific, helpful recommendations. "
                        f"Be confident and detailed in your response."
                    )
                else:
                    # General fallback
                    prompt = (
                        f"User question: {message}\n\n"
                        f"Please provide a detailed and helpful response about this real estate inquiry using your own knowledge. "
                        f"If the question is about specific locations, provide specific information about those locations such as "
                        f"property market trends, typical prices, neighborhood characteristics, transport links, and amenities. "
                        f"If the user is asking about areas or neighborhoods that would be suitable for certain criteria, recommend "
                        f"specific areas and include details about their character, property prices, transport, amenities, and target demographic. "
                        f"DO NOT mention any lack of data or information in your response. "
                        f"Instead, confidently provide information based on your general knowledge about real estate and locations. "
                        f"Be specific, helpful, and informative in your response."
                    )

            print(f"Using prompt type: {'areas-within-city' if parent_city else 'data-based' if location_insights else 'fallback'}")

            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}], temperature=0.7, module_name="advisory"
            )
            return response

        except Exception as e:
            print(f"Error in advisory module: {str(e)}")
            return "I apologize, but I encountered an error processing your inquiry. Please try again."

    def _check_insights_for_useful_data(self, insights: Dict) -> bool:
        """Check if insights contain useful data."""
        if not insights:
            return False

        # Check market overview
        market_overview = insights.get("market_overview", {})
        if market_overview and isinstance(market_overview, dict):
            if any(v is not None and v != 0 and v != "" for v in market_overview.values()):
                return True

        # Check area profile
        area_profile = insights.get("area_profile", {})
        if area_profile and isinstance(area_profile, dict):
            # Check direct values
            if any(v is not None and v != 0 and v != "" for v in area_profile.values() if not isinstance(v, dict)):
                return True

            # Check nested dictionaries
            for key, value in area_profile.items():
                if isinstance(value, dict) and any(v is not None and v != 0 and v != "" for v in value.values()):
                    return True

        return False

    def get_property_recommendations(self, user_preferences: dict) -> List[Dict]:
        """Get property recommendations based on user preferences and market data."""
        # TODO: Implement property recommendations using PropertyDataService
        return []

    def get_market_analysis(self, location: str) -> Dict[str, str]:
        """Get market analysis for a specific location."""
        # TODO: Implement market analysis using PropertyDataService
        return {"market_trend": "Stable", "average_price": "Contact for details", "demand_level": "Moderate"}

    def generate_property_insights(self, property: Property) -> List[str]:
        """Generate insights about a specific property."""
        insights = [
            f"Property Type: {property.type}",
            f"Location: {property.location}",
            "Additional insights will be generated based on property data",
        ]
        return insights
