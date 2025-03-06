from typing import Dict, Optional
from .intent_classification import IntentClassifier, Intent
from .property_context import PropertyContextModule
from .advisory import AdvisoryModule
from .communication import CommunicationModule
from .communication.seller_buyer_communication import SellerBuyerCommunicationModule
from .context_manager import ContextManager
from .greeting.greeting_module import GreetingModule
from .website_info import WebsiteInfoModule
from .property_listings import PropertyListingsModule


class MessageRouter:
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.property_context = PropertyContextModule()
        self.advisory_module = AdvisoryModule()
        self.communication_module = CommunicationModule()
        self.seller_buyer_communication = SellerBuyerCommunicationModule()
        self.context_manager = ContextManager()
        self.greeting_module = GreetingModule()
        self.website_info_module = WebsiteInfoModule()
        self.property_listings_module = PropertyListingsModule()

    async def process_message(
        self, message: str, context: Optional[Dict] = None
    ) -> str:
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
            Intent.GREETING: self.greeting_module.handle_greeting,
            Intent.PROPERTY_INQUIRY: self.property_context.handle_inquiry,
            Intent.AVAILABILITY_AND_BOOKING_REQUEST: self.property_context.handle_booking,
            Intent.PRICE_INQUIRY: self.property_context.handle_pricing,
            Intent.BUYER_SELLER_COMMUNICATION: self.seller_buyer_communication.handle_message,
            Intent.NEGOTIATION: self.seller_buyer_communication.handle_message,
            Intent.GENERAL_QUESTION: self.advisory_module.handle_general_inquiry,
            Intent.WEBSITE_FUNCTIONALITY: self.website_info_module.handle_website_functionality,
            Intent.COMPANY_INFORMATION: self.website_info_module.handle_company_information,
            Intent.PROPERTY_LISTINGS_INQUIRY: self.property_listings_module.handle_inquiry,
            Intent.UNKNOWN: self.communication_module.handle_unclear_intent,
        }

        # Update context with the intent for use in handlers
        context["intent"] = intent.value

        handler = intent_handlers.get(
            intent, self.communication_module.handle_unclear_intent
        )
        return await handler(message, context)

    async def route_message(
        self, message: str, context: Optional[Dict] = None, chat_type: str = "general"
    ) -> Dict[str, str]:
        """Route incoming message and return response with metadata."""
        try:
            if chat_type == "general":
                # Use simplified classification for general chat
                intent = await self.intent_classifier.classify_general(message)
                
                # Route to either greeting or advisory module
                if intent == Intent.GREETING:
                    response = await self.greeting_module.handle_greeting(message, context)
                else:
                    # For general chat, we still want to classify the intent more specifically
                    # to catch website and company information queries
                    specific_intent = await self.intent_classifier.classify(message)
                    
                    if specific_intent in [Intent.WEBSITE_FUNCTIONALITY, Intent.COMPANY_INFORMATION, Intent.PROPERTY_LISTINGS_INQUIRY]:
                        # Update context with the intent
                        context_with_intent = context.copy() if context else {}
                        context_with_intent["intent"] = specific_intent.value
                        
                        # Extract user_id from context if available (for property listings)
                        user_id = context.get("user_id") if context else None
                        
                        # Route to appropriate module based on specific intent
                        if specific_intent == Intent.PROPERTY_LISTINGS_INQUIRY:
                            response = await self.property_listings_module.handle_inquiry(message, context_with_intent, user_id)
                        else:
                            # Route to website info module
                            response = await self._route_intent(specific_intent, message, context_with_intent)
                        
                        return {
                            "response": response,
                            "intent": specific_intent.value,
                            "context": context_with_intent,
                        }
                    else:
                        # Default to advisory module for other general questions
                        response = await self.advisory_module.handle_general_inquiry(message, context or {})
                
                return {
                    "response": response,
                    "intent": intent.value,
                    "context": context or {},
                }
            
            # Normal intent classification for property chat
            intent = await self.intent_classifier.classify(message)
            response = await self._route_intent(intent, message, context or {})

            return {
                "response": response,
                "intent": intent.value,
                "context": context or {},
            }

        except Exception as e:
            print(f"Error in message routing: {str(e)}")
            return {
                "response": (
                    "I apologize, but I encountered an error processing your message. "
                    "Please try again or rephrase your question."
                ),
                "intent": Intent.UNKNOWN.value,
                "context": context or {},
            }
