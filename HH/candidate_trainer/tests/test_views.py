from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from candidate_trainer.models import (
    AnalysisSkill,
    InterviewSession,
    Skill,
    VacancyAnalysis,
)
from userapp.models import WebSiteUser


class CandidateTrainerAccessTest(TestCase):
    def setUp(self):
        self.owner = WebSiteUser.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="test-password",
        )
        self.other = WebSiteUser.objects.create_user(
            username="other",
            email="other@example.com",
            password="test-password",
        )
        self.analysis = VacancyAnalysis.objects.create(
            user=self.owner,
            query="Python",
            normalized_query="python",
            area_id="1",
            area_name="Москва",
            cache_key="owner-cache",
            status=VacancyAnalysis.Status.COMPLETED,
        )
        self.skill = Skill.objects.create(
            canonical_name="Python",
            normalized_name="python",
        )
        self.analysis_skill = AnalysisSkill.objects.create(
            analysis=self.analysis,
            skill=self.skill,
            vacancy_count=1,
            frequency_percent="100.00",
            rank=1,
            variants=["Python"],
        )
        self.session = InterviewSession.objects.create(
            user=self.owner,
            analysis=self.analysis,
            current_skill=self.skill,
        )

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("candidate_trainer:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/user/login/", response.url)

    def test_other_user_cannot_open_analysis(self):
        self.client.force_login(self.other)

        response = self.client.get(
            reverse(
                "candidate_trainer:analysis_detail",
                kwargs={"pk": self.analysis.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_open_interview(self):
        self.client.force_login(self.other)

        response = self.client.get(
            reverse(
                "candidate_trainer:interview_detail",
                kwargs={"pk": self.session.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_other_user_cannot_request_skill_explanation(self):
        self.client.force_login(self.other)

        response = self.client.post(
            reverse(
                "candidate_trainer:skill_explanation",
                kwargs={"pk": self.analysis_skill.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    @patch("candidate_trainer.views.run_analysis")
    def test_analysis_run_forces_refresh(self, run_analysis):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "candidate_trainer:analysis_run",
                kwargs={"pk": self.analysis.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "candidate_trainer:analysis_detail",
                kwargs={"pk": self.analysis.pk},
            ),
        )
        run_analysis.assert_called_once_with(self.analysis.pk, force=True)
