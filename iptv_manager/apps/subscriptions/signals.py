from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.accounts.middleware import get_current_user
from .models import Suscripcion
from apps.clients.models import HistorialCliente


@receiver(post_save, sender=Suscripcion)
def historial_suscripcion_post_save(sender, instance, created, raw, **kwargs):
    if raw:
        return

    usuario = get_current_user()

    if created:
        cambio = (
            f'Nueva suscripción: {instance.plan.nombre} '
            f'(inicia {instance.fecha_inicio.strftime("%d/%m/%Y")}, '
            f'vence {instance.fecha_vencimiento.strftime("%d/%m/%Y")})'
        )
    else:
        cambio = (
            f'Suscripción {instance.plan.nombre} '
            f'actualizada a estado "{instance.get_estado_display()}"'
        )

    HistorialCliente.objects.create(
        cliente=instance.cliente,
        usuario=usuario,
        cambio=cambio,
    )
