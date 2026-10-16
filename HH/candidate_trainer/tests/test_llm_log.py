from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from candidate_trainer.models import LLMRequestLog
from candidate_trainer.services.exceptions import LLMError
from candidate_trainer.services.llm import LLMResponse, humanize_llm_error
from candidate_trainer.services.llm_log import record_llm_call

from .fakes import QueueLLMClient


class RecordLLMCallTest(TestCase):
    def call_with(self, client, operation=LLMRequestLog.Operation.EXPLANATION):
        with record_llm_call(
            operation,
            provider=client.provider,
            model=client.model,
        ) as call:
            call.remember(client.complete("Системная инструкция", []))

    def test_successful_call_is_journalled(self):
        self.call_with(QueueLLMClient(["Готово"]))

        entry = LLMRequestLog.objects.get()
        self.assertEqual(entry.status, LLMRequestLog.Status.OK)
        self.assertEqual(entry.operation, LLMRequestLog.Operation.EXPLANATION)
        self.assertEqual(entry.provider, "test")
        self.assertEqual(entry.model, "test-llm")
        self.assertIsNone(entry.http_status)
        self.assertEqual(entry.error_detail, "")
        self.assertGreaterEqual(entry.duration_ms, 0)

    def test_failed_call_is_journalled_and_reraised(self):
        client = QueueLLMClient(
            [
                LLMError(
                    "LLM-сервис вернул HTTP 400",
                    http_status=400,
                    provider_detail='{"detail":"Model not supported"}',
                )
            ]
        )

        with self.assertRaises(LLMError):
            self.call_with(client)

        entry = LLMRequestLog.objects.get()
        self.assertEqual(entry.status, LLMRequestLog.Status.ERROR)
        self.assertEqual(entry.http_status, 400)
        self.assertIn("Model not supported", entry.error_detail)
        # Провайдер и модель известны до запроса и должны попасть в журнал даже
        # тогда, когда ответа нет.
        self.assertEqual(entry.provider, "test")
        self.assertEqual(entry.model, "test-llm")

    def test_prompt_and_answer_text_are_not_stored(self):
        client = QueueLLMClient(["Секретный ответ модели"])

        with record_llm_call(
            LLMRequestLog.Operation.ANSWER_EVALUATION,
            provider=client.provider,
            model=client.model,
        ) as call:
            call.remember(
                client.complete(
                    "СЕКРЕТНЫЙ_ПРОМТ",
                    [{"role": "user", "content": "СЕКРЕТНЫЙ_ОТВЕТ_КАНДИДАТА"}],
                )
            )

        entry = LLMRequestLog.objects.get()
        stored = " ".join(
            str(getattr(entry, field.name)) for field in LLMRequestLog._meta.fields
        )
        self.assertNotIn("СЕКРЕТНЫЙ", stored)

    def test_token_usage_is_recorded(self):
        class TokenClient(QueueLLMClient):
            provider = "proxyapi"
            model = "test-model"

            def complete(self, system_prompt, messages, max_tokens=None):
                return LLMResponse(
                    text="Готово",
                    provider=self.provider,
                    model=self.model,
                    prompt_tokens=120,
                    completion_tokens=45,
                )

        self.call_with(TokenClient([]))

        entry = LLMRequestLog.objects.get()
        self.assertEqual(entry.prompt_tokens, 120)
        self.assertEqual(entry.completion_tokens, 45)

    def test_user_is_recorded(self):
        user = get_user_model().objects.create_user(
            username="candidate",
            password="secret",
        )
        client = QueueLLMClient(["Готово"])

        with record_llm_call(
            LLMRequestLog.Operation.CHECK,
            user=user,
            provider=client.provider,
            model=client.model,
        ):
            pass

        entry = LLMRequestLog.objects.get()
        self.assertEqual(entry.user, user)

    def test_journal_failure_does_not_break_the_call(self):
        client = QueueLLMClient(["Готово"])

        with patch(
            "candidate_trainer.services.llm_log.LLMRequestLog.objects.create",
            side_effect=Exception("журнал недоступен"),
        ):
            # Журнал не должен ломать основную операцию: даже если запись не
            # удалась, результат вызова остаётся доступен вызывающему коду.
            with record_llm_call(
                LLMRequestLog.Operation.CHECK,
                provider=client.provider,
                model=client.model,
            ) as call:
                response = call.remember(client.complete("system", []))

        self.assertEqual(response.text, "Готово")
        self.assertEqual(LLMRequestLog.objects.count(), 0)


class HumanizeLLMErrorTest(SimpleTestCase):
    def test_model_not_supported_points_at_llm_model(self):
        error = LLMError(
            "LLM-сервис вернул HTTP 400",
            http_status=400,
            provider_detail='{"detail":"Model not supported"}',
        )

        message = humanize_llm_error(error)

        self.assertIn("LLM_MODEL", message)
        self.assertNotIn("{", message)

    def test_limit_parameter_error_points_at_settings(self):
        error = LLMError(
            "LLM-сервис вернул HTTP 400",
            http_status=400,
            provider_detail=(
                "Unsupported parameter: 'max_tokens' is not supported with "
                "this model."
            ),
        )

        self.assertIn("LLM_MAX_TOKENS_PARAM", humanize_llm_error(error))

    def test_rejected_key_is_reported(self):
        error = LLMError(
            "LLM-сервис вернул HTTP 401",
            http_status=401,
            provider_detail='{"error":"invalid api key"}',
        )

        self.assertIn("LLM_API_KEY", humanize_llm_error(error))

    def test_error_without_provider_body_keeps_its_message(self):
        error = LLMError("Превышен таймаут обращения к LLM")

        self.assertEqual(
            humanize_llm_error(error),
            "Превышен таймаут обращения к LLM",
        )

    def test_foreign_error_is_returned_unchanged(self):
        self.assertEqual(
            humanize_llm_error(ValueError("другая ошибка")),
            "другая ошибка",
        )
