from django.test import TestCase
from .models import Vacancies, Employer
from mixer.backend.django import mixer

class VacanciesEmployerTestCaseMixer(TestCase):

    def setUp(self):
        self.vac_str = mixer.blend(Vacancies, vac_name = 'test_vac_str', employer__employer_name = 'test_employer')
        self.emp_str = mixer.blend(Employer, employer_name = 'test_employer_name')

    def test_vac_str(self):
        self.assertEqual(str(self.vac_str), 'test_vac_str, employer: test_employer')

    def test_emp_str(self):
        self.assertEqual(str(self.emp_str), 'test_employer_name')