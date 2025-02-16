from typing import Dict, Optional
from .intent_classification import IntentClassifier, Intent
from .property_context import PropertyContextModule
from .advisory import AdvisoryModule
from .communication import CommunicationModule
from .context_manager import ContextManager

class MessageRouter:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.property_context = PropertyContextModule()
        self.advisory_module = AdvisoryModule()
        self.communication_module = CommunicationModule()
        self.context_manager = ContextManager()

    async def process_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Process an incoming message and return a response."""
        try:
            # Classify intent
            intent = await self.intent_classifier.classify(message)
            
            # Update context with the message
            self.context_manager.add_message(message)
            
            # Route to appropriate handler
            response = await self._route_intent(intent, message, context or {})
            
            # Add response to context
            self.context_manager.add_message(response, role="assistant")
            
            return response
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return "I apologize, but I encountered an error processing your message. Please try again."

    async def _route_intent(self, intent: Intent, message: str, context: Dict) -> str:
        """Route the message to the appropriate handler based on intent."""
        intent_handlers = {
            Intent.PROPERTY_INQUIRY: self.property_context.handle_inquiry,
            Intent.AVAILABILITY_AND_BOOKING_REQUEST: self.property_context.handle_booking,
            Intent.PRICE_INQUIRY: self.property_context.handle_pricing,
            Intent.SELLER_MESSAGE: self.communication_module.handle_seller_message,
            Intent.GENERAL_QUESTION: self.advisory_module.handle_general_inquiry,
            Intent.UNKNOWN: self.communication_module.handle_unclear_intent
        }
        
        handler = intent_handlers.get(intent, self.communication_module.handle_unclear_intent)
        return await handler(message, context)

    async def route_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, str]:
        """Route incoming message and return response with metadata."""
        try:
            # Classify message intent
            intent = await self.intent_classifier.classify(message)
            
            # Get appropriate handler
            response = await self._route_intent(intent, message, context or {})
            
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