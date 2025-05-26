import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database.models import PropertyQuestion, PropertyConversation, PropertyMessage, ExternalReference
from app.api.controllers import Role
from app.modules.communication.seller_buyer_communication import SellerBuyerCommunicationModule

# Create a test client
client = TestClient(app)

@pytest.fixture
def db_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    return session

@pytest.fixture
def mock_property_conversation():
    """Create a mock property conversation."""
    conversation = MagicMock(spec=PropertyConversation)
    conversation.id = 1
    conversation.session_id = "test_session"
    conversation.user_id = "test_buyer"
    conversation.property_id = "test_property"
    conversation.role = Role.BUYER
    conversation.counterpart_id = "test_seller"
    conversation.conversation_status = "active"
    conversation.messages = []
    conversation.property_context = {}
    return conversation

@pytest.fixture
def mock_property_question():
    """Create a mock property question."""
    question = MagicMock(spec=PropertyQuestion)
    question.id = 1
    question.property_id = "test_property"
    question.buyer_id = "test_buyer"
    question.seller_id = "test_seller"
    question.conversation_id = 1
    question.question_message_id = 1
    question.question_text = "How far is the nearest tube station?"
    question.status = "pending"
    question.created_at = datetime.utcnow()
    question.answered_at = None
    question.answer_text = None
    return question

@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for testing."""
    from app.database import get_db
    from app.main import app
    
    async def _get_db_override():
        yield db_session
    
    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_buyer_asking_question(db_session, mock_property_conversation):
    """Test a buyer asking a question that needs seller input."""
    # Create communication module
    comm_module = SellerBuyerCommunicationModule()

    # Mock database queries
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,  # No existing question with this message_id
        mock_property_conversation  # For conversation lookup
    ]

    # Create context
    context = {
        "conversation_id": mock_property_conversation.id,
        "user_id": "test_buyer",
        "role": "buyer",
        "counterpart_id": "test_seller",
        "property_id": "test_property",
        "db": db_session,
        "message_id": 1
    }

    # Test asking a question
    message = "Can you ask the seller how far the nearest tube station is?"
    response = await comm_module.handle_message(message=message, context=context)

    # Verify response
    assert response == "I will forward your question to the seller and let you know once I have a response."

    # Verify both PropertyQuestion and ExternalReference were created
    assert db_session.add.call_count == 2

    # Verify the correct objects were created
    calls = db_session.add.call_args_list
    assert len(calls) == 2
    assert isinstance(calls[0][0][0], PropertyQuestion)
    assert isinstance(calls[1][0][0], ExternalReference)

@pytest.mark.asyncio
async def test_seller_answering_question(db_session, mock_property_question, mock_property_conversation):
    """Test a seller answering a buyer's question."""
    # Create communication module
    comm_module = SellerBuyerCommunicationModule()
    
    # Mock database queries
    db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_property_question,  # First query for the question
        mock_property_conversation  # Second query for the conversation
    ]
    
    # Test answering the question
    answer = "The nearest tube station is Baker Street, about 5 minutes walk away."
    result = await comm_module.handle_seller_response(
        question_id=1,
        answer=answer,
        db=db_session
    )
    
    # Verify result
    assert result is True
    
    # Verify question was updated
    assert mock_property_question.status == "answered"
    assert mock_property_question.answer_text == answer
    assert mock_property_question.answered_at is not None
    
    # Verify answer message was created
    db_session.add.assert_called_once()
    added_message = db_session.add.call_args[0][0]
    assert isinstance(added_message, PropertyMessage)
    assert added_message.conversation_id == mock_property_conversation.id
    assert added_message.role == "assistant"
    assert "The seller has responded to your question" in added_message.content
    assert answer in added_message.content
    assert added_message.intent == "buyer_seller_communication"
    assert added_message.message_metadata["is_seller_response"] is True
    assert added_message.message_metadata["original_question_id"] == mock_property_question.id

@pytest.mark.asyncio
async def test_get_seller_questions_endpoint(db_session, mock_property_question, override_get_db):
    """Test the endpoint for getting a seller's questions."""
    # Mock database query to return a list of questions
    mock_questions = [mock_property_question]
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.all.return_value = mock_questions
    db_session.query.return_value = mock_query
    
    # Make request to get seller's questions
    response = client.get("/api/v1/seller/questions/test_seller_1")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert isinstance(data["questions"], list)
    assert len(data["questions"]) == 1
    
    # Verify question structure
    question = data["questions"][0]
    assert question["id"] == mock_property_question.id
    assert question["property_id"] == mock_property_question.property_id
    assert question["buyer_id"] == mock_property_question.buyer_id
    assert question["question_text"] == mock_property_question.question_text
    assert question["status"] == mock_property_question.status
    assert "created_at" in question
    assert "answered_at" in question
    assert "answer_text" in question

