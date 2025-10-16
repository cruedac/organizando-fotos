import sqlite3, os
DB='data/multimedia.db'
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
cur=conn.cursor()
cur.execute('SELECT * FROM movies_old LIMIT 10')
rows=cur.fetchall()
print('rows fetched:', len(rows))
for r in rows:
    def norm_date(val):
        if val is None:
            return None
        s = str(val).strip()
        if s == '' or s.lower() == 'none':
            return None
        try:
            from datetime import datetime
            datetime.fromisoformat(s)
            return s
        except Exception:
            if len(s) >= 10:
                candidate = s[:10]
                try:
                    datetime.fromisoformat(candidate)
                    return candidate
                except Exception:
                    return None
            return None
    try:
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
        print('NUM', r['NUM'], 'len(values)=', len(values))
    except Exception as e:
        print('NUM', r['NUM'], 'error building values:', e)

conn.close()
