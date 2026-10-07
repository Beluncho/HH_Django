"""Тесты демонстрационных management-команд этапов 3 и 4.

Команды не должны ходить в HH API, LLM и Hugging Face: `run_analysis`,
`explain_skill` и LLM-клиент подменяются, а данные создаются прямо в тестовой
базе.
"""

import tempfile
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from candidate_trainer.management.demo_utils import (
    build_embedding_service,
    parse_int_list,
    resolve_area,
    resolve_user,
)
from candidate_trainer.models import (
    AnalysisSkill,
    HHVacancySnapshot,
    Skill,
    VacancyAnalysis,
)
from candidate_trainer.services.embeddings import (
    HashEmbeddingService,
    SentenceTransformerEmbeddingService,
)
from userapp.models import WebSiteUser

RUN_EXPERIMENT = "candidate_trainer.management.commands.run_experiment.run_analysis"
RUN_DEMO = "candidate_trainer.management.commands.run_analysis_demo.run_analysis"
EXPLAIN_SKILL = "candidate_trainer.management.commands.run_analysis_demo.explain_skill"

DESCRIPTION = "Python Python Python. Django ORM. SQL запросы."


def seed_analysis(analysis_id, **kwargs):
    """Замена run_analysis: наполняет анализ готовыми данными, без сети."""
    analysis = VacancyAnalysis.objects.get(pk=analysis_id)

    snapshot = HHVacancySnapshot.objects.create(
        external_id=f"snap-{analysis.pk}",
        title="Python developer",
        employer="One",
        url="https://hh.test/1",
        description=DESCRIPTION,
    )
    analysis.vacancies.add(snapshot)
    analysis.vacancies_found = 1
    analysis.vacancies_processed = 1
    analysis.status = VacancyAnalysis.Status.COMPLETED
    analysis.save(
        update_fields=["vacancies_found", "vacancies_processed", "status"]
    )

    python_skill, _ = Skill.objects.get_or_create(
        normalized_name="python",
        defaults={"canonical_name": "Python"},
    )
    django_skill, _ = Skill.objects.get_or_create(
        normalized_name="django",
        defaults={"canonical_name": "Django"},
    )
    AnalysisSkill.objects.create(
        analysis=analysis,
        skill=python_skill,
        vacancy_count=1,
        frequency_percent=Decimal("100.00"),
        rank=1,
        variants=["Python"],
    )
    AnalysisSkill.objects.create(
        analysis=analysis,
        skill=django_skill,
        vacancy_count=1,
        frequency_percent=Decimal("100.00"),
        rank=2,
        variants=["Django"],
    )
    return analysis


class DemoUtilsTest(TestCase):
    def test_resolve_area_returns_name_from_settings(self):
        self.assertEqual(resolve_area("1"), ("1", "Москва"))

    def test_resolve_area_rejects_unknown_id(self):
        with self.assertRaises(CommandError):
            resolve_area("999")

    def test_resolve_user_returns_first_existing_user(self):
        user = WebSiteUser.objects.create_user(
            username="candidate",
            email="candidate@example.com",
        )
        resolved, created = resolve_user(None)
        self.assertEqual(resolved, user)
        self.assertFalse(created)

    def test_resolve_user_creates_demo_when_database_is_empty(self):
        resolved, created = resolve_user(None)
        self.assertTrue(created)
        self.assertEqual(resolved.username, "demo")

    def test_resolve_user_rejects_unknown_username(self):
        with self.assertRaises(CommandError):
            resolve_user("no-such-user")

    def test_parse_int_list_reads_comma_separated_values(self):
        self.assertEqual(parse_int_list("3, 4,6"), [3, 4, 6])

    def test_parse_int_list_rejects_garbage(self):
        with self.assertRaises(CommandError):
            parse_int_list("3,abc")

    def test_parse_int_list_enforces_bounds(self):
        with self.assertRaises(CommandError):
            parse_int_list("0", minimum=1)
        with self.assertRaises(CommandError):
            parse_int_list("21", maximum=20)
        with self.assertRaises(CommandError):
            parse_int_list(" , ")

    def test_build_embedding_service_uses_hash_provider(self):
        with override_settings(
            EMBEDDING_PROVIDER="hash",
            EMBEDDING_MODEL="local-hash-v1",
            EMBEDDING_DIMENSION=16,
        ):
            service = build_embedding_service(None)
        self.assertIsInstance(service, HashEmbeddingService)
        self.assertEqual(service.dimension, 16)

    def test_build_embedding_service_selects_sentence_transformers(self):
        service = build_embedding_service("sentence_transformers")
        self.assertIsInstance(service, SentenceTransformerEmbeddingService)

    def test_build_embedding_service_rejects_unknown_provider(self):
        with self.assertRaises(CommandError):
            build_embedding_service("fasttext")


