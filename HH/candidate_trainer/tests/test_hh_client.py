from unittest.mock import Mock

from django.test import SimpleTestCase, override_settings

from candidate_trainer.services.exceptions import HHAPIError
from candidate_trainer.services.hh_client import HHClient


@override_settings(
    HH_API_DOMAIN="https://api.hh.test/",
    HH_ACCESS_TOKEN="secret-token",
    HH_REQUIRE_ACCESS_TOKEN=True,
    HH_USER_AGENT="HH_Django tests",
    HH_REQUEST_TIMEOUT=7,
)
class HHClientTest(SimpleTestCase):
    def test_search_uses_area_token_user_agent_and_deduplicates_ids(self):
        response = Mock()
        response.json.return_value = {
            "items": [{"id": "10"}, {"id": "10"}, {"id": "11"}],
        }
        session = Mock()
        session.get.return_value = response

        result = HHClient(session=session).search_vacancy_ids(
            "Python",
            "1",
            limit=20,
        )

        self.assertEqual(result, ["10", "11"])
        session.get.assert_called_once_with(
            "https://api.hh.test/vacancies",
            params={
                "text": "Python",
                "area": "1",
                "page": 0,
                "per_page": 20,
            },
            headers={
                "User-Agent": "HH_Django tests",
                "Authorization": "Bearer secret-token",
            },
            timeout=7,
        )
        response.raise_for_status.assert_called_once()

    def test_incomplete_card_has_safe_defaults(self):
        response = Mock()
        response.json.return_value = {
            "id": "10",
            "name": "Python developer",
            "alternate_url": "https://hh.test/vacancy/10",
            "employer": None,
            "description": None,
            "key_skills": None,
        }
        session = Mock()
        session.get.return_value = response

        card = HHClient(session=session).get_vacancy("10")

        self.assertEqual(card.employer, "")
        self.assertEqual(card.description, "")
        self.assertEqual(card.key_skills, ())

    @override_settings(HH_ACCESS_TOKEN="")
    def test_missing_required_token_stops_before_request(self):
        session = Mock()

        with self.assertRaisesMessage(
            HHAPIError,
            "HH_ACCESS_TOKEN",
        ):
            HHClient(session=session).search_vacancy_ids("Python", "1")

        session.get.assert_not_called()
