from typing import Dict, Optional
import logging
from ..llm import LLMClient
from .api_client import PropertyListingsAPIClient

logger = logging.getLogger(__name__)


class PropertyListingsModule:
    """Module for handling property listings inquiries in general chat."""

    def __init__(self):
        self.api_client = PropertyListingsAPIClient()
        self.llm_client = LLMClient()

    async def handle_inquiry(self, message: str, context: Dict, user_id: Optional[str] = None) -> str:
        """
        Handle property listings inquiries.

        Args:
            message: The user's message
            context: Conversation context
            user_id: Optional user ID for authenticated users

        Returns:
            Response message
        """
        try:
            # 1. Fetch all available properties
            properties = await self.api_client.get_all_properties()

            # 2. If user is logged in, fetch their saved properties
            user_dashboard = None
            if user_id:
                user_dashboard = await self.api_client.get_user_dashboard(user_id)

            # 3. Prepare context for LLM
            llm_context = {"available_properties": properties, "user_dashboard": user_dashboard, "user_query": message}

            # 4. Generate response using LLM
            response = await self.llm_client.generate_response(
                messages=[
                    {"role": "system", "content": self._get_property_listings_prompt()},
                    {"role": "user", "content": self._format_context_for_llm(llm_context)},
                ],
                temperature=0.7,
            )

            return response

        except Exception as e:
            logger.error(f"Error in property listings module: {str(e)}")
            return "I'm sorry, I couldn't retrieve property listings information at the moment. Please try again later."

    def _get_property_listings_prompt(self) -> str:
        """Generate the prompt for property listings inquiries."""
        return """
        You are a helpful real estate assistant for MaiSON. Your task is to help users find properties 
        that match their criteria based on the available listings. You have access to:
        
        1. A list of all available properties on MaiSON
        2. The user's saved properties (if they are logged in)
        
        When responding to property inquiries:
        - Recommend properties that match the user's criteria
        - Highlight key features that align with their interests
        - If they're looking for something specific not in our listings, acknowledge that
        - For logged-in users, reference their saved properties when relevant
        - Keep responses concise but informative
        - DO NOT include property IDs in your responses to users
        - Be conversational and helpful
        - If the user asks for properties with specific criteria (like number of bedrooms), only show properties that match those criteria
        - If no properties match the exact criteria, suggest similar alternatives
        
        The user's query and available properties will be provided in the next message.
        """

    def _format_context_for_llm(self, context: Dict) -> str:
        """
        Format the context data for the LLM.

        Args:
            context: Dictionary containing properties and user data

        Returns:
            Formatted text for LLM consumption
        """
        properties = context.get("available_properties", [])
        user_dashboard = context.get("user_dashboard")
        user_query = context.get("user_query", "")

        formatted_text = f"USER QUERY: {user_query}\n\n"

        # Format available properties
        formatted_text += "AVAILABLE PROPERTIES:\n"
        for i, prop in enumerate(properties[:10]):  # Limit to 10 properties to avoid token limits
            # Get bedrooms from both top-level and specs
            bedrooms = prop.get("bedrooms")
            if bedrooms is None and "specs" in prop and prop["specs"]:
                bedrooms = prop.get("specs", {}).get("bedrooms")

            # Get bathrooms from both top-level and specs
            bathrooms = prop.get("bathrooms")
            if bathrooms is None and "specs" in prop and prop["specs"]:
                bathrooms = prop.get("specs", {}).get("bathrooms")

            # Get property type from specs
            property_type = prop.get("specs", {}).get("property_type", "Unknown")

            formatted_text += f"Property {i+1}:\n"
            formatted_text += f"- ID: {prop.get('property_id')}\n"  # Include ID for reference but instruct LLM not to show it
            formatted_text += f"- Price: £{prop.get('price', 0):,}\n"
            formatted_text += f"- Location: {prop.get('address', {}).get('city', 'Unknown')}, {prop.get('address', {}).get('postcode', 'Unknown')}\n"
            formatted_text += f"- Bedrooms: {bedrooms or 'Unknown'}\n"
            formatted_text += f"- Bathrooms: {bathrooms or 'Unknown'}\n"
            formatted_text += f"- Type: {property_type}\n"
            formatted_text += f"- Description: {prop.get('details', {}).get('description', 'No description available')[:100]}...\n\n"

        # Add user's saved properties if available
        if user_dashboard:
            formatted_text += "\nUSER'S SAVED PROPERTIES:\n"
            for i, prop in enumerate(user_dashboard.get("saved_properties", [])):
                # Get bedrooms from specs
                bedrooms = prop.get("specs", {}).get("bedrooms", "Unknown")

                # Get property type from specs
                property_type = prop.get("specs", {}).get("property_type", "Unknown")

                formatted_text += f"Saved Property {i+1}:\n"
                formatted_text += f"- ID: {prop.get('property_id')}\n"
                formatted_text += f"- Price: £{prop.get('price', 0):,}\n"
                formatted_text += (
                    f"- Location: {prop.get('address', {}).get('city', 'Unknown')}, {prop.get('address', {}).get('postcode', 'Unknown')}\n"
                )
                formatted_text += f"- Bedrooms: {bedrooms}\n"
                formatted_text += f"- Type: {property_type}\n"
                formatted_text += f"- User Notes: {prop.get('notes', 'No notes')}\n\n"

            # Add negotiations if any
            if user_dashboard.get("negotiations_as_buyer"):
                formatted_text += "\nUSER'S ACTIVE NEGOTIATIONS:\n"
                for i, neg in enumerate(user_dashboard.get("negotiations_as_buyer", [])):
                    formatted_text += f"Negotiation {i+1}:\n"
                    formatted_text += f"- Property ID: {neg.get('property_id')}\n"
                    formatted_text += f"- Current Offer: £{neg.get('current_offer', 0):,}\n"
                    formatted_text += f"- Status: {neg.get('status', 'Unknown')}\n"
                    formatted_text += f"- Awaiting Response From: {neg.get('awaiting_response_from', 'Unknown')}\n\n"

        return formatted_text
