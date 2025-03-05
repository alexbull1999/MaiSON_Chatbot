import requests

# Base URL for the chatbot API
BASE_URL = "http://localhost:8000/api/v1"

# Listings API URL (from PropertyContextModule)
LISTINGS_API_URL = "https://maison-api.jollybush-a62cec71.uksouth.azurecontainerapps.io"


def send_property_chat(
    message, user_id, property_id, role="buyer", counterpart_id="seller_123"
):
    """
    Send a message to a property chat
    """
    url = f"{BASE_URL}/conversations/property"

    payload = {
        "message": message,
        "user_id": user_id,
        "property_id": property_id,
        "role": role,
        "counterpart_id": counterpart_id,
    }

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None


def get_property_details(property_id):
    """
    Get details for a specific property from the listings API
    """
    url = f"{LISTINGS_API_URL}/api/properties/{property_id}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting property details: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception getting property details: {e}")
        return None


def get_similar_properties(location, property_type, bedrooms):
    """
    Get similar properties from the listings API
    """
    url = f"{LISTINGS_API_URL}/api/properties"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    params = {
        "property_type": property_type.lower() if property_type else None,
        "min_bedrooms": bedrooms,
        "city": location,
    }

    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    try:
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting similar properties: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception getting similar properties: {e}")
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


# Test with properties that work and don't work
test_properties = [
    {
        "id": "9c456f41-6bd3-4b06-8541-62f75243c874",  # The problematic property from your example
        "description": "Churchill, London - Has issues",
    },
    {
        "id": "765d1a18-5b63-4a5d-8dbd-ff2b8f37f768",  # Another property ID from your logs
        "description": "Oak Avenue, Manchester",
    },
]

# User ID from our previous tests
user_id = "7b9a6181-3303-4ea2-b505-dc293f9d2fbf"

print("Testing property context retrieval for different properties:\n")

for property_info in test_properties:
    property_id = property_info["id"]
    description = property_info["description"]

    print(f"\n{'='*80}")
    print(f"Testing property: {property_id} - {description}")
    print(f"{'='*80}")

    # 1. Try to get property details directly from listings API
    print("\n1. Attempting to get property details from listings API:")
    property_details = get_property_details(property_id)
    if property_details:
        print("Property details found:")
        print(f"Property ID: {property_details.get('id')}")
        print(
            f"Address: {property_details.get('address', {}).get('street')}, {property_details.get('address', {}).get('city')}"
        )
        print(
            f"Property Type: {property_details.get('specs', {}).get('property_type')}"
        )
        print(f"Bedrooms: {property_details.get('specs', {}).get('bedrooms')}")
        print(f"Bathrooms: {property_details.get('specs', {}).get('bathrooms')}")
        print(
            f"Square Footage: {property_details.get('specs', {}).get('square_footage')}"
        )
        print(f"Price: £{property_details.get('price', 0):,}")

        # 2. Try to get similar properties
        if property_details.get("address", {}).get("city") and property_details.get(
            "specs", {}
        ).get("property_type"):
            print("\n2. Attempting to get similar properties:")
            similar_properties = get_similar_properties(
                property_details.get("address", {}).get("city"),
                property_details.get("specs", {}).get("property_type"),
                property_details.get("specs", {}).get("bedrooms"),
            )

            if similar_properties and isinstance(similar_properties, list):
                print(f"Found {len(similar_properties)} similar properties")
                if len(similar_properties) > 0:
                    print(
                        f"First similar property: {similar_properties[0].get('address', {}).get('street')},"
                        f"{similar_properties[0].get('address', {}).get('city')}"
                    )
            else:
                print("No similar properties found or error in response")
    else:
        print("Could not retrieve property details from listings API.")

        # Try with a generic search to see if we can find any properties
        print("\nAttempting to find any properties in the listings API:")
        all_properties = get_similar_properties(None, None, None)
        if all_properties and isinstance(all_properties, list):
            print(f"Found {len(all_properties)} total properties in the listings API")
            if len(all_properties) > 0:
                print("Sample property IDs:")
                for i, prop in enumerate(all_properties[:5]):
                    print(
                        f"  {i+1}. {prop.get('id')} - {prop.get('address', {}).get('street')}, {prop.get('address', {}).get('city')}"
                    )
        else:
            print("Could not retrieve any properties from the listings API")
