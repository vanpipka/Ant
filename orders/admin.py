from django.contrib import admin
from .models import Order, OrderItem, Product, ProductImage

class OrderItemInline(admin.TabularInline):
    """Позволяет редактировать товары прямо в карточке заказа"""
    model = OrderItem
    extra = 0  # Не добавлять пустые строки по умолчанию
    readonly_fields = ('total',) # Рассчитывается автоматически, лучше запретить ручной ввод
    fields = ('product_id', 'name', 'quantity', 'price', 'total')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Список полей, которые видны в таблице заказов
    list_display = (
        'external_id', 
        'number',
        'user', 
        'client', 
        'status_badge', # Красивое отображение статуса
        'total_amount', 
        'items_count', 
        'created_at'
    )
    
    # Фильтры справа
    list_filter = ('status', 'created_at', 'client')
    
    # Поля, по которым работает поиск
    search_fields = ('external_id', 'user__email', 'client__name', 'number', 'address')
    
    # Группировка полей внутри карточки заказа
    fieldsets = (
        ('Основная информация', {
            'fields': ('external_id', 'number', 'status', 'user', 'client')
        }),
        ('Доставка и оплата', {
            'fields': ('address', 'total_amount')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',) # Свернуть по умолчанию
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]

    def status_badge(self, obj):
        """Цветной индикатор статуса в списке (по желанию)"""
        from django.utils.safestring import mark_safe
        colors = {
            Order.Status.DRAFT: 'gray',
            Order.Status.SENT: 'blue',
            Order.Status.CONFIRMED: 'green',
            Order.Status.REJECTED: 'red',
            Order.Status.DONE: 'black',
        }
        color = colors.get(obj.status, 'black')
        return mark_safe(f'<b style="color:{color};">{obj.get_status_display()}</b>')
    
    status_badge.short_description = 'Статус'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'name', 'order', 'quantity', 'price', 'total')
    list_filter = ('order__status',)
    search_fields = ('name', 'product_id', 'order__external_id')
    

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке товаров
    list_display = ('product_id', 'name', 'client', 'price')
    
    # Поля, по которым можно кликнуть для перехода к редактированию
    list_display_links = ('product_id', 'name')
    
    # Фильтры в правой колонке (очень полезно, если клиентов много)
    list_filter = ('client',)
    
    # Поиск по названию, внутреннему ID и имени клиента (через __name)
    search_fields = ('name', 'product_id', 'client__name')
    
    # Позволяет редактировать цену прямо в списке, не заходя в карточку товара
    list_editable = ('price',)
    
    # Упорядочивание по умолчанию
    ordering = ('client', 'name')
    
    # Группировка полей в самой карточке товара
    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'name', 'product_id')
        }),
        ('Ценообразование', {
            'fields': ('price',),
        }),
    )

    # Опционально: если вы хотите ускорить выбор клиента (если их тысячи)
    raw_id_fields = ('client',)
    
    
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'image')