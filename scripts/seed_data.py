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

        # Create sample property conversation
        property_conv = PropertyConversation(
            user_id="test_user_2",
            session_id="test_session_2",
            property_id="test_property_1",
            seller_id="test_seller_1",
            property_context={
                "last_intent": "property_inquiry",
                "topics_discussed": ["property_inquiry", "price_inquiry"],
                "property_details_requested": True,
                "price_discussed": True
            }
        )
        db.add(property_conv)
        db.flush()

        # Create sample property messages
        property_messages = [
            PropertyMessage(
                conversation_id=property_conv.id,
                role="user",
                content="Hi, I'm interested in the downtown apartment.",
                intent="property_inquiry",
                message_metadata={"confidence": 0.95},
                timestamp=datetime.utcnow() - timedelta(minutes=30)
            ),
            PropertyMessage(
                conversation_id=property_conv.id,
                role="assistant",
                content=(
                    "Hello! I'd be happy to tell you about our downtown apartment. "
                    "It's a modern luxury apartment with 2 bedrooms..."
                ),
                intent="property_inquiry",
                message_metadata={"response_type": "property_details"},
                timestamp=datetime.utcnow() - timedelta(minutes=29)
            ),
            PropertyMessage(
                conversation_id=property_conv.id,
                role="user",
                content="What's the price?",
                intent="price_inquiry",
                message_metadata={"confidence": 0.98},
                timestamp=datetime.utcnow() - timedelta(minutes=28)
            ),
            PropertyMessage(
                conversation_id=property_conv.id,
                role="assistant",
                content="The apartment is priced at $2,500 per month...",
                intent="price_inquiry",
                message_metadata={"response_type": "price_info"},
                timestamp=datetime.utcnow() - timedelta(minutes=27)
            )
        ]
        
        for message in property_messages:
            db.add(message)

        # Create sample external references
        external_refs = [
            ExternalReference(
                property_conversation_id=property_conv.id,
                service_name="property_service",
                external_id="test_property_1",
                reference_metadata={
                    "property_type": "apartment",
                    "location": "downtown",
                    "price": 2500.00
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