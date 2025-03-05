import requests

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"


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
    general_conversations_list = response.get("general_conversations", [])

    print(
        f"Found {len(property_conversations_list)} property conversations for user {user_id}"
    )
    print(
        f"Found {len(general_conversations_list)} general conversations for user {user_id}"
    )

    # Group property conversations by property_id
    property_conversations = {}

    for conv in property_conversations_list:
        property_id = conv.get("property_id")
        if property_id not in property_conversations:
            property_conversations[property_id] = []

        property_conversations[property_id].append(conv)

    # Print conversations grouped by property_id
    print("\nProperty conversations grouped by property_id:")
    for property_id, convs in property_conversations.items():
        print(f"\nProperty ID: {property_id}")
        print(f"Number of conversations: {len(convs)}")

        for i, conv in enumerate(convs, 1):
            print(f"\n  Conversation {i}:")
            print(f"    ID: {conv.get('id')}")
            print(f"    Session ID: {conv.get('session_id')}")
            print(f"    Role: {conv.get('role')}")
            print(f"    Status: {conv.get('conversation_status')}")
            print(f"    Started at: {conv.get('started_at')}")
            print(f"    Last message at: {conv.get('last_message_at')}")
else:
    print(f"No conversations found for user {user_id}")
