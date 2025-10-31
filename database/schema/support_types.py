"""
Schema definition for tipo_soporte table.
Catálogo de tipos de soporte físico o digital para videos.
"""


def create_table(connection):
    """Crea la tabla tipo_soporte con todos sus campos."""
    create_sql = """
    CREATE TABLE IF NOT EXISTS tipo_soporte (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo VARCHAR(100) NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    connection.execute(create_sql)
    print("[OK] Tabla 'tipo_soporte' creada")


def seed_data(connection):
    """
    Pobla la tabla con tipos de soporte comunes.
    Valores basados en uso típico del sistema.
    """
    tipos_soporte = [
        'DVD',
        'Blu-ray',
        'VHS',
        'Digital',
        'Streaming',
        'CD',
        'USB',
        'Disco Duro Externo',
        'Nube',
        'Otro'
    ]
    
    # INSERT OR IGNORE para idempotencia
    insert_sql = """
    INSERT OR IGNORE INTO tipo_soporte (tipo)
    VALUES (?)
    """
    
    connection.executemany(insert_sql, [(t,) for t in tipos_soporte])
    print(f"[OK] {len(tipos_soporte)} tipos de soporte cargados")


def get_schema_info():
    """Retorna información sobre el esquema para documentación."""
    return {
        'table_name': 'tipo_soporte',
        'description': 'Catálogo de tipos de soporte físico o digital para videos',
        'model': 'app.models.database.TipoSoporte',
        'columns': [
            ('id', 'INTEGER', 'Primary key autoincremental'),
            ('tipo', 'VARCHAR(100)', 'Nombre del tipo de soporte (DVD, Blu-ray, Digital, etc.)'),
            ('created_at', 'DATETIME', 'Fecha de creación del registro'),
        ],
        'indices': [],
        'foreign_keys': [],
        'seed_required': True,
        'notes': 'Valores predefinidos comunes, pueden agregarse más desde la UI'
    }
