from django.db import migrations, models


VERTICALES = [
    ('iptv', 'IPTV'),
    ('gimnasio', 'Gimnasio / Gym'),
    ('escuela', 'Escuela / School'),
    ('taller', 'Taller / Workshop'),
    ('consultorio', 'Consultorio / Clinic'),
    ('otro', 'Otro / Other'),
]


def seed_templates(apps, schema_editor):
    BusinessTemplate = apps.get_model('clients', 'BusinessTemplate')
    for key, label in VERTICALES:
        BusinessTemplate.objects.get_or_create(vertical=key)


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0006_customfield'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vertical', models.CharField(choices=[('', '— Global (todas las verticales)'), ('iptv', 'IPTV'), ('gimnasio', 'Gimnasio / Gym'), ('escuela', 'Escuela / School'), ('taller', 'Taller / Workshop'), ('consultorio', 'Consultorio / Clinic'), ('otro', 'Otro / Other')], max_length=50, unique=True, verbose_name='Vertical de negocio')),
                ('aplicado', models.BooleanField(default=False, help_text='Indica si este preset ya fue aplicado para crear los campos personalizados.', verbose_name='Aplicado')),
                ('fecha_aplicado', models.DateTimeField(blank=True, null=True, verbose_name='Fecha de aplicación')),
            ],
            options={
                'verbose_name': 'Plantilla de negocio',
                'verbose_name_plural': 'Plantillas de negocio',
            },
        ),
        migrations.RunPython(seed_templates),
    ]
