"""
Schema definition for file_types table.
Catálogo de tipos de archivo permitidos (extensiones).
"""

from config import Config


def create_table(connection):
    """Crea la tabla file_types con todos sus campos."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS file_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        extension VARCHAR(10) NOT NULL UNIQUE,
        type VARCHAR(20) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    connection.execute(create_sql)
    print("[OK] Tabla 'file_types' creada")


def seed_data(connection):
    """
    Pobla la tabla con extensiones permitidas desde la configuración.
    
    Sincronizado con FileType.init_db() en app/models/database.py
    """
    allowed_extensions = Config.ALLOWED_EXTENSIONS
    
    # Construir lista de valores para INSERT
    values = []
    for file_type, extensions in allowed_extensions.items():
        for ext in extensions:
            # Normalizar extensión: lowercase, sin punto inicial
            normalized_ext = ext.lower().lstrip('.')
            values.append((normalized_ext, file_type))
    
    # INSERT OR IGNORE para idempotencia
    insert_sql = """
    INSERT OR IGNORE INTO file_types (extension, type)
    VALUES (?, ?)
    """
    
    connection.executemany(insert_sql, values)
    print(f"[OK] {len(values)} extensiones de archivo cargadas")


def get_schema_info():
    """Retorna información sobre el esquema para documentación."""
    return {
        'table_name': 'file_types',
        'description': 'Catálogo de extensiones de archivo permitidas',
        'model': 'app.models.database.FileType',
        'columns': [
            ('id', 'INTEGER', 'Primary key autoincremental'),
            ('extension', 'VARCHAR(10)', 'Extensión sin punto (ej: jpg, mp4)'),
            ('type', 'VARCHAR(20)', 'Tipo: image, video, document, etc.'),
            ('created_at', 'DATETIME', 'Fecha de creación del registro'),
        ],
        'indices': [],
        'foreign_keys': [],
        'seed_required': True,
        'notes': 'Sincronizado con Config.ALLOWED_EXTENSIONS'
    }
