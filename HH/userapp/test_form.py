from django.test import TestCase
from .forms import RegistrationForm
from faker import Faker

class RegistrationFormTestCaseFaker(TestCase):

    def setUp(self):
        self.fake = Faker()
        self.pas = self.fake.password()

        self.form_data = {
            'username': f'{self.fake.user_name()}',
            'password1': f'{self.pas}',
            'password2': f'{self.pas}',
            'email': f'{self.fake.email()}'
        }
    def test_reg_form_is_valid(self):

        form = RegistrationForm(data=self.form_data)

        self.assertTrue(form.is_valid()), 'registration form is valid,but return false'

    def test_reg_form_not_valid(self):
        form_data = {
            'username':'',  # username missing
            'password1': f'{self.pas}',
            'password2': f'{self.pas}',
            'email': f'{self.fake.email()}'
        }

        form = RegistrationForm(data=form_data)

        self.assertFalse(form.is_valid()), 'registration form not valid,but return true'

    def test_save_profile(self):
        form = RegistrationForm(data=self.form_data)

        self.assertTrue(form.save()), 'WebSiteUser not save'