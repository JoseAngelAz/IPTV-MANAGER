from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

MARGIN_MAP = {
    'small': 1.5 * cm,
    'normal': 2.54 * cm,
    'large': 3.0 * cm,
}
FONT_MAP = {
    'helvetica': 'Helvetica',
    'times': 'Times-Roman',
    'courier': 'Courier',
}
PADDING_MAP = {
    'compact': (3, 3, 3, 3),
    'normal': (5, 5, 4, 4),
    'spacious': (8, 8, 6, 6),
}

COLOR = {
    'ejecutivo': {
        'primary': HexColor('#2563eb'), 'secondary': HexColor('#1e40af'),
        'line': HexColor('#94a3b8'), 'subheader': HexColor('#475569'),
    },
    'moderno': {
        'primary': HexColor('#7c3aed'), 'secondary': HexColor('#4f46e5'),
        'line': HexColor('#a78bfa'), 'subheader': HexColor('#6b21a8'),
    },
    'clasico': {
        'primary': HexColor('#1e3a5f'), 'secondary': HexColor('#b8860b'),
        'line': HexColor('#8b7355'), 'subheader': HexColor('#4a3728'),
    },
}

FONTS = {
    'ejecutivo': 'Helvetica',
    'moderno': 'Helvetica',
    'clasico': 'Times-Roman',
}


