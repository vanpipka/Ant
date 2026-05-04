from django.views.generic import ListView
from django.http import HttpResponseNotFound, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from accounts.models import ClientAddress
from orders.models import Order
from .services import OrderService


class OrderListView(ListView):
    model = Order
    template_name = 'orders/order_list.html' # Путь к вашему шаблону
    context_object_name = 'orders'
    paginate_by = 6  # Количество записей на одной странице

    def get_queryset(self):
        # 1. Получаем всех клиентов, к которым привязан текущий юзер
        # user_clients = self.request.user.clients.all()
        
        # 2. Фильтруем заказы только этих клиентов
        # Предполагаем, что в модели Order есть ForeignKey на Client
        orders = OrderService.get_orders_for_user(self.request.user)
        return orders # Сортируем по дате, новые сверху

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        clients = self.request.user.clients.all()  
        
        context['clients'] = clients
        
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
        'is_edit': pk is not None,
    }
    
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