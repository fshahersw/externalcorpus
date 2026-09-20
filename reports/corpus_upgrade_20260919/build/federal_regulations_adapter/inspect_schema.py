import sqlite3, json
from pathlib import Path

DB = Path('C:/Users/firas/Downloads/SCRAPE/sources/federal_regulations_20260919/regulations.sqlite3')
db = sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True)
for name, kind, sql in db.execute("SELECT name, type, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type, name"):
    print('==', kind, name)
    print(sql)
    if kind == 'table' and not name.endswith(('_data', '_idx', '_docsize', '_config', '_content')):
        try:
            n = db.execute('SELECT count(*) FROM "%s"' % name).fetchone()[0]
            print('  rows:', n)
            cur = db.execute('SELECT * FROM "%s" LIMIT 2' % name)
            cols = [c[0] for c in cur.description]
            for row in cur.fetchall():
                d = dict(zip(cols, row))
                for k, v in d.items():
                    if isinstance(v, str) and len(v) > 160:
                        d[k] = v[:160] + '...(%d)' % len(v)
                print('  ', json.dumps(d, ensure_ascii=False)[:1500])
        except Exception as e:
            print('  ERR', e)
db.close()

OUL = Path('C:/Users/firas/Downloads/SCRAPE/sources/open_us_law_20260918/catalog.sqlite3')
print('\n#### OUL exists:', OUL.exists())
if OUL.exists():
    db = sqlite3.connect(OUL.as_uri() + '?mode=ro', uri=True)
    for name, kind, sql in db.execute("SELECT name, type, sql FROM sqlite_master WHERE sql IS NOT NULL AND type in ('table','index') ORDER BY name"):
        if name.startswith('records_fts_'):
            continue
        print('==', kind, name)
        print(sql)
    cur = db.execute("SELECT rowid, id, source_id, title, length(text) FROM records WHERE source_id='CFR_T21_P314_S314_80' LIMIT 3")
    print(cur.fetchall())
    cur = db.execute("SELECT rowid, id, source_id, title, length(text) FROM records WHERE source_id='CFR_T16_P1115_S1115_4' LIMIT 3")
    print(cur.fetchall())
    db.close()
