import json, collections

DOC = "C:/Users/firas/Downloads/SW-BULK/catalog/documents.json"
MDL = "C:/Users/firas/Downloads/SCRAPE/sources/jpml_mdl_20260919/mdls.jsonl"

reg = {}
for line in open(MDL, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    reg[int(r["mdl_number"])] = r.get("status")
print("registry mdls:", len(reg))

docs = json.load(open(DOC, encoding="utf-8"))
print("total rows:", len(docs))

keys = set()
for d in docs[:200]:
    keys.update(d)

no_mdl = 0
per_mdl = collections.Counter()
both = 0
have_url = 0
have_sha = 0
cat = collections.Counter()
dates = []
nulldate = 0
sealed = 0
hv = 0
avail = 0
courts = collections.Counter()
srcs = collections.Counter()
mdl_raw_types = collections.Counter()
pacer = 0
mdocket = 0
dup_uid = collections.Counter()

for d in docs:
    m = d.get("mdl_number")
    mdl_raw_types[type(m).__name__] += 1
    if m is None or m == "":
        no_mdl += 1
    else:
        per_mdl[int(m)] += 1
    u = d.get("download_url")
    s = d.get("sha1")
    if u:
        have_url += 1
    if s:
        have_sha += 1
    if u and s:
        both += 1
    cat[d.get("doc_category")] += 1
    dt = d.get("entry_date_filed")
    if dt:
        dates.append(dt)
    else:
        nulldate += 1
    if d.get("is_sealed"):
        sealed += 1
    if d.get("high_value"):
        hv += 1
    if d.get("is_available"):
        avail += 1
    courts[d.get("court")] += 1
    srcs[d.get("source")] += 1
    if d.get("pacer_doc_id"):
        pacer += 1
    if d.get("master_docket_id"):
        mdocket += 1
    dup_uid[d.get("doc_uid")] += 1

print("mdl_number types:", dict(mdl_raw_types))
print("rows with no mdl_number:", no_mdl)
print("distinct mdl numbers in file:", len(per_mdl))
in_reg = {k: v for k, v in per_mdl.items() if k in reg}
print("mdl numbers in file that are in registry:", len(in_reg))
print("rows joining registry mdls:", sum(in_reg.values()))
print("per-mdl (in registry):", sorted((k, v, reg[k]) for k, v in in_reg.items()))
notreg = {k: v for k, v in per_mdl.items() if k not in reg}
print("mdl numbers NOT in registry:", sorted(notreg.items()))
print("rows not in registry (with mdl):", sum(notreg.values()))
print("download_url:", have_url, "sha1:", have_sha, "both:", both)
print("doc_category:", cat.most_common())
print("null entry_date_filed:", nulldate, "min:", min(dates), "max:", max(dates))
print("sealed:", sealed, "high_value:", hv, "is_available:", avail)
print("pacer_doc_id present:", pacer, "master_docket_id present:", mdocket)
print("distinct master_docket_id:", len({d.get('master_docket_id') for d in docs}))
print("distinct courts:", len(courts), courts.most_common(20))
print("source values:", srcs.most_common())
print("distinct doc_uid:", len(dup_uid), "dupe rows:", sum(v - 1 for v in dup_uid.values() if v > 1))
print("field keys sample:", sorted(keys))

pend = {k for k in in_reg if reg[k] == "pending"}
sub = collections.Counter()
subs_all = collections.Counter()
for d in docs:
    m = d.get("mdl_number")
    if not m:
        continue
    mi = int(m)
    c = d.get("doc_category")
    if c in ("settlement", "case_management_order", "bellwether"):
        if mi in pend:
            sub[c] += 1
        if mi in in_reg:
            subs_all[c] += 1
print("pending-registry-mdl subset:", sub.most_common(), "pending count:", len(pend), sorted(pend))
print("all-registry-mdl subset:", subs_all.most_common())
