from django.conf.urls import handler404, handler500, handler403, handler400
from django.conf.urls.static import static
from django.conf import settings

from django.shortcuts import render
from django.urls import path, include
from django.contrib import admin
from django.views.generic import TemplateView



urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path('test-400/', TemplateView.as_view(template_name='errors/400.html')),
    path('test-403/', TemplateView.as_view(template_name='errors/403.html')),
    path('test-404/', TemplateView.as_view(template_name='errors/404.html')),
    path('test-500/', TemplateView.as_view(template_name='errors/500.html')),
    path("", include("orders.urls")),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)


def error_403(request, exception):
    return render(request, "errors/403.html", status=403)


def error_400(request, exception):
    return render(request, "errors/400.html", status=400)


handler404 = error_404
handler500 = error_500
handler403 = error_403
handler400 = error_400