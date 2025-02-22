#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.database import SessionLocal, engine, Base
from app.database.models import (
    GeneralConversation, GeneralMessage,
    PropertyConversation, PropertyMessage,
    ExternalReference
)

def seed_database():
    """Seed the database with sample data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create sample general conversation
        general_conv = GeneralConversation(
            user_id="test_user_1",
            session_id="test_session_1",
            context={
                "last_intent": "general_inquiry",
                "topics_discussed": ["general_inquiry", "service_info"],
                "service_details_requested": True
            }
        )
        db.add(general_conv)
        db.flush()

        # Create sample general messages
        general_messages = [
            GeneralMessage(
                conversation_id=general_conv.id,
                role="user",
                content="Hi, I'd like to know more about your services.",
                intent="general_inquiry",
                message_metadata={"confidence": 0.95},
                timestamp=datetime.utcnow() - timedelta(minutes=30)
            ),
            GeneralMessage(
                conversation_id=general_conv.id,
                role="assistant",
                content=(
                    "Hello! I'd be happy to tell you about our services. "
                    "We offer property listings, virtual tours, and personalized assistance..."
                ),
                intent="service_info",
                message_metadata={"response_type": "service_details"},
                timestamp=datetime.utcnow() - timedelta(minutes=29)
            )
        ]
        
        for message in general_messages:
            db.add(message)

        # Create sample buyer-seller conversations
        buyer_conv = PropertyConversation(
            user_id="test_buyer_1",
            session_id="test_session_2",
            property_id="test_property_1",
            role="buyer",
            counterpart_id="test_seller_1",
            conversation_status="active",
            property_context={
                "last_intent": "negotiation",
                "topics_discussed": ["property_inquiry", "negotiation"],
                "property_details_requested": True,
                "offer_made": True
            }
        )
        db.add(buyer_conv)
        db.flush()

        seller_conv = PropertyConversation(
            user_id="test_seller_1",
            session_id="test_session_3",
            property_id="test_property_1",
            role="seller",
            counterpart_id="test_buyer_1",
            conversation_status="active",
            property_context={
                "last_intent": "buyer_seller_communication",
                "topics_discussed": ["property_inquiry", "negotiation"],
                "counter_offer_made": True
            }
        )
        db.add(seller_conv)
        db.flush()

        # Create sample property messages for buyer conversation
        buyer_messages = [
            PropertyMessage(
                conversation_id=buyer_conv.id,
                role="user",
                content="Hi, I'm interested in making an offer on the property.",
                intent="negotiation",
                message_metadata={"confidence": 0.95},
                timestamp=datetime.utcnow() - timedelta(minutes=30)
            ),
            PropertyMessage(
                conversation_id=buyer_conv.id,
                role="assistant",
                content=(
                    "I'll help you make an offer on this property. "
                    "Please specify your proposed price and any conditions."
                ),
                intent="negotiation",
                message_metadata={"response_type": "negotiation_facilitation"},
                timestamp=datetime.utcnow() - timedelta(minutes=29)
            ),
            PropertyMessage(
                conversation_id=buyer_conv.id,
                role="user",
                content="I'd like to offer $450,000 with a 30-day closing period.",
                intent="negotiation",
                message_metadata={"confidence": 0.98},
                timestamp=datetime.utcnow() - timedelta(minutes=28)
            )
        ]
        
        for message in buyer_messages:
            db.add(message)

        # Create sample property messages for seller conversation
        seller_messages = [
            PropertyMessage(
                conversation_id=seller_conv.id,
                role="user",
                content="Thank you for your interest. I'm considering your offer.",
                intent="buyer_seller_communication",
                message_metadata={"confidence": 0.95},
                timestamp=datetime.utcnow() - timedelta(minutes=27)
            ),
            PropertyMessage(
                conversation_id=seller_conv.id,
                role="assistant",
                content=(
                    "I'll help facilitate the negotiation. "
                    "Would you like to make a counter-offer or accept the current offer?"
                ),
                intent="negotiation",
                message_metadata={"response_type": "negotiation_facilitation"},
                timestamp=datetime.utcnow() - timedelta(minutes=26)
            )
        ]
        
        for message in seller_messages:
            db.add(message)

        # Create sample external references
        external_refs = [
            ExternalReference(
                property_conversation_id=buyer_conv.id,
                service_name="seller_buyer_communication",
                external_id="notification_1",
                reference_metadata={
                    "message_forwarded": True,
                    "forwarded_at": datetime.utcnow().isoformat(),
                    "property_id": "test_property_1",
                    "sender_role": "buyer",
                    "message_type": "negotiation"
                }
            ),
            ExternalReference(
                general_conversation_id=general_conv.id,
                service_name="user_service",
                external_id="test_user_1",
                reference_metadata={
                    "user_type": "prospect",
                    "source": "website"
                }
            )
        ]
        
        for ref in external_refs:
            db.add(ref)
        
        db.commit()
        print("Sample data has been seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database() 