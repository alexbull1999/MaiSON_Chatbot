from typing import Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Message, ExternalReference

class SellerCommunicationModule:
    def __init__(self):
        self.seller_notifications = {}  # In-memory store for demo purposes

    async def forward_message_to_seller(
        self,
        seller_id: str,
        user_message: str,
        conversation_id: int,
        property_id: str,
        user_info: Dict[str, str],
        db: Session
    ) -> bool:
        """
        Forward a user's message to the property seller.
        
        Args:
            seller_id: ID of the seller to receive the message
            user_message: The message content
            conversation_id: ID of the current conversation
            property_id: ID of the property being discussed
            user_info: Dictionary containing user information (name, email)
            db: Database session
        
        Returns:
            bool: True if message was successfully forwarded
        """
        try:
            # Create a record of the forwarded message
            forwarded_message = Message(
                conversation_id=conversation_id,
                role="system",
                content=f"Message forwarded to seller: {user_message}",
                created_at=datetime.utcnow(),
                message_metadata={
                    "forwarded_to_seller": seller_id,
                    "property_id": property_id,
                    "user_info": user_info
                }
            )
            db.add(forwarded_message)

            # Create external reference for seller communication
            external_ref = ExternalReference(
                conversation_id=conversation_id,
                service_name="seller_communication",
                external_id=seller_id,
                reference_metadata={
                    "message_forwarded": True,
                    "forwarded_at": datetime.utcnow().isoformat(),
                    "property_id": property_id
                }
            )
            db.add(external_ref)

            # In a real implementation, this would integrate with a notification service
            # For now, we'll store it in memory
            if seller_id not in self.seller_notifications:
                self.seller_notifications[seller_id] = []
            
            self.seller_notifications[seller_id].append({
                "message": user_message,
                "conversation_id": conversation_id,
                "property_id": property_id,
                "user_info": user_info,
                "timestamp": datetime.utcnow().isoformat()
            })

            db.commit()
            return True

        except Exception as e:
            print(f"Error forwarding message to seller: {str(e)}")
            db.rollback()
            return False

    def get_seller_notifications(self, seller_id: str) -> list:
        """Get all notifications for a seller (demo implementation)."""
        return self.seller_notifications.get(seller_id, []) 