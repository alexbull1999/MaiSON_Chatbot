from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String)
    location = Column(String, index=True)
    price = Column(Float)
    description = Column(String)
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
    user_name = Column(String)
    user_email = Column(String)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)  # e.g., "pending", "responded", "closed"

    # Relationships
    property = relationship("Property", back_populates="inquiries")

class Conversation(Base):
    """Tracks unique conversations between users and the chatbot."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # From auth service
    user_name = Column(String)
    user_email = Column(String)
    property_id = Column(String, nullable=True)  # From property service
    seller_id = Column(String, nullable=True)   # From auth service
    started_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    context = Column(JSON, nullable=True)  # Store any relevant context as JSON

    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Individual messages within a conversation."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String)  # 'user', 'assistant', or 'system'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Message metadata
    intent = Column(String, nullable=True)  # Store classified intent
    message_metadata = Column(JSON, nullable=True)  # Store any additional metadata as JSON

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

class ExternalReference(Base):
    """Tracks references to external service data."""
    __tablename__ = "external_references"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    service_name = Column(String)  # e.g., 'property_service', 'availability_service'
    external_id = Column(String)   # ID in the external service
    reference_metadata = Column(JSON, nullable=True)  # Any additional data from external service
    last_synced = Column(DateTime, default=datetime.utcnow)

    # Relationship to conversation
    conversation = relationship("Conversation") 