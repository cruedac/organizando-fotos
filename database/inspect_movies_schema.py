import sqlite3, os
DB='data/multimedia.db'
if not os.path.exists(DB):
    print('DB not found:', DB)
    raise SystemExit(1)
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
cur=conn.cursor()
for tbl in ('movies_old','movies'):
    try:
        cur.execute("PRAGMA table_info(%s)"%tbl)
        cols=cur.fetchall()
        print('TABLE:',tbl,'columns:',len(cols))
        for c in cols:
            print('  ',c['cid'],c['name'],c['type'])
        cur.execute(f"SELECT * FROM {tbl} LIMIT 1")
        row=cur.fetchone()
        if row:
            print('First row column count:', len(row.keys()))
            print('Keys:', row.keys())
        else:
            print('No rows in',tbl)
    except Exception as e:
        print('Error for',tbl,':',e)
print('done')
conn.close()
