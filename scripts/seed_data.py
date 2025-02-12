#!/usr/bin/env python3
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.database.models import Conversation, Message, ExternalReference
from datetime import datetime, timedelta

def seed_database():
    """Seed the database with sample data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create sample conversation
        conversation = Conversation(
            user_id="test_user_1",
            user_name="John Doe",
            user_email="john@example.com",
            property_id="test_property_1",
            seller_id="test_seller_1",
            context={
                "last_intent": "property_inquiry",
                "topics_discussed": ["property_inquiry", "price_inquiry"],
                "property_details_requested": True,
                "price_discussed": True
            }
        )
        db.add(conversation)
        db.flush()

        # Create sample messages
        messages = [
            Message(
                conversation_id=conversation.id,
                role="user",
                content="Hi, I'm interested in the downtown apartment.",
                intent="property_inquiry",
                message_metadata={"confidence": 0.95},
                created_at=datetime.utcnow() - timedelta(minutes=30)
            ),
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="Hello! I'd be happy to tell you about our downtown apartment. It's a modern luxury apartment with 2 bedrooms...",
                intent="property_inquiry",
                message_metadata={"response_type": "property_details"},
                created_at=datetime.utcnow() - timedelta(minutes=29)
            ),
            Message(
                conversation_id=conversation.id,
                role="user",
                content="What's the price?",
                intent="price_inquiry",
                message_metadata={"confidence": 0.98},
                created_at=datetime.utcnow() - timedelta(minutes=28)
            ),
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="The apartment is priced at $2,500 per month...",
                intent="price_inquiry",
                message_metadata={"response_type": "price_info"},
                created_at=datetime.utcnow() - timedelta(minutes=27)
            )
        ]
        
        for message in messages:
            db.add(message)

        # Create sample external reference
        external_ref = ExternalReference(
            conversation_id=conversation.id,
            service_name="property_service",
            external_id="test_property_1",
            reference_metadata={
                "property_type": "apartment",
                "location": "downtown",
                "price": 2500.00
            }
        )
        db.add(external_ref)
        
        db.commit()
        print("Sample data has been seeded successfully!")
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database() 