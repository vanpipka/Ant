from django.db import models
from django.contrib.auth.models import AbstractUser

class Client(models.Model):
    external_id = models.CharField(max_length=64, unique=True, verbose_name="Внешний ID")
    name = models.CharField(max_length=255, verbose_name="Название компании")
    address = models.CharField(max_length=255, verbose_name="Адрес", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

class User(AbstractUser):
    external_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    # Теперь один пользователь может быть привязан к списку клиентов
    clients = models.ManyToManyField(
        Client, 
        related_name="users", 
        blank=True,
        verbose_name="Доступные клиенты"
    )
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email