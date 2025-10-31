"""
Schema definitions for dynamic tables system.
Incluye dynamic_table y table_field para tablas creadas por usuarios.
"""


def create_table(connection):
    """Crea las tablas del sistema de tablas dinámicas."""
    
    # Tabla dynamic_table - metadata de tablas creadas por usuarios
    dynamic_table_sql = """
    CREATE TABLE IF NOT EXISTS dynamic_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL UNIQUE,
        description VARCHAR(200),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    connection.execute(dynamic_table_sql)
    print("[OK] Tabla 'dynamic_table' creada")
    
    # Tabla table_field - campos de las tablas dinámicas
    table_field_sql = """
    CREATE TABLE IF NOT EXISTS table_field (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id INTEGER NOT NULL,
        name VARCHAR(50) NOT NULL,
        field_type VARCHAR(20) NOT NULL,
        is_required INTEGER DEFAULT 0,
        is_primary_key INTEGER DEFAULT 0,
        is_auto_increment INTEGER DEFAULT 0,
        default_value VARCHAR(100),
        description VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (table_id) REFERENCES dynamic_table(id) ON DELETE CASCADE
    )
    """
    connection.execute(table_field_sql)
    print("[OK] Tabla 'table_field' creada")
    
    # Índice para mejorar búsquedas de campos por tabla
    index_sql = """
    CREATE INDEX IF NOT EXISTS idx_table_field_table_id 
    ON table_field (table_id)
    """
    connection.execute(index_sql)
    print("[OK] Indices del sistema de tablas dinamicas creados")


def seed_data(connection):
    """
    No hay datos iniciales requeridos.
    
    Sin embargo, el sistema puede descubrir tablas existentes
    mediante init_existing_tables() al iniciar la aplicación.
    """
    print("  (No se requieren datos iniciales para tablas dinámicas)")


def get_schema_info():
    """Retorna información sobre el esquema para documentación."""
    return {
        'tables': [
            {
                'table_name': 'dynamic_table',
                'description': 'Metadata de tablas creadas dinámicamente por usuarios',
                'model': 'app.models.database.DynamicTable',
                'columns': [
                    ('id', 'INTEGER', 'Primary key'),
                    ('name', 'VARCHAR(50)', 'Nombre de la tabla (debe ser identificador SQL válido)'),
                    ('description', 'VARCHAR(200)', 'Descripción opcional de la tabla'),
                    ('created_at', 'DATETIME', 'Fecha de creación'),
                ],
                'indices': [],
                'foreign_keys': [],
            },
            {
                'table_name': 'table_field',
                'description': 'Definición de campos para tablas dinámicas',
                'model': 'app.models.database.TableField',
                'columns': [
                    ('id', 'INTEGER', 'Primary key'),
                    ('table_id', 'INTEGER', 'FK a dynamic_table.id'),
                    ('name', 'VARCHAR(50)', 'Nombre del campo'),
                    ('field_type', 'VARCHAR(20)', 'Tipo: TEXT, INTEGER, REAL, DATE, DATETIME, BOOLEAN'),
                    ('is_required', 'INTEGER', 'Boolean: 0=opcional, 1=requerido'),
                    ('is_primary_key', 'INTEGER', 'Boolean: 0=no, 1=sí'),
                    ('is_auto_increment', 'INTEGER', 'Boolean: 0=no, 1=sí'),
                    ('default_value', 'VARCHAR(100)', 'Valor por defecto opcional'),
                    ('description', 'VARCHAR(255)', 'Descripción del campo'),
                    ('created_at', 'DATETIME', 'Fecha de creación'),
                ],
                'indices': [
                    ('idx_table_field_table_id', 'table_id', 'Mejora joins con dynamic_table')
                ],
                'foreign_keys': [
                    ('table_id', 'dynamic_table(id)', 'CASCADE on delete')
                ],
            }
        ],
        'seed_required': False,
        'notes': 'init_existing_tables() descubre tablas pre-existentes al iniciar'
    }
