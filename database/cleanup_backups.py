"""
Script para listar y opcionalmente eliminar backups y tablas antiguas generadas por la migración.
Uso:
  python database/cleanup_backups.py         # lista backups y tablas movies_old*
  python database/cleanup_backups.py --delete  # elimina backups y tables movies_old*
"""
import argparse, os, sqlite3
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--delete', action='store_true', help='Eliminar backups y tablas movies_old*')
args = parser.parse_args()

DB='data/multimedia.db'
if not os.path.exists(DB):
    print('DB not found:', DB)
    raise SystemExit(1)

print('DB:', DB)

# List backup files
backup_dir = os.path.join('data','backup')
backups = []
if os.path.exists(backup_dir):
    backups = sorted([os.path.join(backup_dir,f) for f in os.listdir(backup_dir) if f.endswith('.db')])
print('Backups found:', len(backups))
for b in backups[:20]:
    print('  ', b)

conn = sqlite3.connect(DB)
cur = conn.cursor()
# List tables named movies_old*
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'movies_old%'")
old_tables = [r[0] for r in cur.fetchall()]
print('Old movies tables:', old_tables)

if not args.delete:
    print('\nRun with --delete to remove these backups and tables (irreversible).')
    conn.close()
    raise SystemExit(0)

# Delete backups
for b in backups:
    try:
        os.remove(b)
        print('Deleted backup', b)
    except Exception as e:
        print('Error deleting', b, e)

# Drop old tables
for t in old_tables:
    try:
        cur.execute(f'DROP TABLE IF EXISTS {t}')
        print('Dropped table', t)
    except Exception as e:
        print('Error dropping table', t, e)

conn.commit()
conn.close()
print('Cleanup completed at', datetime.utcnow().isoformat()+'Z')
