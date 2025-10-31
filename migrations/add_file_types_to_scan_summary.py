#!/usr/bin/env python3
"""
Migración para agregar nuevas columnas a photos_scan_summary
"""

import sqlite3
import sys
from pathlib import Path

# Obtener la ruta del proyecto
project_root = Path(__file__).parent.parent
db_path = project_root / 'data' / 'multimedia.db'

def migrate_photos_scan_summary():
    """Agregar nuevas columnas a la tabla photos_scan_summary"""
    
    if not db_path.exists():
        print(f"Base de datos no encontrada en: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='photos_scan_summary'
        """)
        
        if not cursor.fetchone():
            print("Tabla photos_scan_summary no encontrada")
            return False
        
        # Obtener las columnas actuales
        cursor.execute("PRAGMA table_info(photos_scan_summary)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Columnas nuevas a agregar
        new_columns = [
            ('num_audio', 'INTEGER DEFAULT 0'),
            ('num_other', 'INTEGER DEFAULT 0'),
            ('file_types_found', 'TEXT')
        ]
        
        # Agregar cada columna nueva si no existe
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE photos_scan_summary ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Columna '{column_name}' agregada")
                except sqlite3.Error as e:
                    print(f"❌ Error agregando columna '{column_name}': {e}")
            else:
                print(f"⚠️  Columna '{column_name}' ya existe")
        
        conn.commit()
        print("✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("Iniciando migración de photos_scan_summary...")
    success = migrate_photos_scan_summary()
    sys.exit(0 if success else 1)