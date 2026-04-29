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
            
            
def get_status_from_1c(external_id):
    return "Подтвержден"  # Заглушка, в реальной жизни - HTTP запрос к 1С

def send_to_1c(payload):
    return {
        "external_id": "1C123456"
    }  # Заглушка, в реальной жизни - HTTP запрос к 1С