# Deployment - organizando-fotos

Archivos de configuración para despliegue de la aplicación en producción.

## ⚠️ Importante

**Esta aplicación requiere un servidor con control completo** (VPS, servidor dedicado, o Docker).  
**NO es compatible con hosting compartido tradicional** como:
- Hostinger shared hosting
- GoDaddy shared hosting
- Bluehost shared hosting

Esto se debe a que requiere:
- Acceso SSH con permisos para instalar paquetes
- Proceso Python persistente en ejecución
- Control sobre el servidor web y proxy inverso
- Capacidad de instalar dependencias del sistema

## 📋 Opciones de Deployment Viables

### 1. Docker (Recomendado)
Usa los archivos:
- `Dockerfile` - Imagen de la aplicación
- `docker-compose.yml` - Orquestación de servicios
- `nginx.conf` - Configuración de proxy inverso

**Ventajas:**
- Aislamiento completo del entorno
- Fácil escalabilidad
- Reproducible en cualquier sistema con Docker
- Rollbacks sencillos

**Comando rápido:**
```bash
docker-compose up -d
```

### 2. VPS con Linux
Usa los archivos:
- `supervisor.conf` - Gestión del proceso Python
- `nginx.conf` - Proxy inverso y SSL
- `install.sh` - Script de instalación automática
- `backup.sh` - Script de backups automáticos
- `requirements.txt` - Dependencias Python específicas

**Proveedores recomendados:**
- DigitalOcean (Droplets desde $6/mes)
- Linode
- AWS EC2 (t2.micro en free tier)
- Google Cloud Compute Engine
- Azure Virtual Machines

### 3. Desarrollo Local
Perfecto para testing y desarrollo:
```bash
# Clonar repo
git clone https://github.com/tu-usuario/organizando-fotos.git

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\Activate.ps1  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python run.py
```

## 📁 Archivos Incluidos

### Configuración de Servidor
- **nginx.conf** - Configuración de Nginx como proxy inverso
- **supervisor.conf** - Gestión de procesos con Supervisor (mantiene la app corriendo)
- **production_config.py** - Configuración específica de producción

### Docker
- **Dockerfile** - Imagen Docker de la aplicación
- **docker-compose.yml** - Orquestación multi-contenedor
- **.dockerignore** (raíz del proyecto) - Excluye archivos innecesarios

### Scripts de Utilidad
- **install.sh** - Instalación automatizada en VPS Linux
- **backup.sh** - Script de backup automático de base de datos
- **compile_cython.sh** - Compilación opcional de módulos Cython para rendimiento

### Construcción de Binarios
- **organizando_fotos.spec** - Especificación para PyInstaller (legacy, no recomendado)
- **setup.py** - Configuración para empaquetado Python

### Dependencias
- **requirements.txt** - Dependencias Python para producción (similar al de raíz pero sin paquetes de desarrollo)

## 🚀 Guía Rápida de Deployment

### Con Docker

1. Asegúrate de tener Docker y Docker Compose instalados
2. Clona el repositorio en tu servidor
3. Configura variables de entorno (copia `.env.example` a `.env`)
4. Ejecuta:
   ```bash
   docker-compose up -d
   ```
5. Accede a http://IP_SERVIDOR:5000

### En VPS Linux

1. Conecta por SSH a tu VPS
2. Ejecuta el script de instalación:
   ```bash
   wget https://raw.githubusercontent.com/tu-usuario/organizando-fotos/main/deploy/install.sh
   chmod +x install.sh
   sudo ./install.sh
   ```
3. Edita `/opt/organizando-fotos/.env` con tu configuración
4. La aplicación estará corriendo en el puerto 5000, accesible vía Nginx en puertos 80/443

## 🔒 Seguridad

### Antes de ir a producción:

1. **Genera una SECRET_KEY aleatoria:**
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```
   Copia el resultado a tu `.env`:
   ```
   SECRET_KEY=tu_clave_generada_aqui
   ```

2. **Configura FLASK_ENV en producción:**
   ```
   FLASK_ENV=production
   DEBUG=False
   ```

3. **Configura SSL con Let's Encrypt:**
   ```bash
   sudo certbot --nginx -d tu-dominio.com
   ```

4. **Establece permisos correctos:**
   ```bash
   chmod 600 .env
   chmod 666 data/multimedia.db
   chmod 777 data/
   ```

5. **Configura backups automáticos:**
   ```bash
   # Añade a crontab (backup diario a las 3 AM)
   0 3 * * * /opt/organizando-fotos/deploy/backup.sh
   ```

## 📊 Monitoreo

### Ver logs en vivo

**Docker:**
```bash
docker-compose logs -f app
```

**VPS con Supervisor:**
```bash
sudo tail -f /var/log/supervisor/organizando-fotos.log
tail -f /opt/organizando-fotos/logs/app.log
```

### Verificar estado del servicio

**Docker:**
```bash
docker-compose ps
```

**VPS con Supervisor:**
```bash
sudo supervisorctl status organizando-fotos
```

## 🆘 Troubleshooting

### Puerto 5000 ya en uso
Cambia el puerto en `docker-compose.yml` o en `run.py`:
```yaml
ports:
  - "8080:5000"  # Usa puerto 8080 en host
```

### Permisos de SQLite
```bash
chmod 666 data/multimedia.db
chmod 777 data/
```

### Aplicación no inicia
Verifica logs:
```bash
# Docker
docker-compose logs app

# VPS
sudo supervisorctl tail organizando-fotos stderr
```

### SSL no funciona
Verifica que Nginx esté corriendo y que el certificado esté instalado:
```bash
sudo systemctl status nginx
sudo certbot certificates
```

## 📚 Recursos

- [Documentación oficial de Flask Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Docker Documentation](https://docs.docker.com/)
- [Supervisor Documentation](http://supervisord.org/)
- [Let's Encrypt](https://letsencrypt.org/)

---

**Última actualización:** Enero 2025  
**Versión:** 2.0 - Docker-first, sin opciones de hosting compartido
