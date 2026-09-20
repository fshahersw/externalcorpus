import json, io, os, glob, collections
from urllib.parse import urlparse

ROOT = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/court_expansion_file_download_v2_4_2026-08-20/"
paths = sorted(glob.glob(ROOT + "wave_*/court_file_download_results_v2.jsonl"))

n = 0
status = collections.Counter()
ext = collections.Counter()
sha_all = collections.Counter()
jur_empty = 0
jur_codes = collections.Counter()
lanes = collections.Counter()
hosts = collections.Counter()
dl_rows = []
artifacts = set()

for p in paths:
    with io.open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            n += 1
            artifacts.add(o.get("artifact_id"))
            st = o.get("download_status")
            status[st] += 1
            jc = o.get("jurisdiction_codes") or []
            if len(jc) == 0:
                jur_empty += 1
            for c in jc:
                jur_codes[c] += 1
            for la in (o.get("authority_lanes") or []):
                lanes[la] += 1
            e = (o.get("file_extension") or "").lower()
            ext[e] += 1
            s = o.get("sha256")
            if st == "downloaded":
                if s:
                    sha_all[s] += 1
                u = o.get("final_url") or o.get("download_url") or o.get("source_url") or ""
                h = (urlparse(u).hostname or "").lower()
                if h.startswith("www."):
                    h = h[4:]
                hosts[h] += 1
                dl_rows.append((h, o.get("artifact_id"), s))

print("court expansion manifest rows:", n, "distinct artifact_id:", len(artifacts))
print("download_status:", dict(status))
print("downloaded rows with sha256:", sum(sha_all.values()), "unique sha256:", len(sha_all))
dup_bytes = sum(v for v in sha_all.values() if v > 1) - sum(1 for v in sha_all.values() if v > 1)
print("duplicate-extra rows:", dup_bytes, "pct:", round(100.0 * dup_bytes / max(1, sum(sha_all.values())), 2))
print("jurisdiction_codes empty rows:", jur_empty, "distinct codes:", len(jur_codes))
print("rows with >=1 code:", n - jur_empty)
print("authority_lanes:", dict(lanes))
print("top extensions:", ext.most_common(12))
print("distinct hosts (downloaded, www-stripped):", len(hosts))

# state trial court manifest
p2 = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/state_trial_court_acquisition_v1_2026-08-20/artifact_download_results_v1.jsonl"
n2 = 0
st2 = collections.Counter()
first2 = None
hosts2 = collections.Counter()
dl2 = []
with io.open(p2, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        n2 += 1
        if first2 is None:
            first2 = o
        s = o.get("download_status") or o.get("status")
        st2[s] += 1
        if s == "downloaded":
            u = o.get("final_url") or o.get("download_url") or o.get("source_url") or ""
            h = (urlparse(u).hostname or "").lower()
            if h.startswith("www."):
                h = h[4:]
            hosts2[h] += 1
            dl2.append((h, o.get("artifact_id"), o.get("sha256")))
print()
print("state trial court rows:", n2, "status:", dict(st2))
print("keys:", sorted(first2.keys()))
print("distinct hosts:", len(hosts2))

print()
print("COMBINED manifest rows:", n + n2)
print("COMBINED downloaded:", status.get("downloaded", 0) + st2.get("downloaded", 0))
allhosts = collections.Counter()
allhosts.update(hosts)
allhosts.update(hosts2)
print("COMBINED distinct hosts (downloaded):", len(allhosts))

# court spine hosts
spine = {}
spine_rows = 0
uscourts_bare = []
with io.open("C:/Users/firas/Downloads/SCRAPE/sources/court_spine_20260919/courts.jsonl", "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        c = json.loads(line)
        spine_rows += 1
        w = c.get("website")
        if not w:
            continue
        h = (urlparse(w).hostname or "").lower()
        if h.startswith("www."):
            h = h[4:]
        if not h:
            continue
        spine.setdefault(h, []).append(c)
        if h == "uscourts.gov":
            uscourts_bare.append((c.get("id"), c.get("name"), c.get("in_use"), w))
print()
print("court_spine rows:", spine_rows, "distinct website hosts:", len(spine))
print("court_spine rows with website host == uscourts.gov:", len(uscourts_bare))
for r in uscourts_bare:
    print("   ", r)

ambig = {h: len(v) for h, v in spine.items() if len(v) > 1}
print("hosts mapping to >1 court:", len(ambig), "top:", sorted(ambig.items(), key=lambda x: -x[1])[:8])

# join downloaded files to spine
matched = 0
matched_excl = 0
courts_hit = set()
courts_hit_excl = set()
unambig_files = 0
for h, aid, s in (dl_rows + dl2):
    if h in spine:
        matched += 1
        if h != "uscourts.gov":
            matched_excl += 1
            for c in spine[h]:
                courts_hit_excl.add(c.get("id"))
            if len(spine[h]) == 1:
                unambig_files += 1
        for c in spine[h]:
            courts_hit.add(c.get("id"))
print()
print("downloaded files whose host matches a court_spine website host:", matched)
print("  excluding bare uscourts.gov:", matched_excl, "-> distinct courts:", len(courts_hit_excl))
print("  of those, on single-court hosts:", unambig_files)
print("including uscourts.gov -> distinct courts:", len(courts_hit))

amb_rows = sum(1 for h, a, s in (dl_rows + dl2) if h in spine and len(spine[h]) > 1)
print("downloaded rows on ambiguous (multi-court) hosts:", amb_rows)
