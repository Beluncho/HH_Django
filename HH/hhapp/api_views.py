from .models import Employer, Vacancies
from .serializers import EmployerSerializer,VacanciesSerializer
from rest_framework import viewsets



class EmployerViewSet(viewsets.ModelViewSet):
    queryset = Employer.objects.all()
    serializer_class = EmployerSerializer

class VacanciesViewSet(viewsets.ModelViewSet):
    queryset = Vacancies.objects.all()
    serializer_class = VacanciesSerializer