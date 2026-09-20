import json, io, os

p = "C:/Users/firas/Downloads/SCRAPE/sources/jpml_mdl_20260919/mdls.jsonl"
n = 0
first = None
statuses = {}
with io.open(p, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        n += 1
        o = json.loads(line)
        if first is None:
            first = o
        st = o.get("status")
        statuses[st] = statuses.get(st, 0) + 1
print("mdls.jsonl rows=", n, "statuses=", statuses)
print("keys:", sorted(first.keys()))
print("sample:", json.dumps(first)[:2500])
print()

p = "C:/Users/firas/Downloads/SCRAPE/sources/court_spine_20260919/courts.jsonl"
n = 0
first = None
with io.open(p, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        n += 1
        if first is None:
            first = json.loads(line)
print("courts.jsonl rows=", n)
print("keys:", sorted(first.keys()))
print("sample:", json.dumps(first)[:1200])
print()

for name in ["matters", "masters"]:
    p = "C:/Users/firas/Downloads/SW-BULK/catalog/" + name + ".json"
    with io.open(p, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    print("catalog/" + name + ".json type=", type(d).__name__)
    if isinstance(d, dict):
        print("top keys:", list(d.keys())[:20])
        for k in list(d.keys())[:3]:
            print(" ", k, "->", json.dumps(d[k])[:600])
    else:
        print("len=", len(d))
        print("sample:", json.dumps(d[0])[:800])
    print()
