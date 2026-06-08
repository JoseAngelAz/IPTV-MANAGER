from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from apps.accounts.middleware import get_current_user
from .models import Suscripcion
from apps.clients.models import HistorialCliente
from apps.finance.models import MovimientoFinanciero


def _calcular_descuento(instance):
    if instance.descuento_tipo == Suscripcion.DescuentoTipo.PORCENTAJE and instance.descuento_valor:
        pct = min(instance.descuento_valor, 100)
        return instance.plan.precio * pct / 100
    elif instance.descuento_tipo == Suscripcion.DescuentoTipo.FIJO and instance.descuento_valor:
        return min(instance.plan.precio, instance.descuento_valor)
    return 0


def _sincronizar_movimientos(instance):
    MovimientoFinanciero.objects.filter(suscripcion=instance).delete()

    ingreso_desc = f'Ingreso por suscripción: {instance.cliente.nombre} — {instance.plan.nombre}'
    MovimientoFinanciero.objects.create(
        tipo=MovimientoFinanciero.Tipo.INGRESO,
        monto=instance.plan.precio,
        descripcion=ingreso_desc,
        suscripcion=instance,
    )

    descuento = _calcular_descuento(instance)
    if descuento > 0:
        MovimientoFinanciero.objects.create(
            tipo=MovimientoFinanciero.Tipo.EGRESO,
            monto=descuento,
            descripcion=f'Descuento aplicado: {instance.get_descuento_info()} — {instance.cliente.nombre} ({instance.plan.nombre})',
            suscripcion=instance,
        )


@receiver(post_save, sender=Suscripcion)
def historial_suscripcion_post_save(sender, instance, created, raw, **kwargs):
    if raw:
        return

    usuario = get_current_user()

    if created:
        inicio = instance.fecha_inicio or instance.fecha_vencimiento - timezone.timedelta(days=instance.plan.duracion_dias)
        cambio = (
            f'Nueva suscripción: {instance.plan.nombre} '
            f'(inicia {inicio.strftime("%d/%m/%Y")}, '
            f'vence {instance.fecha_vencimiento.strftime("%d/%m/%Y")})'
        )
    else:
        cambio = (
            f'Suscripción {instance.plan.nombre} '
            f'actualizada — estado: "{instance.get_estado_display()}"'
        )
        if instance.descuento_valor:
            cambio += f', descuento: {instance.get_descuento_info()}'

    _sincronizar_movimientos(instance)

    HistorialCliente.objects.create(
        cliente=instance.cliente,
        usuario=usuario,
        cambio=cambio,
    )