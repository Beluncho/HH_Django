from django.shortcuts import render
from django.contrib.auth.views import LogoutView, LoginView

# Create your views here.
class UserLoginView(LoginView):
    template_name = 'userapp/login.html'