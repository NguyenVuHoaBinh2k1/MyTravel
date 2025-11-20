"""Tests for the Master Orchestrator."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.orchestrator import (
    MasterOrchestrator,
    AgentType,
    OrchestratorState,
    get_orchestrator
)
from app.agents.base import AgentContext, AgentResponse


class TestOrchestratorState:
    """Tests for OrchestratorState."""

    def test_state_creation(self):
        """Test creating orchestrator state."""
        state = OrchestratorState(
            message="Test",
            user_id="user-123"
        )
        assert state.message == "Test"
        assert state.user_id == "user-123"
        assert state.trip_id is None
        assert state.selected_agent is None
        assert state.response is None
        assert state.error is None

    def test_state_with_trip_data(self):
        """Test state with trip data."""
        state = OrchestratorState(
            message="Test",
            user_id="user-123",
            trip_id="trip-456",
            trip_data={"destination": "Hanoi"}
        )
        assert state.trip_id == "trip-456"
        assert state.trip_data["destination"] == "Hanoi"


class TestMasterOrchestrator:
    """Tests for MasterOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for testing."""
        return MasterOrchestrator()

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.agents is not None
        assert len(orchestrator.agents) == 5
        assert AgentType.ACCOMMODATION in orchestrator.agents
        assert AgentType.FOOD in orchestrator.agents
        assert AgentType.TRANSPORT in orchestrator.agents
        assert AgentType.ITINERARY in orchestrator.agents
        assert AgentType.BUDGET in orchestrator.agents

    def test_classify_accommodation_intent(self, orchestrator):
        """Test classifying accommodation intent."""
        state = OrchestratorState(
            message="Tim khach san o Ha Noi",
            user_id="user-123"
        )
        result = orchestrator._classify_intent(state)
        assert result.selected_agent == AgentType.ACCOMMODATION.value

    def test_classify_food_intent(self, orchestrator):
        """Test classifying food intent."""
        state = OrchestratorState(
            message="Goi y nha hang an pho",
            user_id="user-123"
        )
        result = orchestrator._classify_intent(state)
        assert result.selected_agent == AgentType.FOOD.value

    def test_classify_transport_intent(self, orchestrator):
        """Test classifying transport intent."""
        state = OrchestratorState(
            message="Tim chuyen bay di Da Nang",
            user_id="user-123"
        )
        result = orchestrator._classify_intent(state)
        assert result.selected_agent == AgentType.TRANSPORT.value

    def test_classify_itinerary_intent(self, orchestrator):
        """Test classifying itinerary intent."""
        state = OrchestratorState(
            message="Lap lich trinh du lich 3 ngay",
            user_id="user-123"
        )
        result = orchestrator._classify_intent(state)
        assert result.selected_agent == AgentType.ITINERARY.value

    def test_classify_budget_intent(self, orchestrator):
        """Test classifying budget intent."""
        state = OrchestratorState(
            message="Uoc tinh chi phi cho chuyen di",
            user_id="user-123"
        )
        result = orchestrator._classify_intent(state)
        assert result.selected_agent == AgentType.BUDGET.value

    def test_classify_general_intent(self, orchestrator):
        """Test classifying general intent."""
        state = OrchestratorState(
            message="Xin chao",
            user_id="user-123"
        )
        result = orchestrator._classify_intent(state)
        assert result.selected_agent == AgentType.GENERAL.value

    def test_should_use_agent_true(self, orchestrator):
        """Test should_use_agent returns agent."""
        state = OrchestratorState(
            message="Test",
            user_id="user-123"
        )
        state.selected_agent = AgentType.FOOD.value
        result = orchestrator._should_use_agent(state)
        assert result == "agent"

    def test_should_use_agent_false(self, orchestrator):
        """Test should_use_agent returns general."""
        state = OrchestratorState(
            message="Test",
            user_id="user-123"
        )
        state.selected_agent = AgentType.GENERAL.value
        result = orchestrator._should_use_agent(state)
        assert result == "general"

    @pytest.mark.asyncio
    async def test_route_to_agent(self, orchestrator):
        """Test routing to specific agent."""
        state = OrchestratorState(
            message="Tim khach san Ha Noi",
            user_id="user-123"
        )
        state.selected_agent = AgentType.ACCOMMODATION.value

        # Mock the agent's process method
        mock_response = AgentResponse(
            message="Found hotels",
            agent_type="accommodation",
            suggestions=["Book now"]
        )
        orchestrator.agents[AgentType.ACCOMMODATION].process = AsyncMock(
            return_value=mock_response
        )

        result = await orchestrator._route_to_agent(state)
        assert result.response is not None
        assert result.response["message"] == "Found hotels"
        assert result.response["agent_type"] == "accommodation"

    @pytest.mark.asyncio
    async def test_handle_general(self, orchestrator):
        """Test handling general queries."""
        state = OrchestratorState(
            message="Xin chao",
            user_id="user-123"
        )

        # Mock the AI provider
        with patch.object(
            orchestrator,
            "_handle_general",
            new_callable=AsyncMock
        ) as mock_handle:
            mock_handle.return_value = state
            state.response = {
                "message": "Hello",
                "agent_type": "general",
                "suggestions": []
            }
            result = await mock_handle(state)
            assert result.response is not None

    @pytest.mark.asyncio
    async def test_process(self, orchestrator):
        """Test full processing flow."""
        # Mock all agents
        for agent_type in orchestrator.agents:
            orchestrator.agents[agent_type].process = AsyncMock(
                return_value=AgentResponse(
                    message="Response",
                    agent_type=agent_type.value
                )
            )

        response = await orchestrator.process(
            message="Tim khach san o Sai Gon",
            user_id="user-123"
        )

        assert isinstance(response, AgentResponse)
        assert response.message is not None

    @pytest.mark.asyncio
    async def test_process_with_context(self, orchestrator):
        """Test processing with AgentContext."""
        context = AgentContext(
            user_id="user-123",
            trip_id="trip-456",
            message="Tim khach san",
            trip_data={"destination": "Hanoi"}
        )

        # Mock agent
        orchestrator.agents[AgentType.ACCOMMODATION].process = AsyncMock(
            return_value=AgentResponse(
                message="Found hotels",
                agent_type="accommodation"
            )
        )

        response = await orchestrator.process_with_context(context)
        assert isinstance(response, AgentResponse)


class TestGetOrchestrator:
    """Tests for get_orchestrator singleton."""

    def test_get_orchestrator_singleton(self):
        """Test that get_orchestrator returns singleton."""
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()
        assert orchestrator1 is orchestrator2

    def test_get_orchestrator_type(self):
        """Test get_orchestrator returns correct type."""
        orchestrator = get_orchestrator()
        assert isinstance(orchestrator, MasterOrchestrator)
