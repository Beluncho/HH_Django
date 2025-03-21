import requests
from django.contrib.auth.forms import UserCreationForm
from django.db.models import TextField, OneToOneField, CASCADE
from .models import WebSiteUser


class RegistrationForm(UserCreationForm):
    class Meta:
        model = WebSiteUser
        fields = ('username', 'password1', 'password2', 'email')


