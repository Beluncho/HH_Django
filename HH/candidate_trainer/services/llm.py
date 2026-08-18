from dataclasses import dataclass

from django.conf import settings
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    OpenAIError,
)

from .exceptions import LLMError


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str


class DisabledLLMClient:
    provider = "disabled"
    model = ""

    def complete(self, system_prompt, messages, max_tokens=None):
        raise LLMError(
            "LLM не настроен. Укажите LLM_PROVIDER, LLM_MODEL и "
            "LLM_API_KEY. Для прокси также укажите LLM_BASE_URL."
        )


def normalize_base_url(base_url):
    normalized = (base_url or "").strip().rstrip("/")
    legacy_suffix = "/chat/completions"
    if normalized.endswith(legacy_suffix):
        normalized = normalized[: -len(legacy_suffix)]
    return normalized


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        provider,
        model,
        api_key,
        timeout,
        base_url="",
        client=None,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = normalize_base_url(base_url)
        self._client = client

    def _get_client(self):
        if self._client is None:
            client_options = {
                "api_key": self.api_key,
                "timeout": self.timeout,
            }
            if self.base_url:
                client_options["base_url"] = self.base_url
            self._client = OpenAI(**client_options)
        return self._client

    def complete(self, system_prompt, messages, max_tokens=None):
        if not self.model or not self.api_key:
            raise LLMError("Настройки LLM заполнены не полностью")

        payload_messages = [{"role": "system", "content": system_prompt}]
        payload_messages.extend(messages)
        try:
            response = self._get_client().chat.completions.create(
                model=self.model,
                messages=payload_messages,
                max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
                temperature=0.2,
            )
            text = response.choices[0].message.content
        except APITimeoutError as error:
            raise LLMError("Превышен таймаут обращения к LLM") from error
        except APIConnectionError as error:
            raise LLMError("Не удалось подключиться к LLM-сервису") from error
        except APIStatusError as error:
            raise LLMError(
                f"LLM-сервис вернул HTTP {error.status_code}"
            ) from error
        except OpenAIError as error:
            raise LLMError("LLM-сервис временно недоступен") from error
        except (AttributeError, IndexError, TypeError) as error:
            raise LLMError("LLM вернул ответ в неожиданном формате") from error

        if not isinstance(text, str) or not text.strip():
            raise LLMError("LLM вернул пустой ответ")
        return LLMResponse(
            text=text.strip(),
            provider=self.provider,
            model=self.model,
        )


def get_llm_client():
    if settings.LLM_PROVIDER == "disabled":
        return DisabledLLMClient()
    return OpenAICompatibleLLMClient(
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        timeout=settings.LLM_TIMEOUT,
        base_url=settings.LLM_BASE_URL,
    )
