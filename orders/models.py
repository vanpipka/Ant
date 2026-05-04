from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "Черновик"
        SENT = "Отправлен"
        CONFIRMED = "Подтвержден"
        REJECTED = "Отклонен"
        DONE = "Выполнен"

    external_id = models.CharField(max_length=64, null=True, blank=True)  # ID из 1С
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey("accounts.Client", on_delete=models.CASCADE)
    address = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def items_count(self):
        # Считает количество строк (позиций) в заказе
        return self.items.count()

    @property
    def total_quantity(self):
        # Если нужно посчитать сумму всех штук (quantity) во всех позициях
        return sum(item.quantity for item in self.items.all())
       
    def get_status_class(self):
        mapping = {
            self.Status.DRAFT: "draft",
            self.Status.SENT: "pending",     # 'pending' из нашего CSS
            self.Status.CONFIRMED: "paid",    # 'paid' (зеленый) для подтвержденных
            self.Status.REJECTED: "overdue",  # 'overdue' (красный) для отклоненных
            self.Status.DONE: "paid",         # тоже зеленый
        }
        # Если статус не найден в словаре, вернем 'draft' по умолчанию
        return mapping.get(self.status, "draft")
    
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)

    product_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255)

    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    total = models.DecimalField(max_digits=12, decimal_places=2)
