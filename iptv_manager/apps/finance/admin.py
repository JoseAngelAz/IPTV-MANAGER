from django.contrib import admin
from .models import MovimientoFinanciero


@admin.register(MovimientoFinanciero)
class MovimientoFinancieroAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'monto', 'descripcion', 'fecha')
    list_filter = ('tipo',)
