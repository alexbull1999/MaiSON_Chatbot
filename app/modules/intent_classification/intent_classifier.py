from enum import Enum

class Intent(Enum):
    PROPERTY_INQUIRY = "property_inquiry"
    AVAILABILITY_CHECK = "availability_check"
    PRICE_INQUIRY = "price_inquiry"
    BOOKING_REQUEST = "booking_request"
    GENERAL_QUESTION = "general_question"
    UNKNOWN = "unknown"

class IntentClassifier:
    def __init__(self):
        self.intents = {intent: [] for intent in Intent}

    def classify(self, message: str) -> Intent:
        """
        Classify the intent of a given message.
        This is a basic implementation that should be enhanced with proper NLP.
        """
        message = message.lower()
        
        # Basic keyword matching (to be replaced with proper ML/NLP)
        if any(word in message for word in ["property", "house", "apartment", "condo"]):
            return Intent.PROPERTY_INQUIRY
        elif any(word in message for word in ["available", "when", "dates", "schedule"]):
            return Intent.AVAILABILITY_CHECK
        elif any(word in message for word in ["price", "cost", "fee", "worth", "value"]):
            return Intent.PRICE_INQUIRY
        elif any(word in message for word in ["book", "reserve", "booking", "schedule"]):
            return Intent.BOOKING_REQUEST
        elif any(word in message for word in ["thank", "bye", "hello", "hi"]):
            return Intent.GENERAL_QUESTION
        
        return Intent.UNKNOWN 