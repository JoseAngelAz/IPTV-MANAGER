from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ThemeSettings, UserActivityLog, CustomPreset, ErrorPageSettings, SessionConfig


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
    list_display = ('title', 'show_pixel_art', 'updated_at')
    fieldsets = (
        (None, {'fields': ('title', 'message', 'show_pixel_art', 'bg_color', 'text_color')}),
    )


@admin.register(SessionConfig)
class SessionConfigAdmin(admin.ModelAdmin):
    list_display = ('timeout_minutes', 'updated_at')
