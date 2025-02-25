from typing import Dict, List, Optional
from enum import Enum
from ..llm import LLMClient, LLMProvider


class MessageType(Enum):
    GREETING = "greeting"
    INQUIRY = "inquiry"
    RESPONSE = "response"
    CONFIRMATION = "confirmation"
    ERROR = "error"


class CommunicationModule:
    def __init__(self):
        self.templates: Dict[MessageType, List[str]] = {
            MessageType.GREETING: [
                "Welcome to MaiSON! How can I assist you today?",
                "Hello! I'm here to help you with your property needs.",
            ],
            MessageType.ERROR: [
                "I apologize, but I couldn't process that request.",
                "Something went wrong. Could you please try again?",
            ],
        }
        # Initialize LLM client with Gemini provider
        self.llm_client = LLMClient(provider=LLMProvider.GEMINI)

    def format_message(self, message_type: MessageType, **kwargs) -> str:
        """Format a message based on the message type and provided parameters."""
        templates = self.templates.get(message_type, [])
        if not templates:
            return "I apologize, but I'm not sure how to respond to that."

        template = templates[0]  # Use first template for now
        try:
            return template.format(**kwargs)
        except KeyError:
            print("Error formatting message: Missing required parameters")
            return template
        except Exception:
            print("Error formatting message")
            return "I apologize, but I couldn't format the response correctly."

    async def generate_response(self, intent: str, context: Optional[Dict] = None) -> str:
        """Generate a response based on intent and context using LLM."""
        try:
            prompt = (
                f"Intent: {intent}\n"
                f"Context: {context}\n"
                "Please provide a response based on this information."
            )
            
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
                module_name="communication"
            )
            
            return response
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return self.format_message(MessageType.ERROR)

    async def handle_unclear_intent(
        self, message: str, context: Optional[Dict] = None
    ) -> str:
        """Handle messages with unclear intent."""
        try:
            prompt = (
                f"User message: {message}\n"
                "The intent of this message is unclear. Please provide a helpful response "
                "that guides the user towards expressing their property-related needs more clearly."
            )
            
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                module_name="communication"
            )
            return response
        except Exception as e:
            print(f"Error handling unclear intent: {str(e)}")
            return self.format_message(MessageType.ERROR)

    async def generate_property_description(self, property_data: Dict) -> str:
        """
        Generate a natural language description of a property using the LLM.
        """
        prompt = {
            "role": "user",
            "content": f"Please generate a natural, engaging description of this property: {str(property_data)}",
        }

        try:
            return await self.llm_client.generate_response(
                messages=[prompt], temperature=0.7, max_tokens=200
            )
        except Exception:
            # Fallback to basic description
            return f"This is a {property_data.get('type', 'property')} located in {property_data.get('location', 'the area')}."
