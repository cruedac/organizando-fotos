# organizando-fotos

Aplicación de escritorio en Python para organizar archivos multimedia. Permite gestionar una base de datos SQLite con interfaz gráfica para el manejo de archivos multimedia.

## Características

### Gestión de Base de Datos
- Abrir y conectar con bases de datos SQLite existentes
- Visualización de datos en formato tabla
- Operaciones CRUD completas:
  - Crear nuevos registros
  - Ver registros existentes
  - Modificar registros
  - Eliminar registros

### Mantenimiento de Tablas
- Visualización de tablas existentes
- Ver estructura detallada de cada tabla
- Creación de nuevas tablas con:
  - Definición de campos personalizados
  - Múltiples tipos de datos (TEXT, INTEGER, REAL, BLOB, DATE, DATETIME)
  - Opciones por campo:
    - Clave primaria
    - Auto incremento
    - Restricción NOT NULL

### Tipos de Archivos Soportados
- Imágenes: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.heic`, `.svg`, `.raw`, `.CR2`, `.CR3`
- Videos: `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.mkv`
- Audio: `.mp3`, `.wav`, `.ogg`, `.aac`, `.flac`

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/cruedac/organizando-fotos.git
cd organizando-fotos
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Inicializar la base de datos:
```bash
python database/create_db.py
```

## Uso

Para iniciar la aplicación:
```bash
python main_app.py
```

### Flujo básico de uso:
1. Ir a "Archivo" -> "Abrir Base de Datos" para conectar con una base de datos
2. Usar el menú "Tablas" para seleccionar la tabla a visualizar
3. Utilizar los botones CRUD para gestionar los registros:
   - "Insertar" para añadir nuevos registros
   - "Modificar" para editar registros existentes
   - "Borrar" para eliminar registros
   - "Actualizar" para refrescar la vista

### Mantenimiento de Tablas:
1. Ir a "Herramientas" -> "Mantenimiento de Tablas"
2. Para ver la estructura de una tabla existente:
   - Seleccionar la tabla del desplegable
   - Hacer clic en "Ver Estructura"
3. Para crear una nueva tabla:
   - Introducir el nombre de la tabla
   - Añadir campos usando "Añadir Campo"
   - Configurar las propiedades de cada campo
   - Hacer clic en "Crear Tabla"

## Dependencias Principales
- PySide6: Interfaz gráfica (Qt para Python)
- Pillow: Procesamiento de imágenes
- Mutagen: Metadata de archivos multimedia

## Estado del Proyecto
- [x] Interfaz gráfica básica
- [x] Operaciones CRUD
- [x] Gestión de tablas
- [ ] Importación de archivos
- [ ] Gestión de metadatos
- [ ] Organización automática
