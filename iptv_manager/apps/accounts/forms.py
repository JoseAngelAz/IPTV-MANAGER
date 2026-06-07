from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, ThemeSettings, CustomPreset, SessionConfig


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white',
                                       'placeholder': 'Usuario', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white',
                                          'placeholder': 'Contraseña'})
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'profile_picture': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
        }


class ThemeForm(forms.ModelForm):
    apply_preset = forms.ChoiceField(
        choices=[('', '--- Seleccionar preset ---')] + list(ThemeSettings.THEME_CHOICES),
        required=False,
        label='Aplicar preset',
        widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'})
    )

    class Meta:
        model = ThemeSettings
        fields = ('theme_name', 'primary_color', 'secondary_color', 'bg_color', 'text_color', 'card_bg', 'sidebar_bg', 'button_style', 'custom_css', 'pixel_bg')
        widgets = {
            'theme_name': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'bg_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'card_bg': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'sidebar_bg': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'button_style': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'custom_css': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white font-mono text-sm', 'rows': 6, 'placeholder': '/* CSS personalizado aquí */'}),
            'pixel_bg': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
        }


class CustomPresetForm(forms.ModelForm):
    class Meta:
        model = CustomPreset
        fields = ('name', 'icon', 'primary_color', 'secondary_color', 'bg_color', 'text_color', 'card_bg', 'sidebar_bg', 'button_style')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white', 'placeholder': 'Nombre de mi preset'}),
            'icon': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'bg_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'card_bg': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'sidebar_bg': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 p-1 border rounded cursor-pointer'}),
            'button_style': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}),
        }


class SessionConfigForm(forms.ModelForm):
    class Meta:
        model = SessionConfig
        fields = ('timeout_minutes',)
        widgets = {
            'timeout_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white',
                'min': 1, 'max': 1440,
            }),
        }
        labels = {'timeout_minutes': 'Tiempo de sesión (minutos)'}
