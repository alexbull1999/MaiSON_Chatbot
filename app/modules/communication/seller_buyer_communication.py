from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ...database.models import ExternalReference, PropertyQuestion, PropertyConversation, PropertyMessage
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
            # Store context for use in _needs_seller_input
            self._current_context = context

            # Validate context
            if not all(
                k in context
                for k in ["user_id", "role", "counterpart_id", "property_id"]
            ):
                return "Missing required context for seller-buyer communication."

            # Get conversation history
            history = context.get("conversation_history", [])

            # If this is a buyer asking a question that needs seller input
            if context["role"] == "buyer" and self._needs_seller_input(message):
                return await self._handle_buyer_question(message, context)

            # For all other messages, just generate a response
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
            # Skip question creation if this is a notification for an existing question
            if context.get("notification_type") == "new_question":
                # Just create the external reference for notification
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
                        "question_id": context.get("question_id")
                    },
                )
                db.add(external_ref)
                db.commit()
                return True

            # Get original question from context if available
            property_context = context.get("property_context", {})
            if "original_question" in context:
                property_context["original_question"] = context["original_question"]

            # Format message for the counterpart
            formatted_message = await self.format_message_for_counterpart(
                message, context["role"], property_context
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
            # If this is a notification for a question, use the original question if available
            if isinstance(property_context, dict) and "original_question" in property_context:
                message = property_context["original_question"]

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

    async def _needs_seller_input(self, message: str) -> bool:
        """
        Use LLM to determine if a message requires seller input based on content analysis
        and conversation history.
        """
        try:
            # Get conversation history from context
            history = getattr(self, '_current_context', {}).get('conversation_history', [])
            
            # Prepare the context for LLM
            conversation_context = {
                "current_message": message,
                "conversation_history": history[-2:] if history else []  # Last 2 messages for context
            }

            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a real estate communication analyzer. Your task is to determine if a message either:\n"
                            "1. Contains a question that needs to be forwarded to the seller, or\n"
                            "2. Is confirming that a previous question should be forwarded to the seller\n\n"
                            "Consider both the current message and the conversation history.\n"
                            "Respond with exactly 'true' if either condition is met, or 'false' otherwise."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            "Please analyze this conversation context:\n"
                            f"{conversation_context}\n\n"
                            "Does this message either contain a question for the seller "
                            "or confirm that a previous question should be forwarded?"
                        )
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent yes/no responses
                module_name="seller_buyer_communication"
            )
            
            return response.strip().lower() == 'true'

        except Exception as e:
            print(f"Error in LLM-based seller input detection: {str(e)}")
            # Fallback to basic pattern matching if LLM fails
            message_lower = message.lower()
            patterns = [
                "ask the seller",
                "can you ask",
                "check with the seller",
                "find out from the seller",
                "ask them about",
                "could you ask",
                "please ask",
                "yes please",
                "yes go ahead",
                "please do",
            ]
            return any(pattern in message_lower for pattern in patterns)

    async def _reformat_buyer_question(self, message: str) -> str:
        """
        Use LLM to reformat a buyer's question into a clear, direct question for the seller.
        """
        try:
            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional real estate communication assistant. "
                            "Your task is to reformat buyer questions into clear, direct questions for sellers. "
                            "Remove phrases like 'can you ask the seller' or 'please ask' and make it a direct question. "
                            "Maintain the original meaning but make it more professional and concise."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Please reformat this buyer's question into a clear, direct question: {message}"
                    }
                ],
                temperature=0.7,
                module_name="seller_buyer_communication"
            )
            return response.strip()
        except Exception as e:
            print(f"Error reformatting buyer question: {str(e)}")
            return message  # Return original message if reformatting fails

    async def _handle_buyer_question(self, message: str, context: Dict) -> str:
        """
        Handle a buyer's question that needs to be forwarded to the seller.
        Creates a PropertyQuestion record and notifies the seller.
        """
        db = context["db"]
        try:
            # Check if a question with this message_id already exists
            existing_question = db.query(PropertyQuestion).filter(
                PropertyQuestion.question_message_id == context["message_id"]
            ).first()
            
            if existing_question:
                return "I will forward your question to the seller and let you know once I have a response."

            # Get conversation history and prepare context for LLM
            history = context.get("conversation_history", [])
            conversation_context = {
                "current_message": message,
                "conversation_history": history[-3:] if history else []  # Last 3 messages for context
            }

            # Use LLM to extract the question to be forwarded
            response = await self.llm_client.generate_response(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a real estate communication analyzer. Your task is to extract a question for the seller from the conversation.\n"
                            "If the current message contains a direct question, return that question.\n"
                            "If the current message is confirming a previous question (like 'yes please'), extract and return the original question from the conversation history.\n"
                            "If no question can be found, respond with exactly 'NO_QUESTION_FOUND'.\n"
                            "Format the response as a clear, direct question for the seller."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Please analyze this conversation and extract the question for the seller:\n{conversation_context}"
                    }
                ],
                temperature=0.3,
                module_name="seller_buyer_communication"
            )

            # If no question was found, ask the user to clarify
            if response.strip() == "NO_QUESTION_FOUND":
                return "I need the original question to forward to the seller. Could you please repeat your question?"

            # Create PropertyQuestion record with the extracted question
            question = PropertyQuestion(
                property_id=context["property_id"],
                buyer_id=context["user_id"],
                seller_id=context["counterpart_id"],
                conversation_id=context["conversation_id"],
                question_message_id=context["message_id"],
                question_text=response.strip(),
            )
            
            # Add to database
            db.add(question)
            db.flush()  # Get the question ID

            # Create notification reference
            external_ref = ExternalReference(
                property_conversation_id=context["conversation_id"],
                service_name="seller_buyer_communication",
                external_id=context["counterpart_id"],
                reference_metadata={
                    "message_forwarded": True,
                    "forwarded_at": datetime.utcnow().isoformat(),
                    "property_id": context["property_id"],
                    "sender_role": context["role"],
                    "message_type": self._classify_message_type(message),
                    "question_id": question.id,
                    "notification_type": "new_question",
                    "original_question": message  # Include original message for context
                },
            )
            db.add(external_ref)

            return "I will forward your question to the seller and let you know once I have a response."

        except Exception as e:
            print(f"Error handling buyer question: {str(e)}")
            raise  # Let the transaction handling in the route handle the rollback

    async def handle_seller_response(
        self, 
        question_id: int, 
        answer: str, 
        db: Session
    ) -> bool:
        """
        Handle a seller's response to a buyer's question.
        Updates the PropertyQuestion record and notifies the buyer.
        """
        try:
            # Get the question record
            question = db.query(PropertyQuestion).filter(
                PropertyQuestion.id == question_id
            ).first()
            
            if not question:
                return False
                
            # Check if question is already answered
            if question.status == "answered":
                return False

            # Update question record
            question.status = "answered"
            question.answer_text = answer
            question.answered_at = datetime.utcnow()
            
            # Get the original conversation
            conversation = db.query(PropertyConversation).filter(
                PropertyConversation.id == question.conversation_id
            ).first()

            if not conversation:
                return False

            # Create a new message in the conversation with the answer
            answer_message = PropertyMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=f"The seller has responded to your question:\n\n{answer}",
                intent="buyer_seller_communication",
                message_metadata={
                    "is_seller_response": True,
                    "original_question_id": question_id
                }
            )
            db.add(answer_message)
            
            # Commit changes
            db.commit()
            
            return True

        except Exception as e:
            print(f"Error handling seller response: {str(e)}")
            db.rollback()
            return False
