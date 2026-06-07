from django.db import models


class ReportTemplate(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    primary_color = models.CharField(max_length=7, default='#2563eb')
    secondary_color = models.CharField(max_length=7, default='#1e40af')
    header_bg = models.CharField(max_length=7, default='#1e293b')
    table_header_bg = models.CharField(max_length=7, default='#3b82f6')
    font_family = models.CharField(max_length=50, default='Helvetica')
    accent_style = models.CharField(max_length=20, default='bars')  # bars, lines, blocks

    class Meta:
        verbose_name = 'Plantilla de reporte'
        verbose_name_plural = 'Plantillas de reporte'

    def __str__(self):
        return self.nombre

    @classmethod
    def get_presets(cls):
        return {
            1: cls(
                nombre='Ejecutivo',
                descripcion='Limpio y minimalista con cabeceras pastel y amplio espaciado.',
                primary_color='#2563eb', secondary_color='#1e40af',
                header_bg='#1e293b', table_header_bg='#3b82f6',
                font_family='Helvetica', accent_style='bars',
            ),
            2: cls(
                nombre='Moderno',
                descripcion='Barras oscuras, colores vibrantes, bordes definidos. Profesional y audaz.',
                primary_color='#7c3aed', secondary_color='#4f46e5',
                header_bg='#0f172a', table_header_bg='#7c3aed',
                font_family='Courier', accent_style='lines',
            ),
            3: cls(
                nombre='Clásico',
                descripcion='Estilo tradicional con líneas dobles, bordes formales y tipografía serif.',
                primary_color='#1e3a5f', secondary_color='#b8860b',
                header_bg='#1e3a5f', table_header_bg='#b8860b',
                font_family='Times-Roman', accent_style='blocks',
            ),
        }
