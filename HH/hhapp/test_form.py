import pprint

from django.test import TestCase
from .forms import ContactForm, VacanciesEmployerForm
from faker import Faker

class ContactFormTestCaseFaker(TestCase):

    def setUp(self):
        self.fake = Faker()
        self.form_data = {
            'name': f'{self.fake.name()}',
            'phone_number': f'{self.fake.phone_number()}',
            'message': f'{self.fake.text()}',
            'email': f'{self.fake.email()}'
        }
        self.form = ContactForm(data=self.form_data)

        self.form_data_not_valid = {
            'name': '',  # username missing
            'phone_number': f'{self.fake.phone_number()}',
            'message': f'{self.fake.text()}',
            'email': f'{self.fake.email()}'
        }

        self.form_not_valid = ContactForm(data=self.form_data_not_valid)

    def test_contact_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_send_email(self):
        self.assertTrue(self.form.send_email)

    def test_contact_form_not_valid(self):
        self.assertFalse(self.form_not_valid.is_valid())

class VacanciesEmployerFormTestCaseFaker(TestCase):
    def setUp(self):
        self.fake = Faker()
        self.form_data = {'vac_name': f'{self.fake.job()}',
                          'url_vac': f'{self.fake.url()}',
                          'salaryFrom': f'{self.fake.postcode()}'
                            }
        self.form = VacanciesEmployerForm(data=self.form_data)

        self.form_data_not_valid = {'vac_name': '',
                                    'url_vac': f'{self.fake.url()}',
                                    'salaryFrom': f'{self.fake.postcode()}'
                                    }

        self.form_not_valid = VacanciesEmployerForm(data=self.form_data_not_valid)

    def test_vacancies_employer_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_vacancies_employer_form_not_valid(self):
        self.assertFalse(self.form_not_valid.is_valid())