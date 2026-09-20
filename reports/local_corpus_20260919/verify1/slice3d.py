import json, io, glob, collections
from urllib.parse import urlparse

ROOT = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/court_expansion_file_download_v2_4_2026-08-20/"
paths = sorted(glob.glob(ROOT + "wave_*/court_file_download_results_v2.jsonl"))
P2 = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/state_trial_court_acquisition_v1_2026-08-20/artifact_download_results_v1.jsonl"


def host(u):
    return (urlparse(u or "").hostname or "").lower()


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

sp = {}
for c in spine:
    h = host(c.get("website"))
    if h:
        sp.setdefault(h, []).append(c)

print("spine hosts (no strip):", len(sp))
# uscourts.gov subdomain single-court hosts
fed_single = {h: cs[0] for h, cs in sp.items() if len(cs) == 1 and h.endswith(".uscourts.gov")}
fed_multi = {h: cs for h, cs in sp.items() if len(cs) > 1 and h.endswith(".uscourts.gov")}
print("single-court *.uscourts.gov hosts:", len(fed_single), " multi-court *.uscourts.gov hosts:", len(fed_multi))
print("  multi examples:", [(h, [c.get("id") for c in cs]) for h, cs in list(fed_multi.items())[:10]])
byjt = collections.Counter(c.get("jurisdiction_type") for c in fed_single.values())
print("  single-court fed by jurisdiction_type:", dict(byjt))

# any spine host containing 'txs.'
print("spine hosts with txs:", [h for h in sp if "txs" in h])
print("spine hosts with txcourts:", [(h, len(sp[h])) for h in sp if "txcourts" in h])

for label, rows in (("court_expansion", ce), ("state_trial", st), ("combined", ce + st)):
    dl = [o for o in rows if o.get("download_status") == "downloaded"]
    m = 0
    m_excl = 0
    courts = set()
    fedfiles = 0
    fedcourts = set()
    amb = 0
    for o in dl:
        h = host(o.get("final_url") or o.get("download_url") or o.get("source_url"))
        if h in sp:
            m += 1
            if h not in ("www.uscourts.gov", "uscourts.gov"):
                m_excl += 1
                for c in sp[h]:
                    courts.add(c.get("id"))
                if len(sp[h]) > 1:
                    amb += 1
        if h in fed_single:
            fedfiles += 1
            fedcourts.add(fed_single[h].get("id"))
    print()
    print(label, "downloaded:", len(dl))
    print("  match any spine host:", m, "| excl bare uscourts.gov:", m_excl, "-> courts:", len(courts))
    print("  files on ambiguous multi-court hosts:", amb)
    print("  files on single-court *.uscourts.gov hosts:", fedfiles, "-> courts:", len(fedcourts))

# ALL rows (not just downloaded) of court expansion matching spine
allm = 0
for o in ce:
    h = host(o.get("final_url") or o.get("download_url") or o.get("source_url"))
    if h in sp:
        allm += 1
print()
print("court_expansion ALL rows matching spine host:", allm)
allm2 = 0
for o in ce + st:
    h = host(o.get("final_url") or o.get("download_url") or o.get("source_url"))
    if h in sp:
        allm2 += 1
print("combined ALL rows matching spine host:", allm2)
