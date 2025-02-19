# app/database/__init__.py
from .db_connection import engine, SessionLocal, Base, get_db
from .models import (
    GeneralConversation as GeneralConversationModel,
    PropertyConversation as PropertyConversationModel,
    GeneralMessage as GeneralMessageModel,
    PropertyMessage as PropertyMessageModel,
    ExternalReference as ExternalReferenceModel
)
from .schemas import (
    GeneralConversationBase, GeneralConversationCreate, GeneralConversation,
    PropertyConversationBase, PropertyConversationCreate, PropertyConversation,
    GeneralMessageBase, GeneralMessageCreate, GeneralMessage,
    PropertyMessageBase, PropertyMessageCreate, PropertyMessage,
    ExternalReferenceBase, ExternalReferenceCreate, ExternalReference,
    GeneralChatResponse, PropertyChatResponse
)

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "GeneralConversationModel",
    "PropertyConversationModel",
    "GeneralMessageModel",
    "PropertyMessageModel",
    "ExternalReferenceModel",
    "GeneralConversationBase",
    "GeneralConversationCreate",
    "GeneralConversation",
    "PropertyConversationBase",
    "PropertyConversationCreate",
    "PropertyConversation",
    "GeneralMessageBase",
    "GeneralMessageCreate",
    "GeneralMessage",
    "PropertyMessageBase",
    "PropertyMessageCreate",
    "PropertyMessage",
    "ExternalReferenceBase",
    "ExternalReferenceCreate",
    "ExternalReference",
    "GeneralChatResponse",
    "PropertyChatResponse"
] 