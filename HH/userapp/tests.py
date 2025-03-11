from django.test import TestCase
from .models import WebSiteUser
from mixer.backend.django import mixer

# Create your tests here.
class WebSiteUserTestCaseMixer(TestCase):

    def setUp(self):
        self.user = mixer.blend(WebSiteUser)

    def test_has_foto(self):
        self.assertFalse(self.user.has_foto())