@pytest.mark.asyncio
async def test_answer_question_endpoint(db_session, mock_property_question, mock_property_conversation, override_get_db):
    """Test the endpoint for answering a question."""
    # Set up the mock question and conversation
    mock_property_question.status = "pending"
    mock_property_question.answer_text = None
    mock_property_question.answered_at = None
    
    # Mock database queries to return the question and conversation
    db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_property_question,  # First query for the question
        mock_property_conversation  # Second query for the conversation
    ]
    
    # Prepare answer data
    answer_data = {
        "question_id": 1,
        "answer": "The nearest tube station is Baker Street, about 5 minutes walk away."
    }
    
    # Make request to answer the question
    response = client.post(
        "/api/v1/seller/questions/1/answer",
        json=answer_data
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Answer recorded and sent to buyer"
    
    # Verify the question was updated
    assert mock_property_question.status == "answered"
    assert mock_property_question.answer_text == answer_data["answer"]
    assert mock_property_question.answered_at is not None
    
    # Verify a message was created
    db_session.add.assert_called_once()
    added_message = db_session.add.call_args[0][0]
    assert isinstance(added_message, PropertyMessage)
    assert added_message.conversation_id == mock_property_conversation.id
    assert "The seller has responded to your question" in added_message.content
    assert answer_data["answer"] in added_message.content

@pytest.mark.asyncio
async def test_question_not_found(db_session):
    """Test handling of non-existent questions."""
    # Create communication module
    comm_module = SellerBuyerCommunicationModule()
    
    # Mock database query to return None (question not found)
    db_session.query.return_value.filter.return_value.first.return_value = None
    
    # Test answering a non-existent question
    result = await comm_module.handle_seller_response(
        question_id=999,
        answer="This is an answer",
        db=db_session
    )
    
    # Verify result
    assert result is False
    
    # Verify no database changes were made
    db_session.add.assert_not_called()
    db_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_invalid_question_status_transition(db_session, mock_property_question):
    """Test attempting to answer an already answered question."""
    # Create communication module
    comm_module = SellerBuyerCommunicationModule()
    
    # Set question as already answered
    mock_property_question.status = "answered"
    mock_property_question.answer_text = "Previous answer"
    mock_property_question.answered_at = datetime.utcnow()
    
    # Mock database queries to return the question but no conversation
    db_session.query.return_value.filter.return_value.first.side_effect = [
        mock_property_question,  # First query for the question
        None  # Second query for the conversation (not found)
    ]
    
    # Test answering an already answered question
    result = await comm_module.handle_seller_response(
        question_id=1,
        answer="New answer",
        db=db_session
    )
    
    # Verify result
    assert result is False
    
    # Verify no database changes were made
    db_session.add.assert_not_called()
    db_session.commit.assert_not_called()
    assert mock_property_question.answer_text == "Previous answer"

@pytest.mark.asyncio
async def test_question_reformatting(db_session, mock_property_conversation):
    """Test that buyer questions are properly reformatted before being saved."""
    # Create communication module
    comm_module = SellerBuyerCommunicationModule()

    # Mock LLM response for question reformatting
    comm_module.llm_client.generate_response = AsyncMock(
        return_value="Does the property have an underground bunker?"
    )

    # Mock database queries
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,  # No existing question with this message_id
        mock_property_conversation  # For conversation lookup
    ]

    # Create context
    context = {
        "conversation_id": mock_property_conversation.id,
        "user_id": "test_buyer",
        "role": "buyer",
        "counterpart_id": "test_seller",
        "property_id": "test_property",
        "db": db_session,
        "message_id": 1
    }

    # Test asking a question that needs reformatting
    message = "yes please can you ask the seller if the property has an underground bunker"
    response = await comm_module.handle_message(message=message, context=context)

    # Verify response
    assert response == "I will forward your question to the seller and let you know once I have a response."

    # Verify the question was reformatted before being saved
    calls = db_session.add.call_args_list
    assert len(calls) == 2  # One for question, one for external reference
    saved_question = calls[0][0][0]
    assert isinstance(saved_question, PropertyQuestion)
    assert saved_question.question_text == "Does the property have an underground bunker?"

    # Verify both PropertyQuestion and ExternalReference were created
    assert db_session.add.call_count == 2

    # Verify the correct objects were created
    assert isinstance(calls[0][0][0], PropertyQuestion)
    assert isinstance(calls[1][0][0], ExternalReference)

