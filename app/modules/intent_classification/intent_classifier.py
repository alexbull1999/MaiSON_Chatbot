from enum import Enum
from typing import Dict, Optional
from ..llm import LLMClient, LLMProvider

class Intent(Enum):
    PROPERTY_INQUIRY = "property_inquiry"
    AVAILABILITY_AND_BOOKING_REQUEST = "availability_and_booking_request"
    PRICE_INQUIRY = "price_inquiry"
    GENERAL_QUESTION = "general_question"
    SELLER_MESSAGE = "seller_message"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "Intent":
        """Convert string to Intent enum, with fallback to UNKNOWN."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.UNKNOWN

class IntentClassifier:
    def __init__(self):
        self.llm_client = LLMClient(provider=LLMProvider.GEMINI)
        self._intent_descriptions = {
            Intent.PROPERTY_INQUIRY: "Questions about property details, features, or specifications",
            Intent.AVAILABILITY_AND_BOOKING_REQUEST: "Questions about property availability, viewing times, or scheduling a viewing",
            Intent.PRICE_INQUIRY: "Questions about property prices, costs, or financial aspects",
            Intent.SELLER_MESSAGE: "Requests to contact or communicate with the property seller",
            Intent.GENERAL_QUESTION: "General questions about buying or selling properties, unrelated to one of the above categories",
            Intent.UNKNOWN: "Messages that don't clearly fit into other categories"
        }

    def _get_classification_prompt(self) -> str:
        """Generate the prompt for intent classification."""
        prompt = """You are an intent classifier for a real estate chatbot. Your task is to classify user messages into one of the following intents:

Available Intents:
"""
        # Add descriptions for each intent
        for intent, description in self._intent_descriptions.items():
            prompt += f"- {intent.value}: {description}\n"

        prompt += """
Instructions:
1. Analyze the user's message carefully
2. Consider the context and implied meaning
3. Return ONLY the intent name (e.g., "property_inquiry") without any additional text or explanation
4. If unsure, return "unknown"

Example classifications:
- "What are the features of this house?" -> "property_inquiry"
- "When can I view the apartment?" -> "availability_and_booking_request"
- "I want to book a viewing" -> "availability_and_booking_request"
- "How much does it cost?" -> "price_inquiry"
- "Can you ask the seller about parking?" -> "seller_message"
- "Hello" -> "unknown"
- "What are good areas to live in London?" -> "general_question"
Classify the following message:
"""
        return prompt

    async def classify(self, message: str) -> Intent:
        """
        Classify the intent of a given message using LLM.
        """
        try:
            # Prepare the full prompt
            prompt = self._get_classification_prompt()
            
            # Call LLM for classification
            response = await self.llm_client.generate_response(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3  # Lower temperature for more consistent results
            )
            
            # Clean up response and convert to Intent
            intent_str = response.strip().lower()
            return Intent.from_string(intent_str)
            
        except Exception as e:
            print(f"Error in intent classification: {str(e)}")
            return Intent.UNKNOWN 