import sqlite3
import os

# Definir rutas
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "multimedia.db")

# Asegurarse de que la carpeta data exista
os.makedirs(DATA_DIR, exist_ok=True)

# Extensiones multimedia
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",".webp",".heic",".svg",".raw",".CR2",".CR3 "}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".aac", ".flac"}

def create_database():
    # Conectar a la base de datos (se crea si no existe)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Crear tabla file_types si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            extension TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('image', 'video', 'audio'))
        )
    ''')

    # Insertar extensiones
    file_data = []
    for ext in IMAGE_EXTENSIONS:
        file_data.append((ext, 'image'))
    for ext in VIDEO_EXTENSIONS:
        file_data.append((ext, 'video'))
    for ext in AUDIO_EXTENSIONS:
        file_data.append((ext, 'audio'))

    cursor.executemany('''
        INSERT OR IGNORE INTO file_types (extension, type)
        VALUES (?, ?)
    ''', file_data)

    conn.commit()
    conn.close()
    print(f"Base de datos creada en: {DB_PATH}")
    print("Tabla 'file_types' inicializada con extensiones multimedia.")

if __name__ == "__main__":
    create_database()
