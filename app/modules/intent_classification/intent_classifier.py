from enum import Enum
from ..llm import LLMClient
import re

class Intent(Enum):
    GREETING = "greeting"
    PROPERTY_INQUIRY = "property_inquiry"
    AVAILABILITY_AND_BOOKING_REQUEST = "availability_and_booking_request"
    PRICE_INQUIRY = "price_inquiry"
    GENERAL_QUESTION = "general_question"
    BUYER_SELLER_COMMUNICATION = "buyer_seller_communication"
    NEGOTIATION = "negotiation"
    WEBSITE_FUNCTIONALITY = "website_functionality"
    COMPANY_INFORMATION = "company_information"
    PROPERTY_LISTINGS_INQUIRY = "property_listings_inquiry"
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
        self.llm_client = LLMClient()
        self._intent_descriptions = {
            Intent.GREETING: (
                "Initial greetings, hellos, or conversation starters"
            ),
            Intent.PROPERTY_INQUIRY: (
                "Questions about specific property features, amenities, specifications, or general details excluding price"
            ),
            Intent.AVAILABILITY_AND_BOOKING_REQUEST: (
                "Questions about property availability, viewing times, or scheduling viewings"
            ),
            Intent.PRICE_INQUIRY: (
                "Direct questions about property prices, asking prices, price history, price comparisons, or any cost-related queries"
            ),
            Intent.BUYER_SELLER_COMMUNICATION: (
                "Messages that need to be relayed between buyers and sellers, excluding specific price inquiries or negotiations"
            ),
            Intent.NEGOTIATION: (
                "Messages specifically about making, accepting, or discussing offers and counteroffers"
            ),
            Intent.GENERAL_QUESTION: (
                "General questions about the property market, buying process, or areas that aren't about a specific property"
            ),
            Intent.WEBSITE_FUNCTIONALITY: (
                "Questions about how to use the MaiSON website, its features, or steps in the buyer/seller journey"
            ),
            Intent.COMPANY_INFORMATION: (
                "Questions about MaiSON company history, mission, team, or other company-specific information"
            ),
            Intent.PROPERTY_LISTINGS_INQUIRY: (
                "Questions about available properties on MaiSON, property recommendations, or searching for properties with specific criteria"
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
            "# Property Inquiry Examples:\n"
            "- \"What are the features of this house?\" -> \"property_inquiry\"\n"
            "- \"How many bedrooms does it have?\" -> \"property_inquiry\"\n"
            "- \"What's the square footage?\" -> \"property_inquiry\"\n"
            "- \"Does it have a garden?\" -> \"property_inquiry\"\n\n"
            "# Price Inquiry Examples:\n"
            "- \"How much does it cost?\" -> \"price_inquiry\"\n"
            "- \"What is the current asking price?\" -> \"price_inquiry\"\n"
            "- \"Has the price changed recently?\" -> \"price_inquiry\"\n"
            "- \"How does the price compare to similar properties?\" -> \"price_inquiry\"\n\n"
            "# Availability Examples:\n"
            "- \"When can I view the apartment?\" -> \"availability_and_booking_request\"\n"
            "- \"Is it still available?\" -> \"availability_and_booking_request\"\n"
            "- \"Can I schedule a viewing?\" -> \"availability_and_booking_request\"\n\n"
            "# Negotiation Examples:\n"
            "- \"I'd like to make an offer of $500,000\" -> \"negotiation\"\n"
            "- \"Would the seller accept $450,000?\" -> \"negotiation\"\n"
            "- \"I want to submit a bid\" -> \"negotiation\"\n\n"
            "# Buyer-Seller Communication Examples:\n"
            "- \"Can you ask the seller about the renovation history?\" -> \"buyer_seller_communication\"\n"
            "- \"Please let the seller know I'm very interested\" -> \"buyer_seller_communication\"\n"
            "- \"Could you relay a question to the owner?\" -> \"buyer_seller_communication\"\n\n"
            "# General Question Examples:\n"
            "- \"What are good areas to live in London?\" -> \"general_question\"\n"
            "- \"How long does the buying process take?\" -> \"general_question\"\n"
            "- \"What documents do I need to buy a house?\" -> \"general_question\"\n\n"
            "# Website Functionality Examples:\n"
            "- \"How do I create a listing on MaiSON?\" -> \"website_functionality\"\n"
            "- \"What steps are involved in the buying process on your platform?\" -> \"website_functionality\"\n"
            "- \"How can I contact a seller through the website?\" -> \"website_functionality\"\n"
            "- \"Can you explain how the offer submission works?\" -> \"website_functionality\"\n\n"
            "# Company Information Examples:\n"
            "- \"When was MaiSON founded?\" -> \"company_information\"\n"
            "- \"Who is on your leadership team?\" -> \"company_information\"\n"
            "- \"What is MaiSON's mission?\" -> \"company_information\"\n"
            "- \"Tell me about your company's history\" -> \"company_information\"\n\n"
            "# Property Listings Inquiry Examples:\n"
            "- \"What properties do you have available in London?\" -> \"property_listings_inquiry\"\n"
            "- \"Show me 3-bedroom houses under £400,000\" -> \"property_listings_inquiry\"\n"
            "- \"Do you have any properties with a garden in Manchester?\" -> \"property_listings_inquiry\"\n"
            "- \"What are your newest listings?\" -> \"property_listings_inquiry\"\n"
            "- \"Can you recommend properties similar to my saved ones?\" -> \"property_listings_inquiry\"\n\n"
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

    async def classify_general(self, message: str) -> Intent:
        """Simplified classification for general chat - only detects greetings."""
        greeting_patterns = [
            r"^hi\b",
            r"^hello\b",
            r"^hey\b",
            r"^good (morning|afternoon|evening)\b",
            r"^greetings\b",
            r"^howdy\b",
            r"^hola\b",
            r"^welcome\b"
        ]
        
        message_lower = message.lower().strip()
        if any(re.search(pattern, message_lower) for pattern in greeting_patterns):
            return Intent.GREETING
        return Intent.GENERAL_QUESTION 