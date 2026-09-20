import json, io, glob, os, random, hashlib

ROOT = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/"
paths = sorted(glob.glob(ROOT + "staging/court_expansion_file_download_v2_4_2026-08-20/wave_*/court_file_download_results_v2.jsonl"))
rows = []
for p in paths:
    with io.open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                o = json.loads(line)
                if o.get("download_status") == "downloaded":
                    rows.append(o)
print("downloaded rows:", len(rows))
random.seed(7)
sample = random.sample(rows, 200)
missing = 0
present = 0
badhash = 0
checked_hash = 0
for o in sample:
    lp = (o.get("local_path") or "").replace("\\", "/")
    full = ROOT + lp
    if os.path.exists(full):
        present += 1
        if checked_hash < 15 and (o.get("bytes") or 0) < 5_000_000:
            h = hashlib.sha256()
            with open(full, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            checked_hash += 1
            if h.hexdigest() != o.get("sha256"):
                badhash += 1
    else:
        missing += 1
print("sample 200: present", present, "missing", missing, "| sha256 re-hashed", checked_hash, "mismatch", badhash)

# state trial files
P2 = ROOT + "staging/state_trial_court_acquisition_v1_2026-08-20/artifact_download_results_v1.jsonl"
r2 = []
with io.open(P2, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            o = json.loads(line)
            if o.get("download_status") == "downloaded":
                r2.append(o)
s2 = random.sample(r2, 100)
p2 = m2 = 0
for o in s2:
    lp = (o.get("local_path") or "").replace("\\", "/")
    if os.path.exists(ROOT + lp):
        p2 += 1
    else:
        m2 += 1
print("state trial sample 100: present", p2, "missing", m2)
print("sample local_path:", r2[0].get("local_path"))
