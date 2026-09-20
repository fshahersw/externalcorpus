import json, io, glob, collections
from urllib.parse import urlparse

ROOT = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/court_expansion_file_download_v2_4_2026-08-20/"
paths = sorted(glob.glob(ROOT + "wave_*/court_file_download_results_v2.jsonl"))
P2 = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/state_trial_court_acquisition_v1_2026-08-20/artifact_download_results_v1.jsonl"


def host(u, strip):
    h = (urlparse(u or "").hostname or "").lower()
    if strip and h.startswith("www."):
        h = h[4:]
    return h


ce, st = [], []
for p in paths:
    with io.open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                ce.append(json.loads(line))
with io.open(P2, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            st.append(json.loads(line))
spine = []
with io.open("C:/Users/firas/Downloads/SCRAPE/sources/court_spine_20260919/courts.jsonl", "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            spine.append(json.loads(line))

for strip in (True,):
    sp = {}
    for c in spine:
        h = host(c.get("website"), strip)
        if h:
            sp.setdefault(h, []).append(c)
    bare = "uscourts.gov"
    for label, rows in (("court_expansion", ce), ("combined", ce + st)):
        dl = [o for o in rows if o.get("download_status") == "downloaded"]
        m = m_excl = amb = 0
        courts = set()
        for o in dl:
            h = host(o.get("final_url") or o.get("download_url") or o.get("source_url"), strip)
            if h in sp:
                m += 1
                if h != bare:
                    m_excl += 1
                    for c in sp[h]:
                        courts.add(c.get("id"))
                    if len(sp[h]) > 1:
                        amb += 1
        print("strip", label, "match:", m, "excl bare:", m_excl, "courts:", len(courts), "ambiguous rows:", amb)

# breakdown of the 107 reached single-court federal courts
sp0 = {}
for c in spine:
    h = host(c.get("website"), False)
    if h:
        sp0.setdefault(h, []).append(c)
fed_single = {h: cs[0] for h, cs in sp0.items() if len(cs) == 1 and h.endswith(".uscourts.gov")}
print()
print("single-court fed domains in spine:", len(fed_single),
      collections.Counter(c.get("jurisdiction_type") for c in fed_single.values()))
reached = collections.Counter()
reached_files = collections.Counter()
for o in ce + st:
    if o.get("download_status") != "downloaded":
        continue
    h = host(o.get("final_url") or o.get("download_url") or o.get("source_url"), False)
    if h in fed_single:
        c = fed_single[h]
        reached[(c.get("jurisdiction_type"))] += 0
        reached_files[c.get("jurisdiction_type")] += 1
hit = set()
for o in ce + st:
    if o.get("download_status") != "downloaded":
        continue
    h = host(o.get("final_url") or o.get("download_url") or o.get("source_url"), False)
    if h in fed_single:
        hit.add(fed_single[h].get("id"))
print("fed single-court courts actually reached by a downloaded file:", len(hit))
print("files by jurisdiction_type on those domains:", dict(reached_files))
jt = collections.Counter()
idmap = {c.get("id"): c for c in spine}
for i in hit:
    jt[idmap[i].get("jurisdiction_type")] += 1
print("reached courts by jurisdiction_type:", dict(jt))

# jurisdiction_type labels
labels = {}
for c in spine:
    labels[c.get("jurisdiction_type")] = c.get("jurisdiction_type_label")
print("labels:", labels)
