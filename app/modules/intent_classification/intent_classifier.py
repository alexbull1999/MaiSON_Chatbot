from enum import Enum
from ..llm import LLMClient, LLMProvider

class Intent(Enum):
    PROPERTY_INQUIRY = "property_inquiry"
    AVAILABILITY_AND_BOOKING_REQUEST = "availability_and_booking_request"
    PRICE_INQUIRY = "price_inquiry"
    GENERAL_QUESTION = "general_question"
    BUYER_SELLER_COMMUNICATION = "buyer_seller_communication"
    NEGOTIATION = "negotiation"
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
            Intent.PROPERTY_INQUIRY: (
                "Questions about property details, features, or specifications"
            ),
            Intent.AVAILABILITY_AND_BOOKING_REQUEST: (
                "Questions about property availability, viewing times, or scheduling viewings"
            ),
            Intent.PRICE_INQUIRY: (
                "Questions about property prices, costs, or financial aspects"
            ),
            Intent.BUYER_SELLER_COMMUNICATION: (
                "Direct communication between buyers and sellers about a property"
            ),
            Intent.NEGOTIATION: (
                "Messages related to price negotiations, offers, or counteroffers"
            ),
            Intent.GENERAL_QUESTION: (
                "General questions about buying or selling properties"
            ),
            Intent.UNKNOWN: (
                "Messages that don't clearly fit into other categories"
            )
        }

    def _get_classification_prompt(self) -> str:
        """Generate the prompt for intent classification."""
        prompt = (
            "You are an intent classifier for a real estate chatbot. "
            "Your task is to classify user messages into one of the following intents:\n\n"
            "Available Intents:\n"
        )
        
        # Add descriptions for each intent
        for intent, description in self._intent_descriptions.items():
            prompt += f"- {intent.value}: {description}\n"

        prompt += (
            "\nInstructions:\n"
            "1. Analyze the user's message carefully\n"
            "2. Consider the context and implied meaning\n"
            "3. Return ONLY the intent name without any additional text\n"
            "4. If unsure, return \"unknown\"\n\n"
            "Example classifications:\n"
            "- \"What are the features of this house?\" -> \"property_inquiry\"\n"
            "- \"When can I view the apartment?\" -> \"availability_and_booking_request\"\n"
            "- \"How much does it cost?\" -> \"price_inquiry\"\n"
            "- \"I'd like to make an offer of $500,000\" -> \"negotiation\"\n"
            "- \"Let me know if you have any questions about the property\" -> \"buyer_seller_communication\"\n"
            "- \"What are good areas to live in London?\" -> \"general_question\"\n"
            "Classify the following message:\n"
        )
        return prompt

    async def classify(self, message: str) -> Intent:
        """Classify the intent of a given message using LLM."""
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