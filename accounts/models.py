from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class Client(models.Model):
    external_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class User(AbstractUser):
    external_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True
    )
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="users", null=True, blank=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email