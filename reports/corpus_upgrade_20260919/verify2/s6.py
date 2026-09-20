import bz2, csv, io, json, collections, sys, os

csv.field_size_limit(10 * 1024 * 1024)
BULK = "C:/Users/firas/Downloads/returnedfiles/bulk/"
HDR = BULK + "financial-disclosures-2026-06-30.csv.bz2"
INV = BULK + "financial-disclosure-investments-2026-06-30.csv.bz2"


def reader(path):
    f = bz2.open(path, "rt", encoding="utf-8", newline="")
    return csv.DictReader(f), f


print("=== headers ===")
r, f = reader(HDR)
print("cols:", r.fieldnames)
n = 0
persons = set()
nullperson = 0
years = collections.Counter()
rtypes = collections.Counter()
for row in r:
    n += 1
    p = (row.get("person_id") or "").strip()
    if p:
        persons.add(p)
    else:
        nullperson += 1
    years[(row.get("year") or "").strip()] += 1
    rtypes[(row.get("report_type") or "").strip()] += 1
f.close()
print("header rows:", n, "distinct person_id:", len(persons), "null person_id:", nullperson)
print("years:", sorted(years.items())[:40])
print("report_type:", rtypes.most_common())

print()
print("=== investments ===")
r, f = reader(INV)
print("cols:", r.fieldnames)
m = 0
fdids = set()
desc = 0
gv = collections.Counter()
inc = collections.Counter()
red = 0
infer = 0
for row in r:
    m += 1
    fdids.add((row.get("financial_disclosure_id") or "").strip())
    if (row.get("description") or "").strip():
        desc += 1
    gv[(row.get("gross_value_code") or "").strip()] += 1
    inc[(row.get("income_during_reporting_period_code") or "").strip()] += 1
    if (row.get("redacted") or "").strip().lower() in ("t", "true", "1"):
        red += 1
    if (row.get("has_inferred_values") or "").strip().lower() in ("t", "true", "1"):
        infer += 1
f.close()
print("investment rows:", m, "distinct financial_disclosure_id:", len(fdids))
print("description nonempty:", desc)
print("gross_value_code:", gv.most_common(30))
print("income code:", inc.most_common(30))
print("redacted true:", red, "has_inferred_values true:", infer)

out = {"header_rows": n, "persons": sorted(persons), "inv_rows": m}
with open("C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/verify2/fd_persons.json", "w", encoding="utf-8") as fh:
    json.dump(out, fh)
print("wrote persons file")
