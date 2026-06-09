from .models import CustomField

PRESETS = {
    'iptv': {
        'nombre': 'IPTV',
        'descripcion': 'Campos para negocio de televisión IP / IPTV business fields',
        'campos': [
            {'nombre': 'Plan / Package', 'field_type': 'text', 'required': True},
            {'nombre': 'Dirección de instalación', 'field_type': 'text', 'required': False},
            {'nombre': 'Tipo de conexión', 'field_type': 'select', 'required': False,
             'options': 'Fibra\nCable\nInalámbrico\n5G'},
            {'nombre': 'Número de receptores', 'field_type': 'number', 'required': False},
            {'nombre': 'Notas de instalación', 'field_type': 'text', 'required': False},
        ],
    },
    'gimnasio': {
        'nombre': 'Gimnasio / Gym',
        'descripcion': 'Campos para administración de gimnasio / Gym management fields',
        'campos': [
            {'nombre': 'Tipo de membresía', 'field_type': 'select', 'required': True,
             'options': 'Mensual\nTrimestral\nSemestral\nAnual'},
            {'nombre': 'Contacto de emergencia', 'field_type': 'text', 'required': False},
            {'nombre': 'Teléfono emergencia', 'field_type': 'text', 'required': False},
            {'nombre': 'Condiciones médicas', 'field_type': 'text', 'required': False},
            {'nombre': 'Fecha de ingreso', 'field_type': 'date', 'required': True},
            {'nombre': 'Vencimiento de membresía', 'field_type': 'date', 'required': False},
        ],
    },
    'escuela': {
        'nombre': 'Escuela / School',
        'descripcion': 'Campos para administración escolar / School management fields',
        'campos': [
            {'nombre': 'Grado / Grade', 'field_type': 'select', 'required': True,
             'options': '1°\n2°\n3°\n4°\n5°\n6°'},
            {'nombre': 'Grupo / Section', 'field_type': 'text', 'required': True},
            {'nombre': 'Nombre del padre/tutor', 'field_type': 'text', 'required': True},
            {'nombre': 'Teléfono del padre/tutor', 'field_type': 'text', 'required': True},
            {'nombre': 'Dirección', 'field_type': 'text', 'required': False},
            {'nombre': 'Alergias / condiciones', 'field_type': 'text', 'required': False},
        ],
    },
    'taller': {
        'nombre': 'Taller / Workshop',
        'descripcion': 'Campos para taller mecánico o de servicios / Workshop fields',
        'campos': [
            {'nombre': 'Tipo de vehículo / equipo', 'field_type': 'select', 'required': True,
             'options': 'Automóvil\nMotocicleta\nCamioneta\nBicicleta\nOtro'},
            {'nombre': 'Marca / Brand', 'field_type': 'text', 'required': True},
            {'nombre': 'Modelo', 'field_type': 'text', 'required': True},
            {'nombre': 'Año / Year', 'field_type': 'number', 'required': False},
            {'nombre': 'Tipo de servicio', 'field_type': 'select', 'required': True,
             'options': 'Mantenimiento\nReparación\nDiagnóstico\nInstalación\nOtro'},
            {'nombre': 'Notas del servicio', 'field_type': 'text', 'required': False},
        ],
    },
    'consultorio': {
        'nombre': 'Consultorio / Clinic',
        'descripcion': 'Campos para consultorio médico / Medical clinic fields',
        'campos': [
            {'nombre': 'Tipo de sangre', 'field_type': 'select', 'required': False,
             'options': 'A+\nA-\nB+\nB-\nAB+\nAB-\nO+\nO-'},
            {'nombre': 'Alergias', 'field_type': 'text', 'required': False},
            {'nombre': 'Aseguradora', 'field_type': 'text', 'required': False},
            {'nombre': 'Número de póliza', 'field_type': 'text', 'required': False},
            {'nombre': 'Contacto de emergencia', 'field_type': 'text', 'required': True},
            {'nombre': 'Teléfono emergencia', 'field_type': 'text', 'required': True},
            {'nombre': 'Fecha de última visita', 'field_type': 'date', 'required': False},
        ],
    },
}


def apply_preset(vertical_key, clear_existing=False):
    """Create CustomField instances from a preset definition."""
    if vertical_key not in PRESETS:
        raise ValueError(f"Preset '{vertical_key}' not found. Available: {list(PRESETS.keys())}")

    preset = PRESETS[vertical_key]
    if clear_existing:
        CustomField.objects.filter(vertical=vertical_key).delete()

    created = []
    for idx, campo in enumerate(preset['campos']):
        cf, was_created = CustomField.objects.get_or_create(
            nombre=campo['nombre'],
            vertical=vertical_key,
            defaults={
                'field_type': campo['field_type'],
                'required': campo.get('required', False),
                'options': campo.get('options', ''),
                'ordering': idx,
                'activo': True,
            },
        )
        if was_created:
            created.append(cf)
    return created
