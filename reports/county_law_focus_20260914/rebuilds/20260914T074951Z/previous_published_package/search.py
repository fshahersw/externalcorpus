"""Search only the focused package, using the shared local archive text index."""
from __future__ import annotations

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]


def search(query, group=None, limit=10, exact=False, state=None):
    if exact:
        query = '"' + query.replace('"', '""') + '"'
    index = ROOT / "catalog/documents.sqlite3"
    if not index.exists() or not (PACKAGE / "focused.sqlite3").exists():
        raise RuntimeError("Keep this package inside the SCRAPE workspace with catalog/documents.sqlite3.")
    with closing(sqlite3.connect(index.as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute("ATTACH DATABASE ? AS focused", ((PACKAGE / "focused.sqlite3").as_uri() + "?mode=ro",))
        where, values = ["content_fts MATCH ?"], [query]
        if group:
            where.append("EXISTS (SELECT 1 FROM json_each(d.package_groups_json) WHERE value=?)")
            values.append(group)
        if state:
            where.append("lower(d.jurisdiction) LIKE ?")
            values.append("%" + state.lower() + "%")
        values.append(max(1, min(limit, 200)))
        sql = """SELECT d.package_group,d.package_groups_json,d.jurisdiction,d.title,d.source_url,
          d.raw_path,d.text_path,d.retrieved_at,d.capture_kind,d.content_kind,d.body_status,
          snippet(content_fts,0,'[',']',' … ',28) AS excerpt,bm25(content_fts) AS score
          FROM content_fts JOIN focused.documents d ON d.content_id=content_fts.rowid
          WHERE """ + " AND ".join(where) + " ORDER BY score,d.source_url LIMIT ?"
        results = [dict(row) for row in db.execute(sql, values)]
        for row in results:
            row["package_groups"] = json.loads(row.pop("package_groups_json"))
            if group:
                row["package_group"] = group
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="SQLite FTS5 query, or a phrase with --exact")
    parser.add_argument("--group", choices=("laws", "judges", "counties"))
    parser.add_argument("--state", help="Filter recorded jurisdiction text, e.g. Arizona or AZ")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--exact", action="store_true")
    args = parser.parse_args()
    try:
        result = search(args.query, args.group, args.limit, args.exact, args.state)
    except (sqlite3.Error, RuntimeError) as exc:
        parser.exit(1, f"Search failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
