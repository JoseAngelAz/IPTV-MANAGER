from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.LogNotificacionListView.as_view(), name='log_notificaciones'),
    path('enviar/<int:suscripcion_id>/', views.enviar_recordatorio_manual, name='enviar_recordatorio'),
]
