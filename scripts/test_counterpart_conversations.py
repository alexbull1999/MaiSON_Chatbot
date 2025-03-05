#!/usr/bin/env python
"""
Test script for the counterpart conversations functionality.
This script tests the /conversations/user/{user_id} endpoint to verify
that it returns conversations where the user is referenced as a counterpart.
"""

import requests
import uuid

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Generate unique IDs for testing
BUYER_ID = str(uuid.uuid4())
SELLER_ID = str(uuid.uuid4())
PROPERTY_ID = f"property_{uuid.uuid4().hex[:8]}"


def create_property_conversation():
    """Create a property conversation with the buyer as the primary user."""
    url = f"{BASE_URL}/chat/property"
    data = {
        "message": "I'm interested in this property",
        "user_id": BUYER_ID,
        "property_id": PROPERTY_ID,
        "role": "buyer",
        "counterpart_id": SELLER_ID,
    }

    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code != 200:
        print(f"Failed to create property conversation: {response.text}")
        return None

    result = response.json()
    print(f"Created property conversation: {result['conversation_id']}")
    return result


def get_user_conversations(user_id, role=None, status=None):
    """Get conversations for a user, optionally filtered by role and status."""
    url = f"{BASE_URL}/conversations/user/{user_id}"
    params = {}
    if role:
        params["role"] = role
    if status:
        params["status"] = status

    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"Failed to get conversations for user {user_id}: {response.text}")
        return None

    return response.json()


def print_conversations(user_id, conversations):
    """Print conversations in a readable format."""
    print(f"\n=== Conversations for user {user_id} ===")

    if not conversations:
        print("No conversations found")
        return

    print("\nGeneral Conversations:")
    for conv in conversations.get("general_conversations", []):
        print(f"  - ID: {conv['id']}, Last message: {conv['last_message_at']}")

    print("\nProperty Conversations:")
    for conv in conversations.get("property_conversations", []):
        counterpart_flag = (
            "COUNTERPART" if conv.get("is_counterpart", False) else "DIRECT"
        )
        print(
            f"  - ID: {conv['id']}, Property: {conv['property_id']}, Role: {conv['role']}, Status: {counterpart_flag}"
        )


def main():
    """Run the test script."""
    print(f"Testing with Buyer ID: {BUYER_ID}")
    print(f"Testing with Seller ID: {SELLER_ID}")
    print(f"Testing with Property ID: {PROPERTY_ID}")

    # Step 1: Create a property conversation
    conversation = create_property_conversation()
    if not conversation:
        print("Test failed: Could not create property conversation")
        return

    # Step 2: Get conversations for the buyer
    print("\nChecking buyer conversations...")
    buyer_conversations = get_user_conversations(BUYER_ID)
    print_conversations(BUYER_ID, buyer_conversations)

    # Step 3: Get conversations for the seller
    print("\nChecking seller conversations...")
    seller_conversations = get_user_conversations(SELLER_ID)
    print_conversations(SELLER_ID, seller_conversations)

    # Step 4: Verify results
    buyer_has_conversation = False
    seller_has_conversation = False

    if buyer_conversations and buyer_conversations.get("property_conversations"):
        for conv in buyer_conversations["property_conversations"]:
            if conv["property_id"] == PROPERTY_ID and not conv.get(
                "is_counterpart", False
            ):
                buyer_has_conversation = True
                break

    if seller_conversations and seller_conversations.get("property_conversations"):
        for conv in seller_conversations["property_conversations"]:
            if conv["property_id"] == PROPERTY_ID and conv.get("is_counterpart", True):
                seller_has_conversation = True
                break

    print("\n=== Test Results ===")
    print(f"Buyer can see the conversation: {buyer_has_conversation}")
    print(f"Seller can see the conversation: {seller_has_conversation}")

    if buyer_has_conversation and seller_has_conversation:
        print("\n✅ TEST PASSED: Both buyer and seller can see the conversation")
    elif buyer_has_conversation:
        print("\n❌ TEST FAILED: Only the buyer can see the conversation")
    elif seller_has_conversation:
        print("\n❌ TEST FAILED: Only the seller can see the conversation")
    else:
        print(
            "\n❌ TEST FAILED: Neither the buyer nor the seller can see the conversation"
        )


if __name__ == "__main__":
    main()
