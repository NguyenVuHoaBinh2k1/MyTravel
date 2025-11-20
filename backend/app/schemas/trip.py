"""
Trip Pydantic schemas for request/response validation.
"""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# Base schemas for nested objects
class AccommodationBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: str = Field(..., max_length=100)
    address: str = Field(..., max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    check_in_date: date
    check_out_date: date
    price_per_night: float = Field(..., gt=0)
    total_price: float = Field(..., gt=0)
    currency: str = "VND"
    booking_url: Optional[str] = None
    status: str = "suggested"
    rating: Optional[float] = Field(None, ge=0, le=5)
    image_url: Optional[str] = None
    amenities: Optional[list[str]] = None
    notes: Optional[str] = None


class AccommodationCreate(AccommodationBase):
    pass


class AccommodationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    booking_reference: Optional[str] = None
    notes: Optional[str] = None


class AccommodationResponse(AccommodationBase):
    id: int
    trip_id: int
    booking_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RestaurantBase(BaseModel):
    name: str = Field(..., max_length=255)
    cuisine_type: str = Field(..., max_length=100)
    address: str = Field(..., max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_range: str = Field(..., max_length=50)
    rating: Optional[float] = Field(None, ge=0, le=5)
    image_url: Optional[str] = None
    specialty_dishes: Optional[list[str]] = None
    opening_hours: Optional[str] = None
    phone: Optional[str] = None
    status: str = "suggested"
    notes: Optional[str] = None


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class RestaurantResponse(RestaurantBase):
    id: int
    trip_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransportationBase(BaseModel):
    type: str = Field(..., max_length=50)
    from_location: str = Field(..., max_length=255)
    to_location: str = Field(..., max_length=255)
    departure_time: datetime
    arrival_time: datetime
    provider: Optional[str] = None
    price: float = Field(..., gt=0)
    currency: str = "VND"
    status: str = "suggested"
    notes: Optional[str] = None


class TransportationCreate(TransportationBase):
    pass


class TransportationUpdate(BaseModel):
    status: Optional[str] = None
    booking_reference: Optional[str] = None
    notes: Optional[str] = None


class TransportationResponse(TransportationBase):
    id: int
    trip_id: int
    booking_reference: Optional[str] = None
    booking_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActivityBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    location: str = Field(..., max_length=500)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    day_number: int = Field(..., ge=1)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    duration_minutes: int = Field(..., gt=0)
    price: Optional[float] = None
    currency: str = "VND"
    category: str = Field(..., max_length=100)
    status: str = "suggested"
    rating: Optional[float] = Field(None, ge=0, le=5)
    image_url: Optional[str] = None
    notes: Optional[str] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    day_number: Optional[int] = Field(None, ge=1)
    start_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    status: Optional[str] = None
    notes: Optional[str] = None


class ActivityResponse(ActivityBase):
    id: int
    trip_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseBase(BaseModel):
    category: str = Field(..., max_length=100)
    description: str = Field(..., max_length=255)
    amount: float = Field(..., gt=0)
    currency: str = "VND"
    date: date
    is_planned: bool = True
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    is_planned: Optional[bool] = None
    notes: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    id: int
    trip_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Trip schemas
class TripBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    destination: str = Field(..., min_length=1, max_length=255)
    start_date: date
    end_date: date
    budget: float = Field(..., gt=0)
    currency: str = "VND"
    travelers_count: int = Field(1, ge=1)
    notes: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    destination: Optional[str] = Field(None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    travelers_count: Optional[int] = Field(None, ge=1)
    status: Optional[str] = None
    notes: Optional[str] = None


class TripResponse(TripBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripDetailResponse(TripResponse):
    """Full trip response with all related data."""
    accommodations: list[AccommodationResponse] = []
    restaurants: list[RestaurantResponse] = []
    transportations: list[TransportationResponse] = []
    activities: list[ActivityResponse] = []
    expenses: list[ExpenseResponse] = []

    class Config:
        from_attributes = True


class TripListResponse(BaseModel):
    """Paginated list of trips."""
    items: list[TripResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BudgetSummary(BaseModel):
    """Budget summary for a trip."""
    total_budget: float
    total_planned: float
    total_spent: float
    remaining: float
    breakdown: list[dict]
