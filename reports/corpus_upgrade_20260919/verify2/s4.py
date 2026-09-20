import json, csv, collections, io

NODES = "C:/Users/firas/Downloads/SW-BULK/catalog/njmcl_nodes.csv"
EDGES = "C:/Users/firas/Downloads/SW-BULK/catalog/njmcl_edges.csv"
SUG = "C:/Users/firas/Downloads/SW-BULK/catalog/njmcl_registry_suggestions.json"
JCCP = "C:/Users/firas/Downloads/returnedfiles/ca_jccp_registry.jsonl"

print("=== NJ nodes ===")
rows = list(csv.DictReader(open(NODES, encoding="utf-8-sig")))
print("cols:", list(rows[0].keys()))
print("rows:", len(rows))
types = collections.Counter(r.get("type") for r in rows)
print("types:", types.most_common())
njmcl = [r for r in rows if r.get("type") == "njmcl"]
fill = collections.Counter()
for r in njmcl:
    for k, v in r.items():
        if v not in (None, "", "[]", "null"):
            fill[k] += 1
print("njmcl count:", len(njmcl), "fill:", sorted(fill.items()))
print("sample njmcl:", json.dumps(njmcl[0], indent=1)[:1200])
urls = [r.get("source_url", "") for r in njmcl]
print("njcourts.gov urls:", sum(1 for u in urls if "njcourts.gov" in u), "distinct:", len(set(urls)))
arch = collections.Counter(r.get("archived") for r in njmcl)
print("archived:", arch.most_common())
dd = [r.get("designation_date") for r in njmcl]
print("designation_date nonempty:", sum(1 for d in dd if d), "sample:", dd[:6])
print("counties:", sorted({r.get("county") for r in njmcl}))
print("judge nonempty:", sum(1 for r in njmcl if r.get("judge")))
print("doc_count nonempty:", sum(1 for r in njmcl if r.get("document_count")))

e = list(csv.DictReader(open(EDGES, encoding="utf-8-sig")))
print("edges rows:", len(e), "cols:", list(e[0].keys()))
print("edge relations:", collections.Counter(x.get("relation") or x.get("type") for x in e).most_common())

sug = json.load(open(SUG, encoding="utf-8"))
print("suggestions type:", type(sug).__name__)
s = json.dumps(sug)
print("suggestions len:", len(s))
import re
print("mdl numbers mentioned:", sorted(set(re.findall(r"\b(2741|2738|2740|2848|2782)\b", s))))
print("all 4-digit MDL-ish tokens:", collections.Counter(re.findall(r"\"mdl[^\"]*\"\s*:\s*\"?(\d{3,4})", s)).most_common())
print(s[:1500])

print()
print("=== CA JCCP ===")
recs = [json.loads(l) for l in open(JCCP, encoding="utf-8") if l.strip()]
print("rows:", len(recs))
print("keys:", sorted({k for r in recs for k in r}))
jn = [r.get("jccp_no") for r in recs]
print("distinct jccp_no:", len({x for x in jn if x is not None}), "null:", sum(1 for x in jn if x in (None, "")))
cnt = collections.Counter()
counties = set()
withc = 0
for r in recs:
    c = r.get("counties") or []
    if c:
        withc += 1
        counties.update(c)
print("rows with non-empty counties:", withc, "distinct county names:", len(counties))
print(sorted(counties))
print("category:", collections.Counter(r.get("category") for r in recs).most_common())
dr = [r.get("date_received") for r in recs]
print("date_received nonempty:", sum(1 for d in dr if d), "samples:", dr[:8])
cn = sum(1 for r in recs if r.get("case_numbers"))
print("rows with case_numbers:", cn)
jud = sum(1 for r in recs if r.get("judges"))
print("rows with judges:", jud)
for tgt in ("4961", "4960"):
    for r in recs:
        if str(r.get("jccp_no")) == tgt:
            print(tgt, "judges:", r.get("judges"), "| counties:", r.get("counties"), "| title:", str(r.get("title"))[:80])
            break
# log year split
import datetime
old = new = bad = 0
for r in recs:
    d = r.get("date_received")
    if not d:
        bad += 1
        continue
    try:
        yy = int(str(d).split("/")[-1])
    except Exception:
        bad += 1
        continue
    yr = 2000 + yy if yy < 50 else 1900 + yy
    if yr <= 2017:
        old += 1
    else:
        new += 1
print("date_received <=2017:", old, ">=2018:", new, "unparsed:", bad)
print("sample record:", json.dumps(recs[0])[:900])
