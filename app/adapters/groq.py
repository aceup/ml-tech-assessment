"""Groq LLM adapter implementation."""

import json

import pydantic
from groq import AsyncGroq, Groq

from app.core.logging import get_logger
from app.ports.llm import LLm

logger = get_logger(__name__)


class GroqAdapter(LLm):
    """Groq implementation of the LLM port."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        timeout: int = 30,
        max_retries: int = 3,
        max_tokens: int | None = None,
    ) -> None:
        """
        Initialize Groq adapter with security enhancements.

        Args:
            api_key: Groq API key
            model: Groq model to use (default: llama-3.3-70b-versatile)
            timeout: API timeout in seconds
            max_retries: Maximum retry attempts
            max_tokens: Maximum tokens in response (None = model default)
        """
        self._model = model
        self._max_tokens = max_tokens

        self._client = Groq(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._aclient = AsyncGroq(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

        logger.info(
            "groq_adapter_init",
            message="Groq adapter initialized",
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            max_tokens=max_tokens,
        )

    def run_completion(
        self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]
    ) -> pydantic.BaseModel:
        """
        Execute synchronous completion request using Groq.

        Args:
            system_prompt: System message
            user_prompt: User input
            dto: Pydantic model for response parsing

        Returns:
            Parsed response as Pydantic model
        """
        try:
            logger.debug(
                "groq_completion_request",
                message="Sending completion request",
                model=self._model,
                max_tokens=self._max_tokens,
            )

            # Build API parameters
            api_params: dict = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            }

            # Add max_tokens if configured
            if self._max_tokens:
                api_params["max_tokens"] = self._max_tokens

            completion = self._client.chat.completions.create(**api_params)

            # Log token usage if available
            if hasattr(completion, "usage") and completion.usage:
                logger.info(
                    "groq_completion_success",
                    message="Completion successful",
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens,
                )

            # Parse JSON response into Pydantic model
            response_content = completion.choices[0].message.content
            if response_content is None:
                raise ValueError("Groq returned empty response")

            return dto.model_validate_json(response_content)

        except Exception as e:
            logger.error(
                "groq_completion_error",
                message="Error during Groq completion",
                error=str(e),
            )
            raise

    async def run_completion_async(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[pydantic.BaseModel],
    ) -> pydantic.BaseModel:
        """
        Execute asynchronous completion request using Groq.

        Args:
            system_prompt: System message
            user_prompt: User input
            dto: Pydantic model for response parsing

        Returns:
            Parsed response as Pydantic model
        """
        try:
            logger.debug(
                "groq_async_completion_request",
                message="Sending async completion request",
                model=self._model,
                max_tokens=self._max_tokens,
            )

            # Build API parameters
            api_params: dict = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            }

            # Add max_tokens if configured
            if self._max_tokens:
                api_params["max_tokens"] = self._max_tokens

            completion = await self._aclient.chat.completions.create(**api_params)

            # Log token usage if available
            if hasattr(completion, "usage") and completion.usage:
                logger.info(
                    "groq_async_completion_success",
                    message="Async completion successful",
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens,
                )

            # Parse JSON response into Pydantic model
            response_content = completion.choices[0].message.content
            if response_content is None:
                raise ValueError("Groq returned empty response")

            return dto.model_validate_json(response_content)

        except Exception as e:
            logger.error(
                "groq_async_completion_error",
                message="Error during Groq async completion",
                error=str(e),
            )
            raise
