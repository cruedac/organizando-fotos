import re
s=open('database/migrate_dates.py','r',encoding='utf-8').read()
m=re.search(r"insert_sql = '''(.*?)'''", s, re.S|re.I)
if m:
    ins=m.group(1)
    print('Placeholder count:', ins.count('?'))
    print('Insert snippet:\n', ins)
else:
    print('insert_sql not found')
