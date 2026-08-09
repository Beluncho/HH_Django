from django.urls import path
from userapp import views
from django.contrib.auth.views import LogoutView

app_name = 'userapp'

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('registration', views.UserCreateView.as_view(), name = 'registration'),
    path('profile/<int:pk>/', views.UserProfileView.as_view(), name = 'profile'),
    path('create-token/', views.create_token, name='create_token'),
    path('update-token-ajax/', views.update_token_ajax)

]