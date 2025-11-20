"""
Tests for Food & Dining Agent.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.food_agent import FoodAgent, VIETNAMESE_CUISINE
from app.agents.base import AgentContext
from app.integrations.google_maps import PlaceResult


@pytest.fixture
def agent():
    """Create food agent instance."""
    return FoodAgent()


@pytest.fixture
def sample_context():
    """Create sample agent context."""
    return AgentContext(
        user_id=1,
        trip_id=1,
        conversation_id=1,
        message="Tìm nhà hàng ở Hà Nội",
        conversation_history=[],
        trip_data={
            "destination": "Hà Nội",
            "travelers_count": 2,
        }
    )


@pytest.fixture
def mock_restaurants():
    """Create mock restaurant results."""
    return [
        PlaceResult(
            name="Phở Thìn Bờ Hồ",
            address="13 Lò Đúc, Hà Nội",
            latitude=21.0245,
            longitude=105.8512,
            rating=4.5,
            review_count=2500,
            price_level=1,
            types=["restaurant"],
            opening_hours="6:00 - 20:30",
        ),
        PlaceResult(
            name="Bún Chả Hương Liên",
            address="24 Lê Văn Hưu, Hà Nội",
            latitude=21.0155,
            longitude=105.8492,
            rating=4.3,
            review_count=3800,
            price_level=1,
            types=["restaurant"],
            opening_hours="8:00 - 20:00",
        ),
    ]


def test_agent_initialization(agent):
    """Test agent is properly initialized."""
    assert agent.name == "food"
    assert "nhà hàng" in agent.description.lower() or "ẩm thực" in agent.description.lower()


def test_vietnamese_cuisine_data():
    """Test Vietnamese cuisine knowledge base structure."""
    assert "north" in VIETNAMESE_CUISINE
    assert "central" in VIETNAMESE_CUISINE
    assert "south" in VIETNAMESE_CUISINE

    # Check north region
    north = VIETNAMESE_CUISINE["north"]
    assert "specialties" in north
    assert len(north["specialties"]) > 0
    assert "street_food" in north


def test_get_region_north(agent):
    """Test region detection for northern cities."""
    assert agent._get_region("Hà Nội") == "north"
    assert agent._get_region("Hanoi") == "north"
    assert agent._get_region("Hạ Long") == "north"


def test_get_region_central(agent):
    """Test region detection for central cities."""
    assert agent._get_region("Huế") == "central"
    assert agent._get_region("Đà Nẵng") == "central"
    assert agent._get_region("Hội An") == "central"


def test_get_region_south(agent):
    """Test region detection for southern cities."""
    assert agent._get_region("Hồ Chí Minh") == "south"
    assert agent._get_region("Sài Gòn") == "south"
    assert agent._get_region("Phú Quốc") == "south"


def test_determine_intent_restaurant(agent):
    """Test intent detection for restaurant search."""
    assert agent._determine_intent("Tìm nhà hàng gần đây") == "search_restaurant"
    assert agent._determine_intent("Ăn ở đâu ngon?") == "search_restaurant"
    assert agent._determine_intent("Quán ăn ngon") == "search_restaurant"


def test_determine_intent_dish(agent):
    """Test intent detection for dish recommendation."""
    assert agent._determine_intent("Món gì ngon ở Huế?") == "recommend_dish"
    assert agent._determine_intent("Đặc sản Đà Nẵng") == "recommend_dish"
    assert agent._determine_intent("Nên thử gì?") == "recommend_dish"


def test_extract_cuisine_type(agent):
    """Test cuisine type extraction."""
    assert agent._extract_cuisine_type("Tìm quán phở") == "phở"
    assert agent._extract_cuisine_type("Quán hải sản") == "hải sản"
    assert agent._extract_cuisine_type("Nhà hàng chay") == "chay"


def test_format_price_level(agent):
    """Test price level formatting."""
    assert agent._format_price_level(0) == "$"
    assert agent._format_price_level(1) == "$$"
    assert agent._format_price_level(2) == "$$$"
    assert agent._format_price_level(None) == "N/A"


def test_format_restaurants_for_ai(agent, mock_restaurants):
    """Test restaurant formatting for AI."""
    formatted = agent._format_restaurants_for_ai(mock_restaurants)

    assert "Phở Thìn" in formatted
    assert "4.5/5" in formatted
    assert "2500" in formatted


def test_get_system_prompt(agent, sample_context):
    """Test system prompt generation."""
    prompt = agent.get_system_prompt(sample_context)

    assert "ẩm thực" in prompt.lower() or "món ăn" in prompt.lower()
    assert "Hà Nội" in prompt


@pytest.mark.asyncio
async def test_process_restaurant_search(agent, sample_context, mock_restaurants):
    """Test processing restaurant search."""
    with patch.object(agent, '_search_restaurants', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_restaurants

        with patch.object(agent, 'call_ai', new_callable=AsyncMock) as mock_ai:
            mock_ai.return_value = AsyncMock(
                content="Đây là một số nhà hàng phở ngon ở Hà Nội..."
            )

            response = await agent.process(sample_context)

            assert response.agent_type == "food"
            assert response.data is not None
            assert "restaurants" in response.data


@pytest.mark.asyncio
async def test_process_dish_recommendation(agent):
    """Test processing dish recommendation."""
    context = AgentContext(
        user_id=1,
        message="Đặc sản Huế nên thử gì?",
        conversation_history=[],
        trip_data={"destination": "Huế"}
    )

    with patch.object(agent, 'call_ai', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = AsyncMock(
            content="Huế nổi tiếng với bún bò Huế, cơm hến..."
        )

        response = await agent.process(context)

        assert response.agent_type == "food"
        assert len(response.suggestions) > 0


@pytest.mark.asyncio
async def test_process_error_handling(agent, sample_context):
    """Test error handling during processing."""
    with patch.object(agent, '_search_restaurants', new_callable=AsyncMock) as mock_search:
        mock_search.side_effect = Exception("API Error")

        response = await agent.process(sample_context)

        assert "sự cố" in response.message.lower()
        assert response.agent_type == "food"
