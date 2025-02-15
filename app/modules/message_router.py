from typing import Optional
from .intent_classification.intent_classifier import IntentClassifier, Intent
from .context_manager.context_manager import ContextManager
from .property_context.property_context_module import PropertyContextModule
from .advisory.advisory_module import AdvisoryModule
from .communication.communication_module import CommunicationModule
from .seller_communication.seller_communication_module import SellerCommunicationModule
from sqlalchemy.orm import Session

class MessageRouter:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.context_manager = ContextManager()
        self.property_context = PropertyContextModule()
        self.advisory_module = AdvisoryModule()
        self.communication_module = CommunicationModule()
        self.seller_communication = SellerCommunicationModule()

    async def process_message(self, message: str, db: Session = None, context: dict = None) -> str:
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
            intent = await self.intent_classifier.classify(message)
            print(f"Debug: Classified intent: {intent}")

            # Get current context if not provided
            if context is None:
                context = self.context_manager.get_context()
            print(f"Debug: Retrieved context: {context}")

            # Route the message based on intent
            response = await self._route_intent(intent, message, context, db)
            print(f"Debug: Generated response: {response[:100]}...")

            # Add response to context
            self.context_manager.add_message(response, role="assistant")
            print("Debug: Added response to context")

            return response
        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            raise

    async def _route_intent(self, intent: Intent, message: str, context: dict, db: Session = None) -> str:
        """
        Route the message to appropriate module based on intent.
        """
        try:
            print(f"Debug: Routing intent: {intent}")
            
            if intent == Intent.SELLER_MESSAGE:
                # Handle seller message
                if not context.get("seller_id"):
                    return "I notice you want to contact the seller, but I don't have the seller's information. Please make sure you're viewing a specific property and try again."
                
                if not db:
                    return "I'm unable to forward your message to the seller at the moment. Please try again later."
                
                # Forward the message to the seller
                success = await self.seller_communication.forward_message_to_seller(
                    seller_id=context["seller_id"],
                    user_message=message,
                    conversation_id=context["conversation_id"],
                    property_id=context.get("property_id"),
                    user_info={
                        "name": context.get("user_name", "Anonymous"),
                        "email": context.get("user_email", "Not provided")
                    },
                    db=db
                )
                
                if success:
                    return "I've forwarded your message to the seller. They will be notified and can respond to you directly. Is there anything else you'd like to know about the property?"
                else:
                    return "I apologize, but I couldn't forward your message to the seller at this time. Please try again later."
            
            elif intent == Intent.PROPERTY_INQUIRY:
                # Handle property inquiry
                current_property = self.property_context.get_current_property()
                if current_property:
                    print(f"Debug: Found current property: {current_property.id}")
                    insights = self.advisory_module.generate_property_insights(current_property)
                    return "\n".join(insights)
            
            elif intent == Intent.AVAILABILITY_AND_BOOKING_REQUEST:
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