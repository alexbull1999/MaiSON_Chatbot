from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.database.schemas import (
    GeneralChatResponse,
    PropertyChatResponse,
)
from app.database.models import (
    GeneralConversation as GeneralConversationModel,
    PropertyConversation as PropertyConversationModel,
)
from .controllers import chat_controller
from pydantic import BaseModel
import uuid
from enum import Enum


class Role(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"


class GeneralChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class PropertyChatRequest(BaseModel):
    message: str
    user_id: str
    property_id: str
    role: Role
    counterpart_id: str
    session_id: Optional[str] = None


class ConversationStatusUpdate(BaseModel):
    status: ConversationStatus


router = APIRouter()


@router.post("/chat/general", response_model=GeneralChatResponse)
async def general_chat_endpoint(
    request: GeneralChatRequest, db: Session = Depends(get_db)
):
    """
    Handle general chat messages and return AI responses.
    This endpoint handles both logged-in and anonymous users.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        response = await chat_controller.handle_general_chat(
            message=request.message,
            user_id=request.user_id,
            session_id=session_id,
            db=db,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/property", response_model=PropertyChatResponse)
async def property_chat_endpoint(
    request: PropertyChatRequest, db: Session = Depends(get_db)
):
    """
    Handle property-specific chat messages between buyers and sellers.
    This endpoint requires user authentication and handles bidirectional communication.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        response = await chat_controller.handle_property_chat(
            message=request.message,
            user_id=request.user_id,
            property_id=request.property_id,
            role=request.role,
            counterpart_id=request.counterpart_id,
            session_id=session_id,
            db=db,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/general/{conversation_id}/history")
async def get_general_conversation_history(
    conversation_id: int, db: Session = Depends(get_db)
):
    """Get the message history for a specific general conversation."""
    conversation = (
        db.query(GeneralConversationModel)
        .filter(GeneralConversationModel.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": conversation_id,
        "session_id": conversation.session_id,
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp,
                "intent": message.intent,
            }
            for message in conversation.messages
        ],
        "context": conversation.context,
    }


@router.get("/conversations/property/{conversation_id}/history")
async def get_property_conversation_history(
    conversation_id: int, db: Session = Depends(get_db)
):
    """Get the message history for a specific property conversation."""
    conversation = (
        db.query(PropertyConversationModel)
        .filter(PropertyConversationModel.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": conversation_id,
        "session_id": conversation.session_id,
        "property_id": conversation.property_id,
        "user_id": conversation.user_id,
        "role": conversation.role,
        "counterpart_id": conversation.counterpart_id,
        "conversation_status": conversation.conversation_status,
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp,
                "intent": message.intent,
            }
            for message in conversation.messages
        ],
        "property_context": conversation.property_context,
    }


@router.patch("/conversations/property/{conversation_id}/status")
async def update_property_conversation_status(
    conversation_id: int,
    status_update: ConversationStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the status of a property conversation."""
    conversation = (
        db.query(PropertyConversationModel)
        .filter(PropertyConversationModel.id == conversation_id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.conversation_status = status_update.status
    db.commit()

    return {"message": "Conversation status updated successfully"}


@router.get("/conversations/user/{user_id}")
async def get_user_conversations(
    user_id: str,
    role: Optional[Role] = None,
    status: Optional[ConversationStatus] = None,
    db: Session = Depends(get_db),
):
    """
    Get all conversations for a specific user.
    Optionally filter by role (buyer/seller) and conversation status.
    """
    general_conversations = (
        db.query(GeneralConversationModel)
        .filter(GeneralConversationModel.user_id == user_id)
        .all()
    )

    property_query = db.query(PropertyConversationModel).filter(
        PropertyConversationModel.user_id == user_id
    )

    if role:
        property_query = property_query.filter(PropertyConversationModel.role == role)
    if status:
        property_query = property_query.filter(
            PropertyConversationModel.conversation_status == status
        )

    property_conversations = property_query.all()

    return {
        "general_conversations": [
            {
                "id": conv.id,
                "session_id": conv.session_id,
                "started_at": conv.started_at,
                "last_message_at": conv.last_message_at,
                "context": conv.context,
            }
            for conv in general_conversations
        ],
        "property_conversations": [
            {
                "id": conv.id,
                "session_id": conv.session_id,
                "property_id": conv.property_id,
                "role": conv.role,
                "counterpart_id": conv.counterpart_id,
                "conversation_status": conv.conversation_status,
                "started_at": conv.started_at,
                "last_message_at": conv.last_message_at,
                "property_context": conv.property_context,
            }
            for conv in property_conversations
        ],
    }
