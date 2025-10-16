"""
Script de migración para normalizar columnas DATE en la tabla movies.

Pasos:
1. Crear backup del fichero SQLite en data/backup/db-YYYYMMDD-HHMMSS.db
2. Conectar a la base de datos (usando SQLAlchemy URL desde config.py)
3. Crear tabla temporal `movies_new` con las mismas columnas pero DATE para DATEADDED y DATEWATCHED
4. Copiar filas desde `movies` a `movies_new`, normalizando las columnas de fecha:
   - '' o valores no ISO -> NULL
   - valores ISO válidos -> se dejan como ISO (o como DATE dependiendo del motor)
5. Renombrar tablas: drop old, rename new
6. Guardar informe en data/import_reports/migrate_dates_*.json

Uso:
    python database/migrate_dates.py

Advertencia: ejecutar solo después de backup.
"""
import os
import shutil
import sqlite3
import json
from datetime import datetime

# Intentar importar configuración de la app para obtener la ruta de la DB
try:
    from config import Config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
except Exception:
    # Fallback: asumir sqlite:///data/multimedia.db
    db_uri = 'sqlite:///data/multimedia.db'

# Resolver path absoluto del fichero sqlite
def sqlite_path_from_uri(uri):
    if uri.startswith('sqlite:///'):
        return uri.replace('sqlite:///', '')
    raise RuntimeError('No se pudo resolver URI SQLite')

DB_FILE = sqlite_path_from_uri(db_uri)
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, 'data')
BACKUP_DIR = os.path.join(DATA_DIR, 'backup')
REPORTS_DIR = os.path.join(DATA_DIR, 'import_reports')

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

report = {
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'db_file': DB_FILE,
    'backup_file': None,
    'rows_total': 0,
    'rows_migrated': 0,
    'rows_skipped': 0,
    'errors': []
}

# 1) Backup
try:
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError(f'DB file not found: {DB_FILE}')
    stamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
    backup_name = f"multimedia_{stamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(DB_FILE, backup_path)
    report['backup_file'] = backup_path
    print(f'Backup creado en: {backup_path}')
except Exception as e:
    print(f'Error creando backup: {e}')
    report['errors'].append(str(e))
    with open(os.path.join(REPORTS_DIR, f'migrate_dates_failed_{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'), 'w', encoding='utf-8') as rf:
        json.dump(report, rf, ensure_ascii=False, indent=2)
    raise

# 2) Conexión a sqlite con sqlite3
conn = sqlite3.connect(DB_FILE)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

