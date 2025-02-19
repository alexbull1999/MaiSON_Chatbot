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

router = APIRouter()


class GeneralChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class PropertyChatRequest(BaseModel):
    message: str
    user_id: str
    property_id: str
    seller_id: str
    session_id: Optional[str] = None


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
    Handle property-specific chat messages.
    This endpoint requires user authentication and property/seller information.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        response = await chat_controller.handle_property_chat(
            message=request.message,
            user_id=request.user_id,
            property_id=request.property_id,
            seller_id=request.seller_id,
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
        "seller_id": conversation.seller_id,
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


@router.get("/conversations/user/{user_id}")
async def get_user_conversations(user_id: str, db: Session = Depends(get_db)):
    """Get all conversations for a specific user."""
    general_conversations = (
        db.query(GeneralConversationModel)
        .filter(GeneralConversationModel.user_id == user_id)
        .all()
    )

    property_conversations = (
        db.query(PropertyConversationModel)
        .filter(PropertyConversationModel.user_id == user_id)
        .all()
    )

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
                "seller_id": conv.seller_id,
                "started_at": conv.started_at,
                "last_message_at": conv.last_message_at,
                "property_context": conv.property_context,
            }
            for conv in property_conversations
        ],
    }
