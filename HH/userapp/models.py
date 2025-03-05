from django.db.models import EmailField, BooleanField
from django.contrib.auth.models import AbstractUser



# Create your models here.
class WebSiteUser(AbstractUser):
    email = EmailField(unique=True)
    is_employer = BooleanField(default=False)