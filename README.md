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
- Flask: Framework web
- SQLAlchemy: ORM para base de datos
- Bootstrap: Framework CSS
- Python-dotenv: Gestión de configuración
- Jinja2: Motor de plantillas
- SQLite: Base de datos relacional

## Estado del Proyecto
- [x] Interfaz web responsive
- [x] Sistema de blueprints Flask
- [x] Gestión de tablas dinámicas
- [x] Análisis de directorios
- [x] API REST para escaneo
- [x] Importación de archivos
- [x] Gestión de metadatos de video
- [x] Catálogo de videos
- [ ] Organización automática
- [ ] Sistema de usuarios
- [ ] Procesamiento de imágenes
- [ ] API completa
