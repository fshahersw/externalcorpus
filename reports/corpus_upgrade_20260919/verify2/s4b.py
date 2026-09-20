import json, collections, os, re

SUG = "C:/Users/firas/Downloads/SW-BULK/catalog/njmcl_registry_suggestions.json"
JCCP = "C:/Users/firas/Downloads/returnedfiles/ca_jccp_registry.jsonl"
MDL = "C:/Users/firas/Downloads/SCRAPE/sources/jpml_mdl_20260919/mdls.jsonl"

sug = json.load(open(SUG, encoding="utf-8"))
ent = {k: v for k, v in sug.items() if not k.startswith("__")}
print("suggestion entries:", len(ent), sorted(ent))
for k, v in ent.items():
    print(" ", k, "mdl_number=", v.get("mdl_number"), "master_docket_id=", v.get("master_docket_id"), "njmcl=", v.get("njmcl"))

reg = {}
for line in open(MDL, encoding="utf-8"):
    if line.strip():
        r = json.loads(line)
        reg[int(r["mdl_number"])] = (r.get("status"), r.get("title", "")[:50])
for n in (2741, 2738, 2740, 2848, 2782):
    print("registry has mdl", n, ":", reg.get(n))

# do njmcl slugs in suggestions exist in nodes?
import csv
nodes = list(csv.DictReader(open("C:/Users/firas/Downloads/SW-BULK/catalog/njmcl_nodes.csv", encoding="utf-8-sig")))
slugs = {r["id"].split(":", 1)[1] for r in nodes if r["type"] == "njmcl"}
for k, v in ent.items():
    s = v.get("njmcl")
    print("  njmcl slug", s, "in nodes:", s in slugs)
print("njjudge rows:", [r for r in nodes if r["type"] == "njjudge"][:9])

recs = [json.loads(l) for l in open(JCCP, encoding="utf-8") if l.strip()]
print("log values:", collections.Counter(r.get("log") for r in recs).most_common())
yrs = collections.Counter()
for r in recs:
    d = str(r.get("date_received") or "")
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", d)
    if m:
        yrs[m.group(3)] += 1
    else:
        yrs["UNPARSED:" + d] += 1
print("date_received year tokens:", sorted(yrs.items()))
print("text field nonempty:", sum(1 for r in recs if r.get("text")))
print("title nonempty:", sum(1 for r in recs if r.get("title")))
# judges fragment stats
frag = 0
tot = 0
for r in recs:
    for j in (r.get("judges") or []):
        tot += 1
        if len(j.split()) < 3 or j.rstrip().endswith("."):
            frag += 1
print("judge strings total:", tot, "obvious fragments:", frag)

print()
print("=== licence search under SW-BULK ===")
hits = []
for root, dirs, files in os.walk("C:/Users/firas/Downloads/SW-BULK"):
    for f in files:
        lf = f.lower()
        if any(t in lf for t in ("licen", "terms", "copyright", "notice", "readme")):
            hits.append(os.path.join(root, f))
print(len(hits), hits[:40])
print("returnedfiles top-level:")
print(sorted(os.listdir("C:/Users/firas/Downloads/returnedfiles"))[:60])
