import bz2, csv, json, collections, os

csv.field_size_limit(50 * 1024 * 1024)
BULK = "C:/Users/firas/Downloads/returnedfiles/bulk/"


def rd(path):
    f = bz2.open(path, "rt", encoding="utf-8", newline="")
    return csv.DictReader(f, doublequote=False, escapechar="\\"), f


cl = set(json.load(open("C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/verify2/overlap.json")))
r, f = rd(BULK + "financial-disclosures-2026-06-30.csv.bz2")
fd2person = {}
hdr_for_bridged = 0
years_bridged = collections.Counter()
for row in r:
    pid = int(row["person_id"])
    fd2person[row["id"].strip()] = pid
    if pid in cl:
        hdr_for_bridged += 1
        years_bridged[row["year"]] += 1
f.close()
print("headers belonging to bridged judges:", hdr_for_bridged)
print("disclosure years for bridged judges: min", min(years_bridged), "max", max(years_bridged))
print("year hist (bridged, last 10):", sorted(years_bridged.items())[-10:])

r, f = rd(BULK + "financial-disclosure-investments-2026-06-30.csv.bz2")
inv_bridged = 0
inv_total = 0
orphan = 0
for row in r:
    inv_total += 1
    fid = (row.get("financial_disclosure_id") or "").strip()
    p = fd2person.get(fid)
    if p is None:
        orphan += 1
    elif p in cl:
        inv_bridged += 1
f.close()
print("investment rows total:", inv_total, "attached to bridged judges:", inv_bridged, "orphan fd ids:", orphan)

print()
print("=== catalog freshness / draft signals ===")
for p in ("C:/Users/firas/Downloads/SW-BULK/missing_mdl.csv",
          "C:/Users/firas/Downloads/SW-BULK/catalog/catalog_report.csv",
          "C:/Users/firas/Downloads/SW-BULK/catalog/recap_prefix_manifest.json"):
    print("---", p)
    try:
        print(open(p, encoding="utf-8", errors="replace").read()[:1500])
    except Exception as e:
        print("ERR", e)
