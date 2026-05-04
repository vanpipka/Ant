from django.urls import path
from .views import create_order_view, OrderListView

urlpatterns = [
    path("create/", create_order_view, name = "create_order"),
    path("", OrderListView.as_view(), name="order_list"),
]