import json, io, gzip, collections, os

REL = "C:/Users/firas/Downloads/SW-BULK/AWS-BATCH1-DOCKETS/releases/b2b-cdbb8d040b95c7b65cfc/"
m = json.load(io.open(REL + "manifest.json", "r", encoding="utf-8"))
for k in ["release_id", "status", "built_at", "schema_version", "predecessor"]:
    print(k, "=", json.dumps(m.get(k))[:400])
print("descriptor:", json.dumps(m.get("descriptor"))[:1500])
print("validation:", json.dumps(m.get("validation"))[:1500])
print()
# releases dir
rd = "C:/Users/firas/Downloads/SW-BULK/AWS-BATCH1-DOCKETS/releases/"
print("releases:", os.listdir(rd))
top = "C:/Users/firas/Downloads/SW-BULK/AWS-BATCH1-DOCKETS/"
print("batch1 dir:", sorted(os.listdir(top))[:40])
print()
# documents verification status
n = collections.Counter()
have_s3 = 0
with gzip.open(REL + "documents.jsonl.gz", "rt", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        n[o.get("verification_status")] += 1
        if o.get("s3_key"):
            have_s3 += 1
print("documents verification_status:", dict(n), "with s3_key:", have_s3)
print()
# outcomes detail (settlement amounts)
with gzip.open(REL + "outcomes.jsonl.gz", "rt", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            print("outcome:", json.dumps(json.loads(line))[:300])
