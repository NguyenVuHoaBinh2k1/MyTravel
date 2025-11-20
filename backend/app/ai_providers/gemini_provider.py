"""
Google Gemini AI Provider Implementation.
"""

import json
from typing import Any, AsyncIterator, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.ai_providers.base import (
    BaseAIProvider,
    AIProviderConfig,
    AIMessage,
    AIResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini AI provider implementation.

    Uses the google-generativeai SDK to interact with Gemini models.
    """

    def __init__(self, config: AIProviderConfig):
        """Initialize Gemini provider."""
        super().__init__(config)

        # Configure the API
        genai.configure(api_key=config.api_key)

        # Default model name for Gemini
        model_name = config.model_name
        if model_name == "default":
            model_name = "gemini-1.5-flash"

        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        # Create the model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                top_p=config.top_p,
            ),
            safety_settings=self.safety_settings,
        )

    def _convert_messages_to_gemini(
        self,
        messages: list[AIMessage],
        system_prompt: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        """
        Convert messages to Gemini format.

        Args:
            messages: List of AIMessage objects
            system_prompt: Optional system prompt

        Returns:
            Tuple of (history, current_message)
        """
        history = []
        current_message = None

        # Add system prompt to first user message if provided
        first_user = True

        for msg in messages:
            if msg.role == "user":
                content = msg.content
                if first_user and system_prompt:
                    content = f"{system_prompt}\n\n{content}"
                    first_user = False

                if messages.index(msg) == len(messages) - 1:
                    current_message = content
                else:
                    history.append({
                        "role": "user",
                        "parts": [content]
                    })
            elif msg.role == "assistant":
                history.append({
                    "role": "model",
                    "parts": [msg.content]
                })

        return history, current_message

    async def generate(
        self,
        messages: list[AIMessage],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AIResponse:
        """Generate a response using Gemini."""
        try:
            history, current_message = self._convert_messages_to_gemini(
                messages, system_prompt
            )

            # Create chat session
            chat = self.model.start_chat(history=history)

            # Generate response
            response = await chat.send_message_async(current_message)

            # Extract usage if available
            usage = None
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }

            return AIResponse(
                content=response.text,
                model=self.model.model_name,
                usage=usage,
                finish_reason="stop"
            )

        except Exception as e:
            logger.error("gemini_generate_error", error=str(e))
            raise

    async def generate_stream(
        self,
        messages: list[AIMessage],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """Generate a streaming response using Gemini."""
        try:
            history, current_message = self._convert_messages_to_gemini(
                messages, system_prompt
            )

            # Create chat session
            chat = self.model.start_chat(history=history)

            # Generate streaming response
            response = await chat.send_message_async(
                current_message,
                stream=True
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error("gemini_stream_error", error=str(e))
            raise

    async def generate_structured(
        self,
        messages: list[AIMessage],
        response_schema: dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> dict[str, Any]:
        """Generate a structured JSON response using Gemini."""
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
                **kwargs
            )

            # Parse JSON from response
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])

            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error("gemini_json_parse_error", error=str(e))
            raise ValueError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            logger.error("gemini_structured_error", error=str(e))
            raise

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            # Simple test generation
            response = self.model.generate_content("Say 'OK'")
            return response.text is not None
        except Exception as e:
            logger.error("gemini_health_check_failed", error=str(e))
            return False
