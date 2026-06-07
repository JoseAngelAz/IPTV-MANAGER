from django.contrib import admin
from .models import Cliente, HistorialCliente, Nota


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'dispositivo_id', 'fecha_registro', 'activo')
    search_fields = ('nombre', 'telefono', 'dispositivo_id')


@admin.register(HistorialCliente)
class HistorialClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'usuario', 'cambio', 'fecha')
    readonly_fields = ('cliente', 'usuario', 'cambio', 'fecha')


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'usuario', 'contenido', 'fecha')
