import requests
from rest_framework.test import APIClient
from django.test import TestCase, Client
from faker import Faker
from userapp.models import WebSiteUser
from mixer.backend.django import mixer
from .models import Employer, Vacancies
from .views import VacancyCreateView, EmployerCreateView


class ApiRequestViewsTest(TestCase):
    def setUp(self):
        token = 'ace6427c9f11f1334bccd249f59587f7662d2b8b'
        self.headers = {'Authorization': f'Token {token}'}
        self.fake = Faker()
        self.client = Client()
        self.client_api = APIClient()
        VacancyCreateView.create_vacancy = mixer.blend(Vacancies)
        EmployerCreateView.create_employer = mixer.blend(Employer)
    def test_status_code(self):

        response = requests.get('http://127.0.0.1:8000/api/v0/vacancies/', auth=('testuser', '3230589AVB'))
        self.assertEqual(response.status_code,403), 'test base auth'
        response = requests.get('http://127.0.0.1:8000/api/v0/employers/', headers=self.headers)
        self.assertEqual(response.status_code,200), 'test token'

        user_name = f'{self.fake.user_name()}'
        email = f'{self.fake.email()}'
        password = f'{self.fake.password()}'

        WebSiteUser.objects.create_user(username=user_name,
                                        email=email,
                                        password=password, is_employer=True)

        self.client.login(username=user_name, password=password)

        response = self.client.get('http://127.0.0.1:8000/api/v0/employers/')
        self.assertEqual(response.status_code, 200), 'test session auth'

        response = self.client.get('http://127.0.0.1:8000/api/v0/vacancies/')
        self.assertEqual(response.status_code, 200), 'test session auth'

        self.client_api.login(username=user_name, password=password)

        response = self.client_api.get("http://127.0.0.1:8000/api/v0/employers/1/")
        self.assertEqual(response.status_code, 200)

        response = self.client_api.get("http://127.0.0.1:8000/api/v0/vacancies/1/")
        self.assertEqual(response.status_code, 200)

        response = self.client_api.put("http://127.0.0.1:8000/api/v0/employers/1/",
                                       {"employer_name":"test_employer_name"})
        self.assertEqual(response.status_code, 200)

        response = self.client_api.delete("http://127.0.0.1:8000/api/v0/vacancies/1/")
        self.assertEqual(response.status_code, 204)

        response = self.client_api.delete("http://127.0.0.1:8000/api/v0/employers/1/")
        self.assertEqual(response.status_code, 204)

        response = self.client_api.post("http://127.0.0.1:8000/api/v0/employers/",
                                        {"employer_name":"test_employer_name"})
        self.assertEqual(response.status_code, 201)

        self.client_api.logout()
        response = self.client_api.post("http://127.0.0.1:8000/api/v0/employers/",
                                        {"employer_name": "test_employer_name"})
        self.assertEqual(response.status_code, 403)