from django.db import models
from django.db.models import Model, CharField, TextField, DateTimeField, ForeignKey
from django.db.models import  URLField, FloatField, IntegerField


class Employer(Model):
    employer_name = CharField(max_length=50, unique=True)
    def __str__(self):
        return self.employer_name

class Vacancies(Model):

    published = DateTimeField()
    vac_name = CharField(max_length=50)
    url_vac = URLField()
    employer = ForeignKey(Employer, on_delete=models.CASCADE)
    salaryFrom = IntegerField(default=0)

    def __str__(self):
        return self.vac_name