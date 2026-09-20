import json, io, gzip, collections, os
from urllib.parse import urlparse

# --- MVP mdl_counsel layer ---
base = "C:/Users/firas/Downloads/SCRAPE/sources/mdl_counsel_20260919/"
for f in ["attorneys.jsonl", "firms.jsonl", "parties.jsonl", "edges.jsonl", "seeds.jsonl", "unresolved.jsonl"]:
    p = base + f
    if not os.path.exists(p):
        print(f, "MISSING")
        continue
    n = 0
    first = None
    with io.open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                n += 1
                if first is None:
                    first = json.loads(line)
    print(f, "rows=", n, "keys=", sorted(first.keys()) if first else None)
    if first:
        print("   sample:", json.dumps(first)[:400])

p = base + "attorneys.jsonl"
full = 0
nameonly = 0
mdls = set()
with io.open(p, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        keys = set(o.keys())
        if o.get("cl_attorney_id") or o.get("attorney_id"):
            full += 1
        else:
            nameonly += 1
print("attorneys with an id:", full, "without:", nameonly)

p = base + "coverage.json"
if os.path.exists(p):
    print("coverage.json:", json.dumps(json.load(io.open(p, "r", encoding="utf-8")))[:2000])

p = base + "validation.json"
if os.path.exists(p):
    print("validation.json:", json.dumps(json.load(io.open(p, "r", encoding="utf-8")))[:1500])

# --- court spine 9 placeholders detail ---
print()
spine = [json.loads(l) for l in io.open("C:/Users/firas/Downloads/SCRAPE/sources/court_spine_20260919/courts.jsonl", "r", encoding="utf-8") if l.strip()]
byid = {c["id"]: c for c in spine}
for i in ["bapma", "californiad", "illinoisd", "ohiod", "okwd", "pennsylvaniad", "reglrailreorgct", "tennessed", "usjc"]:
    c = byid.get(i)
    print(i, "in_use=", c.get("in_use"), "end_date=", c.get("end_date"), "jt=", c.get("jurisdiction_type"), "website=", c.get("website"))

print()
for c in spine:
    w = (c.get("website") or "")
    if "txs.uscourts.gov" in w or "txsb" == c.get("id") or "txsd" == c.get("id"):
        print("TX:", c.get("id"), c.get("name"), c.get("website"))

# --- worktree copy diff on mdl_master_docket_id ---
a = "C:/Users/firas/Downloads/SW-BULK/catalog/matters.json"
b = "C:/Users/firas/Downloads/SW-BULK/.worktrees/batch2-corpus-execution/catalog/matters.json"
if os.path.exists(b):
    A = json.load(io.open(a, "r", encoding="utf-8"))
    B = json.load(io.open(b, "r", encoding="utf-8"))
    print()
    print("main catalog/matters.json rows:", len(A), " worktree rows:", len(B))
    da = {x["docket_id"]: x for x in A}
    db = {x["docket_id"]: x for x in B}
    diff = [k for k in da if k in db and da[k].get("mdl_master_docket_id") != db[k].get("mdl_master_docket_id")]
    print("docket_ids differing on mdl_master_docket_id:", len(diff))
    print("main non-null mdl_master_docket_id:", sum(1 for x in A if x.get("mdl_master_docket_id")))
    print("worktree non-null:", sum(1 for x in B if x.get("mdl_master_docket_id")))
else:
    print()
    print("worktree catalog/matters.json MISSING at", b)
