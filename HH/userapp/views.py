import requests
from django.shortcuts import render,reverse, HttpResponseRedirect
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import RegistrationForm
from django.views.generic import CreateView, DetailView, UpdateView
from .models import WebSiteUser, Profile
from rest_framework.authtoken.models import Token
from django.http import JsonResponse


# Create your views here.
class UserLoginView(LoginView):
    template_name = 'userapp/login.html'


class UserCreateView(CreateView):
    model = WebSiteUser
    template_name = 'userapp/registration.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('user:login')

class UserProfileUpdateView(UpdateView):
    model = Profile
    fields = ["info"]
    success_url = reverse_lazy('hhapp:index')


class UserProfileView(DetailView, UserProfileUpdateView):
    template_name = 'userapp/profile.html'
    model = Profile

def create_token(request):
    user = request.user
    Token.objects.create(user=user)
    return HttpResponseRedirect(reverse('hhapp:index'))

def update_token_ajax(request):
    user = request.user
    # если уже есть
    if user.auth_token:
        # обновить
        user.auth_token.delete()
        token = Token.objects.create(user=user)
    else:
        # создать
        token = Token.objects.create(user=user)
    return JsonResponse({'key': token.key})