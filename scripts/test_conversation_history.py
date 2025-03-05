import requests

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"


# Function to get conversation history
def get_conversation_history(conversation_id):
    url = f"{BASE_URL}/conversations/property/{conversation_id}/history"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


# Check history for the first conversation of each property
conversation_ids = [1, 2]  # Updated to use the conversation IDs we just created

for conversation_id in conversation_ids:
    print(f"\nChecking history for conversation ID: {conversation_id}")
    history = get_conversation_history(conversation_id)

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
