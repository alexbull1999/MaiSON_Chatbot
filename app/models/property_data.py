from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

class PropertyPrice(BaseModel):
    average_price: float
    price_change_1y: float
    number_of_sales: int
    last_updated: datetime

class AgeGroups(BaseModel):
    young: str
    adult: str
    senior: str

class ResidentProfile(BaseModel):
    age_groups: AgeGroups
    income_level: str
    education_level: str

class Community(BaseModel):
    safety: str
    lifestyle: str

class Demographics(BaseModel):
    resident_profile: ResidentProfile
    amenities: List[str]
    community: Community

class TransportSummary(BaseModel):
    count: int
    average_distance: float

class AreaProfile(BaseModel):
    demographics: Optional[Dict]
    crime_rate: Optional[float]
    amenities_summary: Dict[str, int]
    transport_summary: Dict[str, Dict[str, float]]
    education: Dict[str, Dict[str, float]]

class Amenity(BaseModel):
    name: str
    type: str
    distance: float

class Station(BaseModel):
    name: str
    distance: float
    frequency: Optional[float]

class School(BaseModel):
    name: str
    type: str
    distance: float

class LocationHighlights(BaseModel):
    nearest_amenities: List[Amenity]
    nearest_stations: List[Station]
    nearest_schools: List[School]

class AreaInsights(BaseModel):
    market_overview: Optional[PropertyPrice]
    area_profile: AreaProfile

class PropertySpecificInsights(BaseModel):
    market_overview: Optional[PropertyPrice]
    location_highlights: LocationHighlights 