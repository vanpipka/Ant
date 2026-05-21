import os
from io import BytesIO
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import models
from accounts.models import Client
from PIL import Image


class Order(models.Model):
    
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        SENT = "sent", "Отправлен"
        CONFIRMED = "confirmed", "Подтвержден"
        REJECTED = "rejected", "Отклонен"
        DONE = "done", "Выполнен"

    external_id = models.CharField(max_length=64, null=True, blank=True)  # ID из 1С
    number = models.CharField(max_length=15, null=True, blank=True, default="")  # number из 1С
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey("accounts.Client", on_delete=models.CASCADE)
    address = models.CharField(max_length=255, default="")
    date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    description = models.TextField(blank=True, default="")

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
            self.Status.SENT: "draft",     # 'pending' из нашего CSS
            self.Status.CONFIRMED: "pending",    # 'paid' (зеленый) для подтвержденных
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


class Product(models.Model):
    
    client = models.ForeignKey(Client, related_name="products", on_delete=models.CASCADE, null=True, blank=True)
    product_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    
    search_name = models.CharField(max_length=255, db_index=True, blank=True, editable=False)

    price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Автоматически переводим имя в нижний регистр перед сохранением
        if self.name:
            self.search_name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class ProductImage(models.Model):

    product_id = models.CharField(max_length=64)
    external_id = models.CharField(max_length=64, null=True, blank=True)  # ID из 1С
    
    # Поле для загрузки картинки. Файлы будут сохраняться в папку media/products/
    image = models.ImageField(
        upload_to='img/products/original', verbose_name="Изображение")
    
    preview_img = models.ImageField(
        upload_to='img/products/preview', null=True, blank=True)
    
    # Автоматически сохраняем дату добавления (полезно для сортировки)
    uploaded_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Дата загрузки"
    )
    
    def save(self, *args, **kwargs):
        # 1. Сначала проверяем, загружено ли вообще изображение
        if self.image and not self.preview_img:
            # 2. Открываем оригинальную картинку через Pillow
            img = Image.open(self.image)
            
            # Конвертируем в RGB, если это PNG/RGBA (чтобы корректно сохранить в JPEG)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 3. Делаем crop/resize с сохранением пропорций (метод thumbnail)
            # Если картинка прямоугольная, thumbnail сожмет её по большей стороне, например 100x75
            img.thumbnail((100, 100), Image.Resampling.LANCZOS)
            
            # 4. Сохраняем сжатую картинку в байтовый поток в памяти
            temp_thumb = BytesIO()
            img.save(temp_thumb, format='JPEG', quality=85) # Оптимальное качество
            temp_thumb.seek(0)
            
            # 5. Присваиваем файловому полю имя и данные из памяти
            # Берем базовое имя оригинального файла
            filename = os.path.basename(self.image.name)
            thumb_filename = f"thumb_{filename}"
            
            self.preview_img.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)
            temp_thumb.close()

        # Вызываем стандартный метод save для записи в базу
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ['-uploaded_at'] # Новые фото будут отображаться первыми