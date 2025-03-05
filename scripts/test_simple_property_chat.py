import requests
import uuid
from pprint import pprint

# Production API URL
API_URL = "https://maisonbot-api.xyz"


def test_property_chat():
    print("\n=== Starting Simple Property Chat Test ===\n")

    # Test data
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    test_property_id = (
        "9c456f41-6bd3-4b06-8541-62f75243c874"  # Churchill, London property
    )

    print(f"Test User ID: {test_user_id}")
    print(f"Test Property ID: {test_property_id}")

    # Step 1: Create a property chat
    print("\n1. Creating property chat...")
    create_chat_url = f"{API_URL}/api/v1/chat/property"

    create_chat_data = {
        "message": "Hi, I'm interested in this property. Is it still available?",
        "user_id": test_user_id,
        "property_id": test_property_id,
        "role": "buyer",
        "counterpart_id": "seller_123",
    }

    response = requests.post(create_chat_url, json=create_chat_data)
    print(f"Status Code: {response.status_code}")
    print("Response:")
    pprint(response.json())

    if response.status_code != 200:
        print("❌ Failed to create property chat")
        return

    # Extract conversation details
    conversation_data = response.json()
    conversation_id = conversation_data.get("conversation_id")
    session_id = conversation_data.get("session_id")

    if not conversation_id or not session_id:
        print("❌ Missing conversation_id or session_id in response")
        return

    print(f"\nCreated conversation_id: {conversation_id}")
    print(f"Session ID: {session_id}")

    # Step 2: Send another message to the same conversation
    print("\n2. Sending follow-up message...")

    follow_up_data = {
        "message": "I'd like to schedule a viewing. What times are available?",
        "user_id": test_user_id,
        "property_id": test_property_id,
        "role": "buyer",
        "counterpart_id": "seller_123",
        "session_id": session_id,
    }

    response = requests.post(create_chat_url, json=follow_up_data)
    print(f"Status Code: {response.status_code}")
    print("Response:")
    pprint(response.json())

    # Step 3: Retrieve conversation history
    print("\n3. Retrieving conversation history...")
    history_url = f"{API_URL}/api/v1/conversations/property/{conversation_id}/history"

    response = requests.get(history_url)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        history = response.json()
        print("\nConversation History:")
        messages = history.get("messages", [])
        for msg in messages:
            print(f"\n[{msg.get('role')}]: {msg.get('content')}")
    else:
        print("❌ Failed to retrieve conversation history")
        print("Response:")
        pprint(response.json())


if __name__ == "__main__":
    test_property_chat()
