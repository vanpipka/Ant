from django.db import models

class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "Черновик"
        SENT = "Отправлен"
        CONFIRMED = "Подтвержден"
        REJECTED = "Отклонен"
        DONE = "Выполнен"

    external_id = models.CharField(max_length=64, null=True, blank=True)  # ID из 1С
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    client_id = models.CharField(max_length=64)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)

    product_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255)

    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    total = models.DecimalField(max_digits=12, decimal_places=2)
