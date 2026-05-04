from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Client, ClientAddress


class ClientAddressInline(admin.TabularInline):
    model = ClientAddress
    extra = 1 # Сколько пустых полей для новых адресов показывать сразу
    
    
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'external_id', 'created_at')
    search_fields = ('name',)
    inlines = [ClientAddressInline]

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_staff')
    
    # Это добавит удобный интерфейс выбора клиентов
    filter_horizontal = ('clients',) 

    fieldsets = UserAdmin.fieldsets + (
        ('Доступы', {
            'fields': ('clients', 'external_id'),
        }),
    )