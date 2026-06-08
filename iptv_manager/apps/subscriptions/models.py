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

    class DescuentoTipo(models.TextChoices):
        PORCENTAJE = 'porcentaje', 'Porcentaje (%)'
        FIJO = 'fijo', 'Fijo ($)'

    class MetodoPago(models.TextChoices):
        EFECTIVO = 'efectivo', 'Efectivo'
        CHEQUE = 'cheque', 'Cheque'
        TARJETA_DEBITO = 'tarjeta_debito', 'Tarjeta de Débito'
        CORTESIA = 'cortesia', 'Cortesía'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='suscripciones', verbose_name='Cliente')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, verbose_name='Plan')
    fecha_inicio = models.DateTimeField('Fecha de inicio', default=timezone.now, null=True, blank=True)
    fecha_vencimiento = models.DateTimeField('Fecha de vencimiento', editable=False)
    estado = models.CharField('Estado', max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    descuento_tipo = models.CharField('Tipo de descuento', max_length=12, choices=DescuentoTipo.choices, null=True, blank=True)
    descuento_valor = models.DecimalField('Valor de descuento', max_digits=10, decimal_places=2, null=True, blank=True)
    metodo_pago = models.CharField('Método de pago', max_length=20, choices=MetodoPago.choices, default=MetodoPago.EFECTIVO)

    class Meta:
        verbose_name = 'Suscripción'
        verbose_name_plural = 'Suscripciones'
        ordering = ['-fecha_inicio']

    def save(self, *args, **kwargs):
        if not self.fecha_vencimiento:
            self.fecha_vencimiento = self.fecha_inicio + timezone.timedelta(days=self.plan.duracion_dias)
        super().save(*args, **kwargs)

    def get_precio_final(self):
        precio = self.plan.precio
        if self.descuento_tipo == self.DescuentoTipo.PORCENTAJE and self.descuento_valor:
            descuento = precio * self.descuento_valor / 100
            return precio - descuento
        elif self.descuento_tipo == self.DescuentoTipo.FIJO and self.descuento_valor:
            return max(0, precio - self.descuento_valor)
        return precio

    def get_monto_ingreso(self):
        if self.descuento_tipo == self.DescuentoTipo.PORCENTAJE and self.descuento_valor:
            descuento = self.plan.precio * self.descuento_valor / 100
            return self.plan.precio - descuento
        elif self.descuento_tipo == self.DescuentoTipo.FIJO and self.descuento_valor:
            return max(0, self.plan.precio - self.descuento_valor)
        return self.plan.precio

    def get_descuento_info(self):
        if self.descuento_tipo == self.DescuentoTipo.PORCENTAJE and self.descuento_valor is not None:
            return f'{self.descuento_valor}%'
        elif self.descuento_tipo == self.DescuentoTipo.FIJO and self.descuento_valor is not None:
            return f'${self.descuento_valor}'
        return '—'

    def __str__(self):
        return f'{self.cliente} — {self.plan.nombre} ({self.get_estado_display()})'
