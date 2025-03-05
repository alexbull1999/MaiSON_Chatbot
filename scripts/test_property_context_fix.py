import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.abspath("."))

# Import the PropertyContextModule
from app.modules.property_context.property_context_module import PropertyContextModule


async def test_property_context():
    """Test the PropertyContextModule with our fix."""
    property_module = PropertyContextModule()

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

    print("Testing property context module with our fix:\n")

    for property_info in test_properties:
        property_id = property_info["id"]
        description = property_info["description"]

        print(f"\n{'='*80}")
        print(f"Testing property: {property_id} - {description}")
        print(f"{'='*80}")

        # Get property details using the module
        property_data = await property_module.get_or_fetch_property(property_id)

        if property_data:
            print("\nProperty instance created successfully:")
            print(f"Property ID: {property_data.id}")
            print(f"Name: {property_data.name}")
            print(f"Type: {property_data.type}")
            print(f"Location: {property_data.location}")
            print(f"Price: {property_data.details.get('formatted_price')}")
            print(f"Address: {property_data.details.get('formatted_address')}")
            print(
                f"Square Footage: {property_data.details.get('specs', {}).get('square_footage')}"
            )

            # Test handling an inquiry
            print("\nTesting property inquiry:")
            inquiry = "How big is this property?"
            context = {"property_id": property_id}

            response = await property_module.handle_inquiry(inquiry, context)
            print(f"Response: {response}")
        else:
            print("Failed to create property instance.")


# Run the test
if __name__ == "__main__":
    asyncio.run(test_property_context())
