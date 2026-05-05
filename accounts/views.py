from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.db import transaction
from django.http import JsonResponse
from django.contrib import messages
import json

from accounts.models import Client, ClientAddress, User


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user:
            if not user.is_active:
                messages.error(request, "Аккаунт не активирован")
                return redirect("login")

            login(request, user)
            return redirect("order_list")

        messages.error(request, "Неверные данные")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    return render(request, "accounts/dashboard.html")


@login_required
@require_POST
def create_user_api(request):
    """Создание нового пользователя"""
    try:
        # Если данные идут через обычную форму (request.POST)
        data = request.POST
        # Если данные идут как JSON (через fetch)
        if not data:
            data = json.loads(request.body)

        username = data.get('username')
        external_id = data.get('external_id')
        email = data.get('email')
        password = data.get('password')

        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': f'user with username {username} exists'}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password, external_id=external_id)
        
        # Можно сразу добавить доп. поля (Имя, Фамилия)
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.save()

        return JsonResponse({'success': True, 'user_id': user.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def update_user_api(request):
    try:
        data = json.loads(request.body)
        
        # 1. Извлекаем данные пользователя
        user_data = data.get('user', {})
        user_ext_id = user_data.get('external_id')
        
        if not user_ext_id:
            return JsonResponse({'success': False, 'error': 'external_id пользователя обязателен'}, status=400)

        # Используем транзакцию, чтобы если упадет один адрес, не создался "битый" юзер
        with transaction.atomic():
            # 2. Обновляем или создаем пользователя
            user, u_created = User.objects.update_or_create(
                external_id=user_ext_id,
                defaults={
                    'username': user_data.get('username', user_data.get('email')),
                    'email': user_data.get('email'),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                }
            )

            # Если пользователь новый и нет пароля — ставим заглушку (потом сменит)
            if u_created and 'password' in user_data:
                user.set_password(user_data['password'])
                user.save()

            # 3. Обработка списка клиентов
            client_list = data.get('clients', [])
            current_client_ids = []

            for cl_data in client_list:
                cl_ext_id = cl_data.get('external_id')
                client, _ = Client.objects.update_or_create(
                    external_id=cl_ext_id,
                    defaults={'name': cl_data.get('name')}
                )
                current_client_ids.append(client.id)

                # 4. Обработка адресов клиента
                address_list = cl_data.get('addresses', [])
                for addr_data in address_list:
                    ClientAddress.objects.update_or_create(
                        external_id=addr_data.get('external_id'),
                        defaults={
                            'client': client,
                            'address_line': addr_data.get('address_line')
                        }
                    )

            # 5. Синхронизируем связи ManyToMany (set заменяет старый список новым)
            user.clients.set(current_client_ids)

        return JsonResponse({
            'success': True, 
            'message': f'Данные пользователя {user.email} и его клиентов синхронизированы'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)