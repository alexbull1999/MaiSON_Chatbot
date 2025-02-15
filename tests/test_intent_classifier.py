import pytest
from app.modules.intent_classification.intent_classifier import IntentClassifier, Intent

@pytest.fixture
def classifier():
    return IntentClassifier()

def test_intent_classifier_initialization(classifier):
    assert classifier.llm_client is not None
    assert classifier._intent_descriptions is not None
    assert len(classifier._intent_descriptions) == len(Intent)

@pytest.mark.asyncio
async def test_property_inquiry_intent(classifier):
    messages = [
        "What are the features of this property?",
        "Tell me about this house",
        "What amenities does this apartment have?",
        "Can you describe the property?"
    ]
    for message in messages:
        intent = await classifier.classify(message)
        assert intent == Intent.PROPERTY_INQUIRY

@pytest.mark.asyncio
async def test_availability_check_intent(classifier):
    messages = [
        "When is this property available for viewing?",
        "What are the available time slots?",
        "Can I see the property tomorrow?",
        "Is the property available next week?"
    ]
    for message in messages:
        intent = await classifier.classify(message)
        assert intent == Intent.AVAILABILITY_AND_BOOKING_REQUEST

@pytest.mark.asyncio
async def test_price_inquiry_intent(classifier):
    messages = [
        "How much does it cost?",
        "What's the price of this property?",
        "Is the price negotiable?",
        "Can you tell me about the monthly payments?"
    ]
    for message in messages:
        intent = await classifier.classify(message)
        assert intent == Intent.PRICE_INQUIRY

@pytest.mark.asyncio
async def test_booking_request_intent(classifier):
    messages = [
        "I would like to book a viewing",
        "Can I schedule a visit?",
        "Book the property for next week",
        "I want to reserve a viewing slot"
    ]
    for message in messages:
        intent = await classifier.classify(message)
        assert intent == Intent.AVAILABILITY_AND_BOOKING_REQUEST

@pytest.mark.asyncio
async def test_seller_message_intent(classifier):
    messages = [
        "Can you ask the seller about parking?",
        "I want to send a message to the seller",
        "Please tell the seller I'm interested",
        "Contact the seller for me"
    ]
    for message in messages:
        intent = await classifier.classify(message)
        assert intent == Intent.SELLER_MESSAGE

@pytest.mark.asyncio
async def test_general_question_intent(classifier):
    messages = [
        "What are good areas to live in London?",
        "What type of properties have good resale value?",
        "What cities in the UK are good to live in?",
    ]
    for message in messages:
        intent = await classifier.classify(message)
        assert intent == Intent.GENERAL_QUESTION

@pytest.mark.asyncio
async def test_unknown_intent(classifier):
    messages = [
        "xyz123",
        "random text",
        "!@#$%^",
        "Hello!",
    ]
    for message in messages:
        intent = await classifier.classify(message)
        assert intent == Intent.UNKNOWN


@pytest.mark.asyncio
async def test_error_handling(classifier):
    """Test that classifier handles errors gracefully."""
    # Simulate an error by passing None
    intent = await classifier.classify(None)
    assert intent == Intent.UNKNOWN 