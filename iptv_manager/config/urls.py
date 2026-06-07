from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.views import about, home, custom_404

handler404 = custom_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('', home, name='home'),
    path('', include('apps.clients.urls')),
    path('suscripciones/', include('apps.subscriptions.urls')),
    path('finanzas/', include('apps.finance.urls')),
    path('notificaciones/', include('apps.notifications.urls')),
    path('reportes/', include('apps.reports.urls')),
    path('about/', about, name='about'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
