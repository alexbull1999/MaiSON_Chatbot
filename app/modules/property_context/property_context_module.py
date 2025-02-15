from typing import Dict, List, Optional
from ..llm import LLMClient, LLMProvider

class Property:
    def __init__(self, id: str, name: str, type: str, location: str):
        self.id = id
        self.name = name
        self.type = type
        self.location = location

class PropertyContextModule:
    """Module for handling property-specific queries and context."""
    
    def __init__(self):
        self.properties: Dict[str, Property] = {}
        self.current_property: Optional[Property] = None
        self.llm_client = LLMClient(provider=LLMProvider.GEMINI)

    def add_property(self, property: Property):
        """Add a property to the context."""
        self.properties[property.id] = property

    def get_property(self, property_id: str) -> Optional[Property]:
        """Get a property by its ID."""
        return self.properties.get(property_id)

    def set_current_property(self, property_id: str) -> bool:
        """Set the current property context."""
        if property_id in self.properties:
            self.current_property = self.properties[property_id]
            return True
        return False

    def get_current_property(self) -> Optional[Property]:
        """Get the current property in context."""
        return self.current_property

    def clear_current_property(self):
        """Clear the current property context."""
        self.current_property = None

    async def handle_inquiry(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle property-specific inquiries."""
        try:
            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a real estate agent. Provide detailed "
                            "information about property features and specifications."
                        )
                    },
                    {"role": "user", "content": message}
                ],
                temperature=0.7
            )
            return response
        except Exception as e:
            print(f"Error in property context module: {str(e)}")
            return (
                "I apologize, but I'm having trouble processing your request. "
                "Please try again or rephrase your question."
            )

    async def handle_booking(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle property viewing and booking requests."""
        try:
            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a booking assistant. Help users schedule "
                            "property viewings and manage appointments."
                        )
                    },
                    {"role": "user", "content": message}
                ],
                temperature=0.7
            )
            return response
        except Exception as e:
            print(f"Error in booking handler: {str(e)}")
            return (
                "I apologize, but I'm having trouble with the booking request. "
                "Please try again later or contact our office directly."
            )

    async def handle_pricing(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle property pricing inquiries."""
        try:
            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a pricing specialist. Provide accurate "
                            "information about property prices and market values."
                        )
                    },
                    {"role": "user", "content": message}
                ],
                temperature=0.7
            )
            return response
        except Exception as e:
            print(f"Error in pricing handler: {str(e)}")
            return (
                "I apologize, but I'm having trouble retrieving pricing information. "
                "Please try again or contact our office for detailed pricing."
            ) 