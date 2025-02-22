from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import model_validator

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

# General Conversation Schemas
class GeneralMessageBase(BaseModel):
    role: str
    content: str
    intent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class GeneralMessageCreate(GeneralMessageBase):
    conversation_id: int

class GeneralMessage(GeneralMessageBase):
    id: int
    conversation_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class GeneralConversationBase(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    is_logged_in: bool = False
    context: Optional[Dict[str, Any]] = None

class GeneralConversationCreate(GeneralConversationBase):
    pass

class GeneralConversation(GeneralConversationBase):
    id: int
    started_at: datetime
    last_message_at: datetime
    messages: List[GeneralMessage] = []

    class Config:
        from_attributes = True

# Property Conversation Schemas
class PropertyMessageBase(BaseModel):
    role: str
    content: str
    intent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PropertyMessageCreate(PropertyMessageBase):
    conversation_id: int

class PropertyMessage(PropertyMessageBase):
    id: int
    conversation_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class PropertyConversationBase(BaseModel):
    session_id: str
    user_id: str
    property_id: str
    role: str  # 'buyer' or 'seller'
    counterpart_id: str
    conversation_status: str = "active"
    property_context: Optional[Dict[str, Any]] = None

    @model_validator(mode='before')
    def validate_role(cls, values):
        if values.get('role') not in ['buyer', 'seller']:
            raise ValueError("Role must be either 'buyer' or 'seller'")
        return values

class PropertyConversationCreate(PropertyConversationBase):
    pass

class PropertyConversation(PropertyConversationBase):
    id: int
    started_at: datetime
    last_message_at: datetime
    messages: List[PropertyMessage] = []

    class Config:
        from_attributes = True

# Chat Response Schemas
class GeneralChatResponse(BaseModel):
    message: str
    conversation_id: int
    session_id: str
    intent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class PropertyChatResponse(BaseModel):
    message: str
    conversation_id: int
    session_id: str
    intent: Optional[str] = None
    property_context: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# External Reference Schemas
class ExternalReferenceBase(BaseModel):
    service_name: str
    external_id: str
    metadata: Optional[Dict[str, Any]] = None

class ExternalReferenceCreate(ExternalReferenceBase):
    general_conversation_id: Optional[int] = None
    property_conversation_id: Optional[int] = None

    @model_validator(mode='before')
    def validate_conversation_ids(cls, values):
        if values.get('general_conversation_id') and values.get('property_conversation_id'):
            raise ValueError("Cannot reference both general and property conversations")
        if not values.get('general_conversation_id') and not values.get('property_conversation_id'):
            raise ValueError("Must reference either general or property conversation")
        return values

class ExternalReference(ExternalReferenceBase):
    id: int
    general_conversation_id: Optional[int] = None
    property_conversation_id: Optional[int] = None
    last_synced: datetime

    class Config:
        from_attributes = True

# Response Schemas
class ChatResponse(BaseModel):
    message: str
    conversation_id: int
    intent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True  # This replaces orm_mode=True in Pydantic v2 