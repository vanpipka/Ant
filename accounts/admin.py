from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = ("email", "client", "is_active", "is_staff")
    search_fields = ("email", "client__name")
    ordering = ("email",)

    fieldsets = UserAdmin.fieldsets + (
        ("Custom fields", {
            "fields": ("external_id", "client")
        }),
    )