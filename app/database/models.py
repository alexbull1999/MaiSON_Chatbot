from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, JSON
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

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    type = Column(String(50))
    location = Column(String(255), index=True)
    price = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    availability_slots = relationship("AvailabilitySlot", back_populates="property")
    inquiries = relationship("Inquiry", back_populates="property")

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_available = Column(Boolean, default=True)

    # Relationships
    property = relationship("Property", back_populates="availability_slots")

class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    user_name = Column(String(255))
    user_email = Column(String(255))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50))  # e.g., "pending", "responded", "closed"

    # Relationships
    property = relationship("Property", back_populates="inquiries")

class GeneralConversation(Base):
    """Tracks general conversations between users and the chatbot."""
    __tablename__ = "general_conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # Nullable for anonymous users
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
    user_id = Column(String(255), nullable=False, index=True)  # Must be logged in
    property_id = Column(String(255), nullable=False, index=True)
    seller_id = Column(String(255), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    property_context = Column(JSON)  # Store property-specific context

    # Relationship to messages
    messages = relationship("PropertyMessage", back_populates="conversation", cascade="all, delete-orphan")

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