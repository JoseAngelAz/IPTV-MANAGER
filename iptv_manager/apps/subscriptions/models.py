from django.db import models
from django.utils import timezone
from apps.clients.models import Cliente


class Plan(models.Model):
    nombre = models.CharField('Nombre', max_length=100, unique=True)
    precio = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    duracion_dias = models.PositiveIntegerField('Duración (días)')
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'

    def __str__(self):
        return f'{self.nombre} — ${self.precio}'


class Suscripcion(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        VENCIDO = 'vencido', 'Vencido'
        CANCELADO = 'cancelado', 'Cancelado'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='suscripciones', verbose_name='Cliente')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, verbose_name='Plan')
    fecha_inicio = models.DateTimeField('Fecha de inicio', default=timezone.now)
    fecha_vencimiento = models.DateTimeField('Fecha de vencimiento', editable=False)
    estado = models.CharField('Estado', max_length=20, choices=Estado.choices, default=Estado.ACTIVO)

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-fecha_inicio']

    def save(self, *args, **kwargs):
        if not self.fecha_vencimiento:
            self.fecha_vencimiento = self.fecha_inicio + timezone.timedelta(days=self.plan.duracion_dias)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.cliente} — {self.plan.nombre} ({self.get_estado_display()})'
