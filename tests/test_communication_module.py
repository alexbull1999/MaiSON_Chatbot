import pytest
from app.modules.communication.communication_module import (
    CommunicationModule,
    MessageType,
)
from unittest.mock import AsyncMock, patch


def test_communication_module_initialization():
    comm = CommunicationModule()
    assert isinstance(comm.templates, dict)
    assert MessageType.GREETING in comm.templates
    assert MessageType.ERROR in comm.templates


def test_format_message_greeting():
    comm = CommunicationModule()
    message = comm.format_message(MessageType.GREETING)
    assert isinstance(message, str)
    assert len(message) > 0
    assert "Welcome to MaiSON" in message or "Hello" in message


def test_format_message_error():
    comm = CommunicationModule()
    message = comm.format_message(MessageType.ERROR)
    assert isinstance(message, str)
    assert len(message) > 0
    assert "apologize" in message or "wrong" in message


def test_format_message_with_params():
    comm = CommunicationModule()
    # Add a test template with parameters
    comm.templates[MessageType.RESPONSE] = [
        "The property {property_name} is located in {location}."
    ]
    message = comm.format_message(
        MessageType.RESPONSE, property_name="Test Property", location="Test Location"
    )
    assert "Test Property" in message
    assert "Test Location" in message


@pytest.mark.asyncio
async def test_generate_response():
    with patch(
        "app.modules.communication.communication_module.LLMClient"
    ) as MockLLMClient:
        # Create mock LLM client
        mock_llm = AsyncMock()
        mock_llm.generate_response.return_value = (
            "I can help you with information about this property."
        )
        MockLLMClient.return_value = mock_llm

        comm = CommunicationModule()
        context = {"property_id": "123"}
        response = await comm.generate_response("property_inquiry", context)

        # Basic validations
        assert isinstance(response, str)
        assert len(response) > 0

        # Check for property-related content - using a broader set of keywords
        assert any(
            keyword in response.lower()
            for keyword in [
                "property",
                "details",
                "information",
                "questions",
                "interested",
                "help",
                "assist",
            ]
        ), f"Response should contain property-related keywords. Got: {response}"

        # Check for professional tone
        assert response[0].isupper(), "Response should start with a capital letter"
        assert any(
            char in ".!?" for char in response[-1:]
        ), "Response should end with proper punctuation"

        # Verify LLM was called correctly
        mock_llm.generate_response.assert_called_once()
