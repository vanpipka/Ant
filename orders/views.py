from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotFound, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from decimal import Decimal
from django.db import transaction

import json

from accounts.models import Client
from accounts.models import ClientAddress
from orders.models import Order, OrderItem
from .services import OrderService

User = get_user_model()


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html' # Путь к вашему шаблону
    context_object_name = 'orders'
    paginate_by = 6  # Количество записей на одной странице

    def get_queryset(self):
        # 1. Получаем всех клиентов, к которым привязан текущий юзер
        # user_clients = self.request.user.clients.all()
        
        # Получаем параметры фильтрации
        status_filter = self.request.GET.get('status')
        search_query = self.request.GET.get('q')
        
        # 2. Фильтруем заказы только этих клиентов
        # Предполагаем, что в модели Order есть ForeignKey на Client
        orders = OrderService.get_orders_for_user(self.request.user, status=status_filter, search_query=search_query)
        return orders # Сортируем по дате, новые сверху

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients = self.request.user.clients.all()  
        
        context['clients'] = clients
        context['order_statuses'] = Order.Status.choices
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        
        # Добавляем инфо о количестве для футера (как на макете)
        context['total_count'] = len(self.get_queryset())
        return context
    
@login_required 
def order_modal_handler(request, pk=None):
    if pk:
        # Режим редактирования
        order = OrderService.get_order_for_user(request.user, pk)
        if (not order):
            return HttpResponseNotFound("Заказ не найден")         
    else:
        # Режим создания
        order = Order(user=request.user)
        order.mock_items = []  # Временное поле для хранения позиций в памяти (не сохраняется в БД) 

    context = {
        'order': order,
        'items': order.items.all() if order.id else order.mock_items,
        'clients': request.user.clients.all(),
        'addresses': [],
        'is_edit': pk is not None,
    }
    
    if order.client_id:
        context['addresses'] = ClientAddress.objects.filter(client=order.client)
    
    # Возвращаем только внутреннюю часть формы
    return render(request, 'orders/partials/order_form_inner.html', context)


@login_required   
def get_addresses(request):
    client_id = request.GET.get('client_id')
    # Получаем адреса и превращаем их в список словарей
    addresses = ClientAddress.objects.filter(client_id=client_id).values('id', 'address_line')
    return JsonResponse(list(addresses), safe=False)


@login_required 
def product_search_api(request):
    query = request.GET.get('q', '').strip()
    
    # Базовый кверисет активных товаров
    #products = Product.objects.all()
    
    #if query:
    #    # Ищем по имени или по артикулу (product_id)
    #    products = products.filter(
    #        Q(name__icontains=query) | Q(product_id__icontains=query)
    #    )
    
    # Берем первые 20 результатов, чтобы не перегружать модалку
    #products = products[:20]
    
    # Формируем список словарей для JSON
    #data = [
    #    {
    #        "product_id": p.product_id,
    #        "name": p.name,
    #        "price": float(p.price), # Decimal нужно преобразовать в float или string
    #    } 
    #    for p in products
    #]
    data = []
    for i in range(30):
        data.append({
            "product_id": f"SKU-{i:03d}",
            "name": f"Продукт {i}",
            "price": 1000 + i * 50,
        })
     
    return JsonResponse(data, safe=False)


@require_POST
def set_order_full(request):
    try:
        data = json.loads(request.body)
        
        # 1. Извлекаем основные данные заказа
        order_ext_id = data.get('external_id')
        user_ext_id = data.get('user_external_id')
        client_ext_id = data.get('client_external_id')
        
        if not all([order_ext_id, client_ext_id]):
            return JsonResponse({'success': False, 'error': 'Отсутствует external_id заказа или клиента'}, status=400)

        with transaction.atomic():
            # 2. Ищем пользователя и клиента (обязательные связи)
            try:
                client = Client.objects.get(external_id=client_ext_id)
            except Client.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Клиент {client_ext_id} не найден'}, status=404)
            
            # Пользователь может быть не указан (например, прямой заказ в 1С)
            user = User.objects.filter(external_id=user_ext_id).first() if user_ext_id else None

            # 3. Создаем или обновляем шапку заказа
            order, created = Order.objects.update_or_create(
                external_id=order_ext_id,
                defaults={
                    'user': user,
                    'client': client,
                    'number': data.get('number', ''),
                    'address': data.get('address', ''),
                    'status': data.get('status', Order.Status.DRAFT),
                    'total_amount': Decimal(str(data.get('total_amount', 0))),
                }
            )

            # 4. Обновляем табличную часть (позиции)
            # Чтобы не усложнять сопоставление строк, проще всего удалить старые и записать новые
            order.items.all().delete()

            items_data = data.get('items', [])
            order_items = []
            
            for item in items_data:
                # Рассчитываем total для строки, если он не пришел из 1С
                quantity = int(item.get('quantity', 0))
                price = Decimal(str(item.get('price', 0)))
                item_total = Decimal(str(item.get('total', quantity * price)))

                order_items.append(OrderItem(
                    order=order,
                    product_id=item.get('product_id'),
                    name=item.get('name'),
                    quantity=quantity,
                    price=price,
                    total=item_total
                ))
            
            # Массовое создание строк (быстрее, чем по одной)
            OrderItem.objects.bulk_create(order_items)

        return JsonResponse({
            'success': True, 
            'order_id': order.id,
            'message': f'Заказ {order_ext_id} успешно {"создан" if created else "обновлен"}'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)