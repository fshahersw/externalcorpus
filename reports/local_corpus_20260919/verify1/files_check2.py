import json, io, os, random, collections

P2 = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/state_trial_court_acquisition_v1_2026-08-20/artifact_download_results_v1.jsonl"
r2 = []
kinds = collections.Counter()
with io.open(P2, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            o = json.loads(line)
            lp = o.get("local_path") or ""
            kinds["absolute" if (len(lp) > 2 and lp[1] == ":") else ("relative" if lp else "empty")] += 1
            if o.get("download_status") == "downloaded":
                r2.append(o)
print("state trial local_path kinds:", dict(kinds))
random.seed(7)
s2 = random.sample(r2, 100)
p = m = 0
for o in s2:
    lp = (o.get("local_path") or "").replace("\\", "/")
    if os.path.exists(lp):
        p += 1
    else:
        m += 1
print("state trial sample 100 present:", p, "missing:", m)

# court expansion path kinds
import glob
kinds2 = collections.Counter()
for path in sorted(glob.glob("C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/court_expansion_file_download_v2_4_2026-08-20/wave_*/court_file_download_results_v2.jsonl")):
    with io.open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                lp = json.loads(line).get("local_path") or ""
                kinds2["absolute" if (len(lp) > 2 and lp[1] == ":") else ("relative" if lp else "empty")] += 1
print("court expansion local_path kinds:", dict(kinds2))
