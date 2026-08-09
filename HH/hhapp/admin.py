from django.contrib import admin
from .models import Vacancies, Employer

class VacanciesAdmin(admin.ModelAdmin):
    list_display = ['vac_name','url_vac', 'employer', 'user']

admin.site.register(Vacancies, VacanciesAdmin)
admin.site.register(Employer)

