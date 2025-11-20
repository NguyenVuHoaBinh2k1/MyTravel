"""
Tests for Trip API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.trip import Trip


@pytest.fixture
async def test_trip(db_session: AsyncSession, test_user: User) -> Trip:
    """Create a test trip."""
    trip = Trip(
        user_id=test_user.id,
        title="Test Trip to Hanoi",
        destination="Hanoi",
        start_date="2024-06-01",
        end_date="2024-06-07",
        budget=5000000,
        currency="VND",
        travelers_count=2,
    )
    db_session.add(trip)
    await db_session.commit()
    await db_session.refresh(trip)
    return trip


@pytest.mark.asyncio
async def test_create_trip(client: AsyncClient, auth_headers: dict):
    """Test creating a new trip."""
    response = await client.post(
        "/api/v1/trips",
        headers=auth_headers,
        json={
            "title": "My Vietnam Trip",
            "destination": "Ho Chi Minh City",
            "start_date": "2024-07-01",
            "end_date": "2024-07-10",
            "budget": 10000000,
            "currency": "VND",
            "travelers_count": 1,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Vietnam Trip"
    assert data["destination"] == "Ho Chi Minh City"
    assert data["budget"] == 10000000
    assert data["status"] == "planning"


@pytest.mark.asyncio
async def test_create_trip_invalid_dates(client: AsyncClient, auth_headers: dict):
    """Test creating trip with end date before start date fails."""
    response = await client.post(
        "/api/v1/trips",
        headers=auth_headers,
        json={
            "title": "Invalid Trip",
            "destination": "Hanoi",
            "start_date": "2024-07-10",
            "end_date": "2024-07-01",
            "budget": 5000000,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_trips(client: AsyncClient, auth_headers: dict, test_trip: Trip):
    """Test getting user's trips."""
    response = await client.get("/api/v1/trips", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == test_trip.title


@pytest.mark.asyncio
async def test_get_trips_pagination(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
):
    """Test trips pagination."""
    # Create multiple trips
    for i in range(15):
        trip = Trip(
            user_id=test_user.id,
            title=f"Trip {i}",
            destination="Hanoi",
            start_date="2024-06-01",
            end_date="2024-06-07",
            budget=1000000,
        )
        db_session.add(trip)
    await db_session.commit()

    # Get first page
    response = await client.get(
        "/api/v1/trips?page=1&page_size=10", headers=auth_headers
    )
    data = response.json()
    assert data["total"] == 15
    assert len(data["items"]) == 10
    assert data["pages"] == 2

    # Get second page
    response = await client.get(
        "/api/v1/trips?page=2&page_size=10", headers=auth_headers
    )
    data = response.json()
    assert len(data["items"]) == 5


@pytest.mark.asyncio
async def test_get_trip_detail(
    client: AsyncClient, auth_headers: dict, test_trip: Trip
):
    """Test getting trip details."""
    response = await client.get(
        f"/api/v1/trips/{test_trip.id}", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == test_trip.title
    assert "accommodations" in data
    assert "restaurants" in data
    assert "activities" in data


@pytest.mark.asyncio
async def test_get_trip_not_found(client: AsyncClient, auth_headers: dict):
    """Test getting nonexistent trip returns 404."""
    response = await client.get("/api/v1/trips/999", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_trip(
    client: AsyncClient, auth_headers: dict, test_trip: Trip
):
    """Test updating a trip."""
    response = await client.patch(
        f"/api/v1/trips/{test_trip.id}",
        headers=auth_headers,
        json={
            "title": "Updated Trip Title",
            "budget": 7000000,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Trip Title"
    assert data["budget"] == 7000000


@pytest.mark.asyncio
async def test_delete_trip(
    client: AsyncClient, auth_headers: dict, test_trip: Trip
):
    """Test deleting a trip."""
    response = await client.delete(
        f"/api/v1/trips/{test_trip.id}", headers=auth_headers
    )

    assert response.status_code == 204

    # Verify trip is deleted
    response = await client.get(
        f"/api/v1/trips/{test_trip.id}", headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_accommodation(
    client: AsyncClient, auth_headers: dict, test_trip: Trip
):
    """Test adding accommodation to a trip."""
    response = await client.post(
        f"/api/v1/trips/{test_trip.id}/accommodations",
        headers=auth_headers,
        json={
            "name": "Hanoi Hotel",
            "type": "hotel",
            "address": "123 Hoan Kiem, Hanoi",
            "check_in_date": "2024-06-01",
            "check_out_date": "2024-06-07",
            "price_per_night": 500000,
            "total_price": 3000000,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Hanoi Hotel"
    assert data["total_price"] == 3000000


@pytest.mark.asyncio
async def test_add_expense(
    client: AsyncClient, auth_headers: dict, test_trip: Trip
):
    """Test adding expense to a trip."""
    response = await client.post(
        f"/api/v1/trips/{test_trip.id}/expenses",
        headers=auth_headers,
        json={
            "category": "food",
            "description": "Dinner at local restaurant",
            "amount": 200000,
            "date": "2024-06-02",
            "is_planned": False,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "food"
    assert data["amount"] == 200000


@pytest.mark.asyncio
async def test_get_budget_summary(
    client: AsyncClient, auth_headers: dict, test_trip: Trip, db_session: AsyncSession
):
    """Test getting budget summary."""
    # Add some expenses first
    from app.models.trip import TripExpense

    expenses = [
        TripExpense(
            trip_id=test_trip.id,
            category="accommodation",
            description="Hotel",
            amount=3000000,
            date="2024-06-01",
            is_planned=True,
        ),
        TripExpense(
            trip_id=test_trip.id,
            category="food",
            description="Meals",
            amount=500000,
            date="2024-06-02",
            is_planned=False,
        ),
    ]
    for exp in expenses:
        db_session.add(exp)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/trips/{test_trip.id}/budget", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_budget"] == test_trip.budget
    assert data["total_planned"] == 3000000
    assert data["total_spent"] == 500000
    assert data["remaining"] == test_trip.budget - 500000
