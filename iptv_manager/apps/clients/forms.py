from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ('nombre', 'telefono', 'email', 'dispositivo_id', 'documento_identidad', 'foto')
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white', 'placeholder': '+521234567890'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'dispositivo_id': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white', 'placeholder': 'XX:XX:XX:XX:XX:XX'}),
            'documento_identidad': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white', 'placeholder': 'INE, Pasaporte, etc. (opcional)'}),
            'foto': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
        }
