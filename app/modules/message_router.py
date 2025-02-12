from typing import Optional
from .intent_classification.intent_classifier import IntentClassifier, Intent
from .context_manager.context_manager import ContextManager
from .property_context.property_context_module import PropertyContextModule
from .advisory.advisory_module import AdvisoryModule
from .communication.communication_module import CommunicationModule

class MessageRouter:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.context_manager = ContextManager()
        self.property_context = PropertyContextModule()
        self.advisory_module = AdvisoryModule()
        self.communication_module = CommunicationModule()

    async def process_message(self, message: str) -> str:
        """
        Process an incoming message and route it to appropriate modules.
        Returns a response string.
        """
        try:
            print(f"Debug: Processing message in router: {message}")
            # Add message to context
            self.context_manager.add_message(message)
            print("Debug: Added message to context")

            # Classify intent
            intent = self.intent_classifier.classify(message)
            print(f"Debug: Classified intent: {intent}")

            # Get current context
            context = self.context_manager.get_context()
            print(f"Debug: Retrieved context: {context}")

            # Generate response using communication module directly for now
            # This bypasses the routing logic temporarily to test Gemini integration
            print("Debug: Generating response using communication module directly")
            response = await self.communication_module.generate_response(
                str(intent.value),
                {
                    "message": message,
                    "intent": str(intent.value),
                    "context": context
                }
            )
            print(f"Debug: Generated response: {response[:100]}...")

            # Add response to context
            self.context_manager.add_message(response, role="assistant")
            print("Debug: Added response to context")

            return response
        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            raise

    async def _route_intent(self, intent: Intent, message: str, context: dict) -> str:
        """
        Route the message to appropriate module based on intent.
        """
        try:
            print(f"Debug: Routing intent: {intent}")
            if intent == Intent.PROPERTY_INQUIRY:
                # Handle property inquiry
                current_property = self.property_context.get_current_property()
                if current_property:
                    print(f"Debug: Found current property: {current_property.id}")
                    insights = self.advisory_module.generate_property_insights(current_property)
                    return "\n".join(insights)
            
            elif intent == Intent.AVAILABILITY_CHECK:
                # Handle availability check
                print("Debug: Handling availability check")
                # TODO: Implement availability checking logic
                pass
            
            elif intent == Intent.PRICE_INQUIRY:
                # Handle price inquiry
                current_property = self.property_context.get_current_property()
                if current_property:
                    print(f"Debug: Found current property for price inquiry: {current_property.id}")
                    market_analysis = self.advisory_module.get_market_analysis(current_property.location)
                    return f"The average price in {current_property.location} is {market_analysis['average_price']}"

            # Generate response using communication module
            print("Debug: Generating response using communication module")
            return await self.communication_module.generate_response(str(intent.value), context)
        except Exception as e:
            print(f"Error in _route_intent: {str(e)}")
            raise 