#!/bin/bash

# Script de backup para la aplicación
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups"
APP_DIR="/var/www"

# Crear directorio de backup si no existe
mkdir -p $BACKUP_DIR

# Backup de datos y logs
echo "Creando backup de datos..."
tar -czf $BACKUP_DIR/organizando_fotos_data_$DATE.tar.gz $APP_DIR/data/ $APP_DIR/logs/

# Backup de configuración
echo "Creando backup de configuración..."
tar -czf $BACKUP_DIR/organizando_fotos_config_$DATE.tar.gz $APP_DIR/.env $APP_DIR/deploy/

# Limpiar backups antiguos (más de 7 días)
echo "Limpiando backups antiguos..."
find $BACKUP_DIR/ -name "organizando_fotos_*.tar.gz" -mtime +7 -delete

echo "Backup completado: $BACKUP_DIR/organizando_fotos_*_$DATE.tar.gz"