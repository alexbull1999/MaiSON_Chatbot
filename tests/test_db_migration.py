import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import text
from app.database.models import GeneralConversation, PropertyConversation, ExternalReference
from app.database import SessionLocal


@pytest.fixture
def db_session(test_db):
    """Create a new database session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.mark.skipif(True, reason="Skipping database structure tests with in-memory SQLite")
def test_models_exist(db_session: Session):
    """Test that the models we're keeping still exist and can be queried."""
    # These should work
    db_session.query(GeneralConversation).first()
    db_session.query(PropertyConversation).first()
    db_session.query(ExternalReference).first()


@pytest.mark.skipif(True, reason="Skipping database structure tests with in-memory SQLite")
def test_properties_table_dropped():
    """Test that the properties table no longer exists."""
    session = SessionLocal()
    try:
        with pytest.raises(ProgrammingError):
            session.execute(text("SELECT * FROM properties"))
    finally:
        session.close()


@pytest.mark.skipif(True, reason="Skipping database structure tests with in-memory SQLite")
def test_availability_slots_table_dropped():
    """Test that the availability_slots table no longer exists."""
    session = SessionLocal()
    try:
        with pytest.raises(ProgrammingError):
            session.execute(text("SELECT * FROM availability_slots"))
    finally:
        session.close()


@pytest.mark.skipif(True, reason="Skipping database structure tests with in-memory SQLite")
def test_inquiries_table_dropped():
    """Test that the inquiries table no longer exists."""
    session = SessionLocal()
    try:
        with pytest.raises(ProgrammingError):
            session.execute(text("SELECT * FROM inquiries"))
    finally:
        session.close() 