"""Тесты LLM-клиента: имя параметра лимита ответа и обработка ошибок HTTP.

Реальных запросов к LLM нет — сессия `requests` подменяется двойником.
"""

from unittest.mock import Mock

import requests
from django.test import TestCase, override_settings

from candidate_trainer.services.exceptions import LLMError
from candidate_trainer.services.llm import (
    DisabledLLMClient,
    OpenAICompatibleLLMClient,
    get_llm_client,
)


def build_client(response):
    session = Mock()
    session.post.return_value = response
    client = OpenAICompatibleLLMClient(
        provider="OpenAI",
        model="test-model",
        api_url="https://llm.test/v1/chat/completions",
        api_key="secret-key",
        timeout=5,
        session=session,
    )
    return client, session


def ok_response(text="Ответ модели."):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": text}}]}
    return response


class OpenAITokenParameterTest(TestCase):
    def test_default_parameter_is_max_tokens(self):
        """Прежнее поведение: без настройки уходит max_tokens."""
        client, session = build_client(ok_response())

        client.complete("система", [{"role": "user", "content": "вопрос"}])

        payload = session.post.call_args.kwargs["json"]
        self.assertIn("max_tokens", payload)
        self.assertNotIn("max_completion_tokens", payload)

    @override_settings(LLM_MAX_TOKENS_PARAM="max_completion_tokens")
    def test_parameter_name_comes_from_settings(self):
        """Новые модели OpenAI принимают только max_completion_tokens."""
        client, session = build_client(ok_response())

        client.complete("система", [{"role": "user", "content": "вопрос"}])

        payload = session.post.call_args.kwargs["json"]
        self.assertIn("max_completion_tokens", payload)
        self.assertNotIn("max_tokens", payload)

    def test_explicit_max_tokens_wins_over_setting(self):
        with override_settings(LLM_MAX_TOKENS=1200):
            client, session = build_client(ok_response())

            client.complete(
                "система",
                [{"role": "user", "content": "вопрос"}],
                max_tokens=42,
            )

        payload = session.post.call_args.kwargs["json"]
        self.assertEqual(payload["max_tokens"], 42)


class OpenAITemperatureTest(TestCase):
    def test_default_sends_temperature(self):
        """Прежнее поведение: без настройки уходит temperature=0.2."""
        client, session = build_client(ok_response())

        client.complete("система", [{"role": "user", "content": "вопрос"}])

        payload = session.post.call_args.kwargs["json"]
        self.assertEqual(payload["temperature"], 0.2)

    @override_settings(LLM_TEMPERATURE=None)
    def test_empty_setting_omits_temperature(self):
        """Часть моделей принимает только значение по умолчанию — параметр не шлём."""
        client, session = build_client(ok_response())

        client.complete("система", [{"role": "user", "content": "вопрос"}])

        payload = session.post.call_args.kwargs["json"]
        self.assertNotIn("temperature", payload)

    @override_settings(LLM_TEMPERATURE=0.0)
    def test_zero_temperature_is_sent(self):
        """Ноль — валидное значение и не должен трактоваться как «не задано»."""
        client, session = build_client(ok_response())

        client.complete("система", [{"role": "user", "content": "вопрос"}])

        payload = session.post.call_args.kwargs["json"]
        self.assertEqual(payload["temperature"], 0.0)


class OpenAIClientErrorsTest(TestCase):
    def test_http_error_becomes_llm_error(self):
        """400 от провайдера не должен утекать наружу как requests-исключение."""
        response = Mock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("400")
        client, _ = build_client(response)

        with self.assertRaises(LLMError):
            client.complete("система", [{"role": "user", "content": "вопрос"}])

    def test_api_key_never_appears_in_error_message(self):
        response = Mock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("401")
        client, _ = build_client(response)

        with self.assertRaises(LLMError) as context:
            client.complete("система", [{"role": "user", "content": "вопрос"}])

        self.assertNotIn("secret-key", str(context.exception))

    def test_incomplete_settings_raise_llm_error(self):
        client = OpenAICompatibleLLMClient(
            provider="OpenAI",
            model="",
            api_url="https://llm.test/v1/chat/completions",
            api_key="secret-key",
            timeout=5,
            session=Mock(),
        )

        with self.assertRaisesMessage(LLMError, "заполнены не полностью"):
            client.complete("система", [])


class GetLLMClientTest(TestCase):
    @override_settings(LLM_PROVIDER="disabled")
    def test_disabled_provider_returns_disabled_client(self):
        self.assertIsInstance(get_llm_client(), DisabledLLMClient)

    @override_settings(
        LLM_PROVIDER="OpenAI",
        LLM_MODEL="test-model",
        LLM_API_URL="https://llm.test/v1/chat/completions",
        LLM_API_KEY="secret-key",
    )
    def test_configured_provider_returns_openai_client(self):
        self.assertIsInstance(get_llm_client(), OpenAICompatibleLLMClient)
