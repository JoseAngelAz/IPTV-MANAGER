from django.contrib import admin
from .models import Cliente, HistorialCliente, Nota, CustomField


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'dispositivo_id', 'fecha_registro', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'telefono', 'dispositivo_id', 'documento_identidad')
    readonly_fields = ('fecha_registro',)


@admin.register(HistorialCliente)
class HistorialClienteAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'usuario', 'cambio', 'fecha')
    readonly_fields = ('cliente', 'usuario', 'cambio', 'fecha')


@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'field_type', 'vertical', 'required', 'activo', 'ordering')
    list_filter = ('field_type', 'vertical', 'activo')
    search_fields = ('nombre',)
    list_editable = ('ordering', 'activo')


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'usuario', 'contenido', 'fecha')