try:
    # Comprobar existencia de tabla movies
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
    if not cur.fetchone():
        raise RuntimeError('Tabla movies no encontrada en la BD')

    # Leer columnas actuales
    cur.execute('PRAGMA table_info(movies)')
    cols = [r['name'] for r in cur.fetchall()]

    # Crear tabla temporal movies_new – usaremos TEXT para muchas columnas y DATE (como TEXT) para fechas
    # Para simplificar mantenemos la mayoría de columnas como TEXT/INTEGER como en el esquema original
    cur.execute('''
    CREATE TABLE IF NOT EXISTS movies_new (
        NUM INTEGER PRIMARY KEY,
        CHECKED TEXT,
        COLORTAG INTEGER,
        MEDIA TEXT,
        MEDIATYPE TEXT,
        SOURCE TEXT,
        DATEADDED DATE,
        BORROWER TEXT,
        DATEWATCHED DATE,
        USERRATING REAL,
        RATING REAL,
        ORIGINALTITLE TEXT,
        TRANSLATEDTITLE TEXT,
        FORMATTEDTITLE TEXT,
        DIRECTOR TEXT,
        PRODUCER TEXT,
        WRITER TEXT,
        COMPOSER TEXT,
        ACTORS TEXT,
        COUNTRY TEXT,
        YEAR INTEGER,
        LENGTH INTEGER,
        CATEGORY TEXT,
        CERTIFICATION TEXT,
        URL TEXT,
        DESCRIPTION TEXT,
        COMMENTS TEXT,
        FILEPATH TEXT,
        VIDEOFORMAT TEXT,
        VIDEOBITRATE INTEGER,
        AUDIOFORMAT TEXT,
        AUDIOBITRATE INTEGER,
        RESOLUTION TEXT,
        FRAMERATE TEXT,
        LANGUAGES TEXT,
        SUBTITLES TEXT,
        FILESIZE TEXT,
        DISKS INTEGER,
        PICTURESTATUS TEXT,
        NBEXTRAS INTEGER,
        PICTURENAME TEXT
    )
    ''')

    # Transferencia fila a fila con normalización de fechas
    # Si existe una ejecución previa que dejó `movies_old`, usarla como origen
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies_old'")
    if cur.fetchone():
        source_table = 'movies_old'
    else:
        source_table = 'movies'

    cur.execute(f'SELECT * FROM {source_table}')
    rows = cur.fetchall()
    report['rows_total'] = len(rows)

    insert_sql = '''INSERT INTO movies_new (
        NUM, CHECKED, COLORTAG, MEDIA, MEDIATYPE, SOURCE, DATEADDED, BORROWER, DATEWATCHED,
        USERRATING, RATING, ORIGINALTITLE, TRANSLATEDTITLE, FORMATTEDTITLE, DIRECTOR, PRODUCER,
        WRITER, COMPOSER, ACTORS, COUNTRY, YEAR, LENGTH, CATEGORY, CERTIFICATION, URL,
        DESCRIPTION, COMMENTS, FILEPATH, VIDEOFORMAT, VIDEOBITRATE, AUDIOFORMAT, AUDIOBITRATE,
        RESOLUTION, FRAMERATE, LANGUAGES, SUBTITLES, FILESIZE, DISKS, PICTURESTATUS, NBEXTRAS, PICTURENAME
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''

    migrated = 0
    skipped = 0
    for r in rows:
        try:
            # Normalizar DATEADDED y DATEWATCHED
            def norm_date(val):
                if val is None:
                    return None
                s = str(val).strip()
                if s == '' or s.lower() == 'none':
                    return None
                # Intentar parsear ISO (YYYY-MM-DD o similar)
                try:
                    # sqlite date column accepts 'YYYY-MM-DD'
                    datetime.fromisoformat(s)
                    return s
                except Exception:
                    # intentar heurística: extraer primera porción de 10 chars
                    if len(s) >= 10:
                        candidate = s[:10]
                        try:
                            datetime.fromisoformat(candidate)
                            return candidate
                        except Exception:
                            return None
                    return None

            dateadded = norm_date(r['DATEADDED'])
            datewatched = norm_date(r['DATEWATCHED'])

            values = [
                r['NUM'], r['CHECKED'], r['COLORTAG'], r['MEDIA'], r['MEDIATYPE'], r['SOURCE'],
                dateadded, r['BORROWER'], datewatched,
                r['USERRATING'], r['RATING'], r['ORIGINALTITLE'], r['TRANSLATEDTITLE'], r['FORMATTEDTITLE'],
                r['DIRECTOR'], r['PRODUCER'], r['WRITER'], r['COMPOSER'], r['ACTORS'], r['COUNTRY'],
                r['YEAR'], r['LENGTH'], r['CATEGORY'], r['CERTIFICATION'], r['URL'], r['DESCRIPTION'],
                r['COMMENTS'], r['FILEPATH'], r['VIDEOFORMAT'], r['VIDEOBITRATE'], r['AUDIOFORMAT'],
                r['AUDIOBITRATE'], r['RESOLUTION'], r['FRAMERATE'], r['LANGUAGES'], r['SUBTITLES'],
                r['FILESIZE'], r['DISKS'], r['PICTURESTATUS'], r['NBEXTRAS'], r['PICTURENAME']
            ]

            cur.execute(insert_sql, values)
            migrated += 1
        except Exception as e:
            skipped += 1
            report['errors'].append(f'NUM {r["NUM"]}: {e}')

    report['rows_migrated'] = migrated
    report['rows_skipped'] = skipped

    # Reemplazar tablas: renombrar la tabla actual movies a backup y renombrar movies_new -> movies
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    # Si source_table era 'movies', significa que estamos migrando la tabla actual
    if source_table == 'movies':
        cur.execute('ALTER TABLE movies RENAME TO movies_old')
    else:
        # existe movies_old, renombrar la tabla movies actual a movies_old_backup_TIMESTAMP
        cur.execute(f"ALTER TABLE movies RENAME TO movies_old_backup_{timestamp}")
    cur.execute('ALTER TABLE movies_new RENAME TO movies')
    conn.commit()
    print(f'Migración completada: {migrated} filas migradas, {skipped} saltadas.')

    # Guardar informe
    report_name = f'migrate_dates_{datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")}.json'
    report_path = os.path.join(REPORTS_DIR, report_name)
    with open(report_path, 'w', encoding='utf-8') as rf:
        json.dump(report, rf, ensure_ascii=False, indent=2)
    print(f'Informe guardado en: {report_path}')

except Exception as e:
    conn.rollback()
    report['errors'].append(str(e))
    print(f'Error durante migración: {e}')
    raise
finally:
    cur.close()
    conn.close()

print('Script finalizado.')
