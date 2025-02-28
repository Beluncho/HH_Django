from django.urls import path
from hhapp import views

app_name = 'hhapp'

urlpatterns = [
    path('', views.VacanciesListView.as_view(), name='index'),
    path('vacancy/<int:pk>/', views.VacDetailView.as_view(), name='vacancy'),
    path('vacancy_create/', views.VacancyCreateView.as_view(), name = 'vacancy_create'),
    path('employers_list/', views.EmployersListView.as_view(), name = 'employers_list'),
    path('employer_detail/<int:pk>/',views.EmployerDetailView.as_view(), name = 'employer_detail'),
    path('employer_create/', views.EmployerCreateView.as_view(), name = 'employer_create'),
    path('employer_update/<int:pk>/', views.EmployerUpdateView.as_view(), name = 'employer_update'),
    path('employer_delete/<int:pk>/', views.EmployerDeleteView.as_view(),name = 'employer_delete')

]