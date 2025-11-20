"""Integration tests for chat workflow."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.trip import Trip
from app.models.conversation import Conversation
from app.services import user_service, trip_service
from app.schemas.user import UserCreate
from app.schemas.trip import TripCreate
from app.core.security import create_access_token


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    user_data = UserCreate(
        email="test@example.com",
        password="testpass123",
        full_name="Test User"
    )
    user = await user_service.create_user(db, user_data)
    return user


@pytest.fixture
async def test_trip(db: AsyncSession, test_user: User) -> Trip:
    """Create a test trip."""
    trip_data = TripCreate(
        title="Ha Noi Trip",
        destination="Ha Noi",
        start_date="2024-06-01",
        end_date="2024-06-05",
        travelers_count=2,
        budget=5000000,
        currency="VND"
    )
    trip = await trip_service.create_trip(db, test_user.id, trip_data)
    return trip


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Get auth headers for test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


class TestChatWorkflow:
    """Integration tests for the chat workflow."""

    @pytest.mark.asyncio
    async def test_create_conversation_and_chat(
        self,
        test_user: User,
        test_trip: Trip,
        auth_headers: dict
    ):
        """Test creating a conversation and sending a chat message."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Send a chat message without conversation_id (should create one)
            response = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Tim khach san o Ha Noi",
                    "trip_id": test_trip.id
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "conversation_id" in data
            assert "message" in data
            assert data["message"]["role"] == "assistant"
            assert data["message"]["content"] != ""
            assert data.get("agent_type") is not None
            assert "suggestions" in data

    @pytest.mark.asyncio
    async def test_chat_with_accommodation_intent(
        self,
        test_user: User,
        test_trip: Trip,
        auth_headers: dict
    ):
        """Test chat with accommodation intent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Goi y khach san 3 sao gan Pho Co",
                    "trip_id": test_trip.id
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should route to accommodation agent
            assert data.get("agent_type") == "accommodation"
            assert data["message"]["content"] != ""

    @pytest.mark.asyncio
    async def test_chat_with_food_intent(
        self,
        test_user: User,
        test_trip: Trip,
        auth_headers: dict
    ):
        """Test chat with food intent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Mon an dac san Ha Noi toi nen thu",
                    "trip_id": test_trip.id
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should route to food agent
            assert data.get("agent_type") == "food"
            assert data["message"]["content"] != ""

    @pytest.mark.asyncio
    async def test_chat_with_transport_intent(
        self,
        test_user: User,
        test_trip: Trip,
        auth_headers: dict
    ):
        """Test chat with transport intent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Chuyen bay tu Sai Gon di Ha Noi",
                    "trip_id": test_trip.id
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should route to transport agent
            assert data.get("agent_type") == "transport"
            assert data["message"]["content"] != ""

    @pytest.mark.asyncio
    async def test_chat_with_budget_intent(
        self,
        test_user: User,
        test_trip: Trip,
        auth_headers: dict
    ):
        """Test chat with budget intent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Uoc tinh chi phi cho chuyen di 3 ngay",
                    "trip_id": test_trip.id
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should route to budget agent
            assert data.get("agent_type") == "budget"
            assert data["message"]["content"] != ""

    @pytest.mark.asyncio
    async def test_chat_with_itinerary_intent(
        self,
        test_user: User,
        test_trip: Trip,
        auth_headers: dict
    ):
        """Test chat with itinerary intent."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Lap lich trinh du lich 3 ngay o Ha Noi",
                    "trip_id": test_trip.id
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Should route to itinerary agent
            assert data.get("agent_type") == "itinerary"
            assert data["message"]["content"] != ""

    @pytest.mark.asyncio
    async def test_chat_conversation_history(
        self,
        test_user: User,
        test_trip: Trip,
        auth_headers: dict
    ):
        """Test that conversation history is maintained."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First message
            response1 = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Xin chao",
                    "trip_id": test_trip.id
                }
            )

            assert response1.status_code == 200
            data1 = response1.json()
            conversation_id = data1["conversation_id"]

            # Second message in same conversation
            response2 = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Tim khach san",
                    "conversation_id": conversation_id
                }
            )

            assert response2.status_code == 200
            data2 = response2.json()

            # Should be same conversation
            assert data2["conversation_id"] == conversation_id

            # Get conversation messages
            response3 = await client.get(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=auth_headers
            )

            assert response3.status_code == 200
            messages = response3.json()

            # Should have 4 messages (2 user, 2 assistant)
            assert len(messages) >= 4
            assert messages[0]["role"] == "user"
            assert messages[0]["content"] == "Xin chao"
            assert messages[2]["role"] == "user"
            assert messages[2]["content"] == "Tim khach san"

    @pytest.mark.asyncio
    async def test_chat_without_trip(
        self,
        test_user: User,
        auth_headers: dict
    ):
        """Test chat without a trip context."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Toi muon di du lich Viet Nam"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "conversation_id" in data
            assert "message" in data
            assert data["message"]["content"] != ""

    @pytest.mark.asyncio
    async def test_chat_unauthorized(self):
        """Test chat without authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/conversations/chat",
                json={
                    "message": "Test message"
                }
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_chat_with_invalid_trip(
        self,
        test_user: User,
        auth_headers: dict
    ):
        """Test chat with non-existent trip."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/conversations/chat",
                headers=auth_headers,
                json={
                    "message": "Test message",
                    "trip_id": 99999  # Non-existent trip
                }
            )

            # Should still work, just without trip context
            assert response.status_code == 200
