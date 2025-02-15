# Root level __init__.py
# This makes the root directory a Python package

from app.modules.message_router import MessageRouter
from app.modules.intent_classification import IntentClassifier, Intent
from app.modules.property_context import PropertyContextModule
from app.modules.advisory import AdvisoryModule
from app.modules.communication import CommunicationModule
from app.modules.llm import LLMClient, LLMProvider, SystemPrompts
from app.database import Base, engine, get_db
from app.config import settings

__version__ = "0.1.0"

__all__ = [
    "settings",
    "MessageRouter",
    "IntentClassifier",
    "Intent",
    "PropertyContextModule",
    "AdvisoryModule",
    "CommunicationModule",
    "LLMClient",
    "LLMProvider",
    "SystemPrompts",
    "Base",
    "engine",
    "get_db"
]
