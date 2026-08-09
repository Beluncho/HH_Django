from dataclasses import dataclass

import requests
from django.conf import settings

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
            "LLM не настроен. Укажите LLM_PROVIDER, LLM_MODEL, "
            "LLM_API_URL и LLM_API_KEY."
        )


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        provider,
        model,
        api_url,
        api_key,
        timeout,
        session=None,
    ):
        self.provider = provider
        self.model = model
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
        self.session = session or requests.Session()

    def complete(self, system_prompt, messages, max_tokens=None):
        if not all((self.model, self.api_url, self.api_key)):
            raise LLMError("Настройки LLM заполнены не полностью")

        payload_messages = [{"role": "system", "content": system_prompt}]
        payload_messages.extend(messages)
        try:
            response = self.session.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": payload_messages,
                    "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
                    "temperature": 0.2,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            text = payload["choices"][0]["message"]["content"]
        except (
            requests.RequestException,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ) as error:
            raise LLMError("LLM-сервис временно недоступен") from error

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
        api_url=settings.LLM_API_URL,
        api_key=settings.LLM_API_KEY,
        timeout=settings.LLM_TIMEOUT,
    )
