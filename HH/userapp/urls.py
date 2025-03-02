from django.urls import path
from userapp import views

app_name = 'userapp'

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login')

]