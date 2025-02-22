from typing import Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum


from app.database import get_db
from app.database.models import (
    GeneralConversation,
    GeneralMessage,
    PropertyConversation,
    PropertyMessage,
)
from app.modules.message_router import MessageRouter
from app.database.schemas import GeneralChatResponse, PropertyChatResponse
from app.modules.communication.seller_buyer_communication import (
    SellerBuyerCommunicationModule,
)


class Role(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"


class ChatController:
    def __init__(self):
        self.message_router = MessageRouter()
        self.seller_buyer_communication = SellerBuyerCommunicationModule()

    async def handle_general_chat(
        self,
        message: str,
        session_id: str,
        user_id: Optional[str] = None,
        db: Session = Depends(get_db),
    ) -> GeneralChatResponse:
        """
        Handle general chat messages, manage conversation state, and generate responses.

        Args:
            message: The user's message
            session_id: Session ID for conversation tracking
            user_id: Optional authenticated user's ID
            db: Database session
        """
        try:
            # Get or create general conversation
            conversation = await self._get_or_create_general_conversation(
                db=db, session_id=session_id, user_id=user_id
            )

            # Create user message
            user_message = GeneralMessage(
                conversation_id=conversation.id,
                role="user",
                content=message,
                timestamp=datetime.utcnow(),
            )
            db.add(user_message)

            # Get conversation history
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation.messages[-5:]  # Last 5 messages for context
            ]

            # Get conversation context
            context = {
                "conversation_id": conversation.id,
                "session_id": conversation.session_id,
                "user_id": conversation.user_id,
                "conversation_history": conversation_history,
                "context": conversation.context or {},
            }

            # Generate response using message router
            response = await self.message_router.route_message(
                message=message, context=context, chat_type="general"
            )
            response_text = response["response"]
            intent = response["intent"]

            # Create assistant message
            assistant_message = GeneralMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                intent=intent,
                timestamp=datetime.utcnow(),
            )
            db.add(assistant_message)

            # Update conversation context
            await self._update_conversation_context(
                conversation, message, response_text
            )

            # Update last message timestamp
            conversation.last_message_at = datetime.utcnow()
            db.commit()

            return GeneralChatResponse(
                message=response_text,
                conversation_id=conversation.id,
                session_id=conversation.session_id,
                intent=intent,
                context=conversation.context,
            )

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def handle_property_chat(
        self,
        message: str,
        user_id: str,
        property_id: str,
        role: Role,
        counterpart_id: str,
        session_id: str,
        db: Session = Depends(get_db),
    ) -> PropertyChatResponse:
        """
        Handle property-specific chat messages between buyers and sellers.

        Args:
            message: The user's message
            user_id: Authenticated user's ID
            property_id: ID of the property being discussed
            role: Role of the user (buyer/seller)
            counterpart_id: ID of the other party in the conversation
            session_id: Session ID for conversation tracking
            db: Database session
        """
        try:
            # Get or create property conversation
            conversation = await self._get_or_create_property_conversation(
                db=db,
                session_id=session_id,
                user_id=user_id,
                property_id=property_id,
                role=role,
                counterpart_id=counterpart_id,
            )

            # Create user message
            user_message = PropertyMessage(
                conversation_id=conversation.id,
                role=role,
                content=message,
                timestamp=datetime.utcnow(),
            )
            db.add(user_message)

            # Get conversation history
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in conversation.messages[-5:]  # Last 5 messages for context
            ]

            # Get conversation context
            context = {
                "conversation_id": conversation.id,
                "session_id": conversation.session_id,
                "user_id": conversation.user_id,
                "property_id": conversation.property_id,
                "role": conversation.role,
                "counterpart_id": conversation.counterpart_id,
                "conversation_history": conversation_history,
                "property_context": conversation.property_context or {},
            }

            # Handle message using seller-buyer communication module
            response_text = await self.seller_buyer_communication.handle_message(
                message=message, context=context
            )

            # Create assistant message
            assistant_message = PropertyMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow(),
            )
            db.add(assistant_message)

            # Notify counterpart about the new message
            await self.seller_buyer_communication.notify_counterpart(
                conversation_id=conversation.id, message=message, db=db, context=context
            )

            # Update conversation context
            await self._update_property_conversation_context(
                conversation, message, response_text
            )

            # Update last message timestamp
            conversation.last_message_at = datetime.utcnow()
            db.commit()

            return PropertyChatResponse(
                message=response_text,
                conversation_id=conversation.id,
                session_id=conversation.session_id,
                intent="property_chat",  # Using a generic intent for now
                property_context=conversation.property_context,
            )

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def _get_or_create_general_conversation(
        self, db: Session, session_id: str, user_id: Optional[str] = None
    ) -> GeneralConversation:
        """Get or create a general conversation."""
        conversation = (
            db.query(GeneralConversation)
            .filter(GeneralConversation.session_id == session_id)
            .first()
        )

        if not conversation:
            conversation = GeneralConversation(
                session_id=session_id,
                user_id=user_id,
                is_logged_in=bool(user_id),
                started_at=datetime.utcnow(),
                last_message_at=datetime.utcnow(),
                context={},
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        return conversation

    async def _get_or_create_property_conversation(
        self,
        db: Session,
        session_id: str,
        user_id: str,
        property_id: str,
        role: Role,
        counterpart_id: str,
    ) -> PropertyConversation:
        """Get or create a property-specific conversation."""
        conversation = (
            db.query(PropertyConversation)
            .filter(PropertyConversation.session_id == session_id)
            .first()
        )

        if not conversation:
            conversation = PropertyConversation(
                session_id=session_id,
                user_id=user_id,
                property_id=property_id,
                role=role,
                counterpart_id=counterpart_id,
                conversation_status="active",
                started_at=datetime.utcnow(),
                last_message_at=datetime.utcnow(),
                property_context={},
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        return conversation

    async def _update_conversation_context(
        self,
        conversation: GeneralConversation,
        user_message: str,
        assistant_response: str,
    ) -> None:
        """Update the context for a general conversation."""
        # Implement context updating logic for general conversations
        # This could include updating user preferences, topics discussed, etc.
        pass

    async def _update_property_conversation_context(
        self,
        conversation: PropertyConversation,
        user_message: str,
        assistant_response: str,
    ) -> None:
        """Update the context for a property-specific conversation."""
        # Implement context updating logic for property conversations
        # This could include updating property details, negotiation state, etc.
        pass


# Initialize controller
chat_controller = ChatController()
