import os
from io import BytesIO
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from PIL import Image


telefono_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message='Teléfono debe estar en formato internacional (ej. +521234567890).'
)

mac_validator = RegexValidator(
    regex=r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',
    message='MAC address debe tener formato XX:XX:XX:XX:XX:XX o XX-XX-XX-XX-XX-XX.'
)


def _procesar_foto(instance, filename):
    ext = '.jpg'
    nombre = f'cliente_{instance.pk or "new"}{ext}'
    return os.path.join('fotos_clientes', nombre)


def comprimir_foto(image_field, max_dim=400, quality=70):
    if not image_field:
        return
    img = Image.open(image_field)
    img = img.convert('RGB')
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    buffer.seek(0)
    image_field.file = buffer
    image_field.name = image_field.name.rsplit('.', 1)[0] + '.jpg'


class Cliente(models.Model):
    nombre = models.CharField('Nombre', max_length=200)
    telefono = models.CharField('Teléfono', max_length=16, validators=[telefono_validator])
    email = models.EmailField('Email', blank=True, default='')
    dispositivo_id = models.CharField('ID Dispositivo / MAC', max_length=20, validators=[mac_validator], unique=True, null=True, blank=True)
    foto = models.ImageField('Foto', upload_to=_procesar_foto, blank=True, null=True)
    documento_identidad = models.CharField('Documento de identidad', max_length=100, blank=True, default='')
    datos_extra = models.JSONField('Datos adicionales', blank=True, null=True, default=dict,
        help_text='Almacena campos personalizados adicionales en formato JSON.')
    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-fecha_registro']

    def save(self, *args, **kwargs):
        if self.foto:
            comprimir_foto(self.foto)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.dispositivo_id:
            return f'{self.nombre} ({self.dispositivo_id})'
        return self.nombre


class HistorialCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='historial', verbose_name='Cliente')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Realizado por')
    cambio = models.TextField('Cambio / Nota')
    fecha = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de Cliente'
        verbose_name_plural = 'Historiales de Cliente'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.cliente} — {self.fecha.strftime("%d/%m/%Y %H:%M")}'


class CustomField(models.Model):
    FIELD_TYPES = (
        ('text', 'Texto / Text'),
        ('number', 'Número / Number'),
        ('boolean', 'Sí/No / Boolean'),
        ('date', 'Fecha / Date'),
        ('email', 'Email'),
        ('select', 'Selección / Select'),
    )
    VERTICAL_CHOICES = (
        ('', '— Global (todas las verticales)'),
        ('iptv', 'IPTV'),
        ('gimnasio', 'Gimnasio / Gym'),
        ('escuela', 'Escuela / School'),
        ('taller', 'Taller / Workshop'),
        ('consultorio', 'Consultorio / Clinic'),
        ('otro', 'Otro / Other'),
    )
    nombre = models.CharField('Nombre del campo', max_length=100)
    field_type = models.CharField('Tipo de campo', max_length=20, choices=FIELD_TYPES, default='text')
    required = models.BooleanField('Requerido', default=False)
    options = models.TextField('Opciones', blank=True,
        help_text='Para tipo "Selección", una opción por línea. / For "Select" type, one option per line.')
    vertical = models.CharField('Vertical de negocio', max_length=50, choices=VERTICAL_CHOICES, blank=True, default='',
        help_text='Dejar vacío para aplicar a todas las verticales. / Leave empty for all verticals.')
    ordering = models.IntegerField('Orden', default=0)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Campo personalizado'
        verbose_name_plural = 'Campos personalizados'
        ordering = ['ordering', 'nombre']

    def __str__(self):
        return self.nombre


class Nota(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notas', verbose_name='Cliente')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name='Creada por')
    contenido = models.TextField('Contenido')
    fecha = models.DateTimeField('Fecha', auto_now_add=True)

    class Meta:
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.cliente} — {self.fecha.strftime("%d/%m/%Y %H:%M")}'
