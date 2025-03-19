from tkinter.constants import CASCADE

from django.db import models
from django.db.models import Model, CharField, TextField, DateTimeField, ForeignKey
from django.db.models import  URLField, FloatField, IntegerField
from userapp.models import WebSiteUser

# дублируются данные employer и employer_name,
# но поля таблиц разные наследование не применимо.
class Employer(Model):
    employer_name = CharField(max_length=50, unique=True)
    def __str__(self):
        return self.employer_name

class Vacancies(Model):

    published = DateTimeField(auto_now_add=True)
    vac_name = CharField(max_length=50)
    url_vac = URLField()
    employer = ForeignKey(Employer, on_delete=models.CASCADE, related_name='employer_vacancies')
    salaryFrom = IntegerField(default=0)
    user = ForeignKey(WebSiteUser, on_delete=models.CASCADE, db_index=True) # for run full_db deffault = 1

    def __str__(self):
        return f'{self.vac_name}, employer: {self.employer.employer_name}'
