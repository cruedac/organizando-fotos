# Database Schema Definitions

Esta carpeta contiene las definiciones SQL puras de todas las tablas de la base de datos.

## Propósito

Consolidar todas las definiciones de tablas en un solo lugar para:
- Facilitar la recreación completa de la base de datos desde cero
- Documentar la estructura completa del esquema
- Permitir migraciones y respaldos consistentes
- Habilitar la funcionalidad de "reset database" en el menú de mantenimiento

## Estructura de Archivos

Los archivos contienen las definiciones SQL puras de cada tabla:

- `file_types.py` - Catálogo de tipos de archivo (extensiones permitidas)
- `movies.py` - Catálogo de videos/películas con todos sus metadatos
- `support_types.py` - Catálogo de tipos de soporte físico/digital
- `photo_scans.py` - Tablas de escaneo de fotos (photos_scan y photos_scan_summary)
- `dynamic_tables.py` - Sistema de tablas dinámicas creadas por el usuario

**Orden de creación**: El script `database/init_database.py` las ejecuta en el orden correcto
considerando las dependencias de claves foráneas.

## Uso

Cada archivo exporta dos funciones:

- `create_table(connection)` - Crea la tabla con todos sus campos, índices y constraints
- `seed_data(connection)` - Opcionalmente pobla datos iniciales (ej: FileType.init_db())

El script `database/init_database.py` ejecuta todos estos esquemas en orden.

## Notas Importantes

1. **SQLite**: Los esquemas están optimizados para SQLite (tipos de datos, sintaxis de índices)
2. **Datos de referencia**: Algunas tablas (file_types, tipo_soporte) deben poblarse con datos iniciales
3. **Tablas dinámicas**: Las tablas creadas por usuarios desde la UI no están aquí, se descubren automáticamente
4. **Legacy**: La tabla `movies` mantiene nombres de columna en MAYÚSCULAS por compatibilidad con SQL legacy

## Sincronización con Modelos ORM

Los modelos SQLAlchemy en `app/models/` deben mantenerse sincronizados con estos esquemas SQL.

**Cuando cambies un esquema aquí, actualiza también el modelo ORM correspondiente.**
