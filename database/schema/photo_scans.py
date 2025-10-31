"""
Schema definitions for photo scanning tables.
Incluye photos_scan y photos_scan_summary.
"""


def create_table(connection):
    """Crea las tablas de escaneo de fotos."""
    
    # Tabla photos_scan - registro detallado por carpeta
    photos_scan_sql = """
    CREATE TABLE IF NOT EXISTS photos_scan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path VARCHAR(255) NOT NULL,
        parent_path VARCHAR(255),
        end_name VARCHAR(255),
        num_images INTEGER NOT NULL DEFAULT 0,
        num_videos INTEGER NOT NULL DEFAULT 0,
        media_types VARCHAR(500),
        last_scan DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        year INTEGER,
        month_number INTEGER,
        month_text VARCHAR(50),
        total_size BIGINT NOT NULL DEFAULT 0
    )
    """
    connection.execute(photos_scan_sql)
    print("[OK] Tabla 'photos_scan' creada")
    
    # Tabla photos_scan_summary - resumen agregado por escaneo
    photos_scan_summary_sql = """
    CREATE TABLE IF NOT EXISTS photos_scan_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path VARCHAR(255) NOT NULL,
        directories_count INTEGER NOT NULL DEFAULT 0,
        num_images INTEGER NOT NULL DEFAULT 0,
        num_videos INTEGER NOT NULL DEFAULT 0,
        year INTEGER,
        month_number INTEGER,
        month_text VARCHAR(50),
        total_size BIGINT NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        directory VARCHAR(500),
        scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        total_files INTEGER DEFAULT 0,
        processed_files INTEGER DEFAULT 0,
        failed_files INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'pending',
        details TEXT
    )
    """
    connection.execute(photos_scan_summary_sql)
    print("[OK] Tabla 'photos_scan_summary' creada")


def seed_data(connection):
    """
    No hay datos iniciales requeridos para las tablas de escaneo.
    Los datos se generan al ejecutar escaneos desde la UI.
    """
    print("  (No se requieren datos iniciales para tablas de escaneo)")


def get_schema_info():
    """Retorna información sobre el esquema para documentación."""
    return {
        'tables': [
            {
                'table_name': 'photos_scan',
                'description': 'Registro detallado de carpetas escaneadas',
                'model': 'app.models.database.PhotoScan',
                'columns': [
                    ('id', 'INTEGER', 'Primary key'),
                    ('path', 'VARCHAR(255)', 'Ruta completa de la carpeta'),
                    ('parent_path', 'VARCHAR(255)', 'Ruta del padre'),
                    ('end_name', 'VARCHAR(255)', 'Nombre de la carpeta'),
                    ('num_images', 'INTEGER', 'Cantidad de imágenes encontradas'),
                    ('num_videos', 'INTEGER', 'Cantidad de videos encontrados'),
                    ('media_types', 'VARCHAR(500)', 'Tipos de medios (JSON)'),
                    ('last_scan', 'DATETIME', 'Fecha del último escaneo'),
                    ('created_at', 'DATETIME', 'Fecha de creación del registro'),
                    ('year', 'INTEGER', 'Año extraído del nombre de carpeta'),
                    ('month_number', 'INTEGER', 'Número de mes (1-12)'),
                    ('month_text', 'VARCHAR(50)', 'Nombre del mes'),
                    ('total_size', 'BIGINT', 'Tamaño total en bytes'),
                ],
                'indices': [],
                'foreign_keys': [],
            },
            {
                'table_name': 'photos_scan_summary',
                'description': 'Resumen agregado por sesión de escaneo',
                'model': 'app.models.database.PhotoScanSummary',
                'columns': [
                    ('id', 'INTEGER', 'Primary key'),
                    ('path', 'VARCHAR(255)', 'Ruta raíz del escaneo'),
                    ('directories_count', 'INTEGER', 'Cantidad de carpetas escaneadas'),
                    ('num_images', 'INTEGER', 'Total de imágenes'),
                    ('num_videos', 'INTEGER', 'Total de videos'),
                    ('year', 'INTEGER', 'Año'),
                    ('month_number', 'INTEGER', 'Mes'),
                    ('month_text', 'VARCHAR(50)', 'Nombre del mes'),
                    ('total_size', 'BIGINT', 'Tamaño total en bytes'),
                    ('created_at', 'DATETIME', 'Fecha de creación'),
                    ('directory', 'VARCHAR(500)', 'Directorio escaneado'),
                    ('scan_date', 'DATETIME', 'Fecha del escaneo'),
                    ('total_files', 'INTEGER', 'Total de archivos'),
                    ('processed_files', 'INTEGER', 'Archivos procesados'),
                    ('failed_files', 'INTEGER', 'Archivos fallidos'),
                    ('status', 'VARCHAR(20)', 'Estado (pending, completed, failed)'),
                    ('details', 'TEXT', 'Detalles adicionales (JSON)'),
                ],
                'indices': [],
                'foreign_keys': [],
            }
        ],
        'seed_required': False,
        'notes': 'Generado dinámicamente por el scanner de fotos'
    }
