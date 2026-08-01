from unittest.mock import Mock, patch

from django.test import TestCase

from hhapp.management.commands.full_db import hh_parce
from hhapp.models import Employer, Vacancies
from hhapp.services import HHAPIError, search_hh_vacancies
from userapp.models import WebSiteUser


class HHServiceTest(TestCase):
    @patch('hhapp.services.requests.get')
    def test_search_normalizes_hh_response(self, mocked_get):
        response = Mock()
        response.json.return_value = {
            'items': [{
                'name': 'Python developer',
                'employer': {'name': 'Example'},
                'alternate_url': 'https://hh.ru/vacancy/1',
                'published_at': '2026-08-01T10:00:00+0300',
                'salary': {
                    'from': 100000,
                    'to': 150000,
                    'currency': 'RUR',
                },
            }],
        }
        mocked_get.return_value = response

        vacancies = search_hh_vacancies('Python')

        self.assertEqual(vacancies[0]['name'], 'Python developer')
        self.assertEqual(vacancies[0]['employer'], 'Example')
        self.assertEqual(vacancies[0]['salary_from'], 100000)
        mocked_get.assert_called_once()
        response.raise_for_status.assert_called_once()


class VacancySearchViewTest(TestCase):
    def setUp(self):
        user = WebSiteUser.objects.create_user(
            username='search_user',
            email='search@example.com',
            password='test-password',
        )
        employer = Employer.objects.create(employer_name='Example')
        Vacancies.objects.create(
            vac_name='Python developer',
            url_vac='https://example.com/python',
            employer=employer,
            salaryFrom=100000,
            user=user,
        )
        Vacancies.objects.create(
            vac_name='Java developer',
            url_vac='https://example.com/java',
            employer=employer,
            salaryFrom=90000,
            user=user,
        )

    @patch('hhapp.views.search_hh_vacancies')
    def test_page_without_query_shows_all_local_vacancies(self, mocked_search):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['vacancies']), 2)
        mocked_search.assert_not_called()

    @patch('hhapp.views.search_hh_vacancies')
    def test_public_search_filters_local_and_shows_hh_results(self, mocked_search):
        mocked_search.return_value = [{
            'name': 'Python backend developer',
            'employer': 'HH employer',
            'url': 'https://hh.ru/vacancy/2',
            'published_at': None,
            'salary_from': None,
            'salary_to': None,
            'currency': '',
        }]

        response = self.client.get('/', {'q': 'Python'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['vacancies']), 1)
        self.assertEqual(response.context['vacancies'][0].vac_name, 'Python developer')
        self.assertEqual(response.context['hh_vacancies'][0]['employer'], 'HH employer')
        mocked_search.assert_called_once_with('Python')

    @patch('hhapp.views.search_hh_vacancies')
    def test_hh_error_does_not_break_local_results(self, mocked_search):
        mocked_search.side_effect = HHAPIError('HH.ru временно недоступен')

        response = self.client.get('/', {'q': 'Python'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['vacancies']), 1)
        self.assertContains(response, 'HH.ru временно недоступен')


class TerminalParserTest(TestCase):
    @patch('hhapp.management.commands.full_db.search_hh_vacancies')
    def test_terminal_parser_still_saves_vacancies(self, mocked_search):
        WebSiteUser.objects.create_user(
            username='parser_bot',
            email='parser@example.com',
            password='test-password',
        )
        mocked_search.return_value = [{
            'name': 'Python developer',
            'employer': 'Example',
            'url': 'https://hh.ru/vacancy/3',
            'published_at': '2026-08-01T10:00:00+0300',
            'salary_from': 120000,
            'salary_to': None,
            'currency': 'RUR',
        }]

        hh_parce('python developer', 'Москва')

        vacancy = Vacancies.objects.get()
        self.assertEqual(vacancy.vac_name, 'Python developer')
        self.assertEqual(vacancy.salaryFrom, 120000)
