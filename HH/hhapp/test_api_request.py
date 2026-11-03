<<<<<<< HEAD
import requests
from rest_framework.test import APIClient
from django.test import TestCase, Client
from faker import Faker
from userapp.models import WebSiteUser
from mixer.backend.django import mixer
from .models import Employer, Vacancies
from .views import VacancyCreateView, EmployerCreateView
=======
from django.test import Client, TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from userapp.models import WebSiteUser

from .models import Employer, Vacancies
>>>>>>> AI_Agents_diploma


class ApiRequestViewsTest(TestCase):
    def setUp(self):
<<<<<<< HEAD
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
=======
        self.password = "test-password"
        self.token_user = WebSiteUser.objects.create_user(
            username="token-user",
            email="token-user@example.com",
            password=self.password,
        )
        self.token = Token.objects.create(user=self.token_user)
        self.employer_user = WebSiteUser.objects.create_user(
            username="employer-user",
            email="employer-user@example.com",
            password=self.password,
            is_employer=True,
        )
        self.employer = Employer.objects.create(
            employer_name="Initial employer",
        )
        self.vacancy = Vacancies.objects.create(
            vac_name="Python developer",
            url_vac="https://example.com/vacancy",
            employer=self.employer,
            salaryFrom=100000,
            user=self.employer_user,
        )
        self.client = Client()
        self.client_api = APIClient()

    def test_status_code(self):
        self.client_api.credentials(
            HTTP_AUTHORIZATION="Basic dGVzdHVzZXI6YmFkLXBhc3N3b3Jk",
        )
        response = self.client_api.get("/api/v0/vacancies/")
        self.assertEqual(response.status_code, 403), "test invalid basic auth"

        self.client_api.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        response = self.client_api.get("/api/v0/employers/")
        self.assertEqual(response.status_code, 200), "test token"

        self.client_api.credentials()
        self.client.login(
            username=self.employer_user.username,
            password=self.password,
        )

        response = self.client.get("/api/v0/employers/")
        self.assertEqual(response.status_code, 200), "test session auth"
        response = self.client.get("/api/v0/vacancies/")
        self.assertEqual(response.status_code, 200), "test session auth"

        self.client_api.login(
            username=self.employer_user.username,
            password=self.password,
        )
        employer_detail_url = f"/api/v0/employers/{self.employer.pk}/"
        vacancy_detail_url = f"/api/v0/vacancies/{self.vacancy.pk}/"

        response = self.client_api.get(employer_detail_url)
        self.assertEqual(response.status_code, 200)

        response = self.client_api.get(vacancy_detail_url)
        self.assertEqual(response.status_code, 200)

        response = self.client_api.put(
            employer_detail_url,
            {"employer_name": "test_employer_name"},
        )
        self.assertEqual(response.status_code, 200)

        response = self.client_api.delete(vacancy_detail_url)
        self.assertEqual(response.status_code, 204)

        response = self.client_api.delete(employer_detail_url)
        self.assertEqual(response.status_code, 204)

        response = self.client_api.post(
            "/api/v0/employers/",
            {"employer_name": "test_employer_name"},
        )
        self.assertEqual(response.status_code, 201)

        self.client_api.logout()
        response = self.client_api.post(
            "/api/v0/employers/",
            {"employer_name": "another_employer_name"},
        )
        self.assertEqual(response.status_code, 403)
>>>>>>> AI_Agents_diploma
