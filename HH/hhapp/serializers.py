from django.urls import path, include
from .models import Employer, Vacancies
from rest_framework import serializers

# Serializers define the API representation.
class EmployerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Employer
        fields = '__all__'


class VacanciesSerializer(serializers.HyperlinkedModelSerializer):
    employer_name = EmployerSerializer(read_only=True)
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Vacancies
        fields = '__all__'