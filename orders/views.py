from django.views.generic import ListView
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from orders.models import Order
from .services import OrderService



class OrderListView(ListView):
    model = Order
    template_name = 'orders/order_list.html' # Путь к вашему шаблону
    context_object_name = 'orders'
    paginate_by = 6  # Количество записей на одной странице

    def get_queryset(self):
        # 1. Получаем всех клиентов, к которым привязан текущий юзер
        user_clients = self.request.user.clients.all()
        
        # 2. Фильтруем заказы только этих клиентов
        # Предполагаем, что в модели Order есть ForeignKey на Client
        orders = OrderService.get_orders_for_user(self.request.user)
        return orders # Сортируем по дате, новые сверху

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем инфо о количестве для футера (как на макете)
        context['total_count'] = 16 #self.get_queryset().count()
        return context
    

def create_order_view(request):
    user = request.user

    items = request.POST.get("items")  # JSON

    order = OrderService.create_order(user, items)

    return JsonResponse({
        "order_id": order.id,
        "status": order.status
    })