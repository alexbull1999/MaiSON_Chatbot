from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('sqlalchemy.engine')

def get_connection_url():
    """Constructs a secure connection URL for Azure PostgreSQL."""
    # Log connection attempt (with masked password)
    logger.debug(
        f"Connecting to PostgreSQL database:\n"
        f"Host: {settings.azure_postgres_host}\n"
        f"Database: {settings.azure_postgres_db}\n"
        f"User: {settings.azure_postgres_user}\n"
        f"Port: {settings.azure_postgres_port}"
    )

    # Build PostgreSQL connection URL
    return (
        f"postgresql://{settings.azure_postgres_user}:"
        f"{settings.azure_postgres_password}@"
        f"{settings.azure_postgres_host}:"
        f"{settings.azure_postgres_port}/"
        f"{settings.azure_postgres_db}"
    )

# Create SQLAlchemy engine
engine = create_engine(
    get_connection_url(),
    echo=True,  # Enable SQL query logging for debugging
    pool_pre_ping=True,  # Helps in detecting stale connections
    pool_size=10,  # Adjust based on workload
    max_overflow=20  # Allow extra connections if needed
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for ORM models
Base = declarative_base()

# Helper functions for JSON handling
def json_to_str(value):
    """Convert Python dict to JSON string for PostgreSQL storage."""
    return json.dumps(value) if value is not None else None

def str_to_json(value):
    """Convert JSON string from PostgreSQL to Python dict."""
    return json.loads(value) if value and isinstance(value, str) else value

def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
