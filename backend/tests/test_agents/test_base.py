"""Tests for base agent functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.base import BaseAgent, AgentContext, AgentResponse
from app.ai_providers import AIMessage


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation for testing."""

    def __init__(self):
        super().__init__(name="test", description="Test agent")

    def get_system_prompt(self, context: AgentContext) -> str:
        return "Test system prompt"

    async def process(self, context: AgentContext) -> AgentResponse:
        return AgentResponse(
            message="Test response",
            agent_type=self.name,
            suggestions=["Suggestion 1"]
        )


class TestAgentContext:
    """Tests for AgentContext."""

    def test_context_creation(self):
        """Test creating an agent context."""
        context = AgentContext(
            user_id="user-123",
            message="Test message"
        )
        assert context.user_id == "user-123"
        assert context.message == "Test message"
        assert context.trip_id is None
        assert context.conversation_history == []
        assert context.trip_data is None

    def test_context_with_trip_data(self):
        """Test context with trip data."""
        trip_data = {
            "destination": "Hanoi",
            "start_date": "2024-01-01",
            "end_date": "2024-01-05",
            "travelers_count": 2,
            "budget": 5000000
        }
        context = AgentContext(
            user_id="user-123",
            trip_id="trip-456",
            message="Test",
            trip_data=trip_data
        )
        assert context.trip_id == "trip-456"
        assert context.trip_data == trip_data

    def test_context_with_history(self):
        """Test context with conversation history."""
        history = [
            AIMessage(role="user", content="Hello"),
            AIMessage(role="assistant", content="Hi there!")
        ]
        context = AgentContext(
            user_id="user-123",
            message="Test",
            conversation_history=history
        )
        assert len(context.conversation_history) == 2


class TestAgentResponse:
    """Tests for AgentResponse."""

    def test_response_creation(self):
        """Test creating an agent response."""
        response = AgentResponse(
            message="Hello",
            agent_type="test"
        )
        assert response.message == "Hello"
        assert response.agent_type == "test"
        assert response.data is None
        assert response.suggestions == []
        assert response.actions == []

    def test_response_with_data(self):
        """Test response with data."""
        response = AgentResponse(
            message="Results",
            agent_type="test",
            data={"hotels": [{"name": "Test Hotel"}]},
            suggestions=["Book now", "See more"],
            actions=[{"type": "book", "label": "Book"}]
        )
        assert response.data == {"hotels": [{"name": "Test Hotel"}]}
        assert len(response.suggestions) == 2
        assert len(response.actions) == 1


class TestBaseAgent:
    """Tests for BaseAgent."""

    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = ConcreteTestAgent()
        assert agent.name == "test"
        assert agent.description == "Test agent"
        assert agent.ai_provider is not None

    def test_extract_entities_locations(self):
        """Test extracting locations from message."""
        agent = ConcreteTestAgent()
        message = "I want to visit Hanoi and Da Nang"
        entities = agent.extract_entities(message)
        assert "locations" in entities
        # Basic entity extraction should find some locations

    def test_extract_entities_dates(self):
        """Test extracting dates from message."""
        agent = ConcreteTestAgent()
        message = "I will travel from January 1 to January 5"
        entities = agent.extract_entities(message)
        assert "dates" in entities

    def test_extract_entities_budget(self):
        """Test extracting budget from message."""
        agent = ConcreteTestAgent()
        message = "My budget is 5000000 VND"
        entities = agent.extract_entities(message)
        assert "budget" in entities

    def test_format_conversation_history(self):
        """Test formatting conversation history."""
        agent = ConcreteTestAgent()
        history = [
            AIMessage(role="user", content="Hello"),
            AIMessage(role="assistant", content="Hi!"),
            AIMessage(role="user", content="How are you?")
        ]
        formatted = agent.format_conversation_history(history)
        assert len(formatted) == 3
        assert formatted[0].role == "user"
        assert formatted[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_process(self):
        """Test agent processing."""
        agent = ConcreteTestAgent()
        context = AgentContext(
            user_id="user-123",
            message="Test message"
        )
        response = await agent.process(context)
        assert response.message == "Test response"
        assert response.agent_type == "test"

    @pytest.mark.asyncio
    async def test_call_ai(self):
        """Test calling AI provider."""
        agent = ConcreteTestAgent()

        # Mock the AI provider
        mock_response = MagicMock()
        mock_response.content = "AI response"
        agent.ai_provider.chat = AsyncMock(return_value=mock_response)

        messages = [AIMessage(role="user", content="Hello")]
        response = await agent.call_ai(messages, "System prompt")

        assert response.content == "AI response"
        agent.ai_provider.chat.assert_called_once()
