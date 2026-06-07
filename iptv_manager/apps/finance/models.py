from django.db import models
from apps.subscriptions.models import Suscripcion


class MovimientoFinanciero(models.Model):
    class Tipo(models.TextChoices):
        INGRESO = 'ingreso', 'Ingreso'
        EGRESO = 'egreso', 'Egreso'

    tipo = models.CharField('Tipo', max_length=10, choices=Tipo.choices)
    monto = models.DecimalField('Monto', max_digits=12, decimal_places=2)
    descripcion = models.TextField('Descripción')
    fecha = models.DateTimeField('Fecha', auto_now_add=True)
    suscripcion = models.ForeignKey(
        Suscripcion, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Suscripción relacionada'
    )

    class Meta:
        verbose_name = 'Movimiento Financiero'
        verbose_name_plural = 'Movimientos Financieros'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()} — ${self.monto} ({self.fecha.strftime("%d/%m/%Y")})'
