from django.test import Client, TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from userapp.models import WebSiteUser

from .models import Employer, Vacancies


class ApiRequestViewsTest(TestCase):
    def setUp(self):
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
