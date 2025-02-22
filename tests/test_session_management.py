import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.modules.session_management import SessionManager
from app.database.models import GeneralConversation, PropertyConversation


@pytest.fixture
def session_manager():
    return SessionManager()


@pytest.fixture
def db_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def mock_general_conversation():
    """Create a mock general conversation."""
    conversation = MagicMock(spec=GeneralConversation)
    conversation.is_logged_in = False
    conversation.last_message_at = datetime.utcnow()
    return conversation


@pytest.fixture
def mock_property_conversation():
    """Create a mock property conversation."""
    conversation = MagicMock(spec=PropertyConversation)
    conversation.conversation_status = "active"
    conversation.last_message_at = datetime.utcnow()
    return conversation


def test_session_manager_initialization():
    """Test that SessionManager initializes with correct expiry times."""
    manager = SessionManager()
    assert manager.anonymous_session_expiry == timedelta(hours=24)
    assert manager.authenticated_session_expiry == timedelta(days=30)


@pytest.mark.asyncio
async def test_cleanup_expired_anonymous_sessions(session_manager, db_session):
    """Test cleanup of expired anonymous sessions."""
    # Create mock expired anonymous conversations
    expired_conv = MagicMock(spec=GeneralConversation)
    expired_conv.is_logged_in = False
    expired_conv.last_message_at = datetime.utcnow() - timedelta(hours=25)

    # Set up mock query results
    mock_query = MagicMock()
    # Return expired anonymous conversation for anonymous query
    mock_query.filter.return_value.all.side_effect = [
        [expired_conv],
        [],
    ]  # First call returns expired anonymous, second call returns no authenticated
    db_session.query.return_value = mock_query

    # Run cleanup
    cleaned_count = await session_manager.cleanup_expired_sessions(db_session)

    # Verify results
    assert cleaned_count == 1
    db_session.delete.assert_called_once_with(expired_conv)
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_expired_authenticated_sessions(session_manager, db_session):
    """Test cleanup of expired authenticated sessions."""
    # Create mock expired authenticated conversations
    expired_conv = MagicMock(spec=GeneralConversation)
    expired_conv.is_logged_in = True
    expired_conv.last_message_at = datetime.utcnow() - timedelta(days=31)

    # Set up mock query results
    mock_query = MagicMock()
    # Return expired authenticated conversation for authenticated query
    mock_query.filter.return_value.all.side_effect = [
        [],
        [expired_conv],
    ]  # First call returns no anonymous, second call returns expired authenticated
    db_session.query.return_value = mock_query

    # Run cleanup
    cleaned_count = await session_manager.cleanup_expired_sessions(db_session)

    # Verify results
    assert cleaned_count == 1
    db_session.delete.assert_called_once_with(expired_conv)
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_both_types_of_sessions(session_manager, db_session):
    """Test cleanup of both anonymous and authenticated expired sessions."""
    # Create mock expired conversations
    expired_anonymous = MagicMock(spec=GeneralConversation)
    expired_anonymous.is_logged_in = False
    expired_anonymous.last_message_at = datetime.utcnow() - timedelta(hours=25)

    expired_authenticated = MagicMock(spec=GeneralConversation)
    expired_authenticated.is_logged_in = True
    expired_authenticated.last_message_at = datetime.utcnow() - timedelta(days=31)

    # Set up mock query results
    mock_query = MagicMock()
    mock_query.filter.return_value.all.side_effect = [
        [expired_anonymous],
        [expired_authenticated],
    ]
    db_session.query.return_value = mock_query

    # Run cleanup
    cleaned_count = await session_manager.cleanup_expired_sessions(db_session)

    # Verify results
    assert cleaned_count == 2
    assert db_session.delete.call_count == 2
    db_session.delete.assert_any_call(expired_anonymous)
    db_session.delete.assert_any_call(expired_authenticated)
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_error_handling(session_manager, db_session):
    """Test error handling during cleanup."""
    # Make commit raise an exception
    db_session.commit.side_effect = Exception("Database error")

    # Create mock expired conversation
    expired_conv = MagicMock(spec=GeneralConversation)
    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [expired_conv]
    db_session.query.return_value = mock_query

    # Verify error handling
    with pytest.raises(Exception) as exc_info:
        await session_manager.cleanup_expired_sessions(db_session)

    assert "Failed to cleanup sessions" in str(exc_info.value)
    db_session.rollback.assert_called_once()


def test_is_session_valid_anonymous(session_manager, mock_general_conversation):
    """Test session validation for anonymous users."""
    # Test valid session
    mock_general_conversation.last_message_at = datetime.utcnow()
    assert session_manager.is_session_valid(mock_general_conversation) is True

    # Test expired session
    mock_general_conversation.last_message_at = datetime.utcnow() - timedelta(hours=25)
    assert session_manager.is_session_valid(mock_general_conversation) is False


def test_is_session_valid_authenticated(session_manager, mock_general_conversation):
    """Test session validation for authenticated users."""
    mock_general_conversation.is_logged_in = True

    # Test valid session
    mock_general_conversation.last_message_at = datetime.utcnow()
    assert session_manager.is_session_valid(mock_general_conversation) is True

    # Test expired session
    mock_general_conversation.last_message_at = datetime.utcnow() - timedelta(days=31)
    assert session_manager.is_session_valid(mock_general_conversation) is False


def test_is_session_valid_none(session_manager):
    """Test session validation with None conversation."""
    assert session_manager.is_session_valid(None) is False


def test_is_property_session_valid(session_manager, mock_property_conversation):
    """Test property session validation."""
    # Test active session
    mock_property_conversation.conversation_status = "active"
    assert session_manager.is_property_session_valid(mock_property_conversation) is True

    # Test closed session
    mock_property_conversation.conversation_status = "closed"
    assert (
        session_manager.is_property_session_valid(mock_property_conversation) is False
    )


def test_is_property_session_valid_none(session_manager):
    """Test property session validation with None conversation."""
    assert session_manager.is_property_session_valid(None) is False


@pytest.mark.asyncio
async def test_refresh_session(session_manager, mock_general_conversation):
    """Test session refresh functionality."""
    old_timestamp = mock_general_conversation.last_message_at
    await session_manager.refresh_session(mock_general_conversation)

    # Verify timestamp was updated
    assert mock_general_conversation.last_message_at > old_timestamp


@pytest.mark.asyncio
async def test_refresh_session_none(session_manager):
    """Test session refresh with None conversation."""
    # Should not raise an exception
    await session_manager.refresh_session(None)
