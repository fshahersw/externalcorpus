# -*- coding: utf-8 -*-
import bz2, csv, json, os, time

BULK = "C:/Users/firas/Downloads/returnedfiles/bulk"
OUT = os.path.dirname(os.path.abspath(__file__))

def reader(fname):
    f = bz2.open(os.path.join(BULK, fname), mode="rt", encoding="utf-8", newline="")
    r = csv.reader(f, escapechar="\\", doublequote=False, strict=False)
    return f, r

result = {}

def distinct_person(fname, person_col):
    f, r = reader(fname)
    header = next(r)
    idx = header.index(person_col)
    s = set()
    n = 0
    for row in r:
        n += 1
        if len(row) == len(header) and row[idx]:
            s.add(row[idx])
    f.close()
    return n, len(s)

specs = [
    ("people-db-political-affiliations-2026-06-30.csv.bz2", "person_id"),
    ("financial-disclosures-2026-06-30.csv.bz2", "person_id"),
    ("search_opinioncluster_panel-2026-06-30.csv.bz2", "person_id"),
    ("people-db-races-2026-06-30.csv.bz2", "person_id"),
    ("people-db-educations-2026-06-30.csv.bz2", "person_id"),
]
for fn, col in specs:
    n, d = distinct_person(fn, col)
    result[fn] = {"rows": n, "distinct_" + col: d}
    print(fn, n, d)

with open(os.path.join(OUT, "measure4.json"), "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=2)
print("DONE")
