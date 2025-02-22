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

    async def generate_response(self, intent: str, context: dict) -> str:
        """Generate a response based on the intent and context using the LLM."""
        if not context:
            return self.format_message(MessageType.ERROR)

        try:
            # Prepare conversation history for LLM
            messages = []

            # Add conversation history if available
            if "conversation_history" in context:
                for msg in context["conversation_history"]:
                    messages.append(
                        {
                            "role": "user" if msg["role"] == "user" else "assistant",
                            "content": msg["content"],
                        }
                    )

            # Add current query with intent and context
            current_query = {
                "role": "user",
                "content": (
                    f"Intent: {intent}\n"
                    f"Context: {str(context)}\n"
                    "Please provide a response based on this information."
                ),
            }
            messages.append(current_query)

            # Generate response using LLM
            response = await self.llm_client.generate_response(
                messages=messages, temperature=0.7, max_tokens=300
            )

            if not response:
                return self.format_message(MessageType.ERROR)

            return response

        except Exception:
            # Log the error and return a fallback response
            print("Error generating LLM response")
            return f"I understand you're interested in {intent}. Let me help you with that."

    async def handle_unclear_intent(
        self, message: str, context: Optional[Dict] = None
    ) -> str:
        """Handle messages with unclear intent."""
        try:
            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful real estate assistant. "
                            "The user's intent is unclear. "
                            "Try to understand their needs and provide relevant assistance."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0.7,
            )
            return response
        except Exception:
            return (
                "I'm not quite sure what you're asking. "
                "Could you please rephrase your question or specify what kind of "
                "property information you're looking for?"
            )

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
