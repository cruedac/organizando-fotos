#!/bin/bash

# Script de instalación para servidor Ubuntu/Debian

# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python y dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv nginx supervisor

# 3. Crear usuario para la aplicación
sudo useradd -m -s /bin/bash organizador
sudo usermod -aG www-data organizador

# 4. Crear directorio de la aplicación
sudo mkdir -p /var/www/organizando-fotos
sudo chown organizador:www-data /var/www/organizando-fotos

# 5. Subir código de la aplicación
# (usar scp, rsync o git clone)

# 6. Crear entorno virtual
cd /var/www/organizando-fotos
sudo -u organizador python3 -m venv venv
sudo -u organizador ./venv/bin/pip install -r requirements.txt

# 7. Configurar permisos
sudo chown -R organizador:www-data /var/www/organizando-fotos
sudo chmod -R 755 /var/www/organizando-fotos

# 8. Crear directorio para datos
sudo mkdir -p /var/www/organizando-fotos/data
sudo mkdir -p /var/www/organizando-fotos/logs
sudo chown -R organizador:www-data /var/www/organizando-fotos/data
sudo chown -R organizador:www-data /var/www/organizando-fotos/logs

echo "Instalación base completada. Configurar Nginx y Supervisor manualmente."