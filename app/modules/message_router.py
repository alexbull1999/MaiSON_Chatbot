from typing import Dict, Optional
from .intent_classification import IntentClassifier, Intent
from .property_context import PropertyContextModule
from .advisory import AdvisoryModule
from .communication import CommunicationModule

class MessageRouter:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.property_context = PropertyContextModule()
        self.advisory = AdvisoryModule()
        self.communication = CommunicationModule()

    async def _handle_property_inquiry(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle property-related inquiries."""
        return await self.property_context.handle_inquiry(message, context)

    async def _handle_availability_booking(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle availability and booking requests."""
        return await self.property_context.handle_booking(message, context)

    async def _handle_price_inquiry(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle price-related inquiries."""
        return await self.property_context.handle_pricing(message, context)

    async def _handle_seller_message(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle messages intended for property sellers."""
        return await self.communication.handle_seller_message(message, context)

    async def _handle_general_question(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle general real estate questions."""
        return await self.advisory.handle_general_inquiry(message, context)

    async def _handle_unknown_intent(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """Handle messages with unclear intent."""
        return await self.communication.handle_unclear_intent(message, context)

    def _get_handler_for_intent(self, intent: Intent):
        """Get the appropriate handler function for a given intent."""
        intent_handlers = {
            Intent.PROPERTY_INQUIRY: self._handle_property_inquiry,
            Intent.AVAILABILITY_AND_BOOKING_REQUEST: self._handle_availability_booking,
            Intent.PRICE_INQUIRY: self._handle_price_inquiry,
            Intent.SELLER_MESSAGE: self._handle_seller_message,
            Intent.GENERAL_QUESTION: self._handle_general_question,
            Intent.UNKNOWN: self._handle_unknown_intent
        }
        return intent_handlers.get(intent, self._handle_unknown_intent)

    async def route_message(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> Dict[str, str]:
        """Route incoming message to appropriate handler based on intent."""
        try:
            # Classify message intent
            intent = await self.intent_classifier.classify(message)
            
            # Get appropriate handler
            handler = self._get_handler_for_intent(intent)
            
            # Process message with handler
            response = await handler(message, context)
            
            return {
                "response": response,
                "intent": intent.value,
                "context": context or {}
            }
            
        except Exception as e:
            print(f"Error in message routing: {str(e)}")
            return {
                "response": (
                    "I apologize, but I encountered an error processing your message. "
                    "Please try again or rephrase your question."
                ),
                "intent": Intent.UNKNOWN.value,
                "context": context or {}
            } 