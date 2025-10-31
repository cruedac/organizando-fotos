"""
Database initialization script.

Este script recrea completamente la base de datos desde cero utilizando
las definiciones de esquema en database/schema/.

USO:
    python database/init_database.py [--drop] [--seed]

OPCIONES:
    --drop    Elimina todas las tablas existentes antes de crear
    --seed    Pobla las tablas con datos iniciales (extensiones, tipos de soporte)

ADVERTENCIA:
    Este script ELIMINARÁ TODOS LOS DATOS si se usa con --drop.
    Siempre crea un backup antes de ejecutar.
"""

import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path para imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config import Config

# Importar módulos de esquema en el orden de dependencias
from database.schema import file_types as file_types_schema
from database.schema import movies as movies_schema
from database.schema import support_types as support_types_schema
from database.schema import photo_scans as photo_scans_schema
from database.schema import dynamic_tables as dynamic_tables_schema


def get_db_connection():
    """Crea una conexión directa a la base de datos SQLite."""
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    db_path = Path(db_path)
    
    # Asegurar que el directorio existe
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    # Habilitar foreign keys
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def get_all_tables(connection):
    """Obtiene lista de todas las tablas en la base de datos."""
    cursor = connection.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    return [row[0] for row in cursor.fetchall()]


def drop_all_tables(connection):
    """
    Elimina todas las tablas de la base de datos.
    
    ADVERTENCIA: Esta operación es irreversible.
    """
    # Desactivar foreign keys temporalmente para evitar errores de dependencias
    connection.execute('PRAGMA foreign_keys = OFF')
    
    tables = get_all_tables(connection)
    
    if not tables:
        print("[INFO] No hay tablas para eliminar")
        return
    
    print(f"\n[WARNING] Eliminando {len(tables)} tablas...")
    for table in tables:
        try:
            connection.execute(f'DROP TABLE IF EXISTS "{table}"')
            print(f"  [OK] Tabla '{table}' eliminada")
        except sqlite3.Error as e:
            print(f"  [ERROR] Error al eliminar '{table}': {e}")
    
    connection.commit()
    
    # Reactivar foreign keys
    connection.execute('PRAGMA foreign_keys = ON')
    print("[OK] Todas las tablas eliminadas")


def create_all_tables(connection, with_seed=False):
    """
    Crea todas las tablas en el orden correcto.
    
    Args:
        connection: Conexion SQLite
        with_seed: Si es True, tambien pobla datos iniciales
    """
    print("\n[CREATE] Creando tablas...")
    
    # Lista de esquemas en orden de dependencias
    schemas = [
        ('Tipos de Archivo', file_types_schema),
        ('Peliculas', movies_schema),
        ('Tipos de Soporte', support_types_schema),
        ('Escaneo de Fotos', photo_scans_schema),
        ('Tablas Dinamicas', dynamic_tables_schema),
    ]
    
    for name, schema in schemas:
        print(f"\n{name}:")
        try:
            schema.create_table(connection)
            
            if with_seed:
                schema.seed_data(connection)
            
        except Exception as e:
            print(f"  [ERROR] Error: {e}")
            raise
    
    connection.commit()
    print("\n[OK] Todas las tablas creadas exitosamente")


def verify_schema(connection):
    """Verifica que todas las tablas esperadas existan."""
    expected_tables = [
        'file_types',
        'movies',
        'tipo_soporte',
        'photos_scan',
        'photos_scan_summary',
        'dynamic_table',
        'table_field',
    ]
    
    existing_tables = get_all_tables(connection)
    
    print("\n[VERIFY] Verificacion de esquema:")
    all_ok = True
    
    for table in expected_tables:
        if table in existing_tables:
            print(f"  [OK] {table}")
        else:
            print(f"  [ERROR] {table} - FALTANTE")
            all_ok = False
    
    if all_ok:
        print("\n[OK] Esquema completo y correcto")
    else:
        print("\n[WARNING] Esquema incompleto")
    
    return all_ok


def print_database_info(connection):
    """Imprime informacion sobre el estado de la base de datos."""
    tables = get_all_tables(connection)
    
    print("\n[INFO] Estado de la base de datos:")
    print(f"  Total de tablas: {len(tables)}")
    
    for table in tables:
        cursor = connection.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        print(f"    - {table}: {count} registros")


def create_backup(db_path):
    """Crea un backup de la base de datos antes de modificarla."""
    if not db_path.exists():
        print("[INFO] No hay base de datos existente, no se requiere backup")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = db_path.parent / 'backup'
    backup_dir.mkdir(exist_ok=True)
    
    backup_path = backup_dir / f'{db_path.stem}_before_init_{timestamp}{db_path.suffix}'
    
    print(f"\n[BACKUP] Creando backup en: {backup_path}")
    
    # Copiar usando sqlite3 backup API
    source_conn = sqlite3.connect(str(db_path))
    backup_conn = sqlite3.connect(str(backup_path))
    
    with backup_conn:
        source_conn.backup(backup_conn)
    
    source_conn.close()
    backup_conn.close()
    
    print("[OK] Backup creado exitosamente")
    return backup_path


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Inicializa/recrea la base de datos completa',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Elimina todas las tablas existentes antes de crear'
    )
    parser.add_argument(
        '--seed',
        action='store_true',
        help='Pobla las tablas con datos iniciales'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='NO crear backup automático (no recomendado)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("  INICIALIZACION DE BASE DE DATOS")
    print("="*60)
    
    db_path_str = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    db_path = Path(db_path_str)
    
    print(f"\nBase de datos: {db_path}")
    print(f"Drop tables: {'Si' if args.drop else 'No'}")
    print(f"Seed data: {'Si' if args.seed else 'No'}")
    
    # Crear backup si existe la BD y no se especificó --no-backup
    if args.drop and not args.no_backup:
        backup_path = create_backup(db_path)
        if backup_path:
            print(f"  Backup guardado en: {backup_path}")
    
    # Confirmación si se va a hacer drop
    if args.drop:
        print("\n[WARNING] [WARNING] [WARNING]  ADVERTENCIA  [WARNING] [WARNING] [WARNING]")
        print("Esta operacion ELIMINARA TODOS LOS DATOS de la base de datos.")
        
        response = input("\nEstas seguro? Escribe 'CONFIRMAR' para continuar: ")
        if response != 'CONFIRMAR':
            print("[CANCELLED] Operacion cancelada")
            return 1
    
    try:
        conn = get_db_connection()
        
        # Drop si se solicitó
        if args.drop:
            drop_all_tables(conn)
        
        # Crear tablas
        create_all_tables(conn, with_seed=args.seed)
        
        # Verificar
        verify_schema(conn)
        
        # Mostrar info
        print_database_info(conn)
        
        conn.close()
        
        print("\n" + "="*60)
        print("  [SUCCESS] INICIALIZACION COMPLETADA EXITOSAMENTE")
        print("="*60)
        
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Error durante la inicializacion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
