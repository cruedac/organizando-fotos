import sqlite3
import os
import sys

# Añadir el directorio raíz al path para importar módulos de la app
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Importar utilidad consolidada de normalización de fechas
from app.services.date_utils import normalize_date_value

DB = 'data/multimedia.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT * FROM movies_old LIMIT 10')
rows = cur.fetchall()
print('rows fetched:', len(rows))

for r in rows:
    try:
        # Usar utilidad consolidada en lugar de función duplicada
        dateadded = normalize_date_value(r['DATEADDED'])
        datewatched = normalize_date_value(r['DATEWATCHED'])
        
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
        print('NUM', r['NUM'], 'len(values)=', len(values))
    except Exception as e:
        print('NUM', r['NUM'], 'error building values:', e)

conn.close()
