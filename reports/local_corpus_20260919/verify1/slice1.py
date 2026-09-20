import gzip, json, io, collections

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
print("mdls rows:", len(mdls))
print("mdl status:", collections.Counter(m.get("status") for m in mdls))
print("mdls with master_docket:", sum(1 for m in mdls if m.get("master_docket")))
print("mdls with cl_court_id:", sum(1 for m in mdls if m.get("cl_court_id")))

# MDL key index
mdl_by_key = collections.defaultdict(list)
for m in mdls:
    c = m.get("cl_court_id")
    d = norm(m.get("master_docket"))
    if c and d:
        mdl_by_key[(c.lower(), d)].append(m)
dupes = {k: len(v) for k, v in mdl_by_key.items() if len(v) > 1}
print("mdl key collisions:", dupes)

matters = list(rd("matters"))
print("matters rows:", len(matters))

# join matters -> mdl
pairs = []
matter_to_mdl = {}
for mt in matters:
    c = (mt.get("court_id") or "").lower()
    d = norm(mt.get("docket_number"))
    k = (c, d)
    if k in mdl_by_key:
        for m in mdl_by_key[k]:
            pairs.append((mt, m))
            matter_to_mdl[mt["matter_id"]] = m
print("MATTER<->MDL pairs (normalized):", len(pairs))
print("distinct matters:", len(set(p[0]["matter_id"] for p in pairs)))
print("distinct mdls:", len(set(p[1]["id"] for p in pairs)))
print("status of joined mdls:", collections.Counter(p[1].get("status") for p in pairs))
term = sorted(set(p[1]["mdl_number"] for p in pairs if p[1].get("status") == "terminated"))
print("terminated mdl numbers joined:", term)

# exact (no normalization) join for comparison
mdl_exact = collections.defaultdict(list)
for m in mdls:
    c = m.get("cl_court_id")
    d = m.get("master_docket")
    if c and d:
        mdl_exact[(c.lower(), str(d).strip().lower())].append(m)
ex = 0
for mt in matters:
    k = ((mt.get("court_id") or "").lower(), str(mt.get("docket_number") or "").strip().lower())
    if k in mdl_exact:
        ex += 1
print("MATTER<->MDL pairs (exact string, no zero-pad norm):", ex)

# aliases
aliases = list(rd("matter_aliases"))
print("matter_aliases rows:", len(aliases))
print("alias namespaces:", collections.Counter(a.get("namespace") for a in aliases))
cl_docket_alias = [a for a in aliases if a.get("namespace") == "courtlistener_docket_id"]
print("matters covered by courtlistener_docket_id alias:", len(set(a["matter_id"] for a in cl_docket_alias)))
print("matters covered by ANY alias:", len(set(a["matter_id"] for a in aliases)))
alias_docket_ids = set(str(a["value"]) for a in cl_docket_alias)
print("distinct cl docket ids in aliases:", len(alias_docket_ids))

# catalog/matters.json docket_id overlap
cat = json.load(io.open("C:/Users/firas/Downloads/SW-BULK/catalog/matters.json", "r", encoding="utf-8"))
cat_ids = [c.get("docket_id") for c in cat]
cat_ids_nonnull = [str(x) for x in cat_ids if x is not None]
print("catalog/matters.json rows:", len(cat), "non-null docket_id:", len(cat_ids_nonnull),
      "distinct:", len(set(cat_ids_nonnull)))
overlap = set(cat_ids_nonnull) & alias_docket_ids
print("catalog docket_id values also in matter_aliases.courtlistener_docket_id:", len(overlap))

# relationships
rels = list(rd("matter_relationships"))
print("matter_relationships rows:", len(rels), collections.Counter(r.get("relationship_type") for r in rels))
mdl_matter_ids = set(matter_to_mdl.keys())
member_from = set(r["from_matter_id"] for r in rels)
to_ids = set(r["to_matter_id"] for r in rels)
print("distinct from_matter_id:", len(member_from), "distinct to_matter_id:", len(to_ids))
print("to_matter_id that are MDL-joined matters:", len(to_ids & mdl_matter_ids))
extra_members = member_from - mdl_matter_ids
print("member matters not already MDL-joined:", len(extra_members))

# masters.json
masters = json.load(io.open("C:/Users/firas/Downloads/SW-BULK/catalog/masters.json", "r", encoding="utf-8"))
print("masters.json rows:", len(masters))
print("masters with mdl_number non-null:", sum(1 for m in masters if m.get("mdl_number") not in (None, "")))
print("mdl_number values:", [m.get("mdl_number") for m in masters])
print("mdl_number types:", collections.Counter(type(m.get("mdl_number")).__name__ for m in masters))
