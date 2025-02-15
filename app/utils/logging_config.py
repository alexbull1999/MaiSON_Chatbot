import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_level=logging.INFO):
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configure file handler for general logs
    file_handler = RotatingFileHandler(
        log_dir / "chatbot.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_format)

    # Configure file handler for database logs
    db_handler = RotatingFileHandler(
        log_dir / "database.log",
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    db_handler.setFormatter(log_format)

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Get SQL Alchemy logger
    sql_logger = logging.getLogger('sqlalchemy.engine')
    sql_logger.setLevel(logging.INFO)  # Set to logging.DEBUG for query logging
    sql_logger.addHandler(db_handler)

    # Add handlers to root logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log startup message
    logger.info("Starting maiSON Chatbot application")
    logger.info("Database logging configured")

    return logger 