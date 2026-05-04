from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages


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