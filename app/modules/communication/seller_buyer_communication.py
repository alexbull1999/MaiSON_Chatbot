from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ...database.models import ExternalReference
from ..llm import LLMClient


class SellerBuyerCommunicationModule:
    """Module for handling communication between sellers and buyers."""

    def __init__(self):
        self.llm_client = LLMClient()

    async def handle_message(self, message: str, context: Dict) -> str:
        """
        Handle messages between sellers and buyers.

        Args:
            message: The message content
            context: Contains conversation details including:
                    - user_id: ID of the sender
                    - role: 'buyer' or 'seller'
                    - counterpart_id: ID of the recipient
                    - property_id: ID of the property
                    - conversation_history: List of previous messages
        """
        try:
            # Validate context
            if not all(
                k in context
                for k in ["user_id", "role", "counterpart_id", "property_id"]
            ):
                return "Missing required context for seller-buyer communication."

            # Get conversation history
            history = context.get("conversation_history", [])

            # Prepare message context for LLM
            message_context = {
                "sender_role": context["role"],
                "property_id": context["property_id"],
                "conversation_history": history,
                "message_type": self._classify_message_type(message),
            }

            # Generate appropriate response
            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional real estate communication assistant. "
                            "Help facilitate clear and effective communication between buyers and sellers. "
                            f"You are currently assisting a {context['role']} communicate with "
                            f"the {'seller' if context['role'] == 'buyer' else 'buyer'}. "
                            "Ensure the communication is professional, clear, and constructive."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context: {message_context}\n\nMessage: {message}",
                    },
                ],
                temperature=0.7,
            )

            return response

        except Exception as e:
            print(f"Error in seller-buyer communication: {str(e)}")
            return "I apologize, but I encountered an error processing your message. Please try again."

    async def notify_counterpart(
        self, conversation_id: int, message: str, db: Session, context: Dict
    ) -> bool:
        """
        Notify the counterpart (buyer/seller) about a new message.
        Creates an external reference and notification record.

        Args:
            conversation_id: ID of the current conversation
            message: The message to forward
            db: Database session
            context: Contains sender and recipient information
        """
        try:
            # Format message for the counterpart
            formatted_message = await self.format_message_for_counterpart(
                message, context["role"], context.get("property_context")
            )

            # Create external reference for notification
            external_ref = ExternalReference(
                property_conversation_id=conversation_id,
                service_name="seller_buyer_communication",
                external_id=context["counterpart_id"],
                reference_metadata={
                    "message_forwarded": True,
                    "forwarded_at": datetime.utcnow().isoformat(),
                    "property_id": context["property_id"],
                    "sender_role": context["role"],
                    "message_type": self._classify_message_type(message),
                },
            )
            db.add(external_ref)

            # In a real implementation, this would integrate with a notification service
            # For example, sending an email, push notification, or SMS
            # For now, we'll just log it
            print(
                f"Notification sent to {context['counterpart_id']}: {formatted_message}"
            )

            db.commit()
            return True

        except Exception as e:
            print(f"Error notifying counterpart: {str(e)}")
            db.rollback()
            return False

    def _classify_message_type(self, message: str) -> str:
        """
        Classify the type of message being sent.
        This helps provide appropriate context to the LLM.
        """
        message_lower = message.lower()

        if any(word in message_lower for word in ["offer", "bid", "price", "propose"]):
            return "negotiation"
        elif any(
            word in message_lower for word in ["when", "time", "schedule", "visit"]
        ):
            return "viewing_arrangement"
        elif any(
            word in message_lower for word in ["condition", "repair", "fix", "issue"]
        ):
            return "property_condition"
        elif any(
            word in message_lower for word in ["document", "contract", "agreement"]
        ):
            return "documentation"
        else:
            return "general_inquiry"

    async def format_message_for_counterpart(
        self, message: str, sender_role: str, property_context: Optional[Dict] = None
    ) -> str:
        """
        Format a message to be sent to the counterpart.
        Adds appropriate context and professional formatting.
        """
        try:
            # Prepare context for message formatting
            format_context = {
                "sender_role": sender_role,
                "property_context": property_context or {},
                "message_type": self._classify_message_type(message),
            }

            # Generate formatted message
            formatted_message = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional real estate communication assistant. "
                            "Format the following message to be professional and clear, "
                            "while maintaining the original intent and content."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context: {format_context}\n\nOriginal Message: {message}",
                    },
                ],
                temperature=0.7,
            )

            return formatted_message

        except Exception as e:
            print(f"Error formatting message: {str(e)}")
            return message  # Return original message if formatting fails

    def validate_message_content(self, message: str, sender_role: str) -> bool:
        """
        Validate message content for appropriateness and completeness.
        Returns True if message is valid, False otherwise.
        """
        if not message.strip():
            return False

        # Basic validation rules
        min_length = 2  # Minimum number of words
        max_length = 1000  # Maximum number of characters

        # Check message length
        if len(message.split()) < min_length or len(message) > max_length:
            return False

        # Check for inappropriate content (basic check)
        inappropriate_terms = ["scam", "illegal", "fraud"]
        if any(term in message.lower() for term in inappropriate_terms):
            return False

        return True
