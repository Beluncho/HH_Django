import pprint

from django.test import Client
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from faker import Faker
from .models import Employer, Vacancies
from userapp.models import WebSiteUser
from .views import ContactView, VacDetailView
from mixer.backend.django import mixer


class ViewsHHappTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.fake = Faker()

    def test_statuses(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200) , 'Not found homepage'

        response = self.client.get('')
        self.assertEqual(response.status_code, 200), 'Not found homepage'

        response = self.client.get('/employers_list/')
        self.assertEqual(response.status_code, 200), 'Not found list of employers'

        response = self.client.get('http://127.0.0.1:8000/#services/vacancy/1/')
        self.assertEqual(response.status_code, 200) , 'Not found vacancy_id=1'
        self.assertTrue('vacancies' in response.context)

        response = self.client.get('http://127.0.0.1:8000/#employers/employers_list/employer_detail/1/')
        self.assertEqual(response.status_code, 200), 'Not found employer_id=1'



    def test_login_required(self):
        user_name = f'{self.fake.user_name()}'
        email = f'{self.fake.email()}'
        password = f'{self.fake.password()}'

        WebSiteUser.objects.create_user(username=user_name,
                                        email=email,
                                        password=password, is_employer = True)

        response = self.client.get('/vacancy_create/')
        self.assertEqual(response.status_code, 302), ('error status code for not login user '
                                                                'in create vacancy')

        response = self.client.get('/employer_create/')
        self.assertEqual(response.status_code, 302), ('error status code for not login user'
                                                      ' in create employer')

        self.client.login(username=user_name, password=password)

        response = self.client.get('/vacancy_create/')
        self.assertEqual(response.status_code, 200), ('error status code for login user '
                                                                'in create vacancy')

        response = self.client.get('/employer_create/')
        self.assertEqual(response.status_code, 200), ('error status code for not login user'
                                                      ' in create employer')

        response = self.client.post('/user/logout/')
        self.assertEqual(response.status_code, 302), 'logout error'

    def test_login_required_403(self):
        user_name = f'{self.fake.user_name()}'
        email = f'{self.fake.email()}'
        password = f'{self.fake.password()}'

        WebSiteUser.objects.create_user(username=user_name,
                                        email=email,
                                        password=password, is_employer=False)

        self.client.login(username=user_name, password=password)

        response = self.client.get('/employer_create/'), 'login user and not employer, create employer'
        self.assertEqual(response.status_code, 403)