from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files.base import ContentFile
from django.http import HttpResponseNotFound, JsonResponse
from django.db.models import F, OuterRef, Subquery
from django.db import transaction
from decimal import Decimal

import json

from accounts.models import Client
from accounts.models import ClientAddress
from orders.models import Order, OrderItem, Product, ProductImage, ClientPrice
from .services import OrderService

User = get_user_model()


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html' # Путь к вашему шаблону
    context_object_name = 'orders'
    paginate_by = 10  # Количество записей на одной странице

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
  

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 25 # Опционально: постраничный вывод

    def get_queryset(self):
        # 1. Получаем текущего клиента через авторизованного юзера.
        try:
            current_client = self.request.user.clients.all()[0]
        except AttributeError:
            # Если у пользователя нет привязанного клиента, отдаем пустой список
            return Product.objects.none()
        
        image_subquery = ProductImage.objects.filter(
            product_id=OuterRef('product_id')
        ).values('image')[:1]
        
        preview_subquery = ProductImage.objects.filter(
            product_id=OuterRef('product_id')
        ).values('preview_img')[:1]

        # 2. Оптимальный вариант: Фильтруем продукты, у которых есть цена для клиента,
        # и сразу добавляем эту цену как виртуальное поле `client_price` к каждому объекту.
        queryset = Product.objects.filter(
            client_prices__client=current_client
        ).annotate(
            client_price=F('client_prices__price'),
            # Добавляем динамические поля (строки с относительным путем к файлам медиа)
            annotated_image=Subquery(image_subquery),
            annotated_preview=Subquery(preview_subquery)
        ).order_by('name')

        return queryset
    
    
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
       
       
    # Если у юзера только один клиент, сразу его установим    
    clients = request.user.clients.all()
    
    if clients.count() == 1:
        order.client = clients[0]

    if request.GET.get('copy') == 'true' and pk:
        # Режим копирования
        order.mock_items = []
        for i in order.items.all():
            
            try:
                product = ClientPrice.objects.filter(client_id=order.client_id, product__product_id=i.product_id).first()
                if product:  
                    i.price = product.price
                    i.total = i.price * i.quantity           
                    order.mock_items.append(i)
            except Product.DoesNotExist:
                continue  # Если товар не найден, пропускаем эту позицию                
       
        order.id = None  # Сброс ID, чтобы при сохранении создался новый заказ
        order.external_id = '' # Сбрасываем external_id, чтобы не было конфликтов при синхронизации с 1С
        order.number = ''  # Очищаем номер, чтобы не было конфликтов 
        order.status = Order.Status.DRAFT  # Сбрасываем статус на черновик
        
    context = {
        'order': order,
        'items': order.items.all() if order.id else order.mock_items,
        'clients': request.user.clients.all(),
        'addresses': [],
        'is_edit': pk is not None,
    }
    
    # если клиент установлен, то сразу проверим адрес
    try:    
        if order.client:
            context['addresses'] = [i.address_line for i in ClientAddress.objects.filter(client=order.client)]         
            if len(context['addresses']) == 1:
                order.address = context['addresses'][0] 
    except:
        ...
    
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
    
    query = request.GET.get('q', '').strip().lower()
    client_id = request.GET.get('client_id', '').strip().lower()
    page_number = request.GET.get('page', 1) # Получаем параметры пагинации из URL (например: /api/products/?page=2&page_size=20)
    page_size = request.GET.get('page_size', 20) # По умолчанию 20 товаров на страницу
    
    try:       
        client = request.user.clients.all().filter(id=client_id)[0]
    except AttributeError:
        return JsonResponse({'error': 'User is not associated with any client'}, status=400)   
    
    # Защита от некорректного ввода page_size
    try:
        page_size = int(page_size)
        if page_size <= 0:
            page_size = 20
    except ValueError:
        page_size = 20
        
    # Базовый кверисет активных товаров
    products = Product.objects.filter(client_prices__client=client)
    
    if query:
    # Ищем по имени или по артикулу (product_id)
        products = products.filter(search_name__icontains=query)
        
    #image_subquery = ProductImage.objects.filter(
    #        product_id=OuterRef('product_id')
    #    ).values('image')[:1]
        
    preview_subquery = ProductImage.objects.filter(
            product_id=OuterRef('product_id')
        ).values('preview_img')[:1]
    
    products = products.annotate(
        client_price=F('client_prices__price'),
        #annotated_image=Subquery(image_subquery),
        annotated_preview=Subquery(preview_subquery)
    ).values(
        'id',             # Внутренний ID Django (число)
        'product_id',     # Строковый ID (например, UID из 1С)
        'name', 
        'unit', 
        'article', 
        'client_price',    # Наша аннотированная цена
        'annotated_preview'
    ).order_by('name')
    
    paginator = Paginator(products, page_size)
    
    try:
        # Получаем данные конкретной страницы
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Если page не число, отдаем первую страницу
        page_obj = paginator.page(1)
    except EmptyPage:
        # Если номер страницы слишком большой (вышли за пределы), отдаем последнюю
        page_obj = paginator.page(paginator.num_pages)
     
    # 5. Формируем структурированный ответ
    response_data = {
        'pagination': {
            'current_page': page_obj.number,
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'page_size': page_size,
        },
        'results': list(page_obj.object_list) # Данные только для текущей страницы
    }

    return JsonResponse(response_data, safe=True, json_dumps_params={'ensure_ascii': False})


