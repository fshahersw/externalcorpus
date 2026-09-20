import gzip, json
base = "C:/Users/firas/Downloads/SW-BULK/AWS-BATCH1-DOCKETS/releases/b2b-cdbb8d040b95c7b65cfc/"
for f in ["matters","matter_aliases","matter_relationships","attorneys","firms","counsel_appearances","parties"]:
    p = base + f + ".jsonl.gz"
    n = 0
    first = None
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            n += 1
            if first is None:
                first = json.loads(line)
    print("===", f, "rows=", n)
    print("keys:", sorted(first.keys()))
    print("sample:", json.dumps(first)[:900])
    print()
