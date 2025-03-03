from django.urls import path
from userapp import views
from django.contrib.auth.views import LogoutView

app_name = 'userapp'

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registration', views.UserCreateView.as_view(), name = 'registration')
]