@override_settings(EMBEDDING_PROVIDER="hash", EMBEDDING_MODEL="local-hash-v1")
class RunAnalysisDemoCommandTest(TestCase):
    def setUp(self):
        self.user = WebSiteUser.objects.create_user(
            username="candidate",
            email="candidate@example.com",
        )

    def run_command(self, *args):
        out = StringIO()
        with patch(RUN_DEMO, side_effect=seed_analysis):
            call_command("run_analysis_demo", *args, stdout=out)
        return out.getvalue()

    def test_prints_skill_table_and_hash_warning(self):
        out = self.run_command("Python-разработчик", "--area", "1")

        self.assertIn("РАНГ", out)
        self.assertIn("Python", out)
        self.assertIn("Django", out)
        self.assertIn("100.00%", out)
        self.assertIn("Найдено вакансий: 1", out)
        self.assertIn("reindex_embeddings", out)

    def test_prints_parameters_before_going_to_hh(self):
        """Терминал не должен молчать, пока идут запросы к HH API."""
        out = self.run_command("Python-разработчик", "--area", "1")

        self.assertIn("Регион: Москва (area=1)", out)
        self.assertIn("Ищу вакансии через HH API", out)

    def test_reports_missing_migrations_instead_of_traceback(self):
        """Без применённых миграций нужна понятная ошибка, а не no such table."""
        fake_connection = MagicMock()
        fake_connection.introspection.table_names.return_value = []

        with patch(
            "candidate_trainer.management.demo_utils.connection",
            fake_connection,
        ):
            with self.assertRaisesMessage(CommandError, "migrate"):
                call_command("run_analysis_demo", "Python", stdout=StringIO())

    def test_rejects_non_positive_limit(self):
        with self.assertRaises(CommandError):
            self.run_command("Python-разработчик", "--limit", "0")

    def test_explain_prints_generated_text_and_sources(self):
        class FakeExplanation:
            content = "Краткое объяснение навыка."
            sources = [
                {"title": "Карточка навыка", "url": "https://hh.test/skill"},
            ]

        out = StringIO()
        with (
            patch(RUN_DEMO, side_effect=seed_analysis),
            patch(EXPLAIN_SKILL, return_value=FakeExplanation()),
        ):
            call_command("run_analysis_demo", "Python", "--explain", stdout=out)

        output = out.getvalue()
        self.assertIn("Краткое объяснение навыка.", output)
        self.assertIn("https://hh.test/skill", output)

    def test_explain_reports_missing_llm_without_traceback(self):
        """Ошибка LLM или RAG не должна приводить к необработанному исключению."""
        out = StringIO()
        with patch(RUN_DEMO, side_effect=seed_analysis):
            with self.assertRaises(CommandError):
                call_command("run_analysis_demo", "Python", "--explain", stdout=out)


@override_settings(EMBEDDING_PROVIDER="hash", EMBEDDING_MODEL="local-hash-v1")
class RunExperimentCommandTest(TestCase):
    def setUp(self):
        self.user = WebSiteUser.objects.create_user(
            username="candidate",
            email="candidate@example.com",
        )

    def run_command(self, *args):
        out = StringIO()
        with patch(RUN_EXPERIMENT, side_effect=seed_analysis):
            call_command("run_experiment", *args, stdout=out)
        return out.getvalue()

    def test_frequency_experiment_compares_vacancies_and_mentions(self):
        out = self.run_command("frequency", "--query", "Python", "--area", "1")

        self.assertIn("=== ЭКСПЕРИМЕНТ: frequency ===", out)
        self.assertIn("УПОМИНАНИЙ", out)

        python_row = next(
            line
            for line in out.splitlines()
            if line.startswith("1 ") and "Python" in line
        )
        # Последние две колонки: вакансий и упоминаний в тексте.
        self.assertEqual(python_row.split()[-2:], ["1", "3"])

    def test_chunk_size_experiment_reports_chunk_counts(self):
        out = self.run_command(
            "chunk-size",
            "--query",
            "Python",
            "--area",
            "1",
            "--chunk-size",
            "100,200",
        )

        self.assertIn("max_chars=100:", out)
        self.assertIn("max_chars=200:", out)
        self.assertIn("Описаний в выборке: 1", out)

    def test_top_k_experiment_validates_range_before_analysis(self):
        """Битый --top-k должен падать до обращения к HH API."""
        with self.assertRaises(CommandError):
            with patch(RUN_EXPERIMENT) as mocked:
                call_command(
                    "run_experiment",
                    "top-k",
                    "--top-k",
                    "0",
                    stdout=StringIO(),
                )
        mocked.assert_not_called()

    def test_prompt_evaluation_requires_answer(self):
        with self.assertRaises(CommandError):
            self.run_command("prompt-evaluation")

    def test_prompt_variant_must_exist(self):
        with self.assertRaises(CommandError):
            self.run_command("prompt-evaluation", "--answer", "ответ", "--prompt-variant", "9")

    def test_out_writes_block_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = StringIO()
            with patch(RUN_EXPERIMENT, side_effect=seed_analysis):
                call_command(
                    "run_experiment",
                    "frequency",
                    "--query",
                    "Python",
                    "--area",
                    "1",
                    "--out",
                    tmp,
                    stdout=out,
                )
            path = Path(tmp) / "experiment_frequency.md"
            self.assertTrue(path.exists())
            self.assertIn("=== ЭКСПЕРИМЕНТ: frequency ===", path.read_text(encoding="utf-8"))
