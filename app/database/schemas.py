from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

# Property Schemas
class PropertyBase(BaseModel):
    name: str
    type: str
    location: str
    price: float
    description: str

class PropertyCreate(PropertyBase):
    pass

class Property(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Availability Slot Schemas
class AvailabilitySlotBase(BaseModel):
    start_date: datetime
    end_date: datetime
    is_available: bool = True

class AvailabilitySlotCreate(AvailabilitySlotBase):
    property_id: int

class AvailabilitySlot(AvailabilitySlotBase):
    id: int
    property_id: int

    class Config:
        orm_mode = True

# Inquiry Schemas
class InquiryBase(BaseModel):
    user_name: str
    user_email: str
    message: str

class InquiryCreate(InquiryBase):
    property_id: int

class Inquiry(InquiryBase):
    id: int
    property_id: int
    created_at: datetime
    status: str

    class Config:
        orm_mode = True

# Message Schemas
class MessageBase(BaseModel):
    role: str
    content: str
    intent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    conversation_id: int

class Message(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Conversation Schemas
class ConversationBase(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    property_id: Optional[str] = None
    seller_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: int
    started_at: datetime
    last_message_at: datetime
    messages: List[Message] = []

    class Config:
        orm_mode = True

# External Reference Schemas
class ExternalReferenceBase(BaseModel):
    service_name: str
    external_id: str
    metadata: Optional[Dict[str, Any]] = None

class ExternalReferenceCreate(ExternalReferenceBase):
    conversation_id: int

class ExternalReference(ExternalReferenceBase):
    id: int
    conversation_id: int
    last_synced: datetime

    class Config:
        orm_mode = True

# Response Schemas
class ChatResponse(BaseModel):
    message: str
    conversation_id: int
    intent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None 