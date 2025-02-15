from typing import Dict, List, Optional
from .communication.communication_module import CommunicationModule, MessageType

class ResponseGenerator:
    def __init__(self):
        self.communication_module = CommunicationModule()

    async def generate_response(self, 
                         intent: str, 
                         context: dict, 
                         property_data: Optional[Dict] = None,
                         market_data: Optional[Dict] = None) -> str:
        """
        Generate a comprehensive response based on intent, context, and available data.
        """
        response_parts = []

        # Add greeting if this is the start of conversation
        if not context.get("conversation_history"):
            response_parts.append(
                self.communication_module.format_message(MessageType.GREETING)
            )

        # Generate main response based on available data
        main_response = await self._generate_main_response(intent, context, property_data, market_data)
        if main_response:
            response_parts.append(main_response)

        # Combine all parts
        return "\n".join(filter(None, response_parts))

    async def _generate_main_response(self,
                              intent: str,
                              context: dict,
                              property_data: Optional[Dict],
                              market_data: Optional[Dict]) -> str:
        """
        Generate the main part of the response based on the intent and available data.
        """
        if property_data:
            return self._format_property_response(property_data, intent)
        elif market_data:
            return self._format_market_response(market_data)
        else:
            return await self.communication_module.generate_response(intent, context)

    def _format_property_response(self, property_data: Dict, intent: str) -> str:
        """Format property-related response."""
        # TODO: Implement proper property response formatting
        return f"Here are the details about the property: {property_data}"

    def _format_market_response(self, market_data: Dict) -> str:
        """Format market-related response."""
        # TODO: Implement proper market response formatting
        return f"Here's the market analysis: {market_data}" 