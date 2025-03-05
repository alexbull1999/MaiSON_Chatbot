import requests

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

# Use the same test user ID from the previous run
TEST_USER_ID = "7b9a6181-3303-4ea2-b505-dc293f9d2fbf"
print(f"Using test user ID: {TEST_USER_ID}")

# Different property IDs to test with
PROPERTY_IDS = ["property_123", "property_456", "property_789"]


# Function to send a property chat message
def send_property_chat(
    message, user_id, property_id, role="buyer", counterpart_id="seller_123"
):
    url = f"{BASE_URL}/chat/property"
    payload = {
        "message": message,
        "user_id": user_id,
        "property_id": property_id,
        "role": role,
        "counterpart_id": counterpart_id,
    }

    headers = {"Content-Type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


# Function to get all conversations for a user
def get_user_conversations(user_id):
    url = f"{BASE_URL}/conversations/user/{user_id}"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


# Send additional messages for each property ID
for property_id in PROPERTY_IDS:
    print(f"\nSending another message for property: {property_id}")
    response = send_property_chat(
        message=f"I'd like to schedule a viewing for {property_id}. Is it available this weekend?",
        user_id=TEST_USER_ID,
        property_id=property_id,
    )

    if response:
        print(f"Response received, conversation ID: {response.get('conversation_id')}")
    else:
        print("Failed to send message")

# Get all conversations for the user
print("\nRetrieving all conversations for the user...")
conversations = get_user_conversations(TEST_USER_ID)

if conversations:
    property_conversations = conversations.get("property_conversations", [])
    print(f"\nFound {len(property_conversations)} property conversations")

    # Group conversations by property_id
    grouped_conversations = {}
    for conv in property_conversations:
        property_id = conv.get("property_id")
        if property_id not in grouped_conversations:
            grouped_conversations[property_id] = []
        grouped_conversations[property_id].append(conv)

    # Print the grouped conversations
    print("\nGrouped conversations by property_id:")
    for property_id, convs in grouped_conversations.items():
        print(f"\nProperty ID: {property_id}")
        print(f"Number of conversations: {len(convs)}")
        for i, conv in enumerate(convs):
            print(f"  Conversation {i+1}:")
            print(f"    ID: {conv.get('id')}")
            print(f"    Session ID: {conv.get('session_id')}")
            print(f"    Role: {conv.get('role')}")
            print(f"    Status: {conv.get('conversation_status')}")
else:
    print("Failed to retrieve conversations")
