from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from orders.models import Order
from .services import OrderService


@login_required
def orders_list_view(request):
    user = request.user

    orders = (
        Order.objects
        .filter(user=user)
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(request, "orders/orders_list.html", {
        "orders": orders
    })
    

def create_order_view(request):
    user = request.user

    items = request.POST.get("items")  # JSON

    order = OrderService.create_order(user, items)

    return JsonResponse({
        "order_id": order.id,
        "status": order.status
    })