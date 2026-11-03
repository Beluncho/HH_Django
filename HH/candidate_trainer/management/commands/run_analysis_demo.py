from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from candidate_trainer.management.demo_utils import (
    HASH_MODEL_NAME,
    build_embedding_service,
    ensure_database_ready,
    resolve_area,
    resolve_user,
    write_run_header,
    write_skill_table,
    write_sources,
)
from candidate_trainer.models import VacancyAnalysis
from candidate_trainer.services.analysis import (
    create_or_get_analysis,
    run_analysis,
)
from candidate_trainer.services.exceptions import CandidateTrainerError
from candidate_trainer.services.interview import explain_skill


class Command(BaseCommand):
    help = (
        "Локальный прогон анализа вакансий: топ-навыки и, по флагу --explain, "
        "объяснение навыка. Запускайте через ./run_local.sh либо с переменными "
        "окружения, экспортированными вручную."
    )

    def add_arguments(self, parser):
        parser.add_argument("query", help="Название вакансии или специальности")
        parser.add_argument(
            "--area",
            default="1",
            help="id региона из HH_AREA_CHOICES (по умолчанию 1 — Москва)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Сколько вакансий брать, 1–20",
        )
        parser.add_argument(
            "--embedding",
            choices=("hash", "sentence_transformers"),
            default=None,
            help="Провайдер embeddings; по умолчанию берётся из настроек",
        )
        parser.add_argument(
            "--explain",
            action="store_true",
            help="Сгенерировать объяснение навыка с рангом 1 через LLM",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Пересчитать уже выполненный анализ того же запроса и региона",
        )
        parser.add_argument(
            "--user",
            default=None,
            help="username; без значения берётся первый пользователь или создаётся demo",
        )

    def handle(self, *args, **options):
        ensure_database_ready()
        area_id, area_name = resolve_area(options["area"])
        user, user_created = resolve_user(options["user"])
        if user_created:
            self.stdout.write(
                self.style.WARNING(f"Создан пользователь «{user.username}»")
            )

        if options["limit"] is not None:
            if options["limit"] < 1:
                raise CommandError("--limit должен быть не меньше 1")
            # run_analysis читает settings.HH_ANALYSIS_LIMIT в момент вызова,
            # а HHClient дополнительно ограничивает значение диапазоном 1..20.
            settings.HH_ANALYSIS_LIMIT = options["limit"]

        embedding_service = build_embedding_service(options["embedding"])

        write_run_header(
            self,
            query=options["query"],
            area_id=area_id,
            area_name=area_name,
            user=user,
            embedding_service=embedding_service,
        )

        try:
            analysis, reused = create_or_get_analysis(
                user=user,
                query=options["query"],
                area_id=area_id,
                area_name=area_name,
            )
        except CandidateTrainerError as error:
            raise CommandError(str(error)) from error

        if (
            reused
            and analysis.status == VacancyAnalysis.Status.COMPLETED
            and not options["force"]
        ):
            self.stdout.write(
                "Использован ранее выполненный анализ этого запроса и региона."
            )

        try:
            analysis = run_analysis(
                analysis.pk,
                embedding_service=embedding_service,
                force=options["force"],
            )
        except CandidateTrainerError as error:
            raise CommandError(str(error)) from error

        self._write_summary(analysis)
        write_skill_table(self, analysis)

        if embedding_service.model_name == HASH_MODEL_NAME:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING(
                    "Использован hash-провайдер: векторы не семантические. "
                    "Перед переходом на реальную модель выполните "
                    "reindex_embeddings, иначе смешаются векторы разных моделей."
                )
            )

        if options["explain"]:
            self._explain_top_skill(analysis, user)

    def _write_summary(self, analysis):
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Анализ #{analysis.pk}: {analysis.query} — {analysis.area_name}"
            )
        )
        self.stdout.write(
            f"Найдено вакансий: {analysis.vacancies_found}, "
            f"обработано: {analysis.vacancies_processed}"
        )
        if analysis.error_message:
            self.stdout.write(self.style.WARNING(analysis.error_message))
        self.stdout.write("")

    def _explain_top_skill(self, analysis, user):
        top_skill = (
            analysis.analysis_skills.select_related("skill").order_by("rank").first()
        )
        if top_skill is None:
            raise CommandError("В анализе нет навыков — объяснять нечего")

        try:
            explanation = explain_skill(top_skill, user=user)
        except CandidateTrainerError as error:
            raise CommandError(str(error)) from error

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Объяснение навыка «{top_skill.skill.canonical_name}»:"
            )
        )
        self.stdout.write(explanation.content)
        if explanation.sources:
            self.stdout.write("")
            write_sources(self, explanation.sources)
