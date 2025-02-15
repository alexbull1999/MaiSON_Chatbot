from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.database.schemas import ChatResponse
from app.database.models import Conversation
from .controllers import chat_controller
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: str
    user_name: str
    user_email: str
    property_id: Optional[str] = None
    seller_id: Optional[str] = None
    conversation_id: Optional[int] = None

class ChatMessageRequest(BaseModel):
    message: str
    sessionId: Optional[str] = None

class ChatMessageResponse(BaseModel):
    message: str
    sessionId: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Handle chat messages and return AI responses.
    
    This endpoint:
    1. Processes incoming chat messages
    2. Maintains conversation context
    3. Generates appropriate responses
    4. Tracks message history
    """
    try:
        response = await chat_controller.handle_chat(
            message=request.message,
            user_id=request.user_id,
            user_name=request.user_name,
            user_email=request.user_email,
            property_id=request.property_id,
            seller_id=request.seller_id,
            conversation_id=request.conversation_id,
            db=db
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/history")
async def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get the message history for a specific conversation."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at,
                "intent": message.intent
            }
            for message in conversation.messages
        ],
        "context": conversation.context
    }

@router.get("/conversations/user/{user_id}")
async def get_user_conversations(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all conversations for a specific user."""
    conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
    return [
        {
            "id": conv.id,
            "property_id": conv.property_id,
            "started_at": conv.started_at,
            "last_message_at": conv.last_message_at,
            "context": conv.context
        }
        for conv in conversations
    ]

@router.post("/chat/message", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Handle chat messages from the frontend.
    
    This endpoint:
    1. Accepts a message and optional sessionId
    2. Processes the message using the chat controller
    3. Returns the AI response and a sessionId for conversation tracking
    """
    try:
        # Convert sessionId to conversation_id if provided
        conversation_id = int(request.sessionId) if request.sessionId else None
        
        # Process the chat request
        response = await chat_controller.handle_chat(
            message=request.message,
            user_id="frontend_user",  # Default user ID for frontend users
            user_name="Website Visitor",
            user_email="visitor@example.com",
            conversation_id=conversation_id,
            db=db
        )
        
        return ChatMessageResponse(
            message=response.message,
            sessionId=str(response.conversation_id)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 