# organizando-fotos

Aplicación web en Flask para organizar archivos multimedia. Proporciona una interfaz moderna y responsive para gestionar archivos multimedia con una base de datos SQLite a través de SQLAlchemy.

## Características

### Gestión de Archivos
- Escaneo recursivo de directorios
- Detección automática de tipos de archivo
- Análisis estadístico de contenido multimedia
- Interfaz web moderna y responsive

### Sistema de Tablas Dinámicas
- Creación y gestión de tablas personalizadas
- Definición flexible de campos:
  - Múltiples tipos de datos (TEXT, INTEGER, REAL, DATE, DATETIME, BOOLEAN)
  - Configuración avanzada por campo:
    - Clave primaria
    - Auto incremento
    - Valores por defecto
    - Restricciones de obligatoriedad

### Gestión de Tipos de Archivo
- Interfaz de administración de tipos de archivo
- Configuración flexible de extensiones soportadas
- Categorización automática por tipo:
  - Imágenes
  - Videos
  - Audio

### Gestión de Videos
- Catálogo completo de videos con metadatos:
  - Información básica (título, año, duración)
  - Detalles técnicos (formato, resolución)
  - Organización (categorías, etiquetas)
- Importación de datos desde sistemas legacy
- Búsqueda y filtrado avanzado:
  - Por título y descripción
  - Por categoría y tipo de medio
  - Por año
- Soporte para múltiples formatos:
  - Digital: mp4, avi, mov, etc.
  - Análogo: 8mm, Hi-8, Digital-8
- Validación del tipo de soporte frente a un catálogo editable
- Almacenamiento y copia directa de la ruta de archivo

### Mantenimiento del Sistema
- Panel con estadísticas en vivo de la base de datos
- Copias de seguridad bajo demanda del fichero SQLite
- Diferenciación entre tablas operativas y de sistema
- Gestión de tablas dinámicas con salvaguardas al eliminar

### Análisis de Archivos
- Escaneo configurable de directorios (con/sin subdirectorios)
- **Progreso en tiempo real durante el escaneo:**
  - Contador de archivos encontrados por tipo (imágenes, videos, audios)
  - Tiempo transcurrido actualizado cada segundo
  - Actualizaciones vía Server-Sent Events (SSE)
  - Indicadores visuales de progreso (spinner, barra de progreso)
- Estadísticas detalladas:
  - Conteo por tipo de archivo
  - Distribución por extensión
  - Detección de archivos sin extensión
- Interfaz visual para resultados
- API REST para integración

### Tipos de Archivos Soportados
- Imágenes: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.heic`, `.svg`, `.raw`, `.CR2`, `.CR3`
- Videos: `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.mkv`, `8mm`, `hi-8`, `digital-8`
- Audio: `.mp3`, `.wav`, `.ogg`, `.aac`, `.flac`

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/cruedac/organizando-fotos.git
cd organizando-fotos
```

2. Crear y activar entorno virtual:
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar el entorno:
```bash
# Copiar el archivo de ejemplo
cp .env.example .env
# Editar .env con tus configuraciones
```

## Uso

1. Iniciar la aplicación:
```bash
python run.py
```

2. Acceder a través del navegador:
```
http://localhost:5000
```

### Funcionalidades Principales:

#### Análisis de Directorios
1. Acceder a la página principal
2. Seleccionar una carpeta para analizar
3. Configurar opciones de escaneo (incluir/excluir subdirectorios)
4. Ver resultados detallados:
   - Resumen por tipo de archivo
   - Estadísticas por extensión
   - Visualización gráfica

#### Gestión de Tipos de Archivo
1. Ir a "Mantenimiento" -> "Tipos de Archivo"
2. Gestionar extensiones soportadas:
   - Añadir nuevas extensiones
   - Modificar tipos existentes
   - Eliminar extensiones no deseadas

#### Tablas Dinámicas
1. Ir a "Mantenimiento" -> "Tablas"
2. Operaciones disponibles:
   - Crear nuevas tablas
   - Añadir y configurar campos
   - Gestionar estructura existente
   - Eliminar tablas y campos

#### Gestión de Videos
1. Ir a "Videos"
2. Operaciones disponibles:
   - Importar datos desde archivos SQL
   - Buscar videos por título, descripción y metadatos
   - Filtrar por categoría, año y tipo de medio
   - Ver detalles técnicos y contenido adicional
   - Gestionar información de videos analógicos y digitales

## Tecnologías Utilizadas
- **Flask 2.0.3**: Framework web
- **SQLAlchemy 1.4**: ORM para base de datos
- **Flask-Caching**: Sistema de cacheo en memoria para optimización
- **Bootstrap 5**: Framework CSS para interfaz responsive
- **Python-dotenv**: Gestión de configuración
- **Jinja2**: Motor de plantillas
- **SQLite**: Base de datos relacional
- **Pillow**: Procesamiento de imágenes
- **Threading & Queue**: Procesamiento asíncrono para progreso en tiempo real
- **Server-Sent Events (SSE)**: Actualizaciones en tiempo real al cliente

## Optimizaciones Implementadas
- ✅ **Sistema de cacheo** con Flask-Caching (timeout 5 minutos)
- ✅ **Índices en base de datos** para búsquedas rápidas (año, categoría, tipo de medio)
- ✅ **Paginación** en listados de videos (25 registros por página)
- ✅ **Consolidación de código** con utilidades compartidas (date_utils.py)
- ✅ **Progreso en tiempo real** mediante SSE con threading
- ✅ **Logs rotativos** para monitoreo (UTF-8, tamaño máximo 10MB)

## Deployment
Esta aplicación requiere **servidor con control completo** (VPS, servidor dedicado, o Docker).

**NO es compatible con hosting compartido** (Hostinger, GoDaddy, Bluehost shared hosting) porque requiere:
- Acceso SSH y permisos para instalar paquetes
- Proceso Python persistente en ejecución
- Control sobre servidor web y proxy inverso

**Opciones de deployment viables:**
1. **Docker** (recomendado) - Ver `deploy/README.md`
2. **VPS Linux** (DigitalOcean, Linode, AWS EC2)
3. **Desarrollo local** (Windows, Linux, macOS)

Consulta la documentación completa en `deploy/README.md`.

## Estado del Proyecto
- [x] Interfaz web responsive
- [x] Sistema de blueprints Flask
- [x] Gestión de tablas dinámicas
- [x] Análisis de directorios con progreso en tiempo real
- [x] API REST para escaneo
- [x] Importación de archivos
- [x] Gestión de metadatos de video
- [x] Catálogo de videos
- [x] Sistema de cacheo y optimización
- [ ] Organización automática
- [ ] Sistema de usuarios y autenticación
- [ ] Procesamiento avanzado de imágenes
- [ ] API completa RESTful
