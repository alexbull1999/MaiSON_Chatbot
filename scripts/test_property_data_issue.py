import requests
from pprint import pprint

# Listings API URL (from PropertyContextModule)
LISTINGS_API_URL = "https://maison-api.jollybush-a62cec71.uksouth.azurecontainerapps.io"


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


def check_property_data_structure(property_data):
    """
    Check if the property data has all the required fields and structure
    """
    required_fields = [
        "id",
        "address.street",
        "address.city",
        "address.postcode",
        "specs.property_type",
        "specs.bedrooms",
        "specs.bathrooms",
        "specs.square_footage",
        "price",
    ]

    missing_fields = []

    for field in required_fields:
        parts = field.split(".")
        value = property_data

        try:
            for part in parts:
                value = value[part]

            # Check if the value is None or empty
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)
        except (KeyError, TypeError):
            missing_fields.append(field)

    return {
        "has_all_fields": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }


# Test properties
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

print("Testing property data structure for different properties:\n")

for property_info in test_properties:
    property_id = property_info["id"]
    description = property_info["description"]

    print(f"\n{'='*80}")
    print(f"Testing property: {property_id} - {description}")
    print(f"{'='*80}")

    # Get property details
    property_data = get_property_details(property_id)

    if property_data:
        print("\nProperty details found:")
        print(f"Property ID: {property_data.get('id')}")
        print(
            f"Address: {property_data.get('address', {}).get('street')}, {property_data.get('address', {}).get('city')}"
        )
        print(f"Property Type: {property_data.get('specs', {}).get('property_type')}")
        print(f"Bedrooms: {property_data.get('specs', {}).get('bedrooms')}")
        print(f"Bathrooms: {property_data.get('specs', {}).get('bathrooms')}")
        print(f"Square Footage: {property_data.get('specs', {}).get('square_footage')}")
        print(f"Price: £{property_data.get('price', 0):,}")

        # Check data structure
        check_result = check_property_data_structure(property_data)

        if check_result["has_all_fields"]:
            print("\n✅ Property data has all required fields")
        else:
            print("\n❌ Property data is missing required fields:")
            for field in check_result["missing_fields"]:
                print(f"  - {field}")

        # Check for id field specifically
        if property_data.get("id") is None:
            print("\n⚠️ WARNING: Property ID is missing in the API response!")
            print(
                "This will cause issues in the PropertyContextModule.get_or_fetch_property method"
            )
            print(
                "The code expects property_data['id'] to exist, but it's None or missing"
            )

        # Print raw data for inspection
        print("\nRaw property data:")
        pprint(property_data)
    else:
        print("Could not retrieve property details from listings API.")
