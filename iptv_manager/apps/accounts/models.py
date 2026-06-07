from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    profile_picture = models.ImageField('Foto de perfil', upload_to='profile_pics/', blank=True, null=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username}'


class ThemeSettings(models.Model):
    THEME_CHOICES = [
        ('modern', 'Moderno — Azul profundo'),
        ('corporate', 'Corporativo — Verde elegante'),
        ('minimal', 'Minimalista — Blanco y negro'),
        ('vibrant', 'Vibrante — Púrpura neón'),
        ('dark-neumorphic', 'Dark Neumorphic — Oscuro esmeralda'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='theme')
    theme_name = models.CharField('Tema', max_length=30, choices=THEME_CHOICES, default='modern')
    primary_color = models.CharField('Color primario', max_length=7, default='#2563eb')
    secondary_color = models.CharField('Color secundario', max_length=7, default='#1d4ed8')
    bg_color = models.CharField('Color de fondo', max_length=7, default='#f1f5f9')
    text_color = models.CharField('Color de texto', max_length=7, default='#1e293b')
    card_bg = models.CharField('Fondo de tarjetas', max_length=7, default='#ffffff')
    sidebar_bg = models.CharField('Fondo de sidebar', max_length=7, default='#111827')
    button_style = models.CharField('Estilo de botones', max_length=10, choices=[
        ('rounded', 'Redondeados'),
        ('square', 'Cuadrados'),
        ('pill', 'Píldora'),
    ], default='rounded')
    custom_css = models.TextField('CSS personalizado', blank=True, default='')
    pixel_bg = models.CharField('Fondo pixel art', max_length=20,
                                choices=[('none', 'Ninguno'), ('stars', 'Estrellas'),
                                         ('grid', 'Cuadrícula'), ('checker', 'Ajedrez'),
                                         ('circuit', 'Circuitos'), ('diamond', 'Diamantes'),
                                         ('rain', 'Lluvia'), ('mountain', 'Montañas'),
                                         ('nebula', 'Nebulosa'), ('matrix', 'Matrix')],
                                default='none')

    class Meta:
        verbose_name = 'Configuración de Tema'
        verbose_name_plural = 'Configuraciones de Tema'

    def __str__(self):
        return f'{self.user} — {self.get_theme_name_display()}'

    def apply_preset(self, preset_name):
        presets = {
            'modern': {'primary_color': '#2563eb', 'secondary_color': '#1d4ed8', 'bg_color': '#f1f5f9',
                       'text_color': '#1e293b', 'card_bg': '#ffffff', 'sidebar_bg': '#111827',
                       'button_style': 'rounded'},
            'corporate': {'primary_color': '#059669', 'secondary_color': '#047857', 'bg_color': '#f0fdf4',
                          'text_color': '#1e293b', 'card_bg': '#ffffff', 'sidebar_bg': '#064e3b',
                          'button_style': 'square'},
            'minimal': {'primary_color': '#334155', 'secondary_color': '#1e293b', 'bg_color': '#f8fafc',
                        'text_color': '#0f172a', 'card_bg': '#ffffff', 'sidebar_bg': '#0f172a',
                        'button_style': 'square'},
            'vibrant': {'primary_color': '#7c3aed', 'secondary_color': '#6d28d9', 'bg_color': '#f5f3ff',
                        'text_color': '#1e1b4b', 'card_bg': '#ffffff', 'sidebar_bg': '#2e1065',
                        'button_style': 'pill'},
            'dark-neumorphic': {'primary_color': '#10b981', 'secondary_color': '#059669', 'bg_color': '#1a202c',
                                'text_color': '#e2e8f0', 'card_bg': '#2d3748', 'sidebar_bg': '#0f172a',
                                'button_style': 'pill'},
        }
        if preset_name in presets:
            for k, v in presets[preset_name].items():
                setattr(self, k, v)
            self.theme_name = preset_name


class CustomPreset(models.Model):
    ICON_CHOICES = [
        ('🎨', '🎨 Paleta'), ('🌈', '🌈 Arcoíris'), ('🎭', '🎭 Teatro'),
        ('🌟', '🌟 Estrella'), ('🔥', '🔥 Fuego'), ('💎', '💎 Diamante'),
        ('🌊', '🌊 Ola'), ('🍃', '🍃 Hoja'), ('🌙', '🌙 Luna'),
        ('☀️', '☀️ Sol'), ('🎯', '🎯 Blanco'), ('💡', '💡 Idea'),
        ('🚀', '🚀 Cohete'), ('🌸', '🌸 Flor'), ('🌺', '🌺 Hibisco'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_presets')
    name = models.CharField('Nombre del preset', max_length=50)
    icon = models.CharField('Icono', max_length=10, choices=ICON_CHOICES, default='🎨')
    primary_color = models.CharField('Color primario', max_length=7, default='#2563eb')
    secondary_color = models.CharField('Color secundario', max_length=7, default='#1d4ed8')
    bg_color = models.CharField('Color de fondo', max_length=7, default='#f1f5f9')
    text_color = models.CharField('Color de texto', max_length=7, default='#1e293b')
    card_bg = models.CharField('Fondo de tarjetas', max_length=7, default='#ffffff')
    sidebar_bg = models.CharField('Fondo de sidebar', max_length=7, default='#111827')
    button_style = models.CharField('Estilo de botones', max_length=10, choices=[
        ('rounded', 'Redondeados'), ('square', 'Cuadrados'), ('pill', 'Píldora'),
    ], default='rounded')

    class Meta:
        verbose_name = 'Preset Personalizado'
        verbose_name_plural = 'Presets Personalizados'
        unique_together = ['user', 'name']

    def __str__(self):
        return f'{self.icon} {self.name}'

    def to_dict(self):
        return {
            'primary_color': self.primary_color, 'secondary_color': self.secondary_color,
            'bg_color': self.bg_color, 'text_color': self.text_color,
            'card_bg': self.card_bg, 'sidebar_bg': self.sidebar_bg,
            'button_style': self.button_style,
        }

    def apply_to(self, theme):
        theme.primary_color = self.primary_color
        theme.secondary_color = self.secondary_color
        theme.bg_color = self.bg_color
        theme.text_color = self.text_color
        theme.card_bg = self.card_bg
        theme.sidebar_bg = self.sidebar_bg
        theme.button_style = self.button_style

    @classmethod
    def apply_builtin_preset(cls, theme, preset_name):
        presets = {
            'modern': {'primary_color': '#2563eb', 'secondary_color': '#1d4ed8', 'bg_color': '#f1f5f9',
                       'text_color': '#1e293b', 'card_bg': '#ffffff', 'sidebar_bg': '#111827', 'button_style': 'rounded'},
            'corporate': {'primary_color': '#059669', 'secondary_color': '#047857', 'bg_color': '#f0fdf4',
                          'text_color': '#1e293b', 'card_bg': '#ffffff', 'sidebar_bg': '#064e3b', 'button_style': 'square'},
            'minimal': {'primary_color': '#334155', 'secondary_color': '#1e293b', 'bg_color': '#f8fafc',
                        'text_color': '#0f172a', 'card_bg': '#ffffff', 'sidebar_bg': '#0f172a', 'button_style': 'square'},
            'vibrant': {'primary_color': '#7c3aed', 'secondary_color': '#6d28d9', 'bg_color': '#f5f3ff',
                        'text_color': '#1e1b4b', 'card_bg': '#ffffff', 'sidebar_bg': '#2e1065', 'button_style': 'pill'},
            'dark-neumorphic': {'primary_color': '#10b981', 'secondary_color': '#059669', 'bg_color': '#1a202c',
                                'text_color': '#e2e8f0', 'card_bg': '#2d3748', 'sidebar_bg': '#0f172a', 'button_style': 'pill'},
        }
        if preset_name in presets:
            for k, v in presets[preset_name].items():
                setattr(theme, k, v)
            theme.theme_name = preset_name


class UserActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Creación'),
        ('update', 'Actualización'),
        ('delete', 'Eliminación'),
        ('login', 'Inicio de sesión'),
        ('logout', 'Cierre de sesión'),
        ('view', 'Visualización'),
        ('other', 'Otro'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                            verbose_name='Usuario')
    username = models.CharField('Nombre de usuario', max_length=150, blank=True, default='')
    action = models.CharField('Acción', max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField('Modelo', max_length=100, blank=True, default='')
    object_repr = models.CharField('Objeto', max_length=255, blank=True, default='')
    object_id = models.PositiveIntegerField('ID del objeto', null=True, blank=True)
    details = models.TextField('Detalles', blank=True, default='')
    ip_address = models.GenericIPAddressField('Dirección IP', blank=True, null=True)
    path = models.CharField('Ruta', max_length=500, blank=True, default='')
    timestamp = models.DateTimeField('Fecha y hora', auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Actividad'
        verbose_name_plural = 'Registros de Actividad'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.username or self.user} — {self.get_action_display()} ({self.timestamp.strftime("%d/%m/%Y %H:%M")})'


class ErrorPageSettings(models.Model):
    title = models.CharField('Título', max_length=200, default='¡Página no encontrada!')
    message = models.TextField('Mensaje', default='La página que buscas no existe o fue movida. Usa la navegación para encontrar lo que necesitas.')
    show_pixel_art = models.BooleanField('Mostrar arte pixelado', default=True)
    bg_color = models.CharField('Color de fondo', max_length=7, default='#1a202c')
    text_color = models.CharField('Color de texto', max_length=7, default='#e2e8f0')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de página 404'
        verbose_name_plural = 'Configuración de página 404'

    def __str__(self):
        return 'Configuración 404'

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'title': '¡Página no encontrada!'})
        return obj


class SessionConfig(models.Model):
    timeout_minutes = models.PositiveIntegerField('Tiempo de sesión (minutos)', default=60)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de sesión'
        verbose_name_plural = 'Configuración de sesión'

    def __str__(self):
        return f'Sesión expira en {self.timeout_minutes} minutos'

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={'timeout_minutes': 60})
        return obj


def log_user_action(user, action, model_name='', object_repr='', object_id=None, details='', request=None):
    if not user or not user.is_authenticated:
        return
    UserActivityLog.objects.create(
        user=user,
        username=user.username,
        action=action,
        model_name=model_name,
        object_repr=str(object_repr)[:255],
        object_id=object_id,
        details=details,
        ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR', None) if request else None,
        path=getattr(request, 'path', '') if request else '',
    )
