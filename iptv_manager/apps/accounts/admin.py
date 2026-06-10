from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ThemeSettings, UserActivityLog, CustomPreset, ErrorPageSettings, SessionConfig, LandingPageConfig, Tarea, WhatsAppConfig, RecordatorioTemplate, ErrorReport


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(ThemeSettings)
class ThemeSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme_name', 'primary_color', 'button_style')
    list_filter = ('theme_name', 'button_style')
    search_fields = ('user__username',)


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('username', 'action', 'model_name', 'timestamp', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('username', 'model_name', 'object_repr')
    date_hierarchy = 'timestamp'
    readonly_fields = ('user', 'username', 'action', 'model_name', 'object_repr', 'object_id', 'details', 'ip_address', 'path', 'timestamp')


@admin.register(CustomPreset)
class CustomPresetAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'user', 'primary_color', 'button_style')
    list_filter = ('button_style',)
    search_fields = ('name', 'user__username')


@admin.register(ErrorPageSettings)
class ErrorPageSettingsAdmin(admin.ModelAdmin):
    list_display = ('title', 'title_500', 'show_pixel_art', 'updated_at')
    fieldsets = (
        ('Página 404', {'fields': ('title', 'message', 'show_pixel_art', 'bg_color', 'text_color')}),
        ('Página 500', {'fields': ('title_500', 'message_500', 'show_pixel_art_500', 'bg_color_500', 'text_color_500')}),
    )


@admin.register(SessionConfig)
class SessionConfigAdmin(admin.ModelAdmin):
    list_display = ('timeout_minutes', 'updated_at')


@admin.register(LandingPageConfig)
class LandingPageConfigAdmin(admin.ModelAdmin):
    list_display = ('background_image_preview', 'show_stats', 'updated_at')
    readonly_fields = ('updated_at',)

    def background_image_preview(self, obj):
        if obj.background_image:
            return f'<img src="{obj.background_image.url}" style="max-height:40px;border-radius:4px">'
        return '(ninguna)'
    background_image_preview.short_description = 'Fondo'
    background_image_preview.allow_tags = True


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'prioridad', 'categoria', 'completada', 'fecha_vencimiento')
    list_filter = ('prioridad', 'categoria', 'completada')


@admin.register(WhatsAppConfig)
class WhatsAppConfigAdmin(admin.ModelAdmin):
    list_display = ('session_status', 'last_qr_at', 'updated_at')
    readonly_fields = ('qr_code', 'session_status', 'last_qr_at', 'updated_at')


@admin.register(RecordatorioTemplate)
class RecordatorioTemplateAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'activo', 'created_by', 'created_at')
    list_filter = ('activo', 'categoria')
    search_fields = ('nombre',)


@admin.register(ErrorReport)
class ErrorReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'url', 'created_at', 'ip_address')
    list_filter = ('created_at',)
    search_fields = ('descripcion', 'user__username')
    readonly_fields = ('url', 'descripcion', 'user', 'ip_address', 'user_agent', 'error_traceback', 'created_at')
