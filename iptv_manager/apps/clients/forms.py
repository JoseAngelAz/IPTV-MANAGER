import json
from django import forms
from .models import Cliente, CustomField


class ClienteForm(forms.ModelForm):
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
        self.fields['dispositivo_id'].required = False
        self._custom_field_names = []

        extra_data = {}
        if self.instance and self.instance.pk and self.instance.datos_extra:
            extra_data = self.instance.datos_extra

        custom_fields = CustomField.objects.filter(activo=True)
        for cf in custom_fields:
            field_name = f'_cf_{cf.pk}'
            self._custom_field_names.append(field_name)
            initial_val = extra_data.get(cf.nombre, '')
            base_attrs = {'class': 'w-full px-3 py-2 border rounded dark:bg-gray-700 dark:text-white'}
            required = cf.required

            if cf.field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=cf.nombre, required=required, initial=initial_val,
                    widget=forms.TextInput(attrs=base_attrs))
            elif cf.field_type == 'number':
                self.fields[field_name] = forms.FloatField(
                    label=cf.nombre, required=required, initial=initial_val,
                    widget=forms.NumberInput(attrs=base_attrs))
            elif cf.field_type == 'boolean':
                self.fields[field_name] = forms.BooleanField(
                    label=cf.nombre, required=False, initial=initial_val in (True, 'True', 'true', 1, '1'))
            elif cf.field_type == 'date':
                self.fields[field_name] = forms.DateField(
                    label=cf.nombre, required=required, initial=initial_val or None,
                    widget=forms.DateInput(attrs={**base_attrs, 'type': 'date'}))
            elif cf.field_type == 'email':
                self.fields[field_name] = forms.EmailField(
                    label=cf.nombre, required=required, initial=initial_val,
                    widget=forms.EmailInput(attrs=base_attrs))
            elif cf.field_type == 'select' and cf.options:
                choices = [('', '---------')] + [(o.strip(), o.strip()) for o in cf.options.split('\n') if o.strip()]
                self.fields[field_name] = forms.ChoiceField(
                    label=cf.nombre, required=required, initial=initial_val, choices=choices,
                    widget=forms.Select(attrs=base_attrs))

    def clean_dispositivo_id(self):
        value = self.cleaned_data.get('dispositivo_id', '')
        if not value or value.strip() == '':
            return None
        return value

    def clean(self):
        cleaned = super().clean()
        extra = {}
        for field_name in self._custom_field_names:
            val = cleaned.get(field_name)
            if val is None or val == '':
                continue
            if isinstance(val, bool) and val is False:
                continue
            if isinstance(val, float) and val == int(val):
                val = int(val)
            pk = int(field_name.replace('_cf_', ''))
            try:
                cf = CustomField.objects.get(pk=pk)
                extra[cf.nombre] = val
            except CustomField.DoesNotExist:
                pass
        cleaned['datos_extra'] = extra
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(self, 'cleaned_data') and 'datos_extra' in self.cleaned_data:
            instance.datos_extra = self.cleaned_data['datos_extra']
        if commit:
            instance.save()
        return instance
