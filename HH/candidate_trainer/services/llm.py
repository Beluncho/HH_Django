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
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


PROVIDER_DETAIL_LIMIT = 500


def provider_error_detail(error):
    """Тело ответа провайдера, обрезанное до разумного размера.

    Именно в теле лежит причина HTTP-ошибки: «Model not supported»,
    «Unsupported parameter: max_tokens». Без него диагностика превращается в
    угадывание.
    """
    text = ""
    response = getattr(error, "response", None)
    if response is not None:
        text = getattr(response, "text", "") or ""
    if not text:
        body = getattr(error, "body", None)
        if body is not None:
            text = str(body)
    return " ".join(text.split())[:PROVIDER_DETAIL_LIMIT]


def humanize_llm_error(error):
    """Короткая фраза для пользователя вместо технической.

    Полный ответ провайдера остаётся в журнале обращений к LLM
    (services/llm_log.py), а в интерфейс уходит то, что человек может
    исправить.
    """
    if not isinstance(error, LLMError):
        return str(error)

    detail = (error.provider_detail or "").lower()
    if "model not supported" in detail or "model_not_found" in detail:
        return (
            "Провайдер не обслуживает модель из LLM_MODEL. Сверьте имя модели "
            "со списком моделей провайдера."
        )
    if "max_tokens" in detail or "max_completion_tokens" in detail:
        return (
            "Модель не принимает выбранное поле лимита ответа. Приведите "
            "LLM_MAX_TOKENS_PARAM в соответствие требованиям провайдера."
        )
    if "temperature" in detail:
        return (
            "Модель не принимает temperature. Оставьте LLM_TEMPERATURE пустым — "
            "тогда параметр не отправляется."
        )
    if error.http_status in (401, 403):
        return "Провайдер отклонил ключ LLM_API_KEY."
    if error.http_status == 429:
        return "Провайдер ограничил частоту запросов. Повторите позже."
    if error.provider_detail:
        return f"{error}. Подробности — в журнале обращений к LLM."
    return str(error)


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
        limit_value = max_tokens or settings.LLM_MAX_TOKENS
        # Имя параметра лимита настраивается: старые OpenAI-совместимые API
        # принимают max_tokens, новые reasoning-модели OpenAI — только
        # max_completion_tokens и отвечают 400 на любое другое поле.
        if settings.LLM_MAX_TOKENS_PARAM == "max_completion_tokens":
            limit_kwargs = {"max_completion_tokens": limit_value}
        else:
            limit_kwargs = {"max_tokens": limit_value}
        create_kwargs = {
            "model": self.model,
            "messages": payload_messages,
            **limit_kwargs,
        }
        # Пустое LLM_TEMPERATURE означает «не отправлять temperature»: часть
        # моделей принимает только значение по умолчанию.
        if settings.LLM_TEMPERATURE is not None:
            create_kwargs["temperature"] = settings.LLM_TEMPERATURE
        try:
            response = self._get_client().chat.completions.create(**create_kwargs)
            text = response.choices[0].message.content
            usage = getattr(response, "usage", None)
        except APITimeoutError as error:
            raise LLMError("Превышен таймаут обращения к LLM") from error
        except APIConnectionError as error:
            raise LLMError("Не удалось подключиться к LLM-сервису") from error
        except APIStatusError as error:
            raise LLMError(
                f"LLM-сервис вернул HTTP {error.status_code}",
                http_status=error.status_code,
                provider_detail=provider_error_detail(error),
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
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
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
