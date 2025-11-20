"""
Trip service layer for business logic.
"""

from typing import Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.trip import (
    Trip, TripAccommodation, TripRestaurant,
    TripTransportation, TripActivity, TripExpense
)
from app.schemas.trip import (
    TripCreate, TripUpdate, AccommodationCreate, AccommodationUpdate,
    RestaurantCreate, RestaurantUpdate, TransportationCreate, TransportationUpdate,
    ActivityCreate, ActivityUpdate, ExpenseCreate, ExpenseUpdate
)
from app.core.logging import get_logger

logger = get_logger(__name__)


# Trip CRUD operations
async def create_trip(db: AsyncSession, user_id: int, trip_data: TripCreate) -> Trip:
    """Create a new trip."""
    trip = Trip(
        user_id=user_id,
        **trip_data.model_dump()
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)

    logger.info("trip_created", trip_id=trip.id, user_id=user_id)
    return trip


async def get_trip(db: AsyncSession, trip_id: int) -> Optional[Trip]:
    """Get trip by ID with all related data."""
    result = await db.execute(
        select(Trip)
        .options(
            selectinload(Trip.accommodations),
            selectinload(Trip.restaurants),
            selectinload(Trip.transportations),
            selectinload(Trip.activities),
            selectinload(Trip.expenses),
        )
        .where(Trip.id == trip_id)
    )
    return result.scalar_one_or_none()


