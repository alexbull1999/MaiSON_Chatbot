import aiohttp
import re
from bs4 import BeautifulSoup
from typing import Dict, Optional
from datetime import datetime

class RightmoveScraper:
    """Simple scraper for Rightmove property data."""
    
    def __init__(self):
        self.base_url = "https://www.rightmove.co.uk"
        self.search_url = f"{self.base_url}/property-for-sale/find.html"
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session with appropriate headers."""
        return aiohttp.ClientSession(headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

    async def get_area_prices(self, location: str) -> Dict:
        """
        Get average property prices and trends for an area.
        
        Args:
            location: Area name or postcode
            
        Returns:
            Dictionary containing average price and price trends
        """
        try:
            params = {
                "searchType": "SALE",
                "locationIdentifier": "",
                "insId": "1",
                "radius": "0.0",
                "minPrice": "",
                "maxPrice": "",
                "minBedrooms": "",
                "maxBedrooms": "",
                "displayPropertyType": "",
                "maxDaysSinceAdded": "",
                "sortByPriceDescending": "",
                "keywords": location,
                "_includeSSTC": "on"
            }
            
            async with self._get_session() as session:
                async with session.get(self.search_url, params=params) as response:
                    if response.status != 200:
                        return self._get_default_prices()
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract average price
                    avg_price = 0.0
                    price_elements = soup.find_all(class_=re.compile("propertyCard-priceValue"))
                    if price_elements:
                        prices = []
                        for elem in price_elements:
                            try:
                                # Clean up price text and convert to number
                                price_text = elem.text.strip().replace('£', '').replace(',', '')
                                if 'pcm' in price_text.lower():
                                    continue  # Skip rental prices
                                price = float(re.sub(r'[^\d.]', '', price_text))
                                if price > 0:
                                    prices.append(price)
                            except (ValueError, AttributeError):
                                continue
                        
                        if prices:
                            avg_price = sum(prices) / len(prices)
                    
                    # Extract price trends if available
                    price_change = 0.0
                    trend_elem = soup.find(text=re.compile(r"Price change in last|Average price change"))
                    if trend_elem:
                        try:
                            trend_text = trend_elem.strip()
                            price_change = float(re.findall(r'[-+]?\d*\.\d+|\d+', trend_text)[0])
                        except (IndexError, ValueError):
                            pass
                    
                    return {
                        "average_price": round(avg_price, 2),
                        "price_change": price_change,
                        "last_updated": datetime.utcnow().isoformat(),
                        "source": "rightmove"
                    }
                    
        except Exception as e:
            print(f"Error scraping Rightmove: {str(e)}")
            return self._get_default_prices()
    
    def _get_default_prices(self) -> Dict:
        """Return default price data structure."""
        return {
            "average_price": 0.0,
            "price_change": 0.0,
            "last_updated": datetime.utcnow().isoformat(),
            "source": "rightmove"
        } 