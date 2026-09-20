import bz2, csv, json, collections

csv.field_size_limit(50 * 1024 * 1024)
BULK = "C:/Users/firas/Downloads/returnedfiles/bulk/"
HDR = BULK + "financial-disclosures-2026-06-30.csv.bz2"
INV = BULK + "financial-disclosure-investments-2026-06-30.csv.bz2"


def rd(path):
    f = bz2.open(path, "rt", encoding="utf-8", newline="")
    return csv.DictReader(f, doublequote=False, escapechar="\\"), f


r, f = rd(HDR)
n = 0
persons = set()
nullp = 0
years = collections.Counter()
rt = collections.Counter()
ids = set()
for row in r:
    n += 1
    p = (row.get("person_id") or "").strip()
    if p.isdigit():
        persons.add(int(p))
    else:
        nullp += 1
    ids.add((row.get("id") or "").strip())
    y = (row.get("year") or "").strip()
    years[y if y.isdigit() else "NONNUM"] += 1
    rt[(row.get("report_type") or "").strip()] += 1
f.close()
print("HDR rows (escape-aware):", n, "distinct id:", len(ids))
print("distinct person_id:", len(persons), "non-numeric/blank person_id rows:", nullp)
print("years:", sorted(years.items()))
print("report_type:", rt.most_common(12))

r, f = rd(INV)
m = 0
fd = set()
gv = collections.Counter()
red = 0
infer = 0
desc = 0
numericcols = collections.Counter()
for row in r:
    m += 1
    fd.add((row.get("financial_disclosure_id") or "").strip())
    g = (row.get("gross_value_code") or "").strip()
    gv[g] += 1
    if (row.get("redacted") or "").strip().lower() in ("t", "true", "1"):
        red += 1
    if (row.get("has_inferred_values") or "").strip().lower() in ("t", "true", "1"):
        infer += 1
    if (row.get("description") or "").strip():
        desc += 1
f.close()
print("INV rows (escape-aware):", m, "distinct financial_disclosure_id:", len(fd))
print("gross_value_code:", gv.most_common(20))
print("redacted:", red, "has_inferred_values:", infer, "description nonempty:", desc)

cl = set(int(x) for x in json.load(open("C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/verify2/cl_persons.json")))
print("judge_structured bridged cl_person ids:", len(cl))
ov = persons & cl
print("OVERLAP person_id in disclosures with bridged judges:", len(ov))
print("disclosure persons not bridged:", len(persons - cl))
# how many disclosure headers belong to bridged judges
print("share of bridged judges with a disclosure: %.1f%%" % (100.0 * len(ov) / len(cl)))
json.dump(sorted(ov), open("C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/verify2/overlap.json", "w"))
