#!/usr/bin/env python
"""
Test script for the counterpart conversations functionality with filters.
This script tests the /conversations/user/{user_id} endpoint with role and status filters.
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


def print_conversations(user_id, conversations, filter_desc=""):
    """Print conversations in a readable format."""
    print(f"\n=== Conversations for user {user_id} {filter_desc} ===")

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

    return len(conversations.get("property_conversations", []))


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

    # Step 2: Get conversations for the buyer without filters
    print("\nChecking buyer conversations (no filters)...")
    buyer_conversations = get_user_conversations(BUYER_ID)
    buyer_count = print_conversations(BUYER_ID, buyer_conversations)

    # Step 3: Get conversations for the seller without filters
    print("\nChecking seller conversations (no filters)...")
    seller_conversations = get_user_conversations(SELLER_ID)
    seller_count = print_conversations(SELLER_ID, seller_conversations)

    # Step 4: Test with buyer role filter
    print("\nChecking buyer conversations (role=buyer)...")
    buyer_role_conversations = get_user_conversations(BUYER_ID, role="buyer")
    buyer_role_count = print_conversations(
        BUYER_ID, buyer_role_conversations, "(role=buyer)"
    )

    # Step 5: Test with seller role filter
    print("\nChecking seller conversations (role=seller)...")
    seller_role_conversations = get_user_conversations(SELLER_ID, role="seller")
    seller_role_count = print_conversations(
        SELLER_ID, seller_role_conversations, "(role=seller)"
    )

    # Step 6: Test with active status filter
    print("\nChecking buyer conversations (status=active)...")
    buyer_status_conversations = get_user_conversations(BUYER_ID, status="active")
    buyer_status_count = print_conversations(
        BUYER_ID, buyer_status_conversations, "(status=active)"
    )

    # Step 7: Test with closed status filter
    print("\nChecking buyer conversations (status=closed)...")
    buyer_closed_conversations = get_user_conversations(BUYER_ID, status="closed")
    buyer_closed_count = print_conversations(
        BUYER_ID, buyer_closed_conversations, "(status=closed)"
    )

    # Step 8: Verify results
    print("\n=== Test Results ===")
    print(f"Buyer conversations (no filters): {buyer_count}")
    print(f"Seller conversations (no filters): {seller_count}")
    print(f"Buyer conversations (role=buyer): {buyer_role_count}")
    print(f"Seller conversations (role=seller): {seller_role_count}")
    print(f"Buyer conversations (status=active): {buyer_status_count}")
    print(f"Buyer conversations (status=closed): {buyer_closed_count}")

    # Check if filters are working correctly
    all_tests_passed = True

    if buyer_count != 1:
        print("❌ FAILED: Buyer should see exactly 1 conversation without filters")
        all_tests_passed = False

    if seller_count != 1:
        print("❌ FAILED: Seller should see exactly 1 conversation without filters")
        all_tests_passed = False

    if buyer_role_count != 1:
        print(
            "❌ FAILED: Buyer should see exactly 1 conversation with role=buyer filter"
        )
        all_tests_passed = False

    if seller_role_count != 1:
        print(
            "❌ FAILED: Seller should see exactly 1 conversation with role=seller filter"
        )
        all_tests_passed = False

    if buyer_status_count != 1:
        print(
            "❌ FAILED: Buyer should see exactly 1 conversation with status=active filter"
        )
        all_tests_passed = False

    if buyer_closed_count != 0:
        print("❌ FAILED: Buyer should see 0 conversations with status=closed filter")
        all_tests_passed = False

    if all_tests_passed:
        print("\n✅ ALL TESTS PASSED: Filters are working correctly")
    else:
        print("\n❌ SOME TESTS FAILED: Check the results above")


if __name__ == "__main__":
    main()