@pytest.mark.asyncio
async def test_question_confirmation_handling(db_session, mock_property_conversation):
    """Test that confirmation responses are properly handled."""
    # First test case: Confirmation with question context
    comm_module = SellerBuyerCommunicationModule()
    comm_module.llm_client.generate_response = AsyncMock(
        return_value="Are there any bakeries near the property?"
    )

    # Mock database queries
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,  # No existing question with this message_id
        mock_property_conversation  # For conversation lookup
    ]

    # Create context with conversation history
    context = {
        "conversation_id": mock_property_conversation.id,
        "user_id": "test_buyer",
        "role": "buyer",
        "counterpart_id": "test_seller",
        "property_id": "test_property",
        "db": db_session,
        "message_id": 1,
        "conversation_history": [
            {"role": "user", "content": "Are there any bakeries near the property?"},
            {"role": "assistant", "content": "Would you like me to ask the seller about bakeries in the area?"},
        ]
    }

    # Test simple confirmation response
    message = "Yes please"
    response = await comm_module.handle_message(message=message, context=context)

    # Verify response
    assert response == "I will forward your question to the seller and let you know once I have a response."

    # Verify the question was created with the original question text
    calls = db_session.add.call_args_list
    assert len(calls) == 2  # One for question, one for external reference
    saved_question = calls[0][0][0]
    assert isinstance(saved_question, PropertyQuestion)
    assert "bakeries" in saved_question.question_text.lower()

    # Second test case: Confirmation without question context
    # Create fresh module instance and mock
    comm_module = SellerBuyerCommunicationModule()
    comm_module.llm_client.generate_response = AsyncMock(
        return_value="NO_QUESTION_FOUND"
    )

    # Reset mock call history
    db_session.reset_mock()
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,  # No existing question with this message_id
        mock_property_conversation  # For conversation lookup
    ]

    # Update context with non-question conversation
    context["conversation_history"] = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "I'm just browsing"},
        {"role": "assistant", "content": "Let me know if you have any questions!"}
    ]
    
    message = "Yes please"
    response = await comm_module.handle_message(message=message, context=context)
    
    # Verify it's treated as a normal message, not a question confirmation
    assert response != "I will forward your question to the seller and let you know once I have a response."
    
    # Check for various forms of clarification responses
    clarification_phrases = [
        "i'm not sure what you're saying yes to",
        "could you please clarify",
        "could you please repeat your question",
        "need the original question",
        "what question would you like me to forward"
    ]
    assert any(phrase in response.lower() for phrase in clarification_phrases), f"Response '{response}' should ask for clarification"

@pytest.mark.asyncio
async def test_llm_based_question_detection(db_session, mock_property_conversation):
    """Test that LLM-based question detection works for various scenarios."""
    # Create communication module
    comm_module = SellerBuyerCommunicationModule()

    # Create a mock for LLM responses
    mock_llm_responses = {
        # Direct question scenarios
        "can you ask the seller about parking": "true",
        "is there parking available": "true",
        "i'd like to know about the heating system": "true",
        
        # Confirmation scenarios
        "sure thing": "true",
        "that would be great": "true",
        "yes please do": "true",
        
        # Non-question scenarios
        "hello": "false",
        "thank you": "false",
        "i understand": "false"
    }

    async def mock_generate_response(*args, **kwargs):
        # Extract the message from the user content
        message = [msg for msg in kwargs.get('messages', []) if msg['role'] == 'user'][0]['content']
        # Find the matching response based on the conversation context
        for key, value in mock_llm_responses.items():
            if key in message.lower():
                return value
        return "false"

    # Set up the mock LLM
    comm_module.llm_client.generate_response = AsyncMock(side_effect=mock_generate_response)

    # Test various message types
    for message, expected_needs_input in [
        # Direct questions
        ("Can you ask the seller about parking", True),
        ("Is there parking available", True),
        ("I'd like to know about the heating system", True),
        
        # Confirmations with conversation history
        ("Sure thing", True),
        ("That would be great", True),
        ("Yes please do", True),
        
        # Non-questions
        ("Hello", False),
        ("Thank you", False),
        ("I understand", False),
    ]:
        # Create context with appropriate history for confirmation cases
        context = {
            "conversation_id": mock_property_conversation.id,
            "user_id": "test_buyer",
            "role": "buyer",
            "counterpart_id": "test_seller",
            "property_id": "test_property",
            "db": db_session,
            "message_id": 1,
            "conversation_history": [
                {"role": "user", "content": "Is there a garage?"},
                {"role": "assistant", "content": "Would you like me to ask the seller about the garage?"},
            ] if "Sure thing" in message or "That would be great" in message or "Yes please do" in message
            else []
        }
        
        # Test the message
        needs_input = await comm_module._needs_seller_input(message)
        assert needs_input == expected_needs_input, f"Failed for message: {message}"

        if expected_needs_input:
            # Test full message handling
            response = await comm_module.handle_message(message=message, context=context)
            assert response == "I will forward your question to the seller and let you know once I have a response."

    # Test LLM failure fallback
    comm_module.llm_client.generate_response = AsyncMock(side_effect=Exception("LLM Error"))
    needs_input = await comm_module._needs_seller_input("yes please ask the seller")
    assert needs_input == True  # Should fall back to pattern matching 