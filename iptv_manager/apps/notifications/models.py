from django.db import models
from apps.clients.models import Cliente
from apps.subscriptions.models import Suscripcion


class LogNotificacion(models.Model):
    class Canal(models.TextChoices):
        WHATSAPP = 'whatsapp', 'WhatsApp'
        EMAIL = 'email', 'Email'

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name='Cliente')
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, verbose_name='Suscripción')
    canal = models.CharField('Canal', max_length=10, choices=Canal.choices)
    destinatario = models.CharField('Destinatario', max_length=200)
    mensaje = models.TextField('Mensaje')
    enviado_ok = models.BooleanField('Enviado correctamente', default=False)
    respuesta_api = models.TextField('Respuesta API', blank=True, default='')
    fecha_envio = models.DateTimeField('Fecha de envío', auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Notificación'
        verbose_name_plural = 'Logs de Notificaciones'
        ordering = ['-fecha_envio']
        unique_together = [('suscripcion', 'canal')]

    def __str__(self):
        return f'{self.get_canal_display()} a {self.cliente} — {"OK" if self.enviado_ok else "FALLO"}'
