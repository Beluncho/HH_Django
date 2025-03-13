import pprint

from django.test import Client
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from faker import Faker
from .models import Employer, Vacancies
from userapp.models import WebSiteUser
from .views import ContactView, VacDetailView, VacancyCreateView, EmployerCreateView
from mixer.backend.django import mixer


class ViewsHHappTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.fake = Faker()

        VacancyCreateView.create_vacancy = mixer.blend(Vacancies)
        EmployerCreateView.create_employer = mixer.blend(Employer)

    def test_statuses(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200) , 'Not found homepage'

        response = self.client.get('')
        self.assertEqual(response.status_code, 200), 'Not found homepage'

        response = self.client.get('/employers_list/')
        self.assertEqual(response.status_code, 200), 'Not found list of employers'


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

        response = self.client.get('/employer_update/1/')
        self.assertEqual(response.status_code, 302), ('error status code for not login user'
                                                      ' in update employer')

        response = self.client.get('/employer_delete/1/')
        self.assertEqual(response.status_code, 302), ('error status code for not login user'
                                                      ' in delete employer')

        response = self.client.get('/employer_detail/1/')
        self.assertEqual(response.status_code, 302), ('error status code for not login user'
                                                      ' in detail employer')


        self.client.login(username=user_name, password=password)

        response = self.client.get('/vacancy_create/')
        self.assertEqual(response.status_code, 200), ('error status code for login user '
                                                                'in create vacancy')

        response = self.client.get('/employer_create/')
        self.assertEqual(response.status_code, 200), ('error status code for not login user'
                                                      ' in create employer')

        response = self.client.get('/employer_detail/1/')
        self.assertEqual(response.status_code, 200), ('error status code for login user'
                                                      ' in detail employer')

        response = self.client.get('/employer_update/1/')
        self.assertEqual(response.status_code, 200), ('error status code for login user'
                                                      ' in update employer')

        response = self.client.get('/employer_delete/1/')
        self.assertEqual(response.status_code, 200), ('error status code for login user'
                                                      ' in delete employer')

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

        response = self.client.get('/employer_create/')
        self.assertEqual(response.status_code, 403), 'login user and not employer, create employer'