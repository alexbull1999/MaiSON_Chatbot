from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
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
    ExternalReference,
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
    user_id: Optional[str] = None  # UUID string for Firebase user ID
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
    request: GeneralChatRequest,
    response: Response,
    session_id: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Handle general chat messages and return AI responses.
    This endpoint handles both logged-in and anonymous users.
    """
    try:
        # Use existing session ID from cookie if available, otherwise generate new one
        current_session_id = session_id or request.session_id or str(uuid.uuid4())

        # Set cookie for anonymous users
        if not request.user_id:
            response.set_cookie(
                key="session_id",
                value=current_session_id,
                max_age=86400,  # 24 hours in seconds
                httponly=True,   # Cookie not accessible via JavaScript
                samesite="lax",  # Protects against CSRF
                secure=True     # Only sent over HTTPS
            )

        chat_response = await chat_controller.handle_general_chat(
            message=request.message,
            user_id=request.user_id,
            session_id=current_session_id,
            db=db,
        )
        return chat_response
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
    user_id: str,  # UUID string for Firebase user ID
    role: Optional[Role] = None,
    status: Optional[ConversationStatus] = None,
    db: Session = Depends(get_db),
):
    """
    Get all conversations for a specific user.
    Optionally filter by role (buyer/seller) and conversation status.
    
    This endpoint returns:
    1. General conversations where the user is directly involved
    2. Property conversations where the user is directly involved
    3. Property conversations where the user is referenced as a counterpart
    """
    # Get general conversations where user is directly involved
    general_conversations = (
        db.query(GeneralConversationModel)
        .filter(GeneralConversationModel.user_id == user_id)
        .all()
    )

    # Get property conversations where user is directly involved
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
    
    # Get property conversations where user is referenced as a counterpart
    counterpart_query = (
        db.query(PropertyConversationModel)
        .join(
            ExternalReference,
            ExternalReference.property_conversation_id == PropertyConversationModel.id
        )
        .filter(ExternalReference.external_id == user_id)
        .filter(ExternalReference.service_name == "seller_buyer_communication")
    )
    
    # Apply the same filters as for direct conversations
    if role:
        # For counterpart conversations, we need to filter by the opposite role
        opposite_role = "seller" if role.value == "buyer" else "buyer"
        counterpart_query = counterpart_query.filter(PropertyConversationModel.role == opposite_role)
    if status:
        counterpart_query = counterpart_query.filter(
            PropertyConversationModel.conversation_status == status
        )
    
    counterpart_conversations = counterpart_query.all()
    
    # Combine direct and counterpart property conversations, avoiding duplicates
    seen_ids = {conv.id for conv in property_conversations}
    for conv in counterpart_conversations:
        if conv.id not in seen_ids:
            property_conversations.append(conv)
            seen_ids.add(conv.id)

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
                "is_counterpart": conv.user_id != user_id,  # Flag to indicate if user is the counterpart
            }
            for conv in property_conversations
        ],
    }
