import json, collections, os

OV = "C:/Users/firas/Downloads/SCRAPE/sources/judge_structured_20260919/overlay.jsonl"
ids = set()
n = 0
shapes = collections.Counter()
for line in open(OV, encoding="utf-8"):
    if not line.strip():
        continue
    n += 1
    r = json.loads(line)
    cl = r.get("courtlistener")
    got = None
    if isinstance(cl, dict):
        for k in ("cl_person_id", "person_id", "id"):
            if cl.get(k) is not None:
                got = cl[k]
                shapes["courtlistener." + k] += 1
                break
    if got is None:
        idd = r.get("ids")
        if isinstance(idd, dict):
            for k in ("cl_person_id", "cl_person", "person_id"):
                if idd.get(k) is not None:
                    got = idd[k]
                    shapes["ids." + k] += 1
                    break
    if got is not None:
        ids.add(str(int(got)))
print("overlay rows:", n, "distinct cl_person ids:", len(ids), "shapes:", shapes.most_common())
json.dump(sorted(ids), open("C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/verify2/cl_persons.json", "w"))

# sample a bridged record for key names
for line in open(OV, encoding="utf-8"):
    r = json.loads(line)
    if isinstance(r.get("courtlistener"), dict):
        print("sample courtlistener block keys:", sorted(r["courtlistener"]))
        print(json.dumps(r["courtlistener"])[:500])
        print("ids block:", json.dumps(r.get("ids"))[:300])
        break
