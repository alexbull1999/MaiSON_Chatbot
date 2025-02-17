#!/usr/bin/env python3
import sys
from pathlib import Path
import asyncio
import json

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.modules.data_integration.property_data_service import PropertyDataService

async def test_area_insights():
    """Test getting area insights for different locations."""
    service = PropertyDataService()
    
    # Test broad areas
    broad_areas = [
        "North London",
        "Manchester City Centre",
        "Birmingham Jewellery Quarter",
        "Edinburgh New Town"
    ]
    
    # Test specific postcodes
    specific_postcodes = [
        "SW1A 1AA",  # London - Westminster
        "M1 1AD",    # Manchester
        "B1 1BB",    # Birmingham
        "EH1 1BB"    # Edinburgh
    ]
    
    try:
        print("\nTesting broad area insights...")
        for area in broad_areas:
            print(f"\nAnalyzing {area}...")
            try:
                insights = await service.get_area_insights(area, is_broad_area=True)
                insights_dict = insights.model_dump()
                print(json.dumps(insights_dict, indent=2, default=str))
                
                # Basic validation
                print("\nValidation:")
                print(f"Market overview available: {bool(insights.market_overview)}")
                print(f"Area profile available: {bool(insights.area_profile)}")
                print(f"Demographics available: {bool(insights.area_profile.demographics)}")
                print(f"Transport summary available: {bool(insights.area_profile.transport_summary)}")
            except Exception as e:
                print(f"Error getting broad area insights: {str(e)}")
                continue
            
            # Add delay between requests
            await asyncio.sleep(2)
        
        print("\nTesting property-specific insights...")
        for postcode in specific_postcodes:
            print(f"\nAnalyzing area around {postcode}...")
            try:
                insights = await service.get_area_insights(postcode, is_broad_area=False)
                insights_dict = insights.model_dump()
                print(json.dumps(insights_dict, indent=2, default=str))
                
                # Basic validation
                print("\nValidation:")
                print(f"Property market data available: {bool(insights.market_overview)}")
                print(f"Location highlights available: {bool(insights.location_highlights)}")
                print(f"Nearest amenities: {len(insights.location_highlights.nearest_amenities)}")
                print(f"Nearest stations: {len(insights.location_highlights.nearest_stations)}")
                print(f"Nearest schools: {len(insights.location_highlights.nearest_schools)}")
            except Exception as e:
                print(f"Error getting property-specific insights for {postcode}: {str(e)}")
                continue
            
            # Add delay between requests
            await asyncio.sleep(2)
            
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_area_insights()) 