# Tiny ERP Manager

Sistema web ERP multipropósito basado en Django 5.1. Originalmente diseñado para gestión IPTV, ahora expandido como ERP genérico adaptable a cualquier vertical de negocio: IPTV, gimnasios, escuelas, talleres, consultorios y más. Centraliza clientes, suscripciones/planes, finanzas, notificaciones y datos personalizados por vertical en un panel de control moderno con integración a WhatsApp.

## ✨ Funcionalidades

### 📊 Dashboard
- Métricas clave: clientes activos, suscripciones vigentes, próximos a vencer, vencidas, saldo del mes
- Gráficos: ingresos vs egresos (6 meses), distribución por plan, neto mensual, suscripciones temporales
- Predicción de ganancias/pérdidas mediante regresión lineal simple
- Métricas de mensajería: total de mensajes enviados, tasa de éxito, desglose WhatsApp/Email

### 👥 Clientes (ERP Multi-vertical)
- CRUD completo con búsqueda por nombre, teléfono, MAC address o documento
- Foto de perfil con compresión automática y galería de fotos
- Historial de cambios por usuario
- Notas internas por cliente
- Desactivación vía modal (con advertencia de suscripciones activas)
- **Datos adicionales** (JSONField) — almacena campos personalizados por vertical de negocio
- **Campos personalizados** (CustomField) — definidos desde el admin de Django, con tipos: texto, número, booleano, fecha, email, selección
- **Plantillas de negocio** (BusinessTemplate) — presets predefinidos para IPTV, Gimnasio, Escuela, Taller, Consultorio y Otro
- **dispositivo_id opcional** — MAC address ya no es obligatoria, permitiendo uso no-IPTV

### 📋 Suscripciones y Planes
- Planes personalizables (nombre, precio, duración en días)
- Suscripciones con descuento (% o monto fijo) y método de pago (efectivo, cheque, débito, cortesía)
- Cálculo automático de fecha de vencimiento
- Creación automática de movimiento financiero al crear/cancelar suscripciones
- Renovación y cancelación con registro en historial

### 💰 Finanzas
- Registro de ingresos y egresos
- Filtrado por tipo
- Dashboard financiero con proyecciones
- Movimientos creados automáticamente desde suscripciones

### 💬 Notificaciones y WhatsApp
- **WhatsApp API** — Microservicio Node.js con `whatsapp-web.js` que se conecta a WhatsApp Web
- Escaneo de QR desde el panel de administración
- **Plantillas de mensaje** con placeholders: `{cliente}`, `{plan}`, `{vencimiento}`, `{precio}`
- Categorías: Vencimiento, Bienvenida, Oferta, Personalizado
- Envío manual desde el panel: selecciona cliente + una o varias plantillas + imagen opcional
- Vista previa en vivo antes de enviar
- Soporte para imágenes adjuntas en mensajes
- Logs de todas las notificaciones enviadas (WhatsApp y Email)
- Recordatorios automáticos vía comando cron

### 🎨 Personalización
- 5 temas predefinidos: Moderno, Corporativo, Minimalista, Vibrante, Dark Neumorphic
- Colores personalizables (primario, secundario, fondo, texto, sidebar, tarjetas)
- Presets guardados por usuario con nombre e icono
- CSS personalizado
- Modo oscuro
- Efectos de texto (negrita, cursiva, subrayado, tachado, borde)
- Fondos pixel art animados

### 📄 Reportes
- Generación de PDF y Excel
- 3 estilos de plantilla: Ejecutivo, Moderno, Clásico
- Secciones: clientes, finanzas, notificaciones, suscripciones
- Filtros por fechas y tipo
- Modo vista previa
- Orientación horizontal, márgenes configurables

### 👮 Roles y Permisos
| Grupo | Permisos |
|---|---|
| **Superadmin** | Acceso completo a todo el sistema |
| **Gerente** | CRUD en clientes, suscripciones, finanzas, notificaciones (sin eliminar clientes) |
| **Soporte** | Vista limitada + crear/editar clientes y suscripciones. Finanzas solo vista |

### 🌐 Traducciones
- Español e Inglés (~300 cadenas por idioma)
- Conmutación desde la barra lateral