async def get_user_trips(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    status: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> tuple[list[Trip], int]:
    """Get paginated list of user's trips."""
    # Base query
    query = select(Trip).where(Trip.user_id == user_id)

    # Apply filters
    if status:
        query = query.where(Trip.status == status)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    total_count = total.scalar()

    # Apply sorting
    sort_column = getattr(Trip, sort_by, Trip.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    trips = result.scalars().all()

    return list(trips), total_count


async def update_trip(db: AsyncSession, trip: Trip, trip_data: TripUpdate) -> Trip:
    """Update a trip."""
    update_data = trip_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(trip, field, value)

    await db.commit()
    await db.refresh(trip)

    logger.info("trip_updated", trip_id=trip.id)
    return trip


async def delete_trip(db: AsyncSession, trip: Trip) -> bool:
    """Delete a trip and all related data."""
    await db.delete(trip)
    await db.commit()

    logger.info("trip_deleted", trip_id=trip.id)
    return True


# Accommodation operations
async def add_accommodation(
    db: AsyncSession, trip_id: int, data: AccommodationCreate
) -> TripAccommodation:
    """Add accommodation to a trip."""
    accommodation = TripAccommodation(trip_id=trip_id, **data.model_dump())
    db.add(accommodation)
    await db.commit()
    await db.refresh(accommodation)
    return accommodation


async def update_accommodation(
    db: AsyncSession, accommodation_id: int, data: AccommodationUpdate
) -> Optional[TripAccommodation]:
    """Update an accommodation."""
    result = await db.execute(
        select(TripAccommodation).where(TripAccommodation.id == accommodation_id)
    )
    accommodation = result.scalar_one_or_none()
    if not accommodation:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(accommodation, field, value)

    await db.commit()
    await db.refresh(accommodation)
    return accommodation


async def delete_accommodation(db: AsyncSession, accommodation_id: int) -> bool:
    """Delete an accommodation."""
    result = await db.execute(
        select(TripAccommodation).where(TripAccommodation.id == accommodation_id)
    )
    accommodation = result.scalar_one_or_none()
    if not accommodation:
        return False

    await db.delete(accommodation)
    await db.commit()
    return True


# Restaurant operations
async def add_restaurant(
    db: AsyncSession, trip_id: int, data: RestaurantCreate
) -> TripRestaurant:
    """Add restaurant to a trip."""
    restaurant = TripRestaurant(trip_id=trip_id, **data.model_dump())
    db.add(restaurant)
    await db.commit()
    await db.refresh(restaurant)
    return restaurant


async def update_restaurant(
    db: AsyncSession, restaurant_id: int, data: RestaurantUpdate
) -> Optional[TripRestaurant]:
    """Update a restaurant."""
    result = await db.execute(
        select(TripRestaurant).where(TripRestaurant.id == restaurant_id)
    )
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(restaurant, field, value)

    await db.commit()
    await db.refresh(restaurant)
    return restaurant


async def delete_restaurant(db: AsyncSession, restaurant_id: int) -> bool:
    """Delete a restaurant."""
    result = await db.execute(
        select(TripRestaurant).where(TripRestaurant.id == restaurant_id)
    )
    restaurant = result.scalar_one_or_none()
    if not restaurant:
        return False

    await db.delete(restaurant)
    await db.commit()
    return True


# Transportation operations
async def add_transportation(
    db: AsyncSession, trip_id: int, data: TransportationCreate
) -> TripTransportation:
    """Add transportation to a trip."""
    transportation = TripTransportation(trip_id=trip_id, **data.model_dump())
    db.add(transportation)
    await db.commit()
    await db.refresh(transportation)
    return transportation


async def update_transportation(
    db: AsyncSession, transportation_id: int, data: TransportationUpdate
) -> Optional[TripTransportation]:
    """Update a transportation."""
    result = await db.execute(
        select(TripTransportation).where(TripTransportation.id == transportation_id)
    )
    transportation = result.scalar_one_or_none()
    if not transportation:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(transportation, field, value)

    await db.commit()
    await db.refresh(transportation)
    return transportation


async def delete_transportation(db: AsyncSession, transportation_id: int) -> bool:
    """Delete a transportation."""
    result = await db.execute(
        select(TripTransportation).where(TripTransportation.id == transportation_id)
    )
    transportation = result.scalar_one_or_none()
    if not transportation:
        return False

    await db.delete(transportation)
    await db.commit()
    return True


# Activity operations
async def add_activity(
    db: AsyncSession, trip_id: int, data: ActivityCreate
) -> TripActivity:
    """Add activity to a trip."""
    activity = TripActivity(trip_id=trip_id, **data.model_dump())
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return activity


async def update_activity(
    db: AsyncSession, activity_id: int, data: ActivityUpdate
) -> Optional[TripActivity]:
    """Update an activity."""
    result = await db.execute(
        select(TripActivity).where(TripActivity.id == activity_id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)

    await db.commit()
    await db.refresh(activity)
    return activity


async def delete_activity(db: AsyncSession, activity_id: int) -> bool:
    """Delete an activity."""
    result = await db.execute(
        select(TripActivity).where(TripActivity.id == activity_id)
    )
    activity = result.scalar_one_or_none()
    if not activity:
        return False

    await db.delete(activity)
    await db.commit()
    return True


# Expense operations
async def add_expense(
    db: AsyncSession, trip_id: int, data: ExpenseCreate
) -> TripExpense:
    """Add expense to a trip."""
    expense = TripExpense(trip_id=trip_id, **data.model_dump())
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


async def update_expense(
    db: AsyncSession, expense_id: int, data: ExpenseUpdate
) -> Optional[TripExpense]:
    """Update an expense."""
    result = await db.execute(
        select(TripExpense).where(TripExpense.id == expense_id)
    )
    expense = result.scalar_one_or_none()
    if not expense:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, field, value)

    await db.commit()
    await db.refresh(expense)
    return expense


async def delete_expense(db: AsyncSession, expense_id: int) -> bool:
    """Delete an expense."""
    result = await db.execute(
        select(TripExpense).where(TripExpense.id == expense_id)
    )
    expense = result.scalar_one_or_none()
    if not expense:
        return False

    await db.delete(expense)
    await db.commit()
    return True


async def get_budget_summary(db: AsyncSession, trip: Trip) -> dict:
    """Calculate budget summary for a trip."""
    # Get all expenses
    result = await db.execute(
        select(TripExpense).where(TripExpense.trip_id == trip.id)
    )
    expenses = result.scalars().all()

    # Calculate totals
    total_planned = sum(e.amount for e in expenses if e.is_planned)
    total_spent = sum(e.amount for e in expenses if not e.is_planned)

    # Calculate by category
    categories = {}
    for expense in expenses:
        if expense.category not in categories:
            categories[expense.category] = {"planned": 0, "actual": 0}
        if expense.is_planned:
            categories[expense.category]["planned"] += expense.amount
        else:
            categories[expense.category]["actual"] += expense.amount

    breakdown = [
        {"category": cat, **values}
        for cat, values in categories.items()
    ]

    return {
        "total_budget": trip.budget,
        "total_planned": total_planned,
        "total_spent": total_spent,
        "remaining": trip.budget - total_spent,
        "breakdown": breakdown,
    }
