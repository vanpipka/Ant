from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
import json

from accounts.models import User


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
        email = data.get('email')
        password = data.get('password')

        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Пользователь с таким логином уже существует'}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Можно сразу добавить доп. поля (Имя, Фамилия)
        user.first_name = data.get('first_name', '')
        user.last_name = data.get('last_name', '')
        user.save()

        return JsonResponse({'success': True, 'user_id': user.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def update_user_api(request):
    """Обновление данных текущего пользователя"""
    try:
        user = request.user
        data = request.POST if request.POST else json.loads(request.body)

        # Обновляем основные поля
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        
        # Если нужно сменить пароль (простая реализация)
        new_password = data.get('password')
        if new_password:
            user.set_password(new_password)
            
        user.save()

        return JsonResponse({'success': True, 'message': 'Данные успешно обновлены'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)