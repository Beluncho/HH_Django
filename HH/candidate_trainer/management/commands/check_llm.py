from django.core.management.base import BaseCommand, CommandError

from candidate_trainer.models import LLMRequestLog
from candidate_trainer.services.exceptions import LLMError
from candidate_trainer.services.llm import get_llm_client
from candidate_trainer.services.llm_log import record_llm_call


class Command(BaseCommand):
    help = "Проверяет настройки LLM и выполняет короткий тестовый запрос."

    def handle(self, *args, **options):
        llm_client = get_llm_client()
        try:
            with record_llm_call(
                LLMRequestLog.Operation.CHECK,
                provider=llm_client.provider,
                model=llm_client.model,
            ) as call:
                response = call.remember(
                    llm_client.complete(
                        "Ты проверяешь доступность LLM API.",
                        [
                            {
                                "role": "user",
                                "content": "Ответь одним словом: OK",
                            }
                        ],
                        max_tokens=8,
                    )
                )
        except LLMError as error:
            # Ответ провайдера печатаем целиком: без него «HTTP 400» не
            # подсказывает, что править. Ключ в теле ответа не приходит.
            message = str(error)
            if error.provider_detail:
                message = f"{message}. Ответ провайдера: {error.provider_detail}"
            raise CommandError(message) from error

        self.stdout.write(
            self.style.SUCCESS(
                "LLM подключена: "
                f"provider={response.provider}, model={response.model}"
            )
        )
