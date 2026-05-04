from django.db import models
from django.contrib.auth.models import AbstractUser


class Client(models.Model):
    external_id = models.CharField(max_length=64, unique=True, verbose_name="Внешний ID")
    name = models.CharField(max_length=255, verbose_name="Название компании")
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


class ClientAddress(models.Model):
    # Связь с клиентом: при удалении клиента удалятся и его адреса (CASCADE)
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name="addresses", 
        verbose_name="Клиент"
    )
    
    address_line = models.CharField(max_length=500, verbose_name="Адрес доставки")
    city = models.CharField(max_length=100, verbose_name="Город", blank=True)
    is_default = models.BooleanField(default=False, verbose_name="Основной адрес")

    def __str__(self):
        return f"{self.client.name} - {self.address_line[:30]}..."

    class Meta:
        verbose_name = "Адрес клиента"
        verbose_name_plural = "Адреса клиентов"