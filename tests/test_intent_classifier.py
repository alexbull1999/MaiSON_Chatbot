import pytest
from unittest.mock import AsyncMock, patch

from app.modules.intent_classification import IntentClassifier, Intent
from app.modules.llm import LLMClient

@pytest.fixture
def intent_classifier():
    return IntentClassifier()

@pytest.fixture
def mock_llm_client():
    with patch('app.modules.intent_classification.intent_classifier.LLMClient') as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.mark.asyncio
async def test_classify_property_inquiry(intent_classifier, mock_llm_client):
    """Test classification of property inquiry messages."""
    mock_llm_client.generate_response.return_value = "property_inquiry"
    message = "What are the features of this house?"
    result = await intent_classifier.classify(message)
    assert result == Intent.PROPERTY_INQUIRY

@pytest.mark.asyncio
async def test_classify_availability_request(intent_classifier, mock_llm_client):
    """Test classification of availability request messages."""
    mock_llm_client.generate_response.return_value = "availability_and_booking_request"
    message = "When can I view this property?"
    result = await intent_classifier.classify(message)
    assert result == Intent.AVAILABILITY_AND_BOOKING_REQUEST

@pytest.mark.asyncio
async def test_classify_price_inquiry(intent_classifier, mock_llm_client):
    """Test classification of price inquiry messages."""
    mock_llm_client.generate_response.return_value = "price_inquiry"
    message = "How much does this property cost?"
    result = await intent_classifier.classify(message)
    assert result == Intent.PRICE_INQUIRY

@pytest.mark.asyncio
async def test_classify_unknown_intent(intent_classifier, mock_llm_client):
    """Test classification of messages with unknown intent."""
    mock_llm_client.generate_response.return_value = "unknown"
    message = "Lorem ipsum dolor sit amet"
    result = await intent_classifier.classify(message)
    assert result == Intent.UNKNOWN

@pytest.mark.asyncio
async def test_classify_error_handling(intent_classifier, mock_llm_client):
    """Test error handling during classification."""
    mock_llm_client.generate_response.side_effect = Exception("Test error")
    message = "What are the features of this house?"
    result = await intent_classifier.classify(message)
    assert result == Intent.UNKNOWN 