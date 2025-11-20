"""
Base Agent Architecture.

This module defines the abstract base class for all AI agents,
providing common functionality for agent interactions.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.ai_providers import get_ai_provider, AIMessage, AIResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentContext(BaseModel):
    """Context passed to agents for processing."""

    user_id: int
    trip_id: Optional[int] = None
    conversation_id: Optional[int] = None
    message: str
    conversation_history: list[dict] = Field(default_factory=list)
    trip_data: Optional[dict] = None
    user_preferences: Optional[dict] = None
    metadata: dict = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent."""

    message: str
    agent_type: str
    data: Optional[dict] = None
    suggestions: list[str] = Field(default_factory=list)
    requires_followup: bool = False
    next_agent: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class AgentMetrics(BaseModel):
    """Metrics for agent performance tracking."""

    agent_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.

    All agent implementations must inherit from this class
    and implement the process() method.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize the agent.

        Args:
            name: Agent name/type identifier
            description: Human-readable description of the agent's purpose
        """
        self.name = name
        self.description = description
        self.ai_provider = get_ai_provider()
        self.logger = get_logger(f"agent.{name}")

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a user message and generate a response.

        Args:
            context: Agent context with message and history

        Returns:
            AgentResponse with the generated response
        """
        pass

    @abstractmethod
    def get_system_prompt(self, context: AgentContext) -> str:
        """
        Get the system prompt for this agent.

        Args:
            context: Agent context

        Returns:
            System prompt string
        """
        pass

    async def call_ai(
        self,
        messages: list[AIMessage],
        system_prompt: str,
        **kwargs: Any
    ) -> AIResponse:
        """
        Call the AI provider with messages.

        Args:
            messages: List of conversation messages
            system_prompt: System prompt for the AI
            **kwargs: Additional parameters

        Returns:
            AI response
        """
        start_time = datetime.utcnow()

        try:
            response = await self.ai_provider.generate(
                messages=messages,
                system_prompt=system_prompt,
                **kwargs
            )

            # Log metrics
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() * 1000

            self.logger.info(
                "ai_call_completed",
                agent=self.name,
                duration_ms=duration,
                tokens=response.usage.get("total_tokens") if response.usage else None,
            )

            return response

        except Exception as e:
            self.logger.error(
                "ai_call_failed",
                agent=self.name,
                error=str(e),
            )
            raise

    async def call_ai_structured(
        self,
        messages: list[AIMessage],
        system_prompt: str,
        response_schema: dict[str, Any],
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Call AI and get structured JSON response.

        Args:
            messages: List of conversation messages
            system_prompt: System prompt for the AI
            response_schema: Expected response JSON schema
            **kwargs: Additional parameters

        Returns:
            Parsed JSON response
        """
        return await self.ai_provider.generate_structured(
            messages=messages,
            system_prompt=system_prompt,
            response_schema=response_schema,
            **kwargs
        )

    def format_conversation_history(
        self,
        history: list[dict],
        max_messages: int = 20
    ) -> list[AIMessage]:
        """
        Format conversation history for AI provider.

        Args:
            history: Raw conversation history
            max_messages: Maximum messages to include

        Returns:
            Formatted AI messages
        """
        messages = []
        recent_history = history[-max_messages:] if len(history) > max_messages else history

        for msg in recent_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            messages.append(AIMessage(role=role, content=content))

        return messages

    def extract_entities(self, text: str) -> dict[str, Any]:
        """
        Extract entities from user text (dates, locations, numbers, etc.).

        Args:
            text: User input text

        Returns:
            Dictionary of extracted entities
        """
        import re

        entities = {}

        # Extract dates (various formats)
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}\s+(?:tháng|thg)\s*\d{1,2}',
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities["dates"] = matches

        # Extract numbers/budget
        money_pattern = r'(\d+(?:\.\d+)?)\s*(?:triệu|tr|VND|đồng|k|nghìn|ngàn)'
        money_matches = re.findall(money_pattern, text, re.IGNORECASE)
        if money_matches:
            entities["amounts"] = money_matches

        # Extract Vietnamese locations
        locations = [
            "Hà Nội", "Hanoi", "HCM", "Hồ Chí Minh", "Saigon", "Sài Gòn",
            "Đà Nẵng", "Da Nang", "Huế", "Hue", "Hội An", "Hoi An",
            "Nha Trang", "Đà Lạt", "Da Lat", "Phú Quốc", "Phu Quoc",
            "Hạ Long", "Ha Long", "Sapa", "Sa Pa", "Cần Thơ", "Can Tho"
        ]
        found_locations = []
        for loc in locations:
            if loc.lower() in text.lower():
                found_locations.append(loc)
        if found_locations:
            entities["locations"] = found_locations

        # Extract number of people
        people_pattern = r'(\d+)\s*(?:người|ng|khách|traveler)'
        people_matches = re.findall(people_pattern, text, re.IGNORECASE)
        if people_matches:
            entities["travelers"] = int(people_matches[0])

        return entities

    def log_interaction(
        self,
        context: AgentContext,
        response: AgentResponse,
        metrics: Optional[AgentMetrics] = None
    ) -> None:
        """
        Log an agent interaction for analytics.

        Args:
            context: Agent context
            response: Agent response
            metrics: Performance metrics
        """
        self.logger.info(
            "agent_interaction",
            agent=self.name,
            user_id=context.user_id,
            trip_id=context.trip_id,
            message_length=len(context.message),
            response_length=len(response.message),
            has_data=response.data is not None,
            suggestions_count=len(response.suggestions),
            duration_ms=metrics.duration_ms if metrics else None,
        )
