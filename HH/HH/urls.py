"""
URL configuration for HH project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from hhapp.api_views import EmployerViewSet, VacanciesViewSet

router = routers.DefaultRouter()
router.register(r'employers', EmployerViewSet)
router.register(r'vacancies', VacanciesViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hhapp.urls', namespace='hhapp')),
    path('user/', include('userapp.urls', namespace= 'user')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v0/', include(router.urls))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),

        # For django versions before 2.0:
        # url(r'^__debug__/', include(debug_toolbar.urls)),

    ] + urlpatterns