"""
Trip management API endpoints.
"""

import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.trip import (
    TripCreate, TripUpdate, TripResponse, TripDetailResponse, TripListResponse,
    AccommodationCreate, AccommodationUpdate, AccommodationResponse,
    RestaurantCreate, RestaurantUpdate, RestaurantResponse,
    TransportationCreate, TransportationUpdate, TransportationResponse,
    ActivityCreate, ActivityUpdate, ActivityResponse,
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, BudgetSummary
)
from app.services import trip_service

router = APIRouter()


# Trip CRUD endpoints
@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TripResponse:
    """Create a new trip."""
    trip = await trip_service.create_trip(db, current_user.id, trip_data)
    return TripResponse.model_validate(trip)


@router.get("", response_model=TripListResponse)
async def get_trips(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TripListResponse:
    """Get user's trips with pagination and filtering."""
    trips, total = await trip_service.get_user_trips(
        db, current_user.id, page, page_size, status, sort_by, sort_order
    )

    return TripListResponse(
        items=[TripResponse.model_validate(t) for t in trips],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{trip_id}", response_model=TripDetailResponse)
async def get_trip(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TripDetailResponse:
    """Get trip details with all related data."""
    trip = await trip_service.get_trip(db, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    if trip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this trip",
        )

    return TripDetailResponse.model_validate(trip)


@router.patch("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: int,
    trip_data: TripUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TripResponse:
    """Update a trip."""
    trip = await trip_service.get_trip(db, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    if trip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this trip",
        )

    updated_trip = await trip_service.update_trip(db, trip, trip_data)
    return TripResponse.model_validate(updated_trip)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a trip."""
    trip = await trip_service.get_trip(db, trip_id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found",
        )

    if trip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this trip",
        )

    await trip_service.delete_trip(db, trip)


# Accommodation endpoints
@router.post("/{trip_id}/accommodations", response_model=AccommodationResponse, status_code=status.HTTP_201_CREATED)
async def add_accommodation(
    trip_id: int,
    data: AccommodationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AccommodationResponse:
    """Add accommodation to a trip."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    accommodation = await trip_service.add_accommodation(db, trip_id, data)
    return AccommodationResponse.model_validate(accommodation)


@router.patch("/{trip_id}/accommodations/{accommodation_id}", response_model=AccommodationResponse)
async def update_accommodation(
    trip_id: int,
    accommodation_id: int,
    data: AccommodationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AccommodationResponse:
    """Update an accommodation."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    accommodation = await trip_service.update_accommodation(db, accommodation_id, data)
    if not accommodation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")

    return AccommodationResponse.model_validate(accommodation)


@router.delete("/{trip_id}/accommodations/{accommodation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_accommodation(
    trip_id: int,
    accommodation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an accommodation."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    if not await trip_service.delete_accommodation(db, accommodation_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accommodation not found")


# Restaurant endpoints
@router.post("/{trip_id}/restaurants", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def add_restaurant(
    trip_id: int,
    data: RestaurantCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RestaurantResponse:
    """Add restaurant to a trip."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    restaurant = await trip_service.add_restaurant(db, trip_id, data)
    return RestaurantResponse.model_validate(restaurant)


@router.patch("/{trip_id}/restaurants/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    trip_id: int,
    restaurant_id: int,
    data: RestaurantUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RestaurantResponse:
    """Update a restaurant."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    restaurant = await trip_service.update_restaurant(db, restaurant_id, data)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")

    return RestaurantResponse.model_validate(restaurant)


@router.delete("/{trip_id}/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(
    trip_id: int,
    restaurant_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a restaurant."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    if not await trip_service.delete_restaurant(db, restaurant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")


# Activity endpoints
@router.post("/{trip_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def add_activity(
    trip_id: int,
    data: ActivityCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ActivityResponse:
    """Add activity to a trip."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    activity = await trip_service.add_activity(db, trip_id, data)
    return ActivityResponse.model_validate(activity)


@router.patch("/{trip_id}/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    trip_id: int,
    activity_id: int,
    data: ActivityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ActivityResponse:
    """Update an activity."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    activity = await trip_service.update_activity(db, activity_id, data)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    return ActivityResponse.model_validate(activity)


@router.delete("/{trip_id}/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    trip_id: int,
    activity_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an activity."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    if not await trip_service.delete_activity(db, activity_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")


# Expense endpoints
@router.post("/{trip_id}/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def add_expense(
    trip_id: int,
    data: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    """Add expense to a trip."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    expense = await trip_service.add_expense(db, trip_id, data)
    return ExpenseResponse.model_validate(expense)


@router.patch("/{trip_id}/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    trip_id: int,
    expense_id: int,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ExpenseResponse:
    """Update an expense."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    expense = await trip_service.update_expense(db, expense_id, data)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    return ExpenseResponse.model_validate(expense)


@router.delete("/{trip_id}/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    trip_id: int,
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an expense."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    if not await trip_service.delete_expense(db, expense_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")


# Budget summary endpoint
@router.get("/{trip_id}/budget", response_model=BudgetSummary)
async def get_budget_summary(
    trip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BudgetSummary:
    """Get budget summary for a trip."""
    trip = await trip_service.get_trip(db, trip_id)
    if not trip or trip.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    summary = await trip_service.get_budget_summary(db, trip)
    return BudgetSummary(**summary)
