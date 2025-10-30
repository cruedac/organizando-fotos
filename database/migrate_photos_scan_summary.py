"""
Script para migrar la tabla photos_scan_summary añadiendo las columnas faltantes
"""
import sqlite3
from pathlib import Path

# Ruta a la base de datos
DB_PATH = Path('data/multimedia.db')

def migrate_photos_scan_summary():
    """Añade las columnas faltantes a la tabla photos_scan_summary"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar si la tabla existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='photos_scan_summary'")
    if not cursor.fetchone():
        print("❌ La tabla photos_scan_summary no existe")
        conn.close()
        return
    
    # Obtener columnas existentes
    cursor.execute("PRAGMA table_info(photos_scan_summary)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"Columnas existentes: {existing_columns}")
    
    # Columnas que necesitamos añadir
    new_columns = {
        'directory': 'TEXT',
        'scan_date': 'DATETIME',
        'total_files': 'INTEGER DEFAULT 0',
        'processed_files': 'INTEGER DEFAULT 0',
        'failed_files': 'INTEGER DEFAULT 0',
        'status': 'TEXT DEFAULT "pending"',
        'details': 'TEXT'
    }
    
    # Añadir columnas faltantes
    changes_made = False
    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            try:
                sql = f"ALTER TABLE photos_scan_summary ADD COLUMN {column_name} {column_type}"
                print(f"Ejecutando: {sql}")
                cursor.execute(sql)
                print(f"✅ Columna '{column_name}' añadida correctamente")
                changes_made = True
            except sqlite3.OperationalError as e:
                print(f"⚠️  Error al añadir columna '{column_name}': {e}")
        else:
            print(f"ℹ️  Columna '{column_name}' ya existe")
    
    if changes_made:
        conn.commit()
        print("\n✅ Migración completada exitosamente")
    else:
        print("\nℹ️  No se requirieron cambios")
    
    # Verificar estructura final
    cursor.execute("PRAGMA table_info(photos_scan_summary)")
    print("\n📋 Estructura final de la tabla:")
    for row in cursor.fetchall():
        print(f"  - {row[1]} ({row[2]})")
    
    conn.close()

if __name__ == '__main__':
    print("🔧 Iniciando migración de photos_scan_summary...\n")
    migrate_photos_scan_summary()
