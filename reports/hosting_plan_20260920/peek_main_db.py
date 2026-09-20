"""Read-only: does the main directory database record where each row came from, well enough to build an export copy without the
restricted sources? Prints table names with row counts and, for provenance-looking columns, the most common values."""
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / 'delivery/archive-directory/directory.sqlite3'
HINTS = ('source', 'provider', 'origin', 'license', 'licence', 'collection', 'dataset', 'corpus')


def main():
    db = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%\\_fts%' ESCAPE '\\' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    for table in tables:
        columns = [row[1] for row in db.execute('PRAGMA table_info("%s")' % table)]
        try:
            count = db.execute('SELECT max(rowid) FROM "%s"' % table).fetchone()[0]
        except sqlite3.DatabaseError:
            count = None
        print('%-34s ~%s rows  %s' % (table, count, ', '.join(columns)[:150]))
        for column in columns:
            if any(hint in column.lower() for hint in HINTS) and not column.lower().endswith(('_url', '_id', 'url', '_json', '_path')):
                try:
                    rows = db.execute('SELECT "%s", count(*) FROM "%s" GROUP BY 1 ORDER BY 2 DESC LIMIT 10' % (column, table)).fetchall()
                except sqlite3.DatabaseError as error:
                    rows = [('error: %s' % error, 0)]
                print('    %s:' % column, '; '.join('%s=%s' % (str(value)[:48], n) for value, n in rows))


if __name__ == '__main__':
    main()
