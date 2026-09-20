import json, io, gzip, glob, os, collections

REL = "C:/Users/firas/Downloads/SW-BULK/AWS-BATCH1-DOCKETS/releases/b2b-cdbb8d040b95c7b65cfc/"
m = json.load(io.open(REL + "manifest.json", "r", encoding="utf-8"))
print("manifest.json keys:", sorted(m.keys()))
print(json.dumps(m)[:3000])
print()

for f in ["coverage", "outcomes", "citations", "courts", "judges", "judicial_assignments",
          "opinions", "docket_entries", "documents"]:
    p = REL + f + ".jsonl.gz"
    n = 0
    first = None
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                n += 1
                if first is None:
                    first = json.loads(line)
    print(f, "rows=", n, "keys=", sorted(first.keys()))
print()

# publiclaw_registry_v2 root
root = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/"
print("publiclaw_registry_v2 entries:", sorted(os.listdir(root))[:40])
st = root + "staging/"
print("staging entries:", sorted(os.listdir(st))[:60])
