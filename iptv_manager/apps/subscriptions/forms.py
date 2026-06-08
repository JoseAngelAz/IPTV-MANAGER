from django import forms
from django.core.exceptions import ValidationError
from .models import Suscripcion, Plan
from apps.clients.models import Cliente


class SuscripcionForm(forms.ModelForm):
    class Meta:
        model = Suscripcion
        fields = ('cliente', 'plan', 'fecha_inicio', 'descuento_tipo', 'descuento_valor', 'metodo_pago')
        widgets = {
            'cliente': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'plan': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'fecha_inicio': forms.DateTimeInput(attrs={'class': 'w-full px-3 py-2 border rounded', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M:%S'),
            'descuento_tipo': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'descuento_valor': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded', 'step': '0.01', 'placeholder': '0.00', 'min': '0'}),
            'metodo_pago': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_inicio'].required = False
        self.fields['descuento_tipo'].required = False
        self.fields['descuento_valor'].required = False
        self.fields['metodo_pago'].required = False

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('descuento_tipo')
        valor = cleaned.get('descuento_valor')
        plan = cleaned.get('plan')

        if tipo and valor is not None and plan:
            if valor < 0:
                raise ValidationError('El descuento no puede ser negativo.')

            if tipo == Suscripcion.DescuentoTipo.PORCENTAJE and valor > 100:
                raise ValidationError('El descuento porcentual no puede superar el 100%.')

            if tipo == Suscripcion.DescuentoTipo.FIJO and valor > plan.precio:
                raise ValidationError(
                    f'El descuento fijo no puede superar el precio del plan (${plan.precio}).'
                )

        return cleaned