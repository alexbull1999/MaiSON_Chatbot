import pytest
from app.modules.communication.communication_module import CommunicationModule, MessageType

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
        MessageType.RESPONSE,
        property_name="Test Property",
        location="Test Location"
    )
    assert "Test Property" in message
    assert "Test Location" in message

@pytest.mark.asyncio
async def test_generate_response():
    comm = CommunicationModule()
    context = {"property_id": "123"}
    response = await comm.generate_response("property_inquiry", context)
    assert isinstance(response, str)
    assert len(response) > 0
    assert "property" in response.lower() 
    assert "details" in response.lower() or "information" in response.lower() or "questions" in response.lower()