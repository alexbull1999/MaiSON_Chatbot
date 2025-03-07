import pytest
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.database import Base


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Set up a test database using SQLite in-memory database."""
    # Use SQLite in-memory database for tests
    test_engine = create_engine("sqlite:///:memory:")
    
    # Create all tables in the test database
    Base.metadata.create_all(bind=test_engine)
    
    # Create a test session factory
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Override the engine and session for tests
    from app.database import db_connection
    original_engine = db_connection.engine
    original_session = db_connection.SessionLocal
    
    # Replace with test versions
    db_connection.engine = test_engine
    db_connection.SessionLocal = TestSessionLocal
    
    yield
    
    # Restore original engine and session
    db_connection.engine = original_engine
    db_connection.SessionLocal = original_session
