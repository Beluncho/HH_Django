from django.core.management.base import BaseCommand, CommandError

from candidate_trainer.services.exceptions import LLMError
from candidate_trainer.services.llm import get_llm_client


class Command(BaseCommand):
    help = "Проверяет настройки LLM и выполняет короткий тестовый запрос."

    def handle(self, *args, **options):
        try:
            response = get_llm_client().complete(
                "Ты проверяешь доступность LLM API.",
                [
                    {
                        "role": "user",
                        "content": "Ответь одним словом: OK",
                    }
                ],
                max_tokens=8,
            )
        except LLMError as error:
            raise CommandError(str(error)) from error

        self.stdout.write(
            self.style.SUCCESS(
                "LLM подключена: "
                f"provider={response.provider}, model={response.model}"
            )
        )
