from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class WebSiteUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_employer = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='users', null=True, blank=True)

    def has_foto(self):
        return bool(self.foto)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not Profile.objects.filter(user=self).exists():
            Profile.objects.create(user=self)


class Profile(models.Model):
    info = models.TextField(blank=True)
    user = models.OneToOneField(WebSiteUser, on_delete=models.CASCADE)
    def __str__(self):
        username = f'{self.user.username}'
        return username