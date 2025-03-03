from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import RegistrationForm
from django.views.generic import CreateView
from .models import WebSiteUser


# Create your views here.
class UserLoginView(LoginView):
    template_name = 'userapp/login.html'


class UserCreateView(CreateView):
    model = WebSiteUser
    template_name = 'userapp/registration.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('user:login')