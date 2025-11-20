"""
Base AI Provider Interface.

This module defines the abstract base class for all AI providers,
enabling easy switching between different AI services (Gemini, OpenAI, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional
from pydantic import BaseModel


class AIProviderConfig(BaseModel):
    """Configuration for AI providers."""

    api_key: str
    model_name: str = "default"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.95
    timeout: int = 60


class AIMessage(BaseModel):
    """Represents a message in the conversation."""

    role: str  # "user", "assistant", "system"
    content: str


class AIResponse(BaseModel):
    """Response from AI provider."""

    content: str
    model: str
    usage: Optional[dict[str, int]] = None
    finish_reason: Optional[str] = None


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers.

    All AI provider implementations must inherit from this class
    and implement the required methods.
    """

    def __init__(self, config: AIProviderConfig):
        """
        Initialize the AI provider.

        Args:
            config: Provider configuration
        """
        self.config = config

    @abstractmethod
    async def generate(
        self,
        messages: list[AIMessage],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AIResponse:
        """
        Generate a response from the AI model.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            AIResponse with generated content
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[AIMessage],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the AI model.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Yields:
            Chunks of generated text
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: list[AIMessage],
        response_schema: dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Generate a structured JSON response from the AI model.

        Args:
            messages: List of conversation messages
            response_schema: JSON schema for the expected response
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            Parsed JSON response matching the schema
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the AI provider is healthy and accessible.

        Returns:
            True if healthy, False otherwise
        """
        pass

    def _format_messages(
        self,
        messages: list[AIMessage],
        system_prompt: Optional[str] = None
    ) -> list[dict[str, str]]:
        """
        Format messages for the specific provider.

        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt

        Returns:
            Formatted messages list
        """
        formatted = []

        if system_prompt:
            formatted.append({
                "role": "system",
                "content": system_prompt
            })

        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })

        return formatted
