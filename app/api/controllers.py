from typing import Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.database.models import Conversation, Message
from app.modules.message_router import MessageRouter
from app.modules.intent_classification.intent_classifier import Intent
from app.database.schemas import ChatResponse

class ChatController:
    def __init__(self):
        self.message_router = MessageRouter()

    async def handle_chat(
        self,
        message: str,
        user_id: str,
        user_name: str,
        user_email: str,
        property_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        conversation_id: Optional[int] = None,
        db: Session = Depends(get_db)
    ) -> ChatResponse:
        """
        Handle incoming chat messages, manage conversation state, and generate responses.
        
        Args:
            message: The user's message
            user_id: Authenticated user's ID
            user_name: User's name
            user_email: User's email
            property_id: Optional ID of the property being discussed
            seller_id: Optional ID of the seller
            conversation_id: Optional ID of an existing conversation
            db: Database session
        """
        try:
            print(f"Debug: Processing chat message: {message}")
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                db=db,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                property_id=property_id,
                seller_id=seller_id,
                conversation_id=conversation_id
            )
            print(f"Debug: Using conversation ID: {conversation.id}")

            # Create user message
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=message,
                created_at=datetime.utcnow()
            )
            db.add(user_message)
            print("Debug: Added user message to database")
            
            # Get conversation history
            conversation_history = [
                {
                    "role": msg.role,
                    "content": msg.content
                }
                for msg in conversation.messages[-5:]  # Last 5 messages for context
            ]
            print(f"Debug: Retrieved conversation history: {len(conversation_history)} messages")

            # Get conversation context
            context = {
                "conversation_id": conversation.id,
                "property_id": conversation.property_id,
                "seller_id": conversation.seller_id,
                "conversation_history": conversation_history,
                "user_context": conversation.context or {}
            }

            try:
                # Generate response using message router
                print("Debug: Generating response using message router")
                response = await self.message_router.route_message(message=message, context=context)
                response_text = response["response"]
                intent = response["intent"]
                print(f"Debug: Generated response: {response_text[:100]}...")
            except Exception as e:
                print(f"Error generating response: {str(e)}")
                raise
            
            try:
                # Create assistant message
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=response_text,
                    intent=intent,
                    created_at=datetime.utcnow(),
                    metadata={
                        "context_used": context,
                        "response_type": "llm"
                    }
                )
                db.add(assistant_message)
                print("Debug: Added assistant message to database")
            except Exception as e:
                print(f"Error creating assistant message: {str(e)}")
                raise

            # Update conversation last_message_at
            conversation.last_message_at = datetime.utcnow()
            
            # Update conversation context based on intent and content
            await self._update_conversation_context(conversation, message, response_text)

            db.commit()
            print("Debug: Committed changes to database")

            return ChatResponse(
                message=response_text,
                conversation_id=conversation.id,
                intent=assistant_message.intent,
                context=conversation.context
            )

        except Exception as e:
            print(f"Error in handle_chat: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error processing message: {str(e)}"
            )

    async def _get_or_create_conversation(
        self,
        db: Session,
        user_id: str,
        user_name: str,
        user_email: str,
        property_id: Optional[str] = None,
        seller_id: Optional[str] = None,
        conversation_id: Optional[int] = None
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        try:
            if conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                if conversation:
                    return conversation

            # Create new conversation
            conversation = Conversation(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                property_id=property_id,
                seller_id=seller_id,
                started_at=datetime.utcnow(),
                last_message_at=datetime.utcnow(),
                context={
                    "last_intent": None,
                    "topics_discussed": [],
                    "property_details_requested": False,
                    "price_discussed": False
                }
            )
            db.add(conversation)
            db.flush()  # Get the ID without committing
            return conversation
        except Exception as e:
            print(f"Error in _get_or_create_conversation: {str(e)}")
            raise

    async def _update_conversation_context(
        self,
        conversation: Conversation,
        user_message: str,
        assistant_response: str
    ) -> None:
        """Update conversation context based on the current interaction."""
        context = conversation.context or {}
        
        # Update last intent
        intent = await self.message_router.intent_classifier.classify(user_message)
        context["last_intent"] = str(intent.value)

        # Track topics discussed
        topics = context.get("topics_discussed", [])
        if str(intent.value) not in topics:
            topics.append(str(intent.value))
        context["topics_discussed"] = topics

        # Track specific discussion flags
        if intent == Intent.PROPERTY_INQUIRY:
            context["property_details_requested"] = True
        elif intent == Intent.PRICE_INQUIRY:
            context["price_discussed"] = True

        conversation.context = context

# Initialize controller
chat_controller = ChatController() 