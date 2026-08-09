from django.contrib import admin
from .models import WebSiteUser, Profile

# Register your models here.
def give_is_employer(modeladmin, request, queryset):
    queryset.update(is_employer = True)

give_is_employer.short_descripyion = 'mark as employer'

class WebSiteUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_employer', 'foto']
    actions = [give_is_employer]


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'info']


admin.site.register(WebSiteUser, WebSiteUserAdmin)
admin.site.register(Profile, ProfileAdmin)