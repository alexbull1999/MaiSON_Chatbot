import httpx
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PropertyListingsAPIClient:
    """Client for interacting with the MaiSON property listings API."""

    def __init__(self, base_url: str = "https://maison-api.jollybush-a62cec71.uksouth.azurecontainerapps.io"):
        self.base_url = base_url
        self.timeout = 10.0  # seconds

    async def get_all_properties(self) -> List[Dict[str, Any]]:
        """
        Fetch all available properties from the listings API.

        Returns:
            List of property dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/properties")
                response.raise_for_status()

                properties = response.json()
                logger.info(f"Retrieved {len(properties)} properties from listings API")
                return properties

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred while fetching properties: {e}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Request error occurred while fetching properties: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error occurred while fetching properties: {e}")
            return []

    async def get_user_dashboard(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a user's dashboard data including saved properties.

        Args:
            user_id: The UUID of the user

        Returns:
            User dashboard data or None if an error occurs
        """
        if not user_id:
            logger.warning("No user_id provided for dashboard request")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/users/{user_id}/dashboard")
                response.raise_for_status()

                dashboard = response.json()
                logger.info(f"Retrieved dashboard for user {user_id} with {len(dashboard.get('saved_properties', []))} saved properties")
                return dashboard

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred while fetching user dashboard: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error occurred while fetching user dashboard: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error occurred while fetching user dashboard: {e}")
            return None

    async def get_property_details(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed information about a specific property.

        Args:
            property_id: The UUID of the property

        Returns:
            Property details or None if an error occurs
        """
        if not property_id:
            logger.warning("No property_id provided for property details request")
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/properties/{property_id}")
                response.raise_for_status()

                property_details = response.json()
                logger.info(f"Retrieved details for property {property_id}")
                return property_details

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred while fetching property details: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error occurred while fetching property details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error occurred while fetching property details: {e}")
            return None
