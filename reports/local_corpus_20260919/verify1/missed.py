import gzip, json, io, glob, collections

S = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/"
dl = []
for p in sorted(glob.glob(S + "court_expansion_file_download_v2_4_2026-08-20/wave_*/court_file_download_results_v2.jsonl")):
    with io.open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                dl.append(json.loads(line))
dlv = [o for o in dl if o.get("download_status") == "downloaded"]
print("downloaded:", len(dlv))

pf = []
with io.open(S + "court_expansion_file_preflight_v2_4_2026-08-20/court_file_preflight_results_v2.jsonl", "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            pf.append(json.loads(line))
print("preflight rows:", len(pf))
by_aid = {}
by_url = {}
for o in pf:
    if o.get("artifact_id"):
        by_aid[o["artifact_id"]] = o
    for k in ("url", "canonical_url", "final_url", "original_url", "requested_url"):
        if o.get(k):
            by_url.setdefault(o[k], o)

hit_aid = sum(1 for o in dlv if o.get("artifact_id") in by_aid)
hit_url = 0
fam = 0
cid = 0
lm = 0
fams = collections.Counter()
for o in dlv:
    q = by_aid.get(o.get("artifact_id"))
    if q is None:
        for k in ("source_url", "download_url", "final_url"):
            if o.get(k) in by_url:
                q = by_url[o[k]]
                break
    if q is None:
        continue
    hit_url += 1
    if q.get("source_families"):
        fam += 1
        for f in q["source_families"]:
            fams[f] += 1
    if q.get("associated_court_ids"):
        cid += 1
    if q.get("last_modified"):
        lm += 1
print("downloaded joined to preflight by artifact_id:", hit_aid, "| by artifact_id or url:", hit_url)
print("  with source_families:", fam, "| with associated_court_ids:", cid, "| with HTTP last_modified:", lm)
print("  source_families distribution:", fams.most_common(20))

uc = []
with gzip.open(S + "court_expansion_corpus_v2_4_2026-08-20/court_expansion_file_url_corpus_v2.jsonl.gz", "rt", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            uc.append(json.loads(line))
print()
print("file_url_corpus rows:", len(uc))
ucby = {}
for o in uc:
    if o.get("url"):
        ucby[o["url"]] = o
h = 0
f2 = 0
c2 = 0
fams2 = collections.Counter()
courts2 = set()
for o in dlv:
    q = ucby.get(o.get("source_url")) or ucby.get(o.get("download_url")) or ucby.get(o.get("final_url"))
    if q is None:
        continue
    h += 1
    if q.get("source_families"):
        f2 += 1
        for x in q["source_families"]:
            fams2[x] += 1
    if q.get("associated_court_ids"):
        c2 += 1
        courts2.update(q["associated_court_ids"])
print("downloaded joined to file_url_corpus by url:", h, "| with source_families:", f2,
      "| with associated_court_ids:", c2, "-> distinct court ids:", len(courts2))
print("families:", fams2.most_common(20))
print("sample court ids:", list(courts2)[:15])
