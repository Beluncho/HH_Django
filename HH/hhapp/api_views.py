from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from .models import Employer, Vacancies
from .permissions import ReadOnly, IsEmployer
from .serializers import EmployerSerializer,VacanciesSerializer
from rest_framework import viewsets


class EmployerViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAdminUser | IsEmployer | ReadOnly]
<<<<<<< HEAD
    queryset = Employer.objects.all()
=======
    queryset = Employer.objects.order_by("pk")
>>>>>>> AI_Agents_diploma
    serializer_class = EmployerSerializer

class VacanciesViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAdminUser | IsEmployer | ReadOnly]
<<<<<<< HEAD
    queryset = Vacancies.objects.select_related('user').all()
=======
    queryset = Vacancies.objects.select_related('user').order_by("pk")
>>>>>>> AI_Agents_diploma
    serializer_class = VacanciesSerializer
