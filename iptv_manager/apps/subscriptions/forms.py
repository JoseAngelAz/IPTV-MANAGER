from django import forms
from .models import Suscripcion, Plan
from apps.clients.models import Cliente


class SuscripcionForm(forms.ModelForm):
    class Meta:
        model = Suscripcion
        fields = ('cliente', 'plan', 'fecha_inicio')
        widgets = {
            'cliente': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'plan': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'fecha_inicio': forms.DateTimeInput(attrs={'class': 'w-full px-3 py-2 border rounded', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_inicio'].required = False
