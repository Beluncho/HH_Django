import pprint

from django.test import TestCase
from .models import WebSiteUser,Profile
from mixer.backend.django import mixer

# Create your tests here.
class WebSiteUserTestCaseMixer(TestCase):

    def setUp(self):
        self.user = mixer.blend(WebSiteUser)

    def test_has_foto(self):
        self.assertFalse(self.user.has_foto())

class ProfileTestCase(TestCase):
    def setUp(self):
        self.profile_str = mixer.blend(WebSiteUser, username='testname')

    def test_profile_str(self):
        self.assertEqual(str(self.profile_str), 'testname')