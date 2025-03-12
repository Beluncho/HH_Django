from django.contrib import admin
from .models import WebSiteUser

# Register your models here.
def give_is_employer(modeladmin, request, queryset):
    queryset.update(is_employer = True)

give_is_employer.short_descripyion = 'mark as employer'

class WebSiteUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_employer']
    actions = [give_is_employer]


admin.site.register(WebSiteUser, WebSiteUserAdmin)