from .models import Order

class OneCOrderClient:

    @staticmethod
    def send_order(order):
        payload = {
            "client_id": order.client_id,
            "order_id": order.id,
            "items": [
                {
                    "product_id": i.product_id,
                    "quantity": i.quantity,
                    "price": str(i.price)
                }
                for i in order.items.all()
            ],
            "total": str(order.total_amount)
        }

        # HTTP запрос в 1С
        response = send_to_1c(payload)

        order.external_id = response["external_id"]
        order.status = Order.Status.SENT
        order.save()