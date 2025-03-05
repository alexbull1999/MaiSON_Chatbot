import requests

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"


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


def get_user_conversations(user_id):
    """
    Get all conversations for a specific user
    """
    url = f"{BASE_URL}/conversations/user/{user_id}"

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


# User ID from our previous tests
user_id = "7b9a6181-3303-4ea2-b505-dc293f9d2fbf"

# Get conversations for this user
response = get_user_conversations(user_id)

if response:
    # Extract property conversations from the response
    property_conversations_list = response.get("property_conversations", [])

    print(
        f"Found {len(property_conversations_list)} property conversations for user {user_id}"
    )

    # Group property conversations by property_id
    property_conversations = {}

    for conv in property_conversations_list:
        property_id = conv.get("property_id")
        if property_id not in property_conversations:
            property_conversations[property_id] = []

        property_conversations[property_id].append(conv)

    # Check messages for each conversation
    print("\nChecking messages for each conversation:")

    for property_id, convs in property_conversations.items():
        print(f"\nProperty ID: {property_id}")

        for i, conv in enumerate(convs, 1):
            conv_id = conv.get("id")
            print(f"\n  Conversation {i} (ID: {conv_id}):")

            # Get conversation history
            history = get_conversation_history(conv_id)

            if history:
                print(f"    Property ID: {history.get('property_id')}")
                print(f"    Session ID: {history.get('session_id')}")

                # Check messages
                messages = history.get("messages", [])
                print(f"    Number of messages: {len(messages)}")

                # Print first message content to verify property_id is mentioned
                if messages:
                    first_message = messages[0]
                    print(f"    First message content: {first_message.get('content')}")

                    # Check if property_id is mentioned in the first message
                    if property_id in first_message.get("content", ""):
                        print(
                            f"    ✅ Property ID {property_id} is mentioned in the first message"
                        )
                    else:
                        print(
                            f"    ❌ Property ID {property_id} is NOT mentioned in the first message"
                        )
            else:
                print(f"    Failed to get history for conversation {conv_id}")
else:
    print(f"No conversations found for user {user_id}")
