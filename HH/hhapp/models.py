from django.db import models
from django.db.models import Model, CharField, TextField, DateTimeField, ForeignKey
from django.db.models import  URLField, FloatField


class Employer(Model):
    employer_name = CharField(max_length=50, unique=True)

class Vacancies(Model):
    published = DateTimeField()
    vac_name = CharField(max_length=50)
    url_vac = URLField()
    employer = ForeignKey(Employer, on_delete=models.CASCADE)
    salaryFrom = FloatField(default=0)