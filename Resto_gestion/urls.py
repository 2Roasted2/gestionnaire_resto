from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('personnel/', include('personnel.urls')),
    path('inventory/', include('inventory.urls')),
    path('accounting/', include('accounting.urls')),
    path('bookings/', include('bookings.urls')),
    path('orders/', include('orders.urls')),
    path('analytics/', include('analytics.urls')),
    path('', lambda request: redirect('accounts:login')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)