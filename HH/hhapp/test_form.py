from django.test import TestCase
from .forms import ContactForm
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

    def test_reg_form_is_valid(self):
        self.assertTrue(self.form.is_valid())

    def test_send_email(self):
        self.assertTrue(self.form.send_email)

    def test_reg_form_not_valid(self):
        self.assertFalse(self.form_not_valid.is_valid())