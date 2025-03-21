import requests
import userapp.views
from django.urls import reverse
from django.test import TestCase, Client
from faker import Faker
from userapp.models import WebSiteUser
from mixer.backend.django import mixer
from hhapp.models import Employer, Vacancies
from userapp.views import create_token


class UserViewsTest(TestCase):
    def setUp(self):
        fake = Faker()
        user_name = f'{fake.user_name()}'
        email = f'{fake.email()}'
        password = f'{fake.password()}'

        WebSiteUser.objects.create_user(username=user_name,
                                        email=email,
                                        password=password, is_employer=True)

        self.client.login(username=user_name, password=password)

    def test_status_code(self):
        response = self.client.get('/user/profile/1/')
        self.assertEqual(response.status_code, 200), 'Not found portfolio'
        response = self.client.post('/user/logout/')
        self.assertEqual(response.status_code, 302)
        self.client.logout()