@login_required 
@require_POST
def set_order_full(request):
    
    if (not request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # 1. Извлекаем основные данные заказа
        order_ext_id = data.get('external_id')
        order_id = data.get('order_id')
        #user_ext_id = data.get('user_external_id')
        client_ext_id = data.get('client_external_id')
        date = data.get('date')  # Если нужно, можно парсить дату из строки
        
        if not all([order_ext_id, client_ext_id]):
            return JsonResponse({'success': False, 'error': 'Отсутствует external_id заказа или клиента'}, status=400)

        order = Order.objects.filter(id=order_id).first()
        if not order:
            return JsonResponse({'success': False, 'error': f'Заказ № {order_id} не найден'}, status=404)
        
        with transaction.atomic():
            # 2. Ищем пользователя и клиента (обязательные связи)
            try:
                client = Client.objects.get(external_id=client_ext_id)
            except Client.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Клиент {client_ext_id} не найден'}, status=404)
            
            # Пользователь может быть не указан (например, прямой заказ в 1С)
            # user = User.objects.filter(external_id=user_ext_id).first() if user_ext_id else None

            # 3. Создаем или обновляем шапку заказа, заказ уже в системе
            order, created = Order.objects.update(
                id=order_id,
                defaults={
                    #'user': user,
                    'external_id': order_ext_id,
                    'date': date,
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
    
  
@login_required   
@transaction.atomic
def save_order(request):
    
    if request.method == 'POST':
        # Получаем одиночные значения
        order_id = request.POST.get('order_id')
        client_id = request.POST.get('client_id')
        description = request.POST.get('order_description', '')
        address = request.POST.get('address_id', '') # Если это ID адреса
        status = request.POST.get('status', 'draft') 
        payment_type = request.POST.get('paymenttype_id', 0) 
        its_backround_submit = request.POST.get('its_backround_submit', False) 
        
        if not address:
            address = request.POST.get('address', '')
        
        if not order_id:     
            
            # Создаем заказ
            order = Order.objects.create(
                user = request.user,
                client_id = client_id,
                description = description,
                address = address, # Или текстовое поле
                status = status,
                payment_type = payment_type
            )
        else:
            # Обновляем существующий заказ
            order = Order.objects.get(id=order_id, user=request.user)
            order.client_id = client_id
            order.address = address
            order.description = description
            order.status = status
            order.payment_type = payment_type
            order.items.all().delete() # Удаляем старые позиции, чтобы записать новые
            

        # Получаем списки (важно: порядок в списках сохраняется)
        product_ids = request.POST.getlist('item_product_id')
        quantities = request.POST.getlist('item_quantity')
        prices = request.POST.getlist('item_price')

        total_amount = 0
        
        # Проходим циклом по спискам
        for i in range(len(product_ids)):
            qty = int(quantities[i])
            price = Decimal(prices[i])
            product_id = product_ids[i]
            subtotal = qty * price
            
            try:
                product = Product.objects.get(product_id=product_id)
                
                OrderItem.objects.create(
                    order=order,
                    product_id=product.product_id,
                    name=product.name,
                    quantity=qty,
                    price=price,
                    total=subtotal
                )
                total_amount += subtotal
            except Product.DoesNotExist:
                continue  # Если товар не найден, пропускаем эту позицию
        
        order.total_amount = total_amount
        order.save()
        
        if (its_backround_submit):
            return JsonResponse({"order_id": order.id})
        else:
            return redirect('/') # Или другой URL
    

@login_required     
@require_POST
def save_product(request, product_id):
    if (not request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Ошибка формата JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    name = data.get('name', '')
    article = data.get('article', '')
    unit = data.get('unit', '')
    
    if not product_id:
        return JsonResponse({'success': False, 'error': 'Поле external_id обязательно'}, status=500)  
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Поле name обязательно'}, status=500)   
    
    product, created = Product.objects.update_or_create(
        product_id=product_id,
        defaults={'name': name, 'article': article, 'unit': unit})
    
    return JsonResponse({
        'success': True, 
        'id': product.id,
    })
    

@login_required     
@require_POST
def set_client_prices(request, client_id):
    
    if (not request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Ошибка формата JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
              
    items = data.get('items', [])

    # Находим клиента
    try:
        client = Client.objects.get(external_id=client_id)
    except Client.DoesNotExist:
        return JsonResponse({'success': False, 'error': f'Клиент {client_id} не найден'}, status=404)

    with transaction.atomic():
        # 1. Собираем список product_id, которые прислала 1С
        incoming_product_ids = [str(item.get('product_id')) for item in items if item.get('product_id')]

        # 2. Удаляем те товары клиента, которых нет в пришедшем списке
        # Это и есть механизм очистки лишних строк
        ClientPrice.objects.filter(client=client).exclude(product__product_id__in=incoming_product_ids).delete()

        # 3. Обновляем существующие или создаем новые товары
        for item_data in items:
            p_id = item_data.get('product_id')
            if not p_id:
                continue
            
            try:
                product = Product.objects.get(product_id=p_id)
            except Product.DoesNotExist:
                continue
                
            # update_or_create вызовет наш метод save() и обновит search_name автоматически
            ClientPrice.objects.update_or_create(
                client=client,
                product=product,
                defaults={
                    'price': Decimal(str(item_data.get('price', 0))),
                }
            )

    return JsonResponse({
        'success': True, 
        'message': f'Синхронизация завершена. Обработано товаров: {len(incoming_product_ids)}'
    })
 
    
@login_required # Обязательно защищаем данные
def export_orders_to_1c(request):
    
    if (not request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
      
    # Получаем все заказы в статусе SENT
    # Используем prefetch_related для оптимизации запросов к товарам
    orders = Order.objects.filter(status=Order.Status.SENT, external_id__isnull=True).prefetch_related('items')

    data = []
    for order in orders:
        # Формируем список товаров для каждого заказа
        order_items = []
        for item in order.items.all():
            order_items.append({
                'product_id': item.product_id,
                'product_name': item.name, 
                'quantity': float(item.quantity),
                'price': float(item.price),
                'sum': float(item.quantity * item.price),
            })

        # Формируем структуру заказа
        data.append({
            'order_id': order.id,         
            'date': order.date.strftime('%Y%m%d%H%M00'),
            'user_id': order.user.external_id if order.user else None,
            'client_id': order.client.external_id,
            'address': order.address,
            'total_amount': float(order.total_amount),
            'description': order.description or "",
            'items': order_items, # Вложенный список товаров
        })

    return JsonResponse({
        'success': True,
        'count': len(data),
        'orders': data
    }, safe=False, json_dumps_params={'ensure_ascii': False}) # Чтобы кириллица была читаемой
    

@login_required
def set_external_id(request):
    
    if (not request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')      # Ваш внутренний ID (например, 105)
        ext_id = data.get('external_id')     # ID из 1С (например, "УТ-00001")
        number = data.get('number', '') 
        
        if not order_id or not ext_id:
            return JsonResponse({'success': False, 'error': 'Missing order_id or external_id'}, status=400)

        # Ищем заказ и обновляем его
        order = Order.objects.get(id=order_id)
        
        if (not order):
            return JsonResponse({'success': False, 'error': f'Order with id {order_id} not found'}, status=404)    
        
        order.external_id = ext_id
        order.number = number
        
        # Дополнительно: можно сбросить статус или пометить как "Выгружен"
        order.status = Order.Status.CONFIRMED 
        
        try:
            order.save()
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'{e}'}, status=404)     

        return JsonResponse({
            'success': True,
            'message': f'Order {order_id} updated with external ID {ext_id}'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    
@login_required   
def upload_product_image(request):
 
    if (not request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'}, status=403)
       
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)

    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'success': False, 'error': 'Missing product_id parameter'}, status=400)
    
    img_id = request.GET.get('img_id')
    if not product_id:
        return JsonResponse({'success': False, 'error': 'Missing img_id parameter'}, status=400)
    
    try:
        img = ProductImage.objects.get(external_id = img_id)       
        if img:
            return JsonResponse({'success': True, 'message': 'Файл был загружен ранее'}, status=200)  
    
    except ProductImage.DoesNotExist:
        ... 
    
    # удалим старые изображения
    ProductImage.objects.filter(product_id = product_id).delete()

    binary_data = request.body
    if not binary_data:
        return JsonResponse({'success': False, 'error': 'Empty request body'}, status=400)

    # 3. Генерируем имя файла (например, на основе ID товара)
    # По хорошему можно вытащить расширение из заголовка Content-Type,
    # но для простоты сохраняем как .jpg
    filename = f"product_{product_id}_uploaded.jpg"

    # 4. Создаем объект файла Django из байтов
    django_file = ContentFile(binary_data, name=filename)

    # 5. Сохраняем в нашу модель ProductImage
    new_image = ProductImage.objects.create(
        product_id=product_id,
        external_id=img_id,
        image=django_file
    )

    return JsonResponse({
        'success': True,
        'message': f'Image successfully added to product ID {product_id}',
        'image_id': new_image.id
    })