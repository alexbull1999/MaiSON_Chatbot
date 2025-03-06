from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class Address(BaseModel):
    house_number: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PropertySpecs(BaseModel):
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    reception_rooms: Optional[int] = None
    square_footage: Optional[float] = None
    property_type: Optional[str] = None
    epc_rating: Optional[str] = None


class PropertyDetails(BaseModel):
    description: Optional[str] = None
    property_type: Optional[str] = None
    construction_year: Optional[int] = None
    parking_spaces: Optional[int] = None
    heating_type: Optional[str] = None


class PropertyFeatures(BaseModel):
    has_garden: Optional[bool] = None
    garden_size: Optional[float] = None
    has_garage: Optional[bool] = None
    parking_spaces: Optional[int] = None


class Property(BaseModel):
    property_id: str
    price: int
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    main_image_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    floorplan_url: Optional[str] = None
    created_at: Optional[str] = None
    last_updated: Optional[str] = None
    seller_id: Optional[str] = None
    status: Optional[str] = None
    address: Optional[Address] = None
    specs: Optional[PropertySpecs] = None
    details: Optional[PropertyDetails] = None
    features: Optional[PropertyFeatures] = None


class SavedProperty(BaseModel):
    property_id: str
    price: int
    main_image_url: Optional[str] = None
    saved_at: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    specs: Optional[Dict[str, Any]] = None


class Transaction(BaseModel):
    transaction_id: str
    offer_amount: int
    made_by: str
    created_at: str


class Negotiation(BaseModel):
    negotiation_id: str
    property_id: str
    buyer_id: str
    current_offer: int
    status: str
    last_offer_by: str
    awaiting_response_from: str
    created_at: str
    updated_at: str
    transactions: List[Transaction]


class UserRole(BaseModel):
    role_type: str


class UserInfo(BaseModel):
    user_id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None


class UserDashboard(BaseModel):
    user: UserInfo
    saved_properties: List[SavedProperty] = []
    listed_properties: List[Property] = []
    negotiations_as_buyer: List[Negotiation] = []
    negotiations_as_seller: List[Negotiation] = []
    roles: List[UserRole] = []
    total_saved_properties: int = 0
    total_properties_listed: int = 0
