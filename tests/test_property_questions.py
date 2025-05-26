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

    # Mock LLM responses for different calls
    async def mock_llm_response(*args, **kwargs):
        messages = kwargs.get('messages', [])
        if any("determine if a buyer's message requires input from the seller" in msg.get('content', '') for msg in messages):
            return "yes"
        elif any("reformat buyer questions" in msg.get('content', '') for msg in messages):
            return "Does the property have an underground bunker?"
        return "need_seller_input"  # Default response

    comm_module.llm_client.generate_response = AsyncMock(side_effect=mock_llm_response)

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
async def test_question_confirmation_flow(db_session, mock_property_conversation):
    """Test the flow of asking a question, getting confirmation, and forwarding to seller."""
    # Create communication module
    comm_module = SellerBuyerCommunicationModule()

    # Track which messages have been processed to handle state
    processed_messages = []

    # Mock LLM responses for different calls
    async def mock_llm_response(*args, **kwargs):
        messages = kwargs.get('messages', [])
        message_content = messages[1]['content'] if len(messages) > 1 else ""
        
        # Store the message for state tracking
        processed_messages.append(message_content)

        # Initial question should trigger needs_seller_input check
        if "Do you know if the property is near a bakery?" in message_content:
            if any("determine if a buyer's message requires input from the seller" in msg.get('content', '') for msg in messages):
                return "no"  # First time, say no to trigger confirmation flow
            return "need_seller_input"
        
        # Confirmation message should be recognized
        elif "Yes please" in message_content:
            if any("determine if a buyer's message is confirming" in msg.get('content', '') for msg in messages):
                return "yes"
            elif any("reformat buyer questions" in msg.get('content', '') for msg in messages):
                return "Are there any bakeries near the property?"
        
        return "need_seller_input"

    comm_module.llm_client.generate_response = AsyncMock(side_effect=mock_llm_response)

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

    # Step 1: Buyer asks initial question
    initial_question = "Do you know if the property is near a bakery?"
    response = await comm_module.handle_message(message=initial_question, context=context)

    # Verify that Mia asks for confirmation
    assert response == "Would you like me to pass this question on to the seller?"
    assert mock_property_conversation.id in comm_module.pending_questions
    assert comm_module.pending_questions[mock_property_conversation.id] == initial_question

    # Step 2: Buyer confirms
    confirmation_response = await comm_module.handle_message(message="Yes please", context=context)

    # Verify that the question was forwarded
    assert confirmation_response == "I will forward your question to the seller and let you know once I have a response."
    assert mock_property_conversation.id not in comm_module.pending_questions

@pytest.mark.asyncio
async def test_property_listing_info_handling(db_session, mock_property_conversation):
    """Test handling of questions about information available in property listing."""
    comm_module = SellerBuyerCommunicationModule()

    # Track which messages have been processed to handle state
    processed_messages = []

    # Mock LLM responses for different calls
    async def mock_llm_response(*args, **kwargs):
        messages = kwargs.get('messages', [])
        message_content = messages[1]['content'] if len(messages) > 1 else ""
        
        # Store the message for state tracking
        processed_messages.append(message_content)

        # Basic property info question
        if "How many bedrooms and bathrooms" in message_content:
            if any("determine if a buyer's message requires input from the seller" in msg.get('content', '') for msg in messages):
                return "no"
            elif any("Answer the buyer's question using the available property listing information" in msg.get('content', '') for msg in messages):
                return "The property has 3 bedrooms and 2 bathrooms."
        
        # Renovation question should need seller input
        elif "renovation" in message_content:
            if any("determine if a buyer's message requires input from the seller" in msg.get('content', '') for msg in messages):
                return "yes"
            elif any("reformat buyer questions" in msg.get('content', '') for msg in messages):
                return "Has there been any recent renovation work?"
        
        # EPC rating question with no context
        elif "EPC rating" in message_content:
            if any("determine if a buyer's message requires input from the seller" in msg.get('content', '') for msg in messages):
                return "no"
            return "need_seller_input"

        return "need_seller_input"

    comm_module.llm_client.generate_response = AsyncMock(side_effect=mock_llm_response)

    # Create context with property information
    context = {
        "conversation_id": mock_property_conversation.id,
        "user_id": "test_buyer",
        "role": "buyer",
        "counterpart_id": "test_seller",
        "property_id": "test_property",
        "db": db_session,
        "message_id": 1,
        "property_context": {
            "bedrooms": 3,
            "bathrooms": 2,
            "price": 500000,
            "size": 1500,
            "location": "London",
            "epc_rating": "B",
            "has_garden": True,
            "parking_spaces": 2
        }
    }

    # Test 1: Question about basic property info
    response = await comm_module.handle_message("How many bedrooms and bathrooms does the property have?", context)
    assert "3 bedrooms" in response.lower()
    assert "2 bathrooms" in response.lower()

    # Test 2: Question requiring seller input
    response = await comm_module.handle_message("Has there been any recent renovation work?", context)
    assert response == "I will forward your question to the seller and let you know once I have a response."

    # Test 3: Question about property info but data not available
    context_without_property_info = context.copy()
    context_without_property_info["property_context"] = {}
    
    response = await comm_module.handle_message("What's the EPC rating?", context_without_property_info)
    assert response == "Would you like me to pass this question on to the seller?" 