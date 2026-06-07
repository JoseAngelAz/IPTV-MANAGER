from django import forms
from .models import MovimientoFinanciero


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoFinanciero
        fields = ('tipo', 'monto', 'descripcion', 'suscripcion')
        widgets = {
            'tipo': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'monto': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded', 'step': '0.01'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded', 'rows': 3}),
            'suscripcion': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
        }
