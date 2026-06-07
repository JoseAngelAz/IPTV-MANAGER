from django.contrib import admin
from .models import LogNotificacion


@admin.register(LogNotificacion)
class LogNotificacionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'canal', 'enviado_ok', 'fecha_envio')
    list_filter = ('canal', 'enviado_ok')
    readonly_fields = ('cliente', 'suscripcion', 'canal', 'destinatario', 'mensaje', 'enviado_ok', 'respuesta_api', 'fecha_envio')
