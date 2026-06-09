from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.contrib.auth.decorators import login_required
from apps.accounts.views import about, home, custom_404, custom_500

handler404 = custom_404
handler500 = custom_500

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
    re_path(r'^media/(?P<path>.*)$', login_required(serve), {'document_root': settings.MEDIA_ROOT}),
]
