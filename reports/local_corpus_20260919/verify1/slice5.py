import gzip, json, io, collections
from urllib.parse import urlparse

REL = "C:/Users/firas/Downloads/SW-BULK/AWS-BATCH1-DOCKETS/releases/b2b-cdbb8d040b95c7b65cfc/"


def rd(name):
    with gzip.open(REL + name + ".jsonl.gz", "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def rdj(path):
    with io.open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def norm(dn):
    if dn is None:
        return None
    s = str(dn).strip().lower()
    if not s:
        return None
    parts = s.split("-")
    try:
        parts[-1] = str(int(parts[-1]))
    except Exception:
        return s
    return "-".join(parts)


mdls = list(rdj("C:/Users/firas/Downloads/SCRAPE/sources/jpml_mdl_20260919/mdls.jsonl"))
mdl_by_key = {}
for m in mdls:
    c = m.get("cl_court_id")
    d = norm(m.get("master_docket"))
    if c and d:
        mdl_by_key[(c.lower(), d)] = m

matters = list(rd("matters"))
matter_mdl = {}
for mt in matters:
    k = ((mt.get("court_id") or "").lower(), norm(mt.get("docket_number")))
    if k in mdl_by_key:
        matter_mdl[mt["matter_id"]] = mdl_by_key[k]["id"]
print("direct MDL-linked matters:", len(matter_mdl))

rels = list(rd("matter_relationships"))
extended = dict(matter_mdl)
added = 0
for r in rels:
    if r.get("relationship_type") != "member_of_mdl":
        continue
    tgt = r["to_matter_id"]
    if tgt in matter_mdl and r["from_matter_id"] not in extended:
        extended[r["from_matter_id"]] = matter_mdl[tgt]
        added += 1
print("member matters added via member_of_mdl edges to an MDL-linked parent:", added,
      "-> extended MDL-linked matters:", len(extended))
orphan_targets = set(r["to_matter_id"] for r in rels) - set(matter_mdl)
print("member_of_mdl target matters NOT in the 59 crosswalk:", len(orphan_targets))

app = list(rd("counsel_appearances"))
print()
print("counsel_appearances rows:", len(app))
print("distinct matters in appearances:", len(set(a["matter_id"] for a in app)))
print("distinct firm_id:", len(set(a.get("firm_id") for a in app)))
print("firm counts:", collections.Counter(a.get("firm_id") for a in app).most_common())
print("roles:", collections.Counter(a.get("role") for a in app).most_common())
print("distinct role spellings:", len(set(a.get("role") for a in app)))
print("appearances with attorney_id:", sum(1 for a in app if a.get("attorney_id")))
print("appearances on MDL-linked matters (direct 59):",
      sum(1 for a in app if a["matter_id"] in matter_mdl))
print("appearances on MDL-linked matters (extended incl member edges):",
      sum(1 for a in app if a["matter_id"] in extended))

parties = list(rd("parties"))
print()
print("parties rows:", len(parties))
print("distinct matters in parties:", len(set(p["matter_id"] for p in parties)))
print("parties on MDL-linked matters (direct 59):", sum(1 for p in parties if p["matter_id"] in matter_mdl))
print("parties on MDL-linked (extended):", sum(1 for p in parties if p["matter_id"] in extended))

atts = list(rd("attorneys"))
firms = list(rd("firms"))
print()
print("attorneys rows:", len(atts), "keys:", sorted(atts[0].keys()))
print("attorney_id looks like uuid:", all(len(a["attorney_id"]) == 36 and a["attorney_id"].count("-") == 4 for a in atts))
print("any courtlistener key in attorneys:", any("courtlistener" in k or k.endswith("cl_id") for a in atts for k in a))
print("firms rows:", len(firms), [f["firm_id"] for f in firms])
print("raw_firm_name distinct:", len(set(a.get("raw_firm_name") for a in app)))

# matters in appearances/parties union
u = set(a["matter_id"] for a in app) | set(p["matter_id"] for p in parties)
print("union matters (appearances+parties):", len(u))
print("of which MDL-linked (direct):", len(u & set(matter_mdl)))
print("of which MDL-linked (extended):", len(u & set(extended)))
print("distinct MDLs touched by appearances (direct):",
      len(set(matter_mdl[a['matter_id']] for a in app if a['matter_id'] in matter_mdl)))
print("distinct MDLs touched (extended):",
      len(set(extended[a['matter_id']] for a in app if a['matter_id'] in extended)))
