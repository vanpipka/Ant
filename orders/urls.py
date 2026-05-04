from django.urls import path
from . import views

urlpatterns = [
    path('api/get-addresses/', views.get_addresses, name='api_get_addresses'),
    path('api/products/', views.product_search_api, name='product_search_api'),
    path('modal/create/', views.order_modal_handler, name='order_modal_create'),
    path('modal/<int:pk>/edit/', views.order_modal_handler, name='order_modal'),
    path("", views.OrderListView.as_view(), name="order_list"),
    
]