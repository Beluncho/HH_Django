from django.urls import path
from hhapp import views

app_name = 'hhapp'

urlpatterns = [
    path('', views.main_view, name='index'),
    path('vac/<int:id>/', views.vac_view, name='vacancy')
]