from django.contrib import admin
from .models import Plan, Suscripcion


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'duracion_dias', 'activo')


@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'plan', 'fecha_inicio', 'fecha_vencimiento', 'estado')
    list_filter = ('estado', 'plan')
    search_fields = ('cliente__nombre',)
