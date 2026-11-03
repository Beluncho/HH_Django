from django.test import TestCase, override_settings

from candidate_trainer.models import KnowledgeChunk, VacancyAnalysis
from candidate_trainer.services.analysis import (
    create_or_get_analysis,
    run_analysis,
)
from candidate_trainer.services.embeddings import HashEmbeddingService
from candidate_trainer.services.exceptions import CandidateTrainerError, HHAPIError
from candidate_trainer.services.hh_client import HHVacancyData
from userapp.models import WebSiteUser

from .fakes import FakeHHClient


@override_settings(HH_ANALYSIS_LIMIT=20)
class VacancyAnalysisServiceTest(TestCase):
    def setUp(self):
        self.user = WebSiteUser.objects.create_user(
            username="candidate",
            email="candidate@example.com",
            password="test-password",
        )
        self.embedding_service = HashEmbeddingService(
            dimension=16,
            model_name="test-hash-v1",
        )

    def create_analysis(self, query="Python developer"):
        analysis, _ = create_or_get_analysis(
            user=self.user,
            query=query,
            area_id="1",
            area_name="Москва",
        )
        return analysis

    def test_frequency_counts_source_vacancies_not_word_repetitions(self):
        cards = [
            HHVacancyData(
                external_id="1",
                title="Python developer",
                employer="One",
                url="https://hh.test/1",
                published_at="2026-08-01T10:00:00+03:00",
                description=(
                    "<p>Python Python Python. Разработка API на Django.</p>"
                ),
                key_skills=("Python", "python3", "Django"),
            ),
            HHVacancyData(
                external_id="2",
                title="Backend developer",
                employer="Two",
                url="https://hh.test/2",
                published_at=None,
                description="<p>Работа с Python и SQL в production.</p>",
                key_skills=("python3", "SQL"),
            ),
        ]
        analysis = self.create_analysis()

        run_analysis(
            analysis.pk,
            hh_client=FakeHHClient(cards),
            embedding_service=self.embedding_service,
        )

        analysis.refresh_from_db()
        python_skill = analysis.analysis_skills.select_related("skill").get(
            skill__normalized_name="python"
        )
        self.assertEqual(analysis.status, VacancyAnalysis.Status.COMPLETED)
        self.assertEqual(analysis.vacancies_processed, 2)
        self.assertEqual(python_skill.vacancy_count, 2)
        self.assertEqual(str(python_skill.frequency_percent), "100.00")
        self.assertEqual(python_skill.variants, ["Python", "python3"])
        self.assertGreater(
            KnowledgeChunk.objects.filter(skill=python_skill.skill).count(),
            0,
        )

    def test_same_normalized_query_and_area_reuses_analysis(self):
        first, first_created = create_or_get_analysis(
            user=self.user,
            query=" Python   Developer ",
            area_id="1",
            area_name="Москва",
        )
        second, second_created = create_or_get_analysis(
            user=self.user,
            query="python developer",
            area_id="1",
            area_name="Москва",
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first.pk, second.pk)

    def test_single_card_error_keeps_partial_result(self):
        card = HHVacancyData(
            external_id="1",
            title="Python developer",
            employer="One",
            url="https://hh.test/1",
            published_at=None,
            description="Разработка приложений.",
            key_skills=("Python",),
        )
        analysis = self.create_analysis()
        client = FakeHHClient(
            [card],
            vacancy_ids=["1", "2"],
            failing_ids=["2"],
        )

        run_analysis(
            analysis.pk,
            hh_client=client,
            embedding_service=self.embedding_service,
        )

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, VacancyAnalysis.Status.COMPLETED)
        self.assertEqual(analysis.vacancies_found, 2)
        self.assertEqual(analysis.vacancies_processed, 1)
        self.assertIn("1", analysis.error_message)

    def test_all_card_errors_mark_analysis_failed(self):
        analysis = self.create_analysis()
        client = FakeHHClient([], vacancy_ids=["1"], failing_ids=["1"])

        with self.assertRaises(HHAPIError):
            run_analysis(
                analysis.pk,
                hh_client=client,
                embedding_service=self.embedding_service,
            )

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, VacancyAnalysis.Status.FAILED)
        self.assertIn("ни одной", analysis.error_message)

    def test_missing_description_and_skills_do_not_break_analysis(self):
        card = HHVacancyData(
            external_id="1",
            title="Developer",
            employer="One",
            url="https://hh.test/1",
            published_at=None,
            description="",
            key_skills=(),
        )
        analysis = self.create_analysis()

        run_analysis(
            analysis.pk,
            hh_client=FakeHHClient([card]),
            embedding_service=self.embedding_service,
        )

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, VacancyAnalysis.Status.COMPLETED)
        self.assertEqual(analysis.analysis_skills.count(), 0)

    def test_alias_variants_in_one_vacancy_are_kept_without_double_counting(self):
        card = HHVacancyData(
            external_id="1",
            title="Python developer",
            employer="One",
            url="https://hh.test/1",
            published_at=None,
            description="Разработка приложений.",
            key_skills=("Python", "python3"),
        )
        analysis = self.create_analysis()

        run_analysis(
            analysis.pk,
            hh_client=FakeHHClient([card]),
            embedding_service=self.embedding_service,
        )

        python_skill = analysis.analysis_skills.get(
            skill__normalized_name="python"
        )
        self.assertEqual(python_skill.vacancy_count, 1)
        self.assertEqual(python_skill.variants, ["Python", "python3"])

    def test_duplicate_search_ids_are_processed_once(self):
        card = HHVacancyData(
            external_id="1",
            title="Python developer",
            employer="One",
            url="https://hh.test/1",
            published_at=None,
            description="Разработка приложений.",
            key_skills=("Python",),
        )
        analysis = self.create_analysis()
        client = FakeHHClient([card], vacancy_ids=["1", "1"])

        run_analysis(
            analysis.pk,
            hh_client=client,
            embedding_service=self.embedding_service,
        )

        analysis.refresh_from_db()
        self.assertEqual(client.detail_calls, ["1"])
        self.assertEqual(analysis.vacancies_found, 1)
        self.assertEqual(analysis.vacancies_processed, 1)

    def test_force_reruns_completed_analysis_and_replaces_skill_result(self):
        first_card = HHVacancyData(
            external_id="1",
            title="Python developer",
            employer="One",
            url="https://hh.test/1",
            published_at=None,
            description="Python.",
            key_skills=("Python",),
        )
        second_card = HHVacancyData(
            external_id="2",
            title="SQL developer",
            employer="Two",
            url="https://hh.test/2",
            published_at=None,
            description="SQL.",
            key_skills=("SQL",),
        )
        analysis = self.create_analysis()
        run_analysis(
            analysis.pk,
            hh_client=FakeHHClient([first_card]),
            embedding_service=self.embedding_service,
        )

        run_analysis(
            analysis.pk,
            hh_client=FakeHHClient([second_card]),
            embedding_service=self.embedding_service,
            force=True,
        )

        analysis.refresh_from_db()
        self.assertEqual(
            list(
                analysis.analysis_skills.values_list(
                    "skill__normalized_name",
                    flat=True,
                )
            ),
            ["sql"],
        )
        self.assertEqual(
            list(analysis.vacancies.values_list("external_id", flat=True)),
            ["2"],
        )

    def test_running_analysis_cannot_be_claimed_twice(self):
        analysis = self.create_analysis()
        analysis.status = VacancyAnalysis.Status.RUNNING
        analysis.save(update_fields=["status"])

        with self.assertRaisesMessage(
            CandidateTrainerError,
            "уже выполняется",
        ):
            run_analysis(
                analysis.pk,
                hh_client=FakeHHClient([]),
                embedding_service=self.embedding_service,
            )

        analysis.refresh_from_db()
        self.assertEqual(analysis.status, VacancyAnalysis.Status.RUNNING)
