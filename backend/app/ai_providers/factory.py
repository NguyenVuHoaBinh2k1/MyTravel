"""
AI Provider Factory.

This module provides a factory for creating AI provider instances
based on configuration.
"""

from typing import Type
from app.ai_providers.base import BaseAIProvider, AIProviderConfig
from app.ai_providers.gemini_provider import GeminiProvider
from app.ai_providers.openai_provider import OpenAIProvider
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIProviderFactory:
    """
    Factory for creating AI provider instances.

    Supports registering custom providers and creating instances
    based on provider name.
    """

    # Registry of available providers
    _providers: dict[str, Type[BaseAIProvider]] = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
    }

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: Type[BaseAIProvider]
    ) -> None:
        """
        Register a custom AI provider.

        Args:
            name: Provider name
            provider_class: Provider class (must inherit from BaseAIProvider)
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise TypeError(
                f"Provider class must inherit from BaseAIProvider"
            )
        cls._providers[name] = provider_class
        logger.info("ai_provider_registered", name=name)

    @classmethod
    def create(
        cls,
        provider_name: str | None = None,
        config: AIProviderConfig | None = None
    ) -> BaseAIProvider:
        """
        Create an AI provider instance.

        Args:
            provider_name: Name of the provider (default from settings)
            config: Provider configuration (default from settings)

        Returns:
            AI provider instance

        Raises:
            ValueError: If provider name is not found
        """
        # Use defaults from settings if not provided
        provider_name = provider_name or settings.AI_PROVIDER

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown AI provider: {provider_name}. "
                f"Available providers: {list(cls._providers.keys())}"
            )

        # Create config from settings if not provided
        if config is None:
            if provider_name == "gemini":
                config = AIProviderConfig(
                    api_key=settings.GEMINI_API_KEY,
                    model_name="gemini-1.5-flash",
                )
            elif provider_name == "openai":
                config = AIProviderConfig(
                    api_key=settings.OPENAI_API_KEY,
                    model_name="gpt-4-turbo-preview",
                )
            else:
                raise ValueError(
                    f"No default config for provider: {provider_name}"
                )

        # Create and return provider instance
        provider_class = cls._providers[provider_name]
        provider = provider_class(config)

        logger.info(
            "ai_provider_created",
            provider=provider_name,
            model=config.model_name
        )

        return provider

    @classmethod
    def list_providers(cls) -> list[str]:
        """
        List available provider names.

        Returns:
            List of registered provider names
        """
        return list(cls._providers.keys())


# Convenience function for getting the default provider
def get_ai_provider() -> BaseAIProvider:
    """
    Get the default AI provider based on settings.

    Returns:
        AI provider instance
    """
    return AIProviderFactory.create()
