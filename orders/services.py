from django.db.models import Q
from datetime import datetime
from decimal import Decimal
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
    def get_orders_for_user(user, status=None, search_query=None):
        # return get_mock_orders(user, status, search_query)
        query = Order.objects.filter(client__in=user.clients.all())
        if status:
            query = query.filter(status=status)
        if search_query:
            query = query.filter(Q(number__icontains=search_query) | Q(id__icontains=search_query))
        return query.order_by('-created_at')
        
    @staticmethod
    def get_order_for_user(user, id):
        # return get_mock_order(user, id)
        
        return Order.objects.filter(id=id)[0]
        
        # return Order.objects.filter(client__in=user.clients.all()).order_by('-created_at')    
            
def get_status_from_1c(external_id):
    return "Подтвержден"  # Заглушка, в реальной жизни - HTTP запрос к 1С

def send_to_1c(payload):
    return {
        "external_id": "1C123456"
    }  # Заглушка, в реальной жизни - HTTP запрос к 1С
    

def get_mock_orders(user, status=None, search_query=None):
    # Берем первого доступного клиента пользователя
    client = user.clients.first()
    if not client:
        raise ValueError("Сначала привяжите клиента к пользователю!")

    orders = []  
    for i in range(10):     
        order = create_random_order(user, client)
        if status and order.status != status:
            continue  # Если фильтр по статусу задан и не совпало - пропускаем
        if search_query and search_query.lower() not in order.external_id.lower():
            continue  # Если фильтр по поиску задан и не совпало - пропускаем
        
        orders.append(order) 
  
    return orders


def get_mock_order(user, id):
    # Берем первого доступного клиента пользователя
    client = user.clients.first()
    if not client:
        raise ValueError("Сначала привяжите клиента к пользователю!")

    return create_random_order(user, client)


def create_random_order(user, client):  
    
    addresses = ['Moscow, Lenina str. 10', 'London, Baker st. 221B', 'Berlin, Hauptstr. 5', 'Paris, Rue de Rivoli 1']

    # 1. Создаем сам заказ
    order = Order.objects.create(
        user=user,
        client=client,
        external_id=f'#ORD-2026-{random.randint(100, 999)}',
        created_at= datetime.now(),
        total_amount=random.uniform(100.0, 10000.0),
        status=random.choice(Order.Status.values),
        address=random.choice(addresses)
    )
    
    order.mock_items = []  # Временное поле для хранения позиций в памяти (не сохраняется в БД)

    # 2. Создаем позиции, привязанные к заказу
    order_item = OrderItem.objects.create(
        order=order,
        product_id="P-01",
        name="Дизайн логотипа",
        quantity=1,
        price=Decimal('1000.00'),
        total=Decimal('1000.00')
    )
    
    order.mock_items.append(order_item)
    
    OrderItem.objects.create(
        order=order,
        product_id="P-02",
        name="Консультация",
        quantity=2,
        price=Decimal('250.00'),
        total=Decimal('500.00')
    )
    
    order.mock_items.append(order_item)
    
    return order
        