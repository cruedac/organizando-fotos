# Guía de Usuario - organizando-fotos

Guía completa de todas las funcionalidades de la aplicación web para organizar archivos multimedia.

---

## 📑 Tabla de Contenidos

1. [Inicio Rápido](#inicio-rápido)
2. [Página Principal](#página-principal)
3. [Análisis de Fotos](#análisis-de-fotos)
4. [Gestión de Videos](#gestión-de-videos)
5. [Tablas Dinámicas](#tablas-dinámicas)
6. [Mantenimiento del Sistema](#mantenimiento-del-sistema)
7. [Utilidades](#utilidades)
8. [Preguntas Frecuentes](#preguntas-frecuentes)

---

## 🚀 Inicio Rápido

### Primera vez usando la aplicación

1. **Arrancar la aplicación:**
   ```bash
   # Activar entorno virtual
   .\.venv\Scripts\Activate.ps1  # Windows
   source .venv/bin/activate      # Linux/Mac
   
   # Iniciar servidor
   python run.py
   ```

2. **Acceder desde el navegador:**
   ```
   http://localhost:5000
   ```

3. **Navegación:** Usa el menú superior para acceder a las diferentes secciones:
   - **Inicio**: Página principal con bienvenida
   - **Fotos**: Análisis de contenido multimedia
   - **Videos**: Catálogo de películas y videos
   - **Mantenimiento**: Administración de la base de datos
   - **Utilidades**: Herramientas adicionales

---

## 🏠 Página Principal

La página de inicio muestra:
- Título y descripción de la aplicación
- Accesos rápidos a las funcionalidades principales
- Estadísticas generales (si están disponibles)

**Funciones disponibles:**
- Navegar a cualquier sección desde el menú superior
- Ver información sobre el proyecto

---

## 📸 Análisis de Fotos

### ¿Qué hace?
Escanea carpetas en tu sistema para encontrar y catalogar archivos multimedia (imágenes, videos, audio).

### Cómo usar:

#### 1. Seleccionar Carpeta

**Opción A: Selector de carpetas visual**
1. Click en **"Seleccionar Carpeta"**
2. Se abre un explorador de archivos integrado
3. Navegación:
   - Click en una **unidad** (C:\, D:\, etc.) para explorarla
   - Click en una **carpeta** para ver su contenido
   - Usa el **breadcrumb** (ruta superior) para volver atrás
4. Click en **"Seleccionar esta carpeta"** cuando encuentres la que deseas

**Opción B: Ruta manual**
1. Escribe o pega la ruta directamente en el campo de texto
   - Ejemplo Windows: `C:\Users\TuUsuario\Pictures`
   - Ejemplo Linux: `/home/usuario/fotos`

#### 2. Configurar Opciones de Escaneo

**Incluir subdirectorios:**
- ✅ **Marcado**: Escanea la carpeta y todas sus subcarpetas (búsqueda recursiva)
- ⬜ **Desmarcado**: Solo escanea la carpeta seleccionada (sin entrar en subcarpetas)

#### 3. Analizar Contenido

1. Click en **"Analizar Contenido"**
2. **Progreso en tiempo real:**
   - El botón muestra un **spinner animado**
   - Aparece una **barra de progreso azul** con:
     - Contador de archivos encontrados: "Encontrados: 150 imágenes, 20 videos, 5 audios"
     - Tiempo transcurrido: "45s transcurridos"
   - Se actualiza cada vez que se procesan 5 archivos

3. **Resultados:**
   Al finalizar el escaneo, verás dos tarjetas:

   **A. Resumen por Tipo:**
   - 📷 **IMAGE**: Cantidad de archivos de imagen
   - 🎬 **VIDEO**: Cantidad de archivos de video
   - 🎵 **AUDIO**: Cantidad de archivos de audio
   - 📄 **OTHER**: Archivos con extensiones no reconocidas

   **B. Desglose por Extensión:**
   - Lista detallada mostrando cada extensión encontrada
   - Cantidad de archivos por extensión
   - Ejemplo: `.jpg: 120`, `.png: 30`, `.mp4: 15`

#### 4. Guardar Resumen (Opcional)

Después de un escaneo exitoso, aparece una tarjeta adicional:
- **"Guardar resumen en la tabla photos_scan"**
- Muestra un resumen de lo encontrado
- Click en **"Guardar"** para almacenar el resultado en la base de datos
- Click en **"Descartar"** si no deseas guardarlo

**Ventajas de guardar:**
- Mantener historial de escaneos
- Comparar resultados entre diferentes fechas
- Analizar evolución de tu biblioteca multimedia

### Tipos de Archivo Soportados

**Imágenes:**
- Formatos comunes: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`
- Formatos profesionales: `.tiff`, `.raw`, `.CR2`, `.CR3`
- Otros: `.svg`, `.heic`

**Videos:**
- Digitales: `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.mkv`
- Analógicos: `8mm`, `hi-8`, `digital-8`

**Audio:**
- `.mp3`, `.wav`, `.ogg`, `.aac`, `.flac`

### Consejos y Trucos

💡 **Para carpetas grandes:**
- Marca "Incluir subdirectorios" para un análisis completo
- El progreso en tiempo real te permite saber que está trabajando
- Escanear 10,000+ archivos puede tomar varios minutos

💡 **Para búsquedas rápidas:**
- Desmarca "Incluir subdirectorios" si solo necesitas ver una carpeta específica
- Útil para verificar el contenido de una carpeta de descarga

💡 **Si no aparecen archivos:**
- Verifica que la ruta sea correcta
- Asegúrate de tener permisos de lectura en la carpeta
- Revisa que las extensiones estén registradas en "Mantenimiento > Tipos de Archivo"

---

## 🎬 Gestión de Videos

### ¿Qué hace?
Catálogo completo de películas y videos con metadatos detallados (título, año, duración, formato, categoría, etc.).

### Funcionalidades Principales:

#### 1. Ver Catálogo de Videos

**Acceso:** Click en "Videos" en el menú principal

**Vista de lista:**
- Muestra 25 videos por página (paginación automática)
- Columnas visibles:
  - **Título**: Nombre de la película/video
  - **Año**: Año de lanzamiento
  - **Categoría**: Género o clasificación
  - **Tipo de Medio**: Formato (Digital, VHS, DVD, etc.)
  - **Acciones**: Botones para Ver/Editar/Eliminar

**Controles de navegación:**
- Botones de paginación en la parte inferior
- Números de página clickeables
- Botones "Anterior" y "Siguiente"

#### 2. Buscar Videos

**Panel de búsqueda avanzada:**

1. **Búsqueda por texto:**
   - Campo: "Buscar por título o descripción"
   - Busca en: Título, descripción, contenido, observaciones
   - No distingue mayúsculas/minúsculas

2. **Filtros:**
   - **Categoría**: Dropdown con todas las categorías existentes
   - **Tipo de Medio**: Dropdown con formatos disponibles
   - **Año**: Dropdown con años encontrados en el catálogo

3. Click en **"Buscar"** para aplicar filtros
4. Click en **"Limpiar"** para resetear todos los filtros

**Ejemplo de búsqueda:**
```
Texto: "acción"
Categoría: "Películas"
Año: "2020"
→ Muestra todas las películas de acción del 2020
```

#### 3. Ver Detalles de un Video

Click en el **icono de ojo** 👁️ en cualquier video:

**Información mostrada:**
- **Básica:**
  - Título completo
  - Año de lanzamiento
  - Categoría/Género
  - Duración (en minutos)

- **Técnica:**
  - Formato de video (MP4, AVI, MKV, etc.)
  - Resolución (1080p, 720p, 4K, etc.)
  - Tipo de medio (Digital, DVD, Blu-ray, VHS, etc.)
  - Tipo de soporte (Disco duro, USB, NAS, etc.)

- **Ubicación:**
  - Ruta del archivo en el sistema
  - Nombre del archivo

- **Contenido:**
  - Descripción detallada
  - Observaciones adicionales
  - Fecha de agregado al catálogo

#### 4. Agregar Nuevo Video

1. Click en **"Añadir Video"** (botón verde superior derecho)
2. Rellenar el formulario:

**Campos obligatorios:**
- **Título**: Nombre de la película/video

**Campos opcionales:**
- **Año**: Año de lanzamiento (4 dígitos)
- **Duración**: En minutos (ejemplo: 120)
- **Categoría**: Tipo/Género (Acción, Drama, Documental, etc.)
- **Descripción**: Sinopsis o descripción breve
- **Formato**: Formato del archivo (mp4, avi, mkv, etc.)
- **Resolución**: Calidad del video (1080p, 720p, 4K, etc.)
- **Tipo de Medio**: Digital, DVD, Blu-ray, VHS, 8mm, etc.
- **Tipo de Soporte**: Dónde está almacenado (HDD, SSD, USB, NAS, etc.)
- **Ruta del Archivo**: Ubicación completa del archivo
- **Nombre del Archivo**: Nombre del archivo con extensión
- **Contenido**: Descripción extendida o notas
- **Observaciones**: Comentarios adicionales

3. Click en **"Guardar"** para agregar el video al catálogo

#### 5. Editar Video Existente

1. Click en el **icono de lápiz** ✏️ junto al video
2. Modificar los campos deseados
3. Click en **"Guardar Cambios"**

**Nota:** Todos los campos son editables excepto el ID interno

#### 6. Eliminar Video

1. Click en el **icono de papelera** 🗑️ junto al video
2. Confirmar la eliminación en el diálogo que aparece
3. El video se elimina permanentemente del catálogo

⚠️ **Advertencia:** Esta acción no se puede deshacer. No elimina el archivo físico, solo el registro en la base de datos.

#### 7. Importar Videos desde SQL

**¿Cuándo usar esto?**
- Migrar datos desde otro sistema
- Restaurar un backup antiguo
- Importar catálogo de películas de terceros

**Pasos:**
1. Preparar archivo SQL con formato:
   ```sql
   INSERT INTO movies (TITLE, YEAR, CATEGORY, ...) VALUES ('Película 1', 2020, 'Acción', ...);
   ```
2. Activar variable de entorno: `IMPORT_LEGACY_SQL=1`
3. Reiniciar la aplicación
4. Acceder a `/videos/import-legacy`
5. Seguir instrucciones en pantalla

**Resultado:**
- Se genera un reporte JSON en `data/import_reports/`
- Registros duplicados se ignoran automáticamente (INSERT OR IGNORE)
- Validación de datos antes de insertar

### Gestión de Tipos de Soporte

**Acceso:** Mantenimiento > Tipos de Soporte

Los tipos de soporte se almacenan en una tabla separada para:
- Evitar errores tipográficos
- Mantener consistencia en el catálogo
- Facilitar búsquedas y filtros

**Operaciones:**
- **Añadir**: Agregar nuevo tipo de soporte
- **Editar**: Modificar nombre existente
- **Eliminar**: Quitar tipo (solo si no está en uso)

---

## 📊 Tablas Dinámicas

### ¿Qué son?
Sistema para crear y gestionar tablas personalizadas en la base de datos sin escribir SQL.

### ¿Para qué sirven?
- Almacenar datos específicos de tu proyecto
- Crear catálogos personalizados
- Extender la funcionalidad de la aplicación

### Funcionalidades:

#### 1. Ver Tablas Existentes

**Acceso:** Mantenimiento > Tablas

**Vista de lista:**
- Nombre de la tabla
- Número de campos
- Número de registros
- Acciones disponibles

**Tipos de tablas mostradas:**
- ✅ **Operativas**: Tablas creadas por el usuario
- ⚠️ **Sistema**: Tablas internas (movies, file_type, etc.)

#### 2. Crear Nueva Tabla

1. Click en **"Crear Nueva Tabla"**
2. Ingresar **nombre de la tabla**:
   - Solo letras, números y guiones bajos
   - No espacios
   - Ejemplo: `mi_catalogo`, `inventario_2025`
3. Click en **"Crear Tabla"**

**Resultado:**
- Se crea la tabla vacía en la base de datos
- Automáticamente se añade un campo `id` como clave primaria
- Redirige a la vista de campos para comenzar a añadir columnas

#### 3. Gestionar Campos de una Tabla

Click en **"Ver Campos"** en cualquier tabla:

**Vista de campos:**
- Lista de todos los campos existentes
- Tipo de dato de cada campo
- Opciones configuradas (PK, NOT NULL, DEFAULT, etc.)

**Añadir nuevo campo:**

1. Click en **"Añadir Campo"**
2. Completar formulario:

   **Nombre del Campo:**
   - Sin espacios (ejemplo: `nombre_producto`, `precio`, `fecha_compra`)

   **Tipo de Dato:**
   - `TEXT`: Texto de cualquier longitud (nombres, descripciones)
   - `INTEGER`: Números enteros (cantidades, años)
   - `REAL`: Números decimales (precios, promedios)
   - `DATE`: Fechas (formato: YYYY-MM-DD)
   - `DATETIME`: Fecha y hora (formato: YYYY-MM-DD HH:MM:SS)
   - `BOOLEAN`: Verdadero/Falso (0/1)

   **Opciones:**
   - ☑️ **Clave Primaria**: Identificador único (solo un campo por tabla)
   - ☑️ **Auto Incremento**: Se incrementa automáticamente (solo con INTEGER)
   - ☑️ **NOT NULL**: Campo obligatorio (no puede estar vacío)
   - **Valor por Defecto**: Valor inicial cuando se crea un registro

3. Click en **"Guardar Campo"**

**Ejemplos de configuración:**

```
Campo: id
Tipo: INTEGER
✓ Clave Primaria
✓ Auto Incremento
→ Identificador único que se genera automáticamente

Campo: nombre
Tipo: TEXT
✓ NOT NULL
→ Nombre obligatorio, no puede estar vacío

Campo: precio
Tipo: REAL
Valor por defecto: 0.00
→ Precio decimal, por defecto es 0.00

Campo: activo
Tipo: BOOLEAN
Valor por defecto: 1
→ Campo true/false, por defecto true (1)

Campo: fecha_registro
Tipo: DATETIME
→ Fecha y hora de registro
```

#### 4. Eliminar Campo

⚠️ **Advertencia:** Esta operación es irreversible y elimina todos los datos de ese campo.

1. Click en el **icono de papelera** junto al campo
2. Confirmar eliminación
3. El campo y sus datos se eliminan permanentemente

**Restricciones:**
- No se puede eliminar la clave primaria de una tabla
- No se puede eliminar un campo si tiene referencias de clave foránea (FK)

#### 5. Gestionar Registros de una Tabla

Click en **"Ver Registros"** en cualquier tabla:

**Vista de registros:**
- Tabla con todas las columnas y filas
- Botones de acción por registro (Ver, Editar, Eliminar)

**Añadir nuevo registro:**

1. Click en **"Añadir Registro"**
2. Completar formulario con valores para cada campo
3. Click en **"Guardar"**

**Editar registro:**

1. Click en el **icono de lápiz** ✏️
2. Modificar valores deseados
3. Click en **"Guardar Cambios"**

**Eliminar registro:**

1. Click en el **icono de papelera** 🗑️
2. Confirmar eliminación
3. El registro se elimina permanentemente

#### 6. Eliminar Tabla Completa

⚠️ **Advertencia Crítica:** Esta operación elimina la tabla y todos sus datos permanentemente.

**Restricciones de seguridad:**
- ❌ No se puede eliminar si tiene registros (debes vaciarla primero)
- ❌ No se puede eliminar si otras tablas la referencian (FK)
- ❌ No se puede eliminar tablas del sistema (protección interna)

**Pasos:**

1. Asegurarse de que la tabla esté vacía
2. Click en **"Eliminar Tabla"**
3. Confirmar eliminación escribiendo el nombre de la tabla
4. La tabla se elimina de la base de datos

---

## 🔧 Mantenimiento del Sistema

### ¿Qué hace?
Panel de administración para gestionar la base de datos, configuraciones y tipos de archivo.

### Funcionalidades:

#### 1. Dashboard de Estadísticas

**Acceso:** Mantenimiento > Inicio

**Información mostrada:**
- **Estadísticas de la Base de Datos:**
  - Ruta del archivo de base de datos
  - Tamaño en disco (MB)
  - Número total de tablas

- **Tablas Operativas:**
  - Lista de tablas creadas por el usuario
  - Nombre, número de columnas y registros

- **Tablas del Sistema:**
  - Lista de tablas internas de la aplicación
  - Información similar a las operativas

**Actualización:**
- Los datos se cargan dinámicamente al acceder a la página
- Puedes recargar la página para ver cambios recientes

#### 2. Gestión de Tipos de Archivo

**Acceso:** Mantenimiento > Tipos de Archivo

**¿Para qué sirve?**
Define qué extensiones de archivo reconoce la aplicación durante el escaneo.

**Vista de lista:**
- **Extensión**: `.jpg`, `.mp4`, `.mp3`, etc.
- **Tipo**: image, video, audio
- **Acciones**: Editar, Eliminar

**Añadir nueva extensión:**

1. Click en **"Añadir Tipo de Archivo"**
2. Completar formulario:
   - **Extensión**: Incluir el punto (ejemplo: `.webm`)
   - **Tipo**: Seleccionar de dropdown (image/video/audio)
3. Click en **"Guardar"**

**Resultado:**
- La extensión queda registrada
- Los futuros escaneos detectarán archivos con esa extensión
- El caché se invalida automáticamente

**Editar extensión:**

1. Click en **"Editar"** junto a la extensión
2. Modificar tipo si es necesario
3. Click en **"Guardar"**

**Eliminar extensión:**

1. Click en **"Eliminar"**
2. Confirmar eliminación
3. Los archivos con esa extensión ya no serán categorizados

💡 **Consejo:** Antes de escanear una carpeta con formatos poco comunes, verifica que las extensiones estén registradas aquí.

#### 3. Gestión de Tipos de Soporte

**Acceso:** Mantenimiento > Tipos de Soporte

**¿Para qué sirve?**
Catálogo de tipos de almacenamiento para el catálogo de videos (HDD, SSD, USB, DVD, etc.).

**Operaciones:**
- **Añadir**: Crear nuevo tipo de soporte
- **Editar**: Modificar nombre
- **Eliminar**: Solo si no está en uso por ningún video

**Validación:**
- Al agregar un video, el tipo de soporte debe existir en esta tabla
- Previene errores tipográficos
- Mantiene consistencia en el catálogo

#### 4. Copias de Seguridad (Backup)

**Acceso:** Mantenimiento > Backup

**¿Qué hace?**
Crea una copia del archivo de base de datos SQLite.

**Opciones:**

**A. Backup Simple:**
1. Click en **"Crear Backup"**
2. Se descarga automáticamente:
   - Nombre: `multimedia_backup_YYYYMMDD_HHMMSS.db`
   - Ubicación: Carpeta de descargas del navegador

**B. Backup a Ubicación Específica:**
1. Ingresar ruta destino en el campo de texto
   - Windows: `C:\Backups\mi_backup.db`
   - Linux: `/home/usuario/backups/mi_backup.db`
2. Click en **"Guardar en Ubicación"**
3. El archivo se copia a la ruta especificada

**Ventajas:**
- ✅ Copia exacta de toda la base de datos
- ✅ Incluye todas las tablas y datos
- ✅ Se puede restaurar en cualquier momento
- ✅ Portátil (el archivo .db es independiente)

**Recomendaciones:**
- Hacer backups antes de operaciones importantes
- Mantener backups periódicos (diarios/semanales)
- Guardar en ubicaciones externas (USB, nube)
- Etiquetar backups con fecha y motivo

#### 5. Exportar Base de Datos

**Acceso:** Mantenimiento > Exportar

**Formatos disponibles:**

**A. Exportar a SQL:**
- Genera archivo con sentencias SQL (CREATE TABLE, INSERT)
- Útil para:
  - Migrar a otro sistema
  - Revisar estructura de datos
  - Regenerar base de datos desde cero

**B. Exportar a JSON:**
- Genera archivo JSON con todos los datos
- Útil para:
  - Integración con otras aplicaciones
  - Análisis de datos
  - Respaldo legible por humanos

**Uso:**
1. Seleccionar formato deseado
2. Click en botón de exportación
3. Se descarga el archivo automáticamente

#### 6. Estadísticas en JSON

**Acceso:** `/maintenance/stats.json` (API endpoint)

**¿Para qué sirve?**
Proporciona información de la base de datos en formato JSON para integraciones.

**Datos incluidos:**
```json
{
  "database_path": "data/multimedia.db",
  "database_size_mb": 15.3,
  "total_tables": 12,
  "operational_tables": [...],
  "system_tables": [...]
}
```

**Uso:**
- Scripts de monitoreo
- Integraciones con otras aplicaciones
- Dashboards externos

---

## 🛠️ Utilidades

### ¿Qué incluye?
Herramientas adicionales para tareas específicas.

**Estado actual:** Sección preparada para funcionalidades futuras

**Funcionalidades planeadas:**
- Herramientas de análisis avanzado
- Convertidores de formato
- Generadores de reportes
- Utilidades de limpieza y mantenimiento

---

## ❓ Preguntas Frecuentes

### Sobre el Escaneo de Archivos

**P: ¿Por qué mi carpeta aparece vacía después de escanear?**

R: Posibles causas:
1. **Sin permisos de lectura**: Verifica que tengas acceso a la carpeta
2. **Extensiones no registradas**: Ve a Mantenimiento > Tipos de Archivo y añade las extensiones
3. **Ruta incorrecta**: Verifica que la ruta sea válida y exista
4. **Subdirectorios desmarcados**: Si tus archivos están en subcarpetas, marca "Incluir subdirectorios"

**P: ¿Cuánto tiempo tarda un escaneo?**

R: Depende de:
- Cantidad de archivos (promedio: 1000 archivos/minuto)
- Velocidad del disco (SSD más rápido que HDD)
- Si escanea subdirectorios o no

**P: ¿Puedo cancelar un escaneo en progreso?**

R: Actualmente no hay botón de cancelación. Puedes:
- Esperar a que termine
- Recargar la página (se perderán los resultados parciales)
- Cerrar la pestaña del navegador

### Sobre Videos

**P: ¿Agregar un video al catálogo mueve o copia el archivo?**

R: No. El catálogo solo guarda la **referencia** al archivo (la ruta). El archivo permanece en su ubicación original.

**P: ¿Qué pasa si muevo un archivo después de agregarlo al catálogo?**

R: La ruta almacenada quedará obsoleta. Debes:
1. Editar el registro del video
2. Actualizar el campo "Ruta del Archivo"

**P: ¿Puedo importar mi colección de películas de Excel/CSV?**

R: No directamente. Opciones:
1. Convertir CSV a SQL usando herramientas online
2. Agregar manualmente usando el formulario
3. Crear un script personalizado (requiere conocimientos técnicos)

### Sobre Tablas Dinámicas

**P: ¿Puedo relacionar dos tablas entre sí (claves foráneas)?**

R: Actualmente no está implementado en la interfaz. Se está trabajando en esta funcionalidad.

**P: ¿Cuántas tablas puedo crear?**

R: No hay límite técnico, pero por rendimiento se recomienda mantener menos de 50 tablas personalizadas.

**P: ¿Puedo exportar solo una tabla específica?**

R: No directamente desde la interfaz. Puedes:
1. Hacer backup completo
2. Abrir el archivo .db con herramientas SQLite (DB Browser)
3. Exportar la tabla específica

### Sobre Mantenimiento

**P: ¿Con qué frecuencia debo hacer backups?**

R: Depende del uso:
- Uso intensivo: Diario
- Uso moderado: Semanal
- Uso ocasional: Antes de operaciones importantes

**P: ¿Puedo restaurar un backup antiguo?**

R: Sí:
1. Detener la aplicación
2. Reemplazar `data/multimedia.db` con tu backup
3. Reiniciar la aplicación

**P: ¿Qué diferencia hay entre Backup y Exportar?**

R:
- **Backup**: Copia exacta del archivo .db (restauración completa)
- **Exportar**: Conversión a SQL o JSON (para análisis o migración)

### Problemas Técnicos

**P: La aplicación no inicia, ¿qué hago?**

R: Verifica:
1. Entorno virtual activado: `.\.venv\Scripts\Activate.ps1`
2. Dependencias instaladas: `pip install -r requirements.txt`
3. Archivo `.env` existe (copia de `.env.example`)
4. Puerto 5000 no está en uso: `netstat -an | findstr :5000`

**P: Error "Database is locked" al guardar**

R: Causas:
1. Otra instancia de la aplicación corriendo
2. Backup en progreso
3. Archivo .db abierto en otro programa

Solución:
- Cierra otras instancias
- Reinicia la aplicación
- Verifica que nadie más tenga el .db abierto

**P: Los cambios no se guardan**

R: Verifica:
1. Campos obligatorios completados (marcados con *)
2. Permisos de escritura en carpeta `data/`
3. Disco no lleno
4. Mensajes de error en la consola del navegador (F12)

---

## 💡 Consejos y Mejores Prácticas

### Organización

1. **Usa nombres descriptivos:**
   - Tablas: `peliculas_clasicas`, `fotos_vacaciones_2024`
   - Campos: `fecha_compra`, `precio_original`

2. **Mantén consistencia:**
   - Siempre usa minúsculas
   - Usa guiones bajos en lugar de espacios
   - Ejemplo: `nombre_producto` ✅ vs `Nombre Producto` ❌

3. **Documenta en el campo "Descripción":**
   - Útil para recordar el propósito meses después
   - Especialmente importante en tablas complejas

### Rendimiento

1. **Escaneos grandes:**
   - Divide en carpetas más pequeñas si es posible
   - Usa "Sin subdirectorios" para búsquedas rápidas
   - Evita escanear unidades completas (C:\) a menos que sea necesario

2. **Base de datos:**
   - Elimina registros antiguos que ya no necesitas
   - Haz limpieza periódica de tablas no usadas
   - Mantén backups comprimidos (los .db se comprimen bien)

3. **Navegador:**
   - Usa Chrome o Firefox para mejor rendimiento
   - Si la página se vuelve lenta, recarga (Ctrl+F5)

### Seguridad

1. **Backups:**
   - Guarda en 3 ubicaciones diferentes (regla 3-2-1)
   - Incluye la fecha en el nombre del backup
   - Prueba restaurar un backup antes de necesitarlo

2. **Datos sensibles:**
   - No almacenes contraseñas en campos de texto
   - Ten cuidado con rutas de archivos privados
   - Los backups incluyen TODOS los datos

### Migración

**Si cambias de computadora:**

1. Hacer backup de `data/multimedia.db`
2. Copiar carpeta completa `organizando-fotos/` a nueva PC
3. Instalar Python y dependencias
4. Copiar backup a `data/multimedia.db`
5. Iniciar aplicación

**Si actualizas la aplicación:**

1. Hacer backup antes de actualizar
2. Hacer `git pull` o descargar nueva versión
3. Ejecutar `pip install -r requirements.txt`
4. Iniciar y verificar que todo funcione

---

## 🆘 Soporte y Ayuda

### Recursos

- **README.md**: Información general del proyecto
- **RESUMEN_OPTIMIZACIONES.md**: Detalles técnicos de optimizaciones
- **deploy/README.md**: Guía de deployment en producción

### Reportar Problemas

Si encuentras un bug o tienes sugerencias:

1. Verifica que no sea un problema conocido en `todo.md`
2. Intenta reproducir el problema
3. Anota los pasos exactos que causaron el error
4. Incluye:
   - Versión de Python
   - Sistema operativo
   - Mensaje de error completo
   - Capturas de pantalla si es posible

### Logs de la Aplicación

Los logs se guardan en `logs/app.log`:
- Incluyen fecha y hora de cada evento
- Útiles para diagnosticar problemas
- Se rotan automáticamente (máximo 10MB)

**Ver logs en tiempo real (Windows):**
```powershell
Get-Content logs/app.log -Wait -Tail 50
```

**Ver logs en tiempo real (Linux/Mac):**
```bash
tail -f logs/app.log
```

---

## 📚 Glosario

- **Blueprint**: Módulo de la aplicación Flask (main, videos, maintenance, etc.)
- **CRUD**: Create, Read, Update, Delete (operaciones básicas de base de datos)
- **FK (Foreign Key)**: Clave foránea, relaciona dos tablas
- **ORM**: Object-Relational Mapping (SQLAlchemy)
- **PK (Primary Key)**: Clave primaria, identificador único
- **SSE**: Server-Sent Events (actualizaciones en tiempo real)
- **SQLite**: Motor de base de datos relacional en un solo archivo
- **VPS**: Virtual Private Server (servidor virtual privado)

---

**Guía creada:** Octubre 2025  
**Versión:** 1.0  
**Aplicación:** organizando-fotos v2.0
