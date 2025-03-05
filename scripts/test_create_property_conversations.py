import requests
import time

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"


def send_property_chat(
    message,
    user_id,
    property_id,
    role="buyer",
    counterpart_id="seller_123",
    session_id=None,
):
    """
    Send a message to the property chat endpoint
    """
    url = f"{BASE_URL}/chat/property"

    payload = {
        "message": message,
        "user_id": user_id,
        "property_id": property_id,
        "role": role,
        "counterpart_id": counterpart_id,
    }

    if session_id:
        payload["session_id"] = session_id

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None


def get_conversation_history(conversation_id):
    """
    Get the history for a specific conversation
    """
    url = f"{BASE_URL}/conversations/property/{conversation_id}/history"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None


# Test properties
test_properties = [
    {"id": "9c456f41-6bd3-4b06-8541-62f75243c874", "name": "Churchill, London"},
    {"id": "765d1a18-5b63-4a5d-8dbd-ff2b8f37f768", "name": "Oak Avenue, Manchester"},
]

# Create conversations for each property
user_id = "test_user_123"
conversations = []

print("Creating property conversations...\n")

for prop in test_properties:
    print(f"Creating conversation for property: {prop['name']} (ID: {prop['id']})")

    # Send initial message
    response = send_property_chat(
        message=f"I'm interested in {prop['name']}. Can you tell me more about it?",
        user_id=user_id,
        property_id=prop["id"],
    )

    if response:
        print(f"Conversation created with ID: {response['conversation_id']}")
        conversations.append(
            {
                "property_id": prop["id"],
                "property_name": prop["name"],
                "conversation_id": response["conversation_id"],
                "session_id": response["session_id"],
            }
        )

        # Send a follow-up message using the session_id
        time.sleep(1)  # Wait a bit to avoid rate limiting
        follow_up = send_property_chat(
            message="What's the price of this property?",
            user_id=user_id,
            property_id=prop["id"],
            session_id=response["session_id"],
        )

        if follow_up:
            print("Follow-up message sent successfully")
        else:
            print("Failed to send follow-up message")
    else:
        print("Failed to create conversation")

    print()

# Check conversation history
print("\nChecking conversation history...\n")

for conv in conversations:
    print(
        f"Checking history for property: {conv['property_name']} (Conversation ID: {conv['conversation_id']})"
    )

    history = get_conversation_history(conv["conversation_id"])

    if history:
        print(f"Property ID: {history.get('property_id')}")
        print(f"Session ID: {history.get('session_id')}")
        print(f"User ID: {history.get('user_id')}")
        print(f"Role: {history.get('role')}")
        print(f"Status: {history.get('conversation_status')}")

        messages = history.get("messages", [])
        print(f"\nMessages ({len(messages)}):")

        for i, msg in enumerate(messages):
            print(f"\n  Message {i+1}:")
            print(f"    Role: {msg.get('role')}")
            print(f"    Content: {msg.get('content')}")
            print(f"    Timestamp: {msg.get('timestamp')}")
    else:
        print("Failed to retrieve conversation history")

    print("\n" + "=" * 80 + "\n")