### 📝 Otras funcionalidades
- Lista de tareas (To-Do) personal con prioridades, categorías y fecha de vencimiento
- Páginas de error 404/500 personalizables (título, mensaje, color, arte pixelado)
- Formulario de reporte de errores en la página 500
- Galería de fotos
- Configuración de tiempo de sesión
- Logs de actividad con filtros y eliminación masiva
- Protección contra fuerza bruta (django-axes)

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|---|---|
| **Backend** | Python 3.11 + Django 5.1.7 |
| **Frontend** | Tailwind CSS + HTMX + Chart.js + Font Awesome |
| **Base de datos** | PostgreSQL 16 (producción) / SQLite (desarrollo) |
| **Servidor web** | Gunicorn + Nginx |
| **WhatsApp** | Node.js 20 + Express + whatsapp-web.js + Puppeteer |
| **Autenticación** | django-axes (protección anti-fuerza bruta) |
| **Reportes** | ReportLab (PDF) + OpenPyXL (Excel) |
| **Contenedores** | Docker + Docker Compose |

## 🚀 Inicio Rápido

### Requisitos
- Docker y Docker Compose
- Git

### 1. Clonar
```bash
git clone https://github.com/JoseAngelAz/IPTV-MANAGER.git
cd IPTV-MANAGER/iptv_manager
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus valores (SECRET_KEY, DB_PASSWORD, etc.)
```

### 3. Generar certificados SSL (para HTTPS local)
```bash
bash scripts/generate_local_ssl.sh
```

### 4. Iniciar servicios
```bash
docker compose up -d
```

La aplicación estará disponible en `https://localhost`.

### 5. Crear superusuario
```bash
docker compose exec web python manage.py createsuperuser
```

### 6. Sincronizar WhatsApp
1. Ve a `https://localhost/accounts/whatsapp/`
2. Escanea el código QR con tu WhatsApp
3. La sesión se guarda automáticamente para usos futuros

### Desarrollo local (sin Docker)
```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## 🔧 Variables de Entorno

| Variable | Default | Descripción |
|---|---|---|
| `SECRET_KEY` | — | Clave secreta de Django |
| `DEBUG` | `False` | Modo debug |
| `ALLOWED_HOSTS` | — | Hosts permitidos |
| `DB_NAME` | `iptv_manager` | Nombre de la BD |
| `DB_USER` | `iptv_user` | Usuario de la BD |
| `DB_PASSWORD` | — | Contraseña de la BD |
| `DB_HOST` | `db` | Host de la BD (Docker) |
| `DB_PORT` | `5432` | Puerto de la BD |
| `HTTPS` | `True` | Habilitar HTTPS |
| `USE_SQLITE` | `False` | Usar SQLite (dev) |
| `WHATSAPP_API_URL` | `http://whatsapp:3000/api/send` | URL de la API de WhatsApp |

## 🐳 Estructura Docker

```
iptv_manager/
├── docker-compose.yml     # 4 servicios
├── Dockerfile             # Web (Python)
├── whatsapp-api/
│   ├── Dockerfile         # WhatsApp (Node.js)
│   ├── server.js          # Express API
│   └── package.json
├── nginx/
│   ├── default.conf       # Reverse proxy + SSL
│   └── certs/             # Certificados SSL
└── scripts/
    ├── entrypoint.sh      # migrate + grupos + gunicorn
    └── generate_local_ssl.sh
```

## 🧪 Pruebas

```bash
# Todas las pruebas
docker compose exec web python manage.py test

# Pruebas específicas
docker compose exec web python manage.py test apps.accounts.tests.PermissionTest -v 2
```

Actualmente **78 pruebas** (accounts + reports) cubren modelos, vistas, permisos, generación de PDF/Excel y flujos críticos. Los módulos de clients, subscriptions, finance y notifications no tienen tests unitarios dedicados aún.

## 📁 Estructura del Proyecto

```
iptv_manager/
├── apps/
│   ├── accounts/          # Usuarios, autenticación, tema, WhatsApp, plantillas, tareas
│   ├── clients/           # Clientes, historial, notas, campos personalizados, presets
│   ├── subscriptions/     # Planes, suscripciones, descuentos
│   ├── finance/           # Movimientos financieros
│   ├── notifications/     # Logs de notificaciones, recordatorios
│   └── reports/           # Reportes PDF/Excel
├── config/                # settings.py, urls.py, wsgi.py
├── static/                # Archivos estáticos (CSS, JS, img)
├── templates/             # Plantillas HTML (37 archivos)
├── whatsapp-api/          # Microservicio WhatsApp (Node.js)
├── nginx/                 # Configuración de Nginx
└── scripts/               # Scripts de utilería
```

## 📸 Capturas

*Dashboard principal — Próximamente*

## 📄 Licencia

© 2026 José Ángel Azucena Méndez. Todos los derechos reservados.
