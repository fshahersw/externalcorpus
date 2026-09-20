import json, io, glob, collections
from urllib.parse import urlparse

ROOT = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/court_expansion_file_download_v2_4_2026-08-20/"
paths = sorted(glob.glob(ROOT + "wave_*/court_file_download_results_v2.jsonl"))
P2 = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/state_trial_court_acquisition_v1_2026-08-20/artifact_download_results_v1.jsonl"


def host(u, strip_www):
    h = (urlparse(u or "").hostname or "").lower()
    if strip_www and h.startswith("www."):
        h = h[4:]
    return h


rows = []
for p in paths:
    with io.open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(("ce", json.loads(line)))
with io.open(P2, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            rows.append(("st", json.loads(line)))

spine = []
with io.open("C:/Users/firas/Downloads/SCRAPE/sources/court_spine_20260919/courts.jsonl", "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            spine.append(json.loads(line))

for strip in (False, True):
    for urlfield in ("source_url", "final_url"):
        sp = {}
        for c in spine:
            h = host(c.get("website"), strip)
            if h:
                sp.setdefault(h, []).append(c)
        hostset_all = collections.Counter()
        hostset_dl = collections.Counter()
        matched = 0
        matched_excl = 0
        courts_excl = set()
        unambig = 0
        bare = "uscourts.gov" if strip else "www.uscourts.gov"
        for src, o in rows:
            h = host(o.get(urlfield) or o.get("download_url") or o.get("source_url"), strip)
            hostset_all[h] += 1
            if o.get("download_status") != "downloaded":
                continue
            hostset_dl[h] += 1
            if h in sp:
                matched += 1
                if h != bare:
                    matched_excl += 1
                    for c in sp[h]:
                        courts_excl.add(c.get("id"))
                    if len(sp[h]) == 1:
                        unambig += 1
        print("strip_www=", strip, "url_field=", urlfield)
        print("   distinct hosts all rows:", len(hostset_all), " downloaded rows:", len(hostset_dl))
        print("   downloaded matching spine host:", matched,
              "| excl bare uscourts.gov:", matched_excl,
              "-> distinct courts:", len(courts_excl),
              "| single-court-host files:", unambig)
    print()

# court-expansion only host counts
ce_hosts = collections.Counter()
for src, o in rows:
    if src != "ce":
        continue
    h = host(o.get("source_url"), False)
    ce_hosts[h] += 1
print("court-expansion-only distinct hosts (source_url, no strip, all rows):", len(ce_hosts))
ce_hosts2 = collections.Counter()
for src, o in rows:
    if src != "ce":
        continue
    h = host(o.get("final_url") or o.get("source_url"), False)
    ce_hosts2[h] += 1
print("court-expansion-only distinct hosts (final_url, no strip, all rows):", len(ce_hosts2))

# federal single-court domain counts by jurisdiction_type / system
sp = {}
for c in spine:
    h = host(c.get("website"), False)
    if h:
        sp.setdefault(h, []).append(c)
single_fed = collections.Counter()
for h, cs in sp.items():
    if len(cs) == 1 and h.endswith("uscourts.gov") and h != "www.uscourts.gov" and h != "uscourts.gov":
        single_fed[cs[0].get("jurisdiction_type")] += 1
print("single-court *.uscourts.gov domains by jurisdiction_type:", dict(single_fed))

# txs.uscourts.gov
print("txs.uscourts.gov ->", [(c.get("id"), c.get("name")) for c in sp.get("txs.uscourts.gov", [])])
print("txcourts.gov ->", len(sp.get("txcourts.gov", [])), [c.get("id") for c in sp.get("txcourts.gov", [])][:25])
