"""Tests for specific agent implementations."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.base import AgentContext, AgentResponse
from app.agents.transport_agent import TransportAgent, TRANSPORT_OPTIONS
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.budget_agent import BudgetAgent, COST_REFERENCE
from app.agents.accommodation_agent import AccommodationAgent
from app.agents.food_agent import FoodAgent
from app.ai_providers import AIMessage


class TestTransportAgent:
    """Tests for TransportAgent."""

    @pytest.fixture
    def agent(self):
        return TransportAgent()

    def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "transport"
        assert "di chuyển" in agent.description.lower() or "transport" in agent.description.lower()

    def test_determine_inter_city_intent(self, agent):
        """Test determining inter-city transport intent."""
        assert agent._determine_transport_intent("Tim chuyen bay di Da Nang") == "inter_city"
        assert agent._determine_transport_intent("Xe khach tu Ha Noi di Sai Gon") == "inter_city"
        assert agent._determine_transport_intent("Tau di Hue") == "inter_city"

    def test_determine_local_intent(self, agent):
        """Test determining local transport intent."""
        assert agent._determine_transport_intent("Gia Grab trong thanh pho") == "local"
        assert agent._determine_transport_intent("Thue xe may") == "local"
        assert agent._determine_transport_intent("Taxi san bay") == "local"

    def test_determine_general_intent(self, agent):
        """Test determining general intent."""
        assert agent._determine_transport_intent("Hello") == "general"

    def test_format_transport_options(self, agent):
        """Test formatting transport options."""
        result = agent._format_transport_options("inter_city")
        assert "Flight" in result or "Bus" in result or "Train" in result

        result = agent._format_transport_options("local")
        assert "Grab" in result or "Taxi" in result

    def test_transport_options_data(self):
        """Test transport options data structure."""
        assert "inter_city" in TRANSPORT_OPTIONS
        assert "local" in TRANSPORT_OPTIONS
        assert "flight" in TRANSPORT_OPTIONS["inter_city"]
        assert "grab" in TRANSPORT_OPTIONS["local"]

    @pytest.mark.asyncio
    async def test_process(self, agent):
        """Test agent processing."""
        context = AgentContext(
            user_id="user-123",
            message="Tim chuyen bay di Da Nang"
        )

        # Mock AI call
        mock_response = MagicMock()
        mock_response.content = "Flight recommendations"
        agent.call_ai = AsyncMock(return_value=mock_response)

        response = await agent.process(context)
        assert isinstance(response, AgentResponse)
        assert response.agent_type == "transport"


class TestItineraryAgent:
    """Tests for ItineraryAgent."""

    @pytest.fixture
    def agent(self):
        return ItineraryAgent()

    def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "itinerary"

    def test_determine_create_intent(self, agent):
        """Test determining create itinerary intent."""
        assert agent._determine_intent("Lap lich trinh du lich") == "create_itinerary"
        assert agent._determine_intent("Tao ke hoach di choi") == "create_itinerary"

    def test_determine_modify_intent(self, agent):
        """Test determining modify itinerary intent."""
        assert agent._determine_intent("Thay doi lich trinh") == "modify_itinerary"
        assert agent._determine_intent("Them hoat dong vao ngay 2") == "modify_itinerary"

    def test_determine_attraction_intent(self, agent):
        """Test determining attraction search intent."""
        assert agent._determine_intent("Diem tham quan o Ha Noi") == "find_attractions"
        assert agent._determine_intent("Di dau o Da Nang") == "find_attractions"

    def test_system_prompt_with_context(self, agent):
        """Test system prompt generation with context."""
        context = AgentContext(
            user_id="user-123",
            message="Test",
            trip_data={
                "destination": "Hanoi",
                "start_date": "2024-01-01",
                "end_date": "2024-01-05",
                "travelers_count": 2
            }
        )
        prompt = agent.get_system_prompt(context)
        assert "Hanoi" in prompt or "ha noi" in prompt.lower()

    @pytest.mark.asyncio
    async def test_process(self, agent):
        """Test agent processing."""
        context = AgentContext(
            user_id="user-123",
            message="Lap lich trinh du lich Ha Noi 3 ngay"
        )

        # Mock AI call and attractions search
        mock_response = MagicMock()
        mock_response.content = "Itinerary created"
        agent.call_ai = AsyncMock(return_value=mock_response)

        with patch("app.agents.itinerary_agent.search_attractions", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            response = await agent.process(context)
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "itinerary"


class TestBudgetAgent:
    """Tests for BudgetAgent."""

    @pytest.fixture
    def agent(self):
        return BudgetAgent()

    def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "budget"

    def test_determine_estimate_intent(self, agent):
        """Test determining estimate intent."""
        assert agent._determine_intent("Uoc tinh chi phi") == "estimate"
        assert agent._determine_intent("Ton bao nhieu tien") == "estimate"

    def test_determine_optimize_intent(self, agent):
        """Test determining optimize intent."""
        assert agent._determine_intent("Cach tiet kiem") == "optimize"
        assert agent._determine_intent("Lam sao giam chi phi") == "optimize"

    def test_determine_breakdown_intent(self, agent):
        """Test determining breakdown intent."""
        assert agent._determine_intent("Phan bo ngan sach") == "breakdown"
        assert agent._determine_intent("Chi tiet cac hang muc") == "breakdown"

    def test_calculate_days(self, agent):
        """Test calculating trip days."""
        trip_data = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-05"
        }
        days = agent._calculate_days(trip_data)
        assert days == 5

    def test_calculate_estimates(self, agent):
        """Test calculating budget estimates."""
        estimates = agent._calculate_estimates(days=3, travelers=2)
        assert "accommodation" in estimates
        assert "food" in estimates
        assert "transport" in estimates
        assert "activities" in estimates

    def test_format_estimates(self, agent):
        """Test formatting estimates."""
        estimates = agent._calculate_estimates(days=3, travelers=2)
        formatted = agent._format_estimates(estimates)
        assert "VND" in formatted
        assert len(formatted) > 0

    def test_cost_reference_data(self):
        """Test cost reference data structure."""
        assert "accommodation" in COST_REFERENCE
        assert "food" in COST_REFERENCE
        assert "transport" in COST_REFERENCE
        assert "activities" in COST_REFERENCE

    @pytest.mark.asyncio
    async def test_process(self, agent):
        """Test agent processing."""
        context = AgentContext(
            user_id="user-123",
            message="Uoc tinh chi phi cho chuyen di 3 ngay",
            trip_data={
                "start_date": "2024-01-01",
                "end_date": "2024-01-03",
                "travelers_count": 2,
                "budget": 5000000
            }
        )

        # Mock AI call
        mock_response = MagicMock()
        mock_response.content = "Budget estimate"
        agent.call_ai = AsyncMock(return_value=mock_response)

        response = await agent.process(context)
        assert isinstance(response, AgentResponse)
        assert response.agent_type == "budget"


class TestAccommodationAgent:
    """Tests for AccommodationAgent."""

    @pytest.fixture
    def agent(self):
        return AccommodationAgent()

    def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "accommodation"

    @pytest.mark.asyncio
    async def test_process(self, agent):
        """Test agent processing."""
        context = AgentContext(
            user_id="user-123",
            message="Tim khach san o Ha Noi"
        )

        # Mock AI call and hotel search
        mock_response = MagicMock()
        mock_response.content = "Hotel recommendations"
        agent.call_ai = AsyncMock(return_value=mock_response)

        with patch("app.agents.accommodation_agent.search_hotels", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            response = await agent.process(context)
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "accommodation"


class TestFoodAgent:
    """Tests for FoodAgent."""

    @pytest.fixture
    def agent(self):
        return FoodAgent()

    def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "food"

    def test_get_region_north(self, agent):
        """Test getting north region."""
        assert agent._get_region("Ha Noi") == "north"
        assert agent._get_region("Sapa") == "north"

    def test_get_region_central(self, agent):
        """Test getting central region."""
        assert agent._get_region("Hue") == "central"
        assert agent._get_region("Da Nang") == "central"

    def test_get_region_south(self, agent):
        """Test getting south region."""
        assert agent._get_region("Ho Chi Minh") == "south"
        assert agent._get_region("Sai Gon") == "south"

    def test_determine_restaurant_intent(self, agent):
        """Test determining restaurant search intent."""
        assert agent._determine_intent("Tim nha hang") == "search_restaurant"
        assert agent._determine_intent("An o dau") == "search_restaurant"

    def test_determine_dish_intent(self, agent):
        """Test determining dish recommendation intent."""
        assert agent._determine_intent("Mon gi ngon") == "recommend_dish"
        assert agent._determine_intent("Dac san Ha Noi") == "recommend_dish"

    @pytest.mark.asyncio
    async def test_process(self, agent):
        """Test agent processing."""
        context = AgentContext(
            user_id="user-123",
            message="Tim nha hang pho o Ha Noi"
        )

        # Mock AI call and restaurant search
        mock_response = MagicMock()
        mock_response.content = "Restaurant recommendations"
        agent.call_ai = AsyncMock(return_value=mock_response)

        with patch("app.agents.food_agent.search_restaurants", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            response = await agent.process(context)
            assert isinstance(response, AgentResponse)
            assert response.agent_type == "food"
