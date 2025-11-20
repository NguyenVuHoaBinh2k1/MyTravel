"""
OpenAI AI Provider Implementation.
"""

import json
from typing import Any, AsyncIterator, Optional
from openai import AsyncOpenAI

from app.ai_providers.base import (
    BaseAIProvider,
    AIProviderConfig,
    AIMessage,
    AIResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI AI provider implementation.

    Uses the openai SDK to interact with OpenAI models.
    """

    def __init__(self, config: AIProviderConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)

        # Create async client
        self.client = AsyncOpenAI(api_key=config.api_key)

        # Default model name for OpenAI
        self.model_name = config.model_name
        if self.model_name == "default":
            self.model_name = "gpt-4-turbo-preview"

    async def generate(
        self,
        messages: list[AIMessage],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AIResponse:
        """Generate a response using OpenAI."""
        try:
            # Format messages
            formatted_messages = self._format_messages(messages, system_prompt)

            # Create completion
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                **kwargs
            )

            # Extract response
            choice = response.choices[0]
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return AIResponse(
                content=choice.message.content,
                model=response.model,
                usage=usage,
                finish_reason=choice.finish_reason
            )

        except Exception as e:
            logger.error("openai_generate_error", error=str(e))
            raise

    async def generate_stream(
        self,
        messages: list[AIMessage],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Generate a streaming response using OpenAI."""
        try:
            # Format messages
            formatted_messages = self._format_messages(messages, system_prompt)

            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=formatted_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("openai_stream_error", error=str(e))
            raise

    async def generate_structured(
        self,
        messages: list[AIMessage],
        response_schema: dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Generate a structured JSON response using OpenAI."""
        try:
            # Add JSON instruction to system prompt
            schema_str = json.dumps(response_schema, indent=2)
            json_instruction = (
                f"\n\nYou must respond with valid JSON matching this schema:\n"
                f"```json\n{schema_str}\n```\n"
                f"Only output the JSON, no other text."
            )

            combined_prompt = (system_prompt or "") + json_instruction

            # Generate response
            response = await self.generate(
                messages,
                system_prompt=combined_prompt,
                response_format={"type": "json_object"},
                **kwargs
            )

            # Parse JSON from response
            return json.loads(response.content)

        except json.JSONDecodeError as e:
            logger.error("openai_json_parse_error", error=str(e))
            raise ValueError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            logger.error("openai_structured_error", error=str(e))
            raise

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'OK'"}],
                max_tokens=5
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.error("openai_health_check_failed", error=str(e))
            return False
