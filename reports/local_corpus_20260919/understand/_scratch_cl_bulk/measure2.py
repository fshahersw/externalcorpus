# -*- coding: utf-8 -*-
import bz2, csv, json, os, time

BULK = "C:/Users/firas/Downloads/returnedfiles/bulk"
OUT = os.path.dirname(os.path.abspath(__file__))

def reader(fname):
    f = bz2.open(os.path.join(BULK, fname), mode="rt", encoding="utf-8", newline="")
    r = csv.reader(f, escapechar="\\", doublequote=False, strict=False)
    return f, r

result = {}

# --- courts header + jurisdiction breakdown + id sample ---
f, r = reader("courts-2026-06-30.csv.bz2")
header = next(r)
idx = {c: i for i, c in enumerate(header)}
court_ids = set()
juris = {}
for row in r:
    if len(row) != len(header):
        continue
    court_ids.add(row[idx["id"]])
    j = row[idx.get("jurisdiction", 0)]
    juris[j] = juris.get(j, 0) + 1
f.close()
result["courts_header"] = header
result["courts_jurisdiction_counts"] = juris
result["courts_id_count"] = len(court_ids)

# --- courthouses header + address completeness ---
f, r = reader("courthouses-2026-06-30.csv.bz2")
header2 = next(r)
idx2 = {c: i for i, c in enumerate(header2)}
n = 0
addr1 = addr2 = city = county = bldg = seat = poa = 0
ch_court_ids = set()
samples = []
for row in r:
    n += 1
    if len(row) != len(header2):
        continue
    def val(name):
        i = idx2.get(name)
        return row[i] if i is not None else ""
    if val("address1").strip(): addr1 += 1
    if val("address2").strip(): addr2 += 1
    if val("city").strip(): city += 1
    if val("county").strip(): county += 1
    if val("building_name").strip(): bldg += 1
    if val("court_seat").strip().lower() in ("t","true","1"): seat += 1
    cid = val("court_id")
    if cid:
        ch_court_ids.add(cid)
    if len(samples) < 5:
        samples.append(dict(zip(header2, row)))
f.close()
result["courthouses_header"] = header2
result["courthouses_rows"] = n
result["courthouses_address1_nonblank"] = addr1
result["courthouses_address2_nonblank"] = addr2
result["courthouses_city_nonblank"] = city
result["courthouses_county_nonblank"] = county
result["courthouses_building_name_nonblank"] = bldg
result["courthouses_court_seat_true"] = seat
result["courthouses_distinct_court_id"] = len(ch_court_ids)
result["courthouses_samples"] = samples

with open(os.path.join(OUT, "measure2.json"), "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=2, default=str)
print(json.dumps({k:v for k,v in result.items() if k not in ("courthouses_samples",)}, indent=2, default=str)[:3000])
print("DONE")
