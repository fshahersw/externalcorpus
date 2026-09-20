import json, io, os, glob, collections
from urllib.parse import urlparse

ROOT = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/court_expansion_file_download_v2_4_2026-08-20/"
paths = sorted(glob.glob(ROOT + "wave_*/court_file_download_results_v2.jsonl"))
print("manifest files found:", len(paths))
for p in paths:
    print("  ", os.path.basename(os.path.dirname(p)))

n = 0
status = collections.Counter()
ext = collections.Counter()
hosts = collections.Counter()
sha = set()
sha_rows = 0
jur_empty = 0
jur_missing = 0
jur_codes = collections.Counter()
lanes = collections.Counter()
first = None
rows = []
for p in paths:
    with io.open(p, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            n += 1
            if first is None:
                first = o
            rows.append(o)
print("TOTAL manifest rows (court expansion):", n)
print("keys:", sorted(first.keys()))
print("sample:", json.dumps(first)[:1500])
