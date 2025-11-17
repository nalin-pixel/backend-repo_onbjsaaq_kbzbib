"""
Database Schemas for Adventist Community Services app

Each Pydantic model corresponds to a MongoDB collection.
Collection name is the lowercase of the class name.

Example: Service -> "service" collection
         Booking -> "booking" collection
"""
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


class Service(BaseModel):
    """Community service offering schema"""
    title: str = Field(..., description="Service title, e.g., Food Pantry Pickup")
    description: str = Field(..., description="Short description of the service")
    category: str = Field(..., description="Category, e.g., Health, Education, Food, Transport")
    location: str = Field(..., description="General location or city")
    address: Optional[str] = Field(None, description="Street address if applicable")
    provider_name: str = Field(..., description="Name of church/organization/person offering the service")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    tags: List[str] = Field(default_factory=list, description="Keywords to help searching")
    booking_required: bool = Field(default=True, description="Whether users should book before using the service")


class Booking(BaseModel):
    """Booking/Request for a service"""
    service_id: str = Field(..., description="ID of the service being booked")
    full_name: str = Field(..., description="Name of the requester")
    email: Optional[EmailStr] = Field(None, description="Requester email")
    phone: Optional[str] = Field(None, description="Requester phone")
    preferred_date: Optional[str] = Field(None, description="Preferred date/time as free text")
    notes: Optional[str] = Field(None, description="Additional details")
    status: str = Field(default="pending", description="Booking status: pending/confirmed/cancelled")
