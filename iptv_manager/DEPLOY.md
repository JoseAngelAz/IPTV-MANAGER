# Instrucciones de Despliegue — IPTV Manager

## Requisitos
- Servidor VPS con Docker y Docker Compose (mínimo 1 GB RAM, 10 GB disco)
- Dominio apuntando al VPS (opcional pero recomendado)

## 1. Preparar el servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo apt install -y docker-compose-plugin

# Cerrar sesión y volver a entrar para aplicar grupo docker
exit
```

## 2. Clonar / Subir el proyecto

```bash
# Opción A: subir vía SCP desde tu máquina local
scp -r iptv_manager/ usuario@vps:/home/usuario/

# Opción B: clonar desde Git
git clone https://github.com/tuusuario/iptv_manager.git
cd iptv_manager
```

## 3. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

**Editar los valores:**
```
SECRET_KEY=genera-una-clave-aleatoria-segura
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
DB_NAME=iptv_manager
DB_USER=iptv_user
DB_PASSWORD=genera-una-contraseña-fuerte
DB_HOST=db
DB_PORT=5432
HTTPS=True
```

Generar SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

## 4. Configurar Nginx para HTTPS (con Certbot)

```bash
# Detener temporalmente Nginx del compose
# Editar nginx/default.conf para incluir el server_name real
server_name tudominio.com www.tudominio.com;

# Iniciar servicios sin HTTPS primero
docker compose up -d db web nginx

# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d tudominio.com -d www.tudominio.com

# Los certificados se renuevan automáticamente
```

## 5. Levantar el sistema

```bash
docker compose up -d --build
```

## 6. Crear Superusuario

```bash
docker compose exec web python manage.py createsuperuser
```

## 7. Verificar logs

```bash
docker compose logs -f web
docker compose logs -f nginx
```

## 8. Configurar Cron (recordatorios automáticos)

```bash
# Editar crontab del usuario appuser dentro del contenedor o en el host
# Ejemplo: ejecutar el comando a las 9:00 AM todos los días
0 9 * * * cd /ruta/a/iptv_manager && docker compose exec -T web python manage.py enviar_recordatorios >> /var/log/iptv_recordatorios.log 2>&1
```

## 9. Mantenimiento

```bash
# Ver estado
docker compose ps

# Respaldar base de datos
docker compose exec db pg_dump -U iptv_user iptv_manager > backup_$(date +%Y%m%d).sql

# Restaurar base de datos
cat backup.sql | docker compose exec -T db psql -U iptv_user iptv_manager

# Actualizar
git pull
docker compose up -d --build
```

## Seguridad adicional (recomendado)

1. **Firewall:** `sudo ufw enable && sudo ufw allow 22/tcp && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp`
2. **Fail2ban:** `sudo apt install fail2ban` (protección extra contra fuerza bruta SSH)
3. **Actualizaciones automáticas:** `sudo apt install unattended-upgrades`
4. **Monitoreo:** Revisar logs con `docker compose logs --tail=50 -f`
