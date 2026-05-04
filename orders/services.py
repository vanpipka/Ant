import random

from .models import Order, OrderItem

class OrderService:

    @staticmethod
    def create_order(user, items):
        order = Order.objects.create(
            user=user,
            client_id=user.client_id,
            status=Order.Status.DRAFT
        )

        total = 0

        for item in items:
            item_total = item["price"] * item["quantity"]

            OrderItem.objects.create(
                order=order,
                product_id=item["product_id"],
                name=item["name"],
                quantity=item["quantity"],
                price=item["price"],
                total=item_total
            )

            total += item_total

        order.total_amount = total
        order.save()

        return order

    @staticmethod
    def update_statuses():
        orders = Order.objects.exclude(external_id=None)

        for order in orders:
            status = get_status_from_1c(order.external_id)
            order.status = status
            order.save()
            
            
    @staticmethod
    def get_orders_for_user(user):
        return get_mock_orders(user)
        # return Order.objects.filter(client__in=user.clients.all()).order_by('-date_issued')
            
def get_status_from_1c(external_id):
    return "Подтвержден"  # Заглушка, в реальной жизни - HTTP запрос к 1С

def send_to_1c(payload):
    return {
        "external_id": "1C123456"
    }  # Заглушка, в реальной жизни - HTTP запрос к 1С
    
def mock_get_orders_for_user(user):
    import random
from datetime import datetime, timedelta
from django.utils import timezone

def get_mock_orders(user):
    # Берем первого доступного клиента пользователя
    client = user.clients.first()
    if not client:
        return "Сначала привяжите клиента к пользователю!"

    addresses = ['Moscow, Lenina str. 10', 'London, Baker st. 221B', 'Berlin, Hauptstr. 5', 'Paris, Rue de Rivoli 1']

    orders = []

    for i in range(1, 16):
        order = Order()
        order.client=client
        order.number=f'#ORD-2026-{i:03d}'
        order.date_issued=timezone.now() - timedelta(days=random.randint(1, 30))
        order.amount=random.uniform(100.0, 10000.0)
        order.status=random.choice(Order.Status.values)
        order.address=random.choice(addresses)  
        
        orders.append(order) 
  
    return orders