class ReportPDF:
    def __init__(self, template_id, sections, data, date_start, date_end, user,
                 margin='normal', font='helvetica', padding='normal',
                 landscape_mode=False, chart_type='bar',
                 chart_ingreso_color='#22c55e', chart_egreso_color='#ef4444'):
        self.template_id = template_id
        self.template_name = {1: 'ejecutivo', 2: 'moderno', 3: 'clasico'}[template_id]
        self.colors = COLOR[self.template_name]
        self.sections = sections
        self.data = data
        self.date_start = date_start
        self.date_end = date_end
        self.user = user
        self.margin = MARGIN_MAP.get(margin, 2.54 * cm)
        self.font_name = FONT_MAP.get(font, 'Helvetica')
        self.padding = PADDING_MAP.get(padding, (5, 5, 4, 4))
        self.landscape_mode = landscape_mode
        self.chart_type = chart_type
        self.chart_ingreso_color = HexColor(chart_ingreso_color)
        self.chart_egreso_color = HexColor(chart_egreso_color)
        self.elements = []
        self._table_num = 0
        self._figure_num = 0

    @property
    def page_size(self):
        return landscape(A4) if self.landscape_mode else A4

    @property
    def usable_width(self):
        pw = self.page_size[0]
        return pw - 2 * self.margin

    def _style(self, name, **kw):
        base = {'fontName': self.font_name, 'textColor': black}
        base.update(kw)
        return ParagraphStyle(name, **base)

    def _h1(self):
        return self._style('H1', fontName=self.font_name, fontSize=20, textColor=self.colors['primary'],
                           spaceAfter=4, leading=24)

    def _h2(self):
        return self._style('H2', fontName=self.font_name, fontSize=13, textColor=self.colors['secondary'],
                           spaceBefore=14, spaceAfter=6, leading=16)

    def _body(self):
        return self._style('Body', fontName=self.font_name, fontSize=10, leading=14, spaceAfter=4)

    def _small(self):
        return self._style('Small', fontName=self.font_name, fontSize=8, textColor=HexColor('#64748b'), leading=10)

    def _footer(self):
        return self._style('Footer', fontName=self.font_name, fontSize=8, textColor=HexColor('#94a3b8'), alignment=TA_CENTER)

    def _make_header(self):
        c = self.colors
        pw = self.page_size[0]
        t = Table([
            [Paragraph('Tiny ERP Manager',
                        self._style('_hdr1', fontSize=16, textColor=white, fontName=self.font_name)),
             Paragraph(datetime.now().strftime('%d/%m/%Y %H:%M'),
                       self._style('_hdr2', fontSize=8, textColor=HexColor('#cbd5e1'), alignment=TA_RIGHT))]
        ], colWidths=[pw - 2 * self.margin - 60])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), c['primary']),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ]))
        return t

    def _make_title(self):
        c = self.colors
        parts = []
        if self.sections:
            labels = {'clientes': 'Clientes', 'finanzas': 'Finanzas', 'notificaciones': 'Notificaciones', 'suscripciones': 'Suscripciones'}
            selected = [labels[s] for s in self.sections]
            parts.append(f'Reporte: {" + ".join(selected)}')
        else:
            parts.append('Reporte General')
        if self.date_start and self.date_end:
            parts.append(f'({self.date_start} al {self.date_end})')
        title = ' | '.join(parts)
        elements = []
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(title, self._h1()))
        elements.append(HRFlowable(width='100%', thickness=1.5, color=c['primary'], spaceAfter=4, spaceBefore=2))
        elements.append(Paragraph(f'Generado por: {self.user.get_full_name() or self.user.username}',
                                  self._small()))
        elements.append(Spacer(1, 10))
        return elements

    def _table_title(self, name):
        self._table_num += 1
        return Paragraph(f'<b>Tabla {self._table_num}.</b> {name}',
                         self._style('_tabtitle', fontName=self.font_name, fontSize=10, textColor=self.colors['subheader'],
                                     spaceBefore=10, spaceAfter=4, leading=13))

    def _figure_label(self, name):
        self._figure_num += 1
        return Paragraph(f'<i>Figura {self._figure_num}.</i> {name}',
                         self._style('_figlabel', fontName=self.font_name, fontSize=9, textColor=HexColor('#64748b'),
                                     spaceBefore=2, spaceAfter=6, leading=11, alignment=TA_CENTER))

    def _cell_style(self, size=10, align=TA_LEFT, bold=False):
        fn = self.font_name
        align_int = {0: TA_LEFT, 1: TA_CENTER, 2: TA_RIGHT,
                     'LEFT': TA_LEFT, 'CENTER': TA_CENTER, 'RIGHT': TA_RIGHT}.get(align, TA_LEFT)
        return self._style('_cell', fontName=fn, fontSize=size, leading=size + 3,
                           alignment=align_int)

    def _make_table(self, headers, rows, col_widths=None, alignments=None):
        c = self.colors
        tp, bp, lp, rp = self.padding

        header_paras = []
        for i, h in enumerate(headers):
            al = (alignments or {}).get(i, TA_LEFT)
            st = self._cell_style(size=10, align=al, bold=True)
            header_paras.append(Paragraph(f'<b>{h}</b>', st))

        body_rows = []
        for row in rows:
            para_row = []
            for i, val in enumerate(row):
                al = (alignments or {}).get(i, TA_LEFT)
                st = self._cell_style(size=9, align=al)
                para_row.append(Paragraph(str(val or ''), st))
            body_rows.append(para_row)

        table_data = [header_paras] + body_rows

        style_cmds = [
            ('LINEABOVE', (0, 0), (-1, 0), 1.5, c['primary']),
            ('LINEBELOW', (0, 0), (-1, 0), 0.8, c['line']),
            ('LINEBELOW', (0, -1), (-1, -1), 1, c['line']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), tp),
            ('BOTTOMPADDING', (0, 0), (-1, -1), bp),
            ('LEFTPADDING', (0, 0), (-1, -1), lp),
            ('RIGHTPADDING', (0, 0), (-1, -1), rp),
        ]

        t = Table(table_data, colWidths=col_widths or None, repeatRows=1)
        t.setStyle(TableStyle(style_cmds))
        return t

    def _chart_drawing(self, width, height):
        return Drawing(min(width, self.usable_width), height)

    def _add_chart(self, drawing, chart_data, labels, title,
                   colors=None, bar_names=None):
        usable = self.usable_width
        if self.chart_type == 'pie':
            pie = Pie()
            pie.x = (usable - 60) / 2
            pie.y = 15
            pie.width = 80
            pie.height = 80
            pie.data = list(chart_data)
            pie.labels = [str(l) for l in labels]
            pie.slices.strokeWidth = 0.5
            pie.slices.strokeColor = white
            if colors:
                for i, clr in enumerate(colors):
                    if i < len(pie.slices):
                        pie.slices[i].fillColor = clr
            drawing.add(pie)
        else:
            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 25
            bc.width = usable - 100
            bc.height = 65
            bc.data = [[v] for v in chart_data]
            bc.categoryAxis.categoryNames = list(labels)
            bc.categoryAxis.labels.fontSize = 8
            bc.categoryAxis.labels.fontName = self.font_name
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = max(chart_data, default=1) * 1.25
            bc.valueAxis.labels.fontSize = 8
            bc.valueAxis.labels.fontName = self.font_name
            bc.valueAxis.labelTextFormat = '$%1.0f' if any(isinstance(v, (int, float)) and v > 100 for v in chart_data) else '%d'
            if colors:
                for i, clr in enumerate(colors):
                    if i < len(bc.bars):
                        bc.bars[i].fillColor = clr
            bc.barWidth = 40 if len(chart_data) <= 3 else 25
            bc.groupSpacing = 40
            bc.strokeColor = None
            drawing.add(bc)
            drawing.add(Line(50, 22, usable - 50, 22, strokeColor=HexColor('#cbd5e1'), strokeWidth=0.5))
        return drawing

    def _section_clients(self):
        clients = self.data.get('clientes', [])
        if not clients:
            return [Paragraph('<i>No hay datos de clientes.</i>', self._body())]
        elements = []
        elements.append(self._table_title('Listado de clientes'))
        headers = ['#', 'Nombre', 'Teléfono', 'Email', 'Dispositivo', 'Registro', 'Subs Act.', 'Total']
        rows = []
        for i, c in enumerate(clients, 1):
            disp = (c.get('dispositivo_id') or '').replace('-', '')
            fecha_raw = c.get('fecha_registro', '')
            fecha_str = fecha_raw.strftime('%Y-%m-%d') if isinstance(fecha_raw, datetime) else (str(fecha_raw)[:10] if fecha_raw else '')
            total = float(c.get('total_gastado') or 0)
            rows.append([
                str(i), c.get('nombre', ''), c.get('telefono', ''),
                c.get('email', ''), disp, fecha_str,
                str(c.get('subs_activas', 0) or 0),
                f'${total:,.2f}'
            ])
        u = self.usable_width
        cw = [u * 0.05, u * 0.20, u * 0.12, u * 0.22, u * 0.12, u * 0.10, u * 0.08, u * 0.11]
        alignments = {0: 'CENTER', 6: 'CENTER', 7: 'RIGHT'}
        elements.append(self._make_table(headers, rows, col_widths=cw, alignments=alignments))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f'Total clientes: {len(clients)}', self._small()))
        return elements

    def _section_finanzas(self):
        finanzas = self.data.get('finanzas', [])
        resumen = self.data.get('resumen_finanzas', {})
        elements = []
        if resumen:
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(
                f'<b>Ingresos:</b> ${float(resumen.get("ingresos", 0)):,.2f} &nbsp;&nbsp;'
                f'<b>Egresos:</b> ${float(resumen.get("egresos", 0)):,.2f} &nbsp;&nbsp;'
                f'<b>Neto:</b> ${float(resumen.get("neto", 0)):,.2f}',
                self._body()))
            elements.append(Spacer(1, 6))
            ingresos = float(resumen.get('ingresos', 0))
            egresos = float(resumen.get('egresos', 0))
            if ingresos > 0 or egresos > 0:
                d = self._chart_drawing(280, 110)
                d = self._add_chart(d, [ingresos, egresos], ['Ingresos', 'Egresos'],
                                    'Ingresos vs Egresos',
                                    colors=[self.chart_ingreso_color, self.chart_egreso_color])
                elements.append(d)
                elements.append(self._figure_label('Comparación de ingresos vs egresos'))
        if not finanzas:
            elements.append(Paragraph('<i>No hay movimientos financieros.</i>', self._body()))
            return elements
        elements.append(self._table_title('Movimientos financieros'))
        headers = ['#', 'Tipo', 'Monto', 'Fecha', 'Descripción']
        rows = []
        for i, m in enumerate(finanzas, 1):
            fecha_raw = m.get('fecha', '')
            fecha_str = fecha_raw.strftime('%Y-%m-%d') if isinstance(fecha_raw, datetime) else (str(fecha_raw)[:10] if fecha_raw else '')
            rows.append([
                str(i), m.get('tipo', ''), f'${float(m.get("monto", 0)):,.2f}',
                fecha_str, m.get('descripcion', '')[:40]
            ])
        u = self.usable_width
        cw = [u * 0.06, u * 0.14, u * 0.14, u * 0.14, u * 0.52]
        alignments = {0: 'CENTER', 2: 'RIGHT', 3: 'CENTER'}
        elements.append(self._make_table(headers, rows, col_widths=cw, alignments=alignments))
        return elements

    def _section_notificaciones(self):
        notifs = self.data.get('notificaciones', [])
        if not notifs:
            return [Paragraph('<i>No hay notificaciones.</i>', self._body())]
        elements = []
        elements.append(self._table_title('Historial de notificaciones'))
        headers = ['#', 'Canal', 'Destinatario', 'Cliente', 'Mensaje', 'Estado', 'Fecha']
        rows = []
        for i, n in enumerate(notifs, 1):
            fecha_raw = n.get('fecha_creacion', '')
            fecha_str = fecha_raw.strftime('%Y-%m-%d') if isinstance(fecha_raw, datetime) else (str(fecha_raw)[:10] if fecha_raw else '')
            rows.append([
                str(i), n.get('canal', ''), n.get('destinatario', ''),
                n.get('cliente_nombre', ''), n.get('mensaje', '')[:40],
                '✓' if n.get('enviado_ok') else '✗',
                fecha_str
            ])
        u = self.usable_width
        cw = [u * 0.05, u * 0.10, u * 0.15, u * 0.15, u * 0.28, u * 0.07, u * 0.20]
        alignments = {0: 'CENTER', 5: 'CENTER', 6: 'CENTER'}
        elements.append(self._make_table(headers, rows, col_widths=cw, alignments=alignments))
        return elements

    def _section_suscripciones(self):
        subs = self.data.get('suscripciones', [])
        if not subs:
            return [Paragraph('<i>No hay suscripciones.</i>', self._body())]
        elements = []

        estados = {}
        for s in subs:
            estados[s.get('estado', '')] = estados.get(s.get('estado', ''), 0) + 1
        if estados and len(estados) > 0:
            d = self._chart_drawing(280, 110)
            clrs = [HexColor('#22c55e'), HexColor('#ef4444'), HexColor('#f59e0b')]
            d = self._add_chart(d, list(estados.values()), list(estados.keys()),
                                'Suscripciones por estado',
                                colors=clrs[:len(estados)])
            elements.append(d)
            elements.append(self._figure_label('Distribución de suscripciones por estado'))
            elements.append(Spacer(1, 6))

        elements.append(self._table_title('Suscripciones registradas'))
        headers = ['#', 'Cliente', 'Tel.', 'Plan', 'Precio', 'Inicio', 'Venc.', 'Días', 'Estado', 'Método de pago']
        rows = []
        for i, s in enumerate(subs, 1):
            for fld in ('fecha_inicio', 'fecha_vencimiento'):
                raw = s.get(fld, '')
                if isinstance(raw, datetime):
                    s[fld] = raw.strftime('%Y-%m-%d')
                else:
                    s[fld] = str(raw)[:10] if raw else ''
            rows.append([
                str(i), s.get('cliente_nombre', ''), s.get('cliente_telefono', ''),
                s.get('plan_nombre', ''),
                f'${float(s.get("plan_precio", 0)):,.2f}',
                s['fecha_inicio'], s['fecha_vencimiento'],
                str(s.get('dias_restantes', 0)),
                s.get('estado', ''),
                s.get('metodo_pago', '')
            ])
        u = self.usable_width
        cw = [u * 0.04, u * 0.14, u * 0.08, u * 0.12,
              u * 0.09, u * 0.09, u * 0.09, u * 0.06, u * 0.14, u * 0.15]
        alignments = {0: 'CENTER', 4: 'RIGHT', 7: 'CENTER'}
        elements.append(self._make_table(headers, rows, col_widths=cw, alignments=alignments))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f'Total suscripciones: {len(subs)}', self._small()))
        return elements

    def build(self):
        self.elements.append(self._make_header())
        self.elements.extend(self._make_title())

        section_order = {'clientes': ('Clientes', self._section_clients),
                         'finanzas': ('Finanzas', self._section_finanzas),
                         'notificaciones': ('Notificaciones', self._section_notificaciones),
                         'suscripciones': ('Suscripciones', self._section_suscripciones)}

        for key in self.sections:
            if key in section_order:
                name, fn = section_order[key]
                self.elements.append(Paragraph(name, self._h2()))
                self.elements.extend(fn())
                if key != self.sections[-1]:
                    c = self.colors
                    self.elements.append(HRFlowable(width='40%', thickness=0.8, color=c['line'],
                                                    spaceAfter=4, spaceBefore=8))

        self.elements.append(Spacer(1, 16))
        c = self.colors
        self.elements.append(HRFlowable(width='100%', thickness=0.5, color=c['line'], spaceAfter=4))
        self.elements.append(Paragraph(
            f'Tiny ERP Manager &mdash; Reporte generado el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}',
            self._footer()))
        return self.elements

    def generate(self):
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=self.page_size,
                                leftMargin=self.margin, rightMargin=self.margin,
                                topMargin=self.margin, bottomMargin=self.margin)
        self.build()
        doc.build(self.elements)
        buf.seek(0)
        return buf


def generate_report_pdf(template_id, sections, data, date_start, date_end, user,
                        margin='normal', font='helvetica', padding='normal',
                        landscape_mode=False, chart_type='bar',
                        chart_ingreso_color='#22c55e', chart_egreso_color='#ef4444'):
    pdf = ReportPDF(template_id, sections, data, date_start, date_end, user,
                    margin=margin, font=font, padding=padding,
                    landscape_mode=landscape_mode, chart_type=chart_type,
                    chart_ingreso_color=chart_ingreso_color, chart_egreso_color=chart_egreso_color)
    return pdf.generate()
