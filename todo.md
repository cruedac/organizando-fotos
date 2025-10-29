# TODO - organizando-fotos

## En Progreso

- En `/tables/create`, cuando se crea una nueva tabla al crear los campos se debería poder vincular una tabla anexa a la tabla principal por algún campo (relaciones FK)
- Revisar el mantenimiento de tablas

## Completado ✅

- ✅ **FOTOS: Barra de progreso cuando se analiza el contenido**
  - Implementado progreso en tiempo real con SSE
  - Contador de archivos por tipo (imágenes, videos, audios)
  - Tiempo transcurrido en segundos
  - Spinner y barra de progreso visual
  - Fecha: 29 octubre 2025

- ✅ **Optimizaciones de rendimiento**
  - Sistema de cacheo con Flask-Caching
  - Índices en base de datos para búsquedas
  - Consolidación de código duplicado
  - Fecha: 28-29 octubre 2025

- ✅ **Limpieza de deployment**
  - Eliminadas referencias a Hostinger (incompatible)
  - Documentación actualizada en `deploy/README.md`
  - Opciones viables: Docker, VPS, desarrollo local
  - Fecha: 29 octubre 2025

## Pendiente

### FOTOS:
- Poner una opción que sea "analizar contenido multimedia" y con el archivo seleccionado que vaya a buscar todas las características (metadatos EXIF, dimensiones, etc.)
  * Está a medias

### UTILIDADES:
- Crear una utilidad que obtenga todas las tablas de la base de datos y genere un archivo que pueda ser importado para reiniciar la base de datos
- Sistema de backup automático programado
- Exportación a diferentes formatos (CSV, JSON, SQL)

### FUNCIONALIDADES FUTURAS:
- Sistema de usuarios y autenticación
- Organización automática de archivos
- Procesamiento avanzado de imágenes (thumbnails, resize, watermark)
- API RESTful completa con documentación OpenAPI/Swagger
- Búsqueda full-text con FTS5 de SQLite
- Integración con servicios en la nube (Google Drive, Dropbox)
- Dashboard con gráficos y estadísticas avanzadas

