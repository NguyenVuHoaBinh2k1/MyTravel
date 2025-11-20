"""
Tests for Accommodation Agent.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import date

from app.agents.accommodation_agent import AccommodationAgent
from app.agents.base import AgentContext
from app.integrations.booking_api import HotelSearchResult


@pytest.fixture
def agent():
    """Create accommodation agent instance."""
    return AccommodationAgent()


@pytest.fixture
def sample_context():
    """Create sample agent context."""
    return AgentContext(
        user_id=1,
        trip_id=1,
        conversation_id=1,
        message="Tìm khách sạn ở Hà Nội",
        conversation_history=[],
        trip_data={
            "destination": "Hà Nội",
            "start_date": "2024-06-01",
            "end_date": "2024-06-05",
            "travelers_count": 2,
            "budget": 5000000
        }
    )


@pytest.fixture
def mock_hotels():
    """Create mock hotel results."""
    return [
        HotelSearchResult(
            name="Khách sạn Mường Thanh",
            type="Khách sạn 4 sao",
            address="123 Đường ABC, Hà Nội",
            latitude=21.0285,
            longitude=105.8542,
            price_per_night=1200000,
            rating=4.2,
            review_count=1250,
            amenities=["Wifi", "Hồ bơi"],
            booking_url="https://booking.com/test",
            source="mock"
        ),
        HotelSearchResult(
            name="Little Hanoi Homestay",
            type="Homestay",
            address="45 Phố cổ, Hà Nội",
            latitude=21.0275,
            longitude=105.8532,
            price_per_night=450000,
            rating=4.5,
            review_count=890,
            amenities=["Wifi"],
            booking_url="https://booking.com/test2",
            source="mock"
        ),
    ]


def test_agent_initialization(agent):
    """Test agent is properly initialized."""
    assert agent.name == "accommodation"
    assert "khách sạn" in agent.description.lower()


def test_get_system_prompt(agent, sample_context):
    """Test system prompt generation."""
    prompt = agent.get_system_prompt(sample_context)

    assert "khách sạn" in prompt.lower()
    assert "Hà Nội" in prompt
    assert "5000000" in prompt or "5.000.000" in prompt


def test_extract_entities(agent):
    """Test entity extraction from message."""
    message = "Tìm khách sạn ở Đà Nẵng cho 3 người, ngân sách 2 triệu/đêm"

    entities = agent.extract_entities(message)

    assert "Đà Nẵng" in entities.get("locations", [])
    assert entities.get("travelers") == 3
    assert "2" in entities.get("amounts", [])


def test_can_perform_search_with_location(agent, sample_context):
    """Test search validation with location."""
    entities = {"locations": ["Hà Nội"]}

    can_search = agent._can_perform_search(sample_context, entities)

    assert can_search is True


def test_can_perform_search_without_location(agent):
    """Test search validation without location."""
    context = AgentContext(
        user_id=1,
        message="Tìm khách sạn",
        conversation_history=[]
    )
    entities = {}

    can_search = agent._can_perform_search(context, entities)

    assert can_search is False


def test_format_hotels_for_ai(agent, mock_hotels):
    """Test hotel formatting for AI context."""
    formatted = agent._format_hotels_for_ai(mock_hotels)

    assert "Mường Thanh" in formatted
    assert "1,200,000" in formatted or "1200000" in formatted
    assert "4.2/5" in formatted
    assert "Wifi" in formatted


@pytest.mark.asyncio
async def test_process_with_hotels(agent, sample_context, mock_hotels):
    """Test processing with hotel results."""
    with patch.object(agent, '_search_hotels', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_hotels

        with patch.object(agent, 'call_ai', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = AsyncMock(
                content="Đây là 2 gợi ý khách sạn phù hợp cho bạn..."
            )

            response = await agent.process(sample_context)

            assert response.agent_type == "accommodation"
            assert response.data is not None
            assert "accommodations" in response.data
            assert len(response.data["accommodations"]) == 2


@pytest.mark.asyncio
async def test_process_info_gathering(agent):
    """Test processing when more info needed."""
    context = AgentContext(
        user_id=1,
        message="Tôi muốn đặt khách sạn",
        conversation_history=[]
    )

    with patch.object(agent, 'call_ai', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AsyncMock(
            content="Bạn muốn ở đâu và thời gian nào?"
        )

        response = await agent.process(context)

        assert response.agent_type == "accommodation"
        assert response.requires_followup is True


@pytest.mark.asyncio
async def test_process_error_handling(agent, sample_context):
    """Test error handling during processing."""
    with patch.object(agent, '_search_hotels', new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = Exception("API Error")

        response = await agent.process(sample_context)

        assert "sự cố" in response.message.lower()
        assert response.agent_type == "accommodation"
