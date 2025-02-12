# app/__init__.py
# This file makes 'app' a Python package. 

__version__ = "0.1.0"

from .config import settings
from .database import Base, engine, get_db
from .api.routes import router

# Create database tables
Base.metadata.create_all(bind=engine)

__all__ = ["settings", "Base", "engine", "get_db", "router"]