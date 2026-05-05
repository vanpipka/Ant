from django.urls import path
from . import views

urlpatterns = [
    path('modal/create/', views.order_modal_handler, name='order_modal_create'),
    path('modal/<int:pk>/edit/', views.order_modal_handler, name='order_modal'),
    path("", views.OrderListView.as_view(), name="order_list"),
    
]