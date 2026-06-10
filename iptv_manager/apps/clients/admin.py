from django.contrib import admin, messages
from django.utils.timezone import now
from .models import Cliente, HistorialCliente, Nota, CustomField, BusinessTemplate
from .presets import PRESETS


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


@admin.register(BusinessTemplate)
class BusinessTemplateAdmin(admin.ModelAdmin):
    list_display = ('vertical', 'aplicado', 'fecha_aplicado', 'campos_count')
    readonly_fields = ('aplicado', 'fecha_aplicado')
    actions = ['apply_template']

    def campos_count(self, obj):
        return CustomField.objects.filter(vertical=obj.vertical).count()
    campos_count.short_description = 'Campos creados'

    def apply_template(self, request, queryset):
        for template in queryset:
            if template.vertical not in PRESETS:
                self.message_user(request, f"Preset '{template.vertical}' no encontrado.", level=messages.ERROR)
                continue
            created = template.apply()
            if created:
                self.message_user(
                    request,
                    f"Plantilla '{template.get_vertical_display()}': {len(created)} campos creados.",
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    f"Plantilla '{template.get_vertical_display()}': todos los campos ya existían.",
                    level=messages.WARNING,
                )
    apply_template.short_description = 'Aplicar plantilla seleccionada (crear campos personalizados)'


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'usuario', 'contenido', 'fecha')
