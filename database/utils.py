# database/utils.py
import sqlite3
import os
from typing import List, Tuple, Any

# Usar ruta absoluta para evitar problemas de importación
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "multimedia.db")

def get_connection(db_path: str = None):
    """Establece conexión con la base de datos."""
    return sqlite3.connect(db_path if db_path else DB_PATH)

def fetch_all(table: str, connection: sqlite3.Connection = None) -> List[Tuple]:
    """Obtiene todos los registros de una tabla."""
    should_close = False
    if not connection:
        connection = get_connection()
        should_close = True
    
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    
    if should_close:
        connection.close()
    return rows

def fetch_columns(table: str, connection: sqlite3.Connection = None) -> List[str]:
    """Obtiene los nombres de las columnas de una tabla."""
    should_close = False
    if not connection:
        connection = get_connection()
        should_close = True

    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    
    if should_close:
        connection.close()
    return columns

def get_tables(connection: sqlite3.Connection) -> List[str]:
    """Obtiene todas las tablas de la base de datos."""
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [table[0] for table in cursor.fetchall()]

def insert_record(table: str, columns: List[str], values: Tuple[Any], connection: sqlite3.Connection = None):
    """Inserta un nuevo registro en la tabla."""
    should_close = False
    if not connection:
        connection = get_connection()
        should_close = True

    placeholders = ", ".join(["?" for _ in values])
    cols = ", ".join(columns)
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", values)
    connection.commit()
    
    if should_close:
        connection.close()

def update_record(table: str, columns: List[str], values: Tuple[Any], record_id: int, connection: sqlite3.Connection = None, id_column: str = "id"):
    """Actualiza un registro por su ID."""
    should_close = False
    if not connection:
        connection = get_connection()
        should_close = True

    set_clause = ", ".join([f"{col} = ?" for col in columns])
    cursor = connection.cursor()
    cursor.execute(f"UPDATE {table} SET {set_clause} WHERE {id_column} = ?", (*values, record_id))
    connection.commit()
    
    if should_close:
        connection.close()

def delete_record(table: str, record_id: int, connection: sqlite3.Connection = None, id_column: str = "id"):
    """Elimina un registro por su ID."""
    should_close = False
    if not connection:
        connection = get_connection()
        should_close = True

    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE {id_column} = ?", (record_id,))
    connection.commit()
    
    if should_close:
        connection.close()
