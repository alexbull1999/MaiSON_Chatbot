from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.types import TypeDecorator
from . import Base
from .db_connection import json_to_str, str_to_json

# Custom JSON Type for SQL Server
class JSONString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json_to_str(value)

    def process_result_value(self, value, dialect):
        return str_to_json(value)

# Removed Property, AvailabilitySlot, and Inquiry models as they are not used

class GeneralConversation(Base):
    """Tracks general conversations between users and the chatbot."""
    __tablename__ = "general_conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # UUID string for Firebase user ID
    is_logged_in = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    context = Column(JSON)  # PostgreSQL native JSON type

    # Relationship to messages
    messages = relationship("GeneralMessage", back_populates="conversation", cascade="all, delete-orphan")

class GeneralMessage(Base):
    """Messages within general conversations."""
    __tablename__ = "general_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("general_conversations.id"), index=True)
    role = Column(String(50))  # 'user', 'assistant', or 'system'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    intent = Column(String(50), nullable=True)  # Store classified intent
    message_metadata = Column(JSON, nullable=True)  # PostgreSQL native JSON type

    # Relationship to conversation
    conversation = relationship("GeneralConversation", back_populates="messages")

class PropertyConversation(Base):
    """Tracks property-specific conversations between users and the chatbot."""
    __tablename__ = "property_conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # UUID string for Firebase user ID
    property_id = Column(String(255), nullable=False, index=True)  # Property being discussed
    role = Column(String(50), nullable=False, index=True)  # 'buyer' or 'seller'
    counterpart_id = Column(String(255), nullable=False, index=True)  # UUID string for the other party
    conversation_status = Column(String(50), nullable=False, default="active")  # e.g., 'active', 'closed', 'pending'
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    property_context = Column(JSON)  # Store property-specific context

    # Relationship to messages
    messages = relationship("PropertyMessage", back_populates="conversation", cascade="all, delete-orphan")

    # Add this to the PropertyConversation class relationships
    questions = relationship("PropertyQuestion", back_populates="conversation", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate role
        if "role" in kwargs and kwargs["role"] not in ["buyer", "seller"]:
            raise ValueError("Role must be either 'buyer' or 'seller'")

class PropertyMessage(Base):
    """Messages within property-specific conversations."""
    __tablename__ = "property_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("property_conversations.id"), index=True)
    role = Column(String(50))  # 'user', 'assistant', or 'system'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    intent = Column(String(50), nullable=True)  # Store classified intent
    message_metadata = Column(JSON, nullable=True)  # PostgreSQL native JSON type

    # Relationship to conversation
    conversation = relationship("PropertyConversation", back_populates="messages")

class ExternalReference(Base):
    """Tracks references to external service data."""
    __tablename__ = "external_references"

    id = Column(Integer, primary_key=True, index=True)
    general_conversation_id = Column(Integer, ForeignKey("general_conversations.id"), nullable=True, index=True)
    property_conversation_id = Column(Integer, ForeignKey("property_conversations.id"), nullable=True, index=True)
    service_name = Column(String(100))  # e.g., 'property_service', 'availability_service'
    external_id = Column(String(255))   # ID in the external service
    reference_metadata = Column(JSON, nullable=True)  # PostgreSQL native JSON type
    last_synced = Column(DateTime, default=datetime.utcnow)

    # Relationships to conversations
    general_conversation = relationship("GeneralConversation")
    property_conversation = relationship("PropertyConversation")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure only one conversation type is set
        if kwargs.get('general_conversation_id') and kwargs.get('property_conversation_id'):
            raise ValueError("Cannot reference both general and property conversations")

class PropertyQuestion(Base):
    """Tracks questions asked by buyers to sellers about specific properties."""
    __tablename__ = "property_questions"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(String(255), nullable=False, index=True)
    buyer_id = Column(String(255), nullable=False, index=True)  # UUID of buyer who asked
    seller_id = Column(String(255), nullable=False, index=True)  # UUID of seller to answer
    conversation_id = Column(Integer, ForeignKey('property_conversations.id'), nullable=False)
    question_message_id = Column(Integer, ForeignKey('property_messages.id'), nullable=False)
    question_text = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, answered, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime, nullable=True)
    answer_text = Column(Text, nullable=True)
    
    # Relationships
    conversation = relationship("PropertyConversation", back_populates="questions")
    question_message = relationship("PropertyMessage", foreign_keys=[question_message_id]) 