from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings

from candidate_trainer.services.exceptions import LLMError
from candidate_trainer.services.llm import (
    DisabledLLMClient,
    LLMResponse,
    OpenAICompatibleLLMClient,
    get_llm_client,
    normalize_base_url,
)


class OpenAICompatibleLLMClientTest(SimpleTestCase):
    def build_sdk_client(self, content=" Готово "):
        sdk_client = Mock()
        sdk_client.chat.completions.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=content),
                )
            ]
        )
        return sdk_client

    def test_proxy_base_url_is_passed_to_openai_sdk(self):
        with patch(
            "candidate_trainer.services.llm.OpenAI"
        ) as openai_client:
            client = OpenAICompatibleLLMClient(
                provider="proxyapi",
                model="anthropic/test-model",
                api_key="secret",
                timeout=12,
                base_url="https://openai.api.proxyapi.ru/v1/",
            )
            client._get_client()

        openai_client.assert_called_once_with(
            api_key="secret",
            timeout=12,
            base_url="https://openai.api.proxyapi.ru/v1",
        )

    def test_direct_openai_uses_sdk_default_base_url(self):
        with patch(
            "candidate_trainer.services.llm.OpenAI"
        ) as openai_client:
            client = OpenAICompatibleLLMClient(
                provider="openai",
                model="test-model",
                api_key="secret",
                timeout=12,
            )
            client._get_client()

        openai_client.assert_called_once_with(
            api_key="secret",
            timeout=12,
        )

    def test_complete_uses_chat_completions_and_returns_text(self):
        sdk_client = self.build_sdk_client()
        client = OpenAICompatibleLLMClient(
            provider="proxyapi",
            model="anthropic/test-model",
            api_key="secret",
            timeout=12,
            base_url="https://openai.api.proxyapi.ru/v1",
            client=sdk_client,
        )

        response = client.complete(
            "Системная инструкция",
            [{"role": "user", "content": "Привет"}],
            max_tokens=25,
        )

        self.assertEqual(
            response,
            LLMResponse(
                text="Готово",
                provider="proxyapi",
                model="anthropic/test-model",
            ),
        )
        sdk_client.chat.completions.create.assert_called_once_with(
            model="anthropic/test-model",
            messages=[
                {
                    "role": "system",
                    "content": "Системная инструкция",
                },
                {"role": "user", "content": "Привет"},
            ],
            max_tokens=25,
            temperature=0.2,
        )

    def test_legacy_full_endpoint_is_converted_to_base_url(self):
        self.assertEqual(
            normalize_base_url(
                "https://provider.test/v1/chat/completions/"
            ),
            "https://provider.test/v1",
        )

    def test_empty_response_raises_domain_error(self):
        client = OpenAICompatibleLLMClient(
            provider="proxyapi",
            model="anthropic/test-model",
            api_key="secret",
            timeout=12,
            client=self.build_sdk_client(content=None),
        )

        with self.assertRaisesMessage(LLMError, "пустой ответ"):
            client.complete("system", [])

    @override_settings(
        LLM_PROVIDER="proxyapi",
        LLM_MODEL="anthropic/test-model",
        LLM_API_KEY="secret",
        LLM_TIMEOUT=12,
        LLM_BASE_URL="https://openai.api.proxyapi.ru/v1",
    )
    def test_factory_builds_proxy_client(self):
        client = get_llm_client()

        self.assertIsInstance(client, OpenAICompatibleLLMClient)
        self.assertEqual(
            client.base_url,
            "https://openai.api.proxyapi.ru/v1",
        )

    @override_settings(LLM_PROVIDER="disabled")
    def test_factory_builds_disabled_client(self):
        self.assertIsInstance(get_llm_client(), DisabledLLMClient)


class CheckLLMCommandTest(SimpleTestCase):
    @patch("candidate_trainer.management.commands.check_llm.get_llm_client")
    def test_command_checks_connection_without_printing_key(
        self,
        get_llm_client_mock,
    ):
        llm_client = Mock()
        llm_client.complete.return_value = LLMResponse(
            text="OK",
            provider="proxyapi",
            model="anthropic/test-model",
        )
        get_llm_client_mock.return_value = llm_client
        stdout = StringIO()

        call_command("check_llm", stdout=stdout)

        self.assertIn("provider=proxyapi", stdout.getvalue())
        self.assertNotIn("secret", stdout.getvalue())
        llm_client.complete.assert_called_once()

    @patch("candidate_trainer.management.commands.check_llm.get_llm_client")
    def test_command_reports_llm_error(self, get_llm_client_mock):
        llm_client = Mock()
        llm_client.complete.side_effect = LLMError("Нет подключения")
        get_llm_client_mock.return_value = llm_client

        with self.assertRaisesMessage(CommandError, "Нет подключения"):
            call_command("check_llm")
