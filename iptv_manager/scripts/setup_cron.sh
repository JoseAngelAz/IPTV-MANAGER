#!/bin/bash
# Instalar cron job para enviar_recordatorios
# Ejecutar: sudo ./scripts/setup_cron.sh

CRON_SCHEDULE="0 9 * * *"
COMMAND="cd /app && python manage.py enviar_recordatorios >> /var/log/cron_recordatorios.log 2>&1"

(crontab -l 2>/dev/null | grep -v "enviar_recordatorios"; echo "$CRON_SCHEDULE $COMMAND") | crontab -

echo "Cron instalado: $CRON_SCHEDULE python manage.py enviar_recordatorios"
