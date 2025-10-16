import sqlite3, os, json
DB='data/multimedia.db'
conn=sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur=conn.cursor()
# Buscar extras con MOVIENUM no presente en movies
cur.execute('SELECT e.NUM, e.MOVIENUM, e.TITLE FROM extras e LEFT JOIN movies m ON e.MOVIENUM = m.NUM WHERE m.NUM IS NULL')
rows = cur.fetchall()
print('Orphan extras count:', len(rows))
for r in rows[:50]:
    print('NUM', r['NUM'], 'MOVIENUM', r['MOVIENUM'], 'TITLE', r['TITLE'])
# Guardar informe
report = {
    'timestamp': __import__('datetime').datetime.utcnow().isoformat()+'Z',
    'orphan_extras_count': len(rows),
    'samples': [{ 'NUM': r['NUM'], 'MOVIENUM': r['MOVIENUM'], 'TITLE': r['TITLE']} for r in rows[:200]]
}
out = os.path.join('data','import_reports','orphan_extras_report.json')
with open(out,'w',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print('Informe guardado en', out)
conn.close()
