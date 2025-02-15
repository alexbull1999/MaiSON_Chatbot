#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.database.db_connection import engine, Base, SessionLocal
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_connection():
    """Test database connection and basic operations."""
    try:
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            logger.info("Successfully connected to database!")
            
            try:
                # Test simple query
                result = connection.execute(text("SELECT version();"))
                version = result.scalar()
                logger.info(f"PostgreSQL Version: {version}")
            except SQLAlchemyError as e:
                logger.error(f"Error executing version query: {str(e)}")
                return False
            
            # Test database session
            logger.info("Testing database session...")
            db = SessionLocal()
            try:
                # Test session with a simple query
                result = db.execute(text("SELECT current_database();"))
                db_name = result.scalar()
                logger.info(f"Connected to database: {db_name}")
                
                # Test if we can create tables
                logger.info("Testing table creation...")
                try:
                    Base.metadata.create_all(bind=engine)
                    logger.info("Successfully created database tables!")
                except SQLAlchemyError as e:
                    logger.error(f"Error creating tables: {str(e)}")
                    return False
                
            except SQLAlchemyError as e:
                logger.error(f"Error in database session: {str(e)}")
                return False
            finally:
                db.close()
                
            return True
            
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        logger.error("Connection test failed!")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
