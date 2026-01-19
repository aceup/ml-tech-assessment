import openai
import pydantic

from app import ports
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIAdapter(ports.LLm):
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: int = 30,
        max_retries: int = 3,
        max_tokens: int | None = None,
        enable_moderation: bool = True,
    ) -> None:
        """
        Initialize OpenAI adapter with security enhancements.

        Args:
            api_key: OpenAI API key
            model: Model name to use
            timeout: API timeout in seconds
            max_retries: Maximum retry attempts
            max_tokens: Maximum tokens in response (None = model default)
            enable_moderation: Enable OpenAI Moderation API
        """
        self._model = model
        self._max_tokens = max_tokens
        self._enable_moderation = enable_moderation

        self._client = openai.OpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._aclient = openai.AsyncOpenAI(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

        logger.info(
            "openai_adapter_init",
            message="OpenAI adapter initialized",
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            max_tokens=max_tokens,
            moderation_enabled=enable_moderation,
        )

    def run_completion(
        self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]
    ) -> pydantic.BaseModel:
        """
        Executes a completion request using the OpenAI API with the provided prompts and response format.

        Args:
            system_prompt (str): The system's introductory message for the chat.
            user_prompt (str): The user input for which a response is needed.
            dto (Type[pydantic.BaseModel]): A Pydantic model class used to define the structure of the API response.

        Returns:
            pydantic.BaseModel: An instance of the provided DTO class populated with the API response data.
            more info: https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat
        """
        try:
            logger.debug(
                "openai_completion_request",
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
                "response_format": dto,
            }

            # Add max_tokens if configured
            if self._max_tokens:
                api_params["max_tokens"] = self._max_tokens

            completion = self._client.beta.chat.completions.parse(**api_params)

            parsed_result = completion.choices[0].message.parsed

            # Log token usage
            if hasattr(completion, "usage") and completion.usage:
                logger.info(
                    "openai_completion_success",
                    message="Completion successful",
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens,
                )

            return parsed_result

        except openai.APIError as e:
            logger.error(
                "openai_api_error",
                message="OpenAI API error",
                error=str(e),
                status_code=getattr(e, "status_code", None),
            )
            raise
        except Exception as e:
            logger.error(
                "openai_completion_error",
                message="Unexpected error during completion",
                error=str(e),
            )
            raise

    async def run_completion_async(
        self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]
    ) -> pydantic.BaseModel:
        """
        Executes a completion request using the OpenAI API with the provided prompts and response format.

        Args:
            system_prompt (str): The system's introductory message for the chat.
            user_prompt (str): The user input for which a response is needed.
            dto (Type[pydantic.BaseModel]): A Pydantic model class used to define the structure of the API response.

        Returns:
         pydantic.BaseModel: An instance of the provided DTO class populated with the API response data.

         more info: https://platform.openai.com/docs/guides/structured-outputs?api-mode=chat
         """
        try:
            logger.debug(
                "openai_async_completion_request",
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
                "response_format": dto,
            }

            # Add max_tokens if configured
            if self._max_tokens:
                api_params["max_tokens"] = self._max_tokens

            completion = await self._aclient.beta.chat.completions.parse(**api_params)

            parsed_result = completion.choices[0].message.parsed

            # Log token usage
            if hasattr(completion, "usage") and completion.usage:
                logger.info(
                    "openai_async_completion_success",
                    message="Async completion successful",
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens,
                )

            return parsed_result

        except openai.APIError as e:
            logger.error(
                "openai_async_api_error",
                message="OpenAI async API error",
                error=str(e),
                status_code=getattr(e, "status_code", None),
            )
            raise
        except Exception as e:
            logger.error(
                "openai_async_completion_error",
                message="Unexpected error during async completion",
                error=str(e),
            )
            raise

    def moderate_content(self, text: str) -> tuple[bool, dict]:
        """
        Check content using OpenAI Moderation API.

        Args:
            text: Content to moderate

        Returns:
            tuple: (is_safe, moderation_results)
                is_safe: True if content passes moderation
                moderation_results: Full moderation API response

        Raises:
            Exception: If moderation API call fails
        """
        if not self._enable_moderation:
            logger.debug("moderation_disabled", message="Content moderation is disabled")
            return True, {}

        try:
            logger.debug("moderation_request", message="Checking content with moderation API")

            response = self._client.moderations.create(input=text)

            result = response.results[0]
            is_flagged = result.flagged

            if is_flagged:
                logger.warning(
                    "content_flagged",
                    message="Content flagged by moderation API",
                    categories=result.categories.model_dump(),
                    category_scores=result.category_scores.model_dump(),
                )

            return not is_flagged, result.model_dump()

        except Exception as e:
            logger.error(
                "moderation_error",
                message="Error during content moderation",
                error=str(e),
            )
            # On error, allow content through but log the failure
            return True, {}

    async def moderate_content_async(self, text: str) -> tuple[bool, dict]:
        """
        Check content using OpenAI Moderation API (async version).

        Args:
            text: Content to moderate

        Returns:
            tuple: (is_safe, moderation_results)
                is_safe: True if content passes moderation
                moderation_results: Full moderation API response

        Raises:
            Exception: If moderation API call fails
        """
        if not self._enable_moderation:
            logger.debug(
                "moderation_disabled_async", message="Content moderation is disabled"
            )
            return True, {}

        try:
            logger.debug(
                "moderation_request_async", message="Checking content with moderation API (async)"
            )

            response = await self._aclient.moderations.create(input=text)

            result = response.results[0]
            is_flagged = result.flagged

            if is_flagged:
                logger.warning(
                    "content_flagged_async",
                    message="Content flagged by moderation API (async)",
                    categories=result.categories.model_dump(),
                    category_scores=result.category_scores.model_dump(),
                )

            return not is_flagged, result.model_dump()

        except Exception as e:
            logger.error(
                "moderation_error_async",
                message="Error during content moderation (async)",
                error=str(e),
            )
            # On error, allow content through but log the failure
            return True, {}
