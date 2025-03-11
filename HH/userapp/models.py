from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class WebSiteUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_employer = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='users', null=True, blank=True)

    def has_foto(self):
        return bool(self.foto)