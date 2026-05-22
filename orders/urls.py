from django.urls import path
from . import views

urlpatterns = [
    path('orders/save/', views.save_order, name='save_order'),
    path('modal/create/', views.order_modal_handler, name='order_modal_create'),
    path('modal/<int:pk>/edit/', views.order_modal_handler, name='order_modal'),
    path("products", views.ProductListView.as_view(), name="product_list"),
    path("", views.OrderListView.as_view(), name="order_list"),
    
]