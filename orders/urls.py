from django.urls import path
from .views import create_order_view, orders_list_view

urlpatterns = [
    path("create/", create_order_view, name = "create_order"),
    path("", orders_list_view, name="orders_list"),
]