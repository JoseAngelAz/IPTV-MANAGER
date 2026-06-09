import json
from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    datos_extra_json = forms.CharField(
        label='Datos adicionales (JSON)',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white font-mono text-sm',
            'rows': 4,
            'placeholder': '{"campo_extra": "valor"}',
        }),
        help_text='Campos personalizados en formato JSON. Ej: {"membresia": "Premium", "tipo": "VIP"}'
    )

    class Meta:
        model = Cliente
        fields = ('nombre', 'telefono', 'email', 'dispositivo_id', 'documento_identidad', 'foto')
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white', 'placeholder': '+521234567890'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'dispositivo_id': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white', 'placeholder': 'XX:XX:XX:XX:XX:XX (opcional)'}),
            'documento_identidad': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white', 'placeholder': 'INE, Pasaporte, etc. (opcional)'}),
            'foto': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.datos_extra:
                self.fields['datos_extra_json'].initial = json.dumps(
                    self.instance.datos_extra, indent=2, ensure_ascii=False
                )
        self.fields['dispositivo_id'].required = False

    def clean_datos_extra_json(self):
        data = self.cleaned_data.get('datos_extra_json', '')
        if not data or not data.strip():
            return {}
        try:
            result = json.loads(data)
            if not isinstance(result, dict):
                raise forms.ValidationError('Debe ser un objeto JSON (diccionario).')
            return result
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'JSON inválido: {e}')

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.datos_extra = self.cleaned_data.get('datos_extra_json', {})
        if commit:
            instance.save()
        return instance
