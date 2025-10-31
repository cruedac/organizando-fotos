"""
Schema definition for movies table.
Catálogo de videos/películas con metadatos completos.
"""


def create_table(connection):
    """Crea la tabla movies con todos sus campos e índices."""
    
    # Tabla principal (mantiene nombres de columnas en MAYÚSCULAS por compatibilidad legacy)
    create_sql = """
    CREATE TABLE IF NOT EXISTS movies (
        NUM INTEGER PRIMARY KEY AUTOINCREMENT,
        CHECKED VARCHAR(5),
        COLORTAG INTEGER,
        MEDIA VARCHAR(100),
        MEDIATYPE VARCHAR(50),
        SOURCE VARCHAR(100),
        DATEADDED DATE,
        BORROWER VARCHAR(100),
        DATEWATCHED DATE,
        USERRATING REAL,
        RATING REAL,
        ORIGINALTITLE VARCHAR(200),
        TRANSLATEDTITLE VARCHAR(200),
        FORMATTEDTITLE VARCHAR(200),
        DIRECTOR VARCHAR(200),
        PRODUCER VARCHAR(200),
        WRITER VARCHAR(200),
        COMPOSER VARCHAR(200),
        ACTORS TEXT,
        COUNTRY VARCHAR(100),
        YEAR INTEGER,
        LENGTH INTEGER,
        CATEGORY VARCHAR(100),
        CERTIFICATION VARCHAR(50),
        URL VARCHAR(500),
        DESCRIPTION TEXT,
        COMMENTS TEXT,
        FILEPATH VARCHAR(500),
        VIDEOFORMAT VARCHAR(50),
        VIDEOBITRATE INTEGER,
        AUDIOFORMAT VARCHAR(50),
        AUDIOBITRATE INTEGER,
        RESOLUTION VARCHAR(50),
        FRAMERATE VARCHAR(20),
        LANGUAGES VARCHAR(200),
        SUBTITLES VARCHAR(200),
        FILESIZE VARCHAR(50),
        DISKS INTEGER,
        PICTURESTATUS VARCHAR(50),
        NBEXTRAS INTEGER,
        PICTURENAME VARCHAR(200)
    )
    """
    connection.execute(create_sql)
    print("[OK] Tabla 'movies' creada")
    
    # Índices para optimizar búsquedas frecuentes
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_movie_year ON movies (YEAR)",
        "CREATE INDEX IF NOT EXISTS idx_movie_category ON movies (CATEGORY)",
        "CREATE INDEX IF NOT EXISTS idx_movie_mediatype ON movies (MEDIATYPE)"
    ]
    
    for index_sql in indices:
        connection.execute(index_sql)
    
    print("[OK] Indices de 'movies' creados")


def seed_data(connection):
    """
    No hay datos iniciales requeridos para movies.
    Los datos se importan desde SQL legacy o se agregan vía UI.
    """
    print("  (No se requieren datos iniciales para 'movies')")


def get_schema_info():
    """Retorna información sobre el esquema para documentación."""
    return {
        'table_name': 'movies',
        'description': 'Catálogo de videos/películas con metadatos completos',
        'model': 'app.models.movie.Movie',
        'columns': [
            ('NUM', 'INTEGER', 'Primary key del video'),
            ('CHECKED', 'VARCHAR(5)', 'Marca si está verificado'),
            ('COLORTAG', 'INTEGER', 'Etiqueta de color'),
            ('MEDIA', 'VARCHAR(100)', 'Medio de almacenamiento'),
            ('MEDIATYPE', 'VARCHAR(50)', 'Tipo de medio (DVD, BluRay, Digital, etc.)'),
            ('SOURCE', 'VARCHAR(100)', 'Fuente de origen'),
            ('DATEADDED', 'DATE', 'Fecha en que se agregó al catálogo'),
            ('BORROWER', 'VARCHAR(100)', 'Persona que lo tiene prestado'),
            ('DATEWATCHED', 'DATE', 'Fecha en que se vio'),
            ('USERRATING', 'REAL', 'Calificación del usuario'),
            ('RATING', 'REAL', 'Calificación general'),
            ('ORIGINALTITLE', 'VARCHAR(200)', 'Título original'),
            ('TRANSLATEDTITLE', 'VARCHAR(200)', 'Título traducido'),
            ('FORMATTEDTITLE', 'VARCHAR(200)', 'Título formateado'),
            ('DIRECTOR', 'VARCHAR(200)', 'Director(es)'),
            ('PRODUCER', 'VARCHAR(200)', 'Productor(es)'),
            ('WRITER', 'VARCHAR(200)', 'Escritor(es)'),
            ('COMPOSER', 'VARCHAR(200)', 'Compositor(es)'),
            ('ACTORS', 'TEXT', 'Lista de actores'),
            ('COUNTRY', 'VARCHAR(100)', 'País de origen'),
            ('YEAR', 'INTEGER', 'Año de producción'),
            ('LENGTH', 'INTEGER', 'Duración en minutos'),
            ('CATEGORY', 'VARCHAR(100)', 'Categoría/Género'),
            ('CERTIFICATION', 'VARCHAR(50)', 'Certificación (PG, R, etc.)'),
            ('URL', 'VARCHAR(500)', 'URL de información adicional'),
            ('DESCRIPTION', 'TEXT', 'Sinopsis/Descripción'),
            ('COMMENTS', 'TEXT', 'Comentarios personales'),
            ('FILEPATH', 'VARCHAR(500)', 'Ruta del archivo'),
            ('VIDEOFORMAT', 'VARCHAR(50)', 'Formato de video (H.264, etc.)'),
            ('VIDEOBITRATE', 'INTEGER', 'Bitrate de video'),
            ('AUDIOFORMAT', 'VARCHAR(50)', 'Formato de audio (AAC, etc.)'),
            ('AUDIOBITRATE', 'INTEGER', 'Bitrate de audio'),
            ('RESOLUTION', 'VARCHAR(50)', 'Resolución (1080p, etc.)'),
            ('FRAMERATE', 'VARCHAR(20)', 'FPS'),
            ('LANGUAGES', 'VARCHAR(200)', 'Idiomas disponibles'),
            ('SUBTITLES', 'VARCHAR(200)', 'Subtítulos disponibles'),
            ('FILESIZE', 'VARCHAR(50)', 'Tamaño del archivo'),
            ('DISKS', 'INTEGER', 'Número de discos'),
            ('PICTURESTATUS', 'VARCHAR(50)', 'Estado de la imagen/portada'),
            ('NBEXTRAS', 'INTEGER', 'Número de extras'),
            ('PICTURENAME', 'VARCHAR(200)', 'Nombre de la imagen de portada'),
        ],
        'indices': [
            ('idx_movie_year', 'YEAR', 'Optimiza búsquedas por año'),
            ('idx_movie_category', 'CATEGORY', 'Optimiza búsquedas por categoría'),
            ('idx_movie_mediatype', 'MEDIATYPE', 'Optimiza búsquedas por tipo de medio'),
        ],
        'foreign_keys': [],
        'seed_required': False,
        'notes': 'Nombres de columna en MAYÚSCULAS por compatibilidad con imports/Cintas.sql'
    }
