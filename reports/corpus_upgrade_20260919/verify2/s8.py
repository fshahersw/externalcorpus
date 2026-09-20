import json, csv, collections, os

MDL = "C:/Users/firas/Downloads/SCRAPE/sources/jpml_mdl_20260919/mdls.jsonl"
reg = {}
for line in open(MDL, encoding="utf-8"):
    if line.strip():
        r = json.loads(line)
        reg[int(r["mdl_number"])] = (r.get("status"), r.get("title", "")[:60])
for n in (2545, 3060, 2100, 2606, 2641, 2734, 2244, 2768, 2921, 1626, 1943, 2434, 2331, 2187, 2327):
    print("registry", n, reg.get(n))

print()
docs = json.load(open("C:/Users/firas/Downloads/SW-BULK/catalog/documents.json", encoding="utf-8"))
nomdl = collections.Counter()
for d in docs:
    if not d.get("mdl_number"):
        nomdl[(d.get("master_docket_id"), d.get("docket_number"), d.get("case_name")[:60])] += 1
print("parked rows grouped:", nomdl.most_common())

print()
print("=== local recap bytes? ===")
cands = ["C:/Users/firas/Downloads/SW-BULK/recap", "C:/Users/firas/Downloads/SW-BULK/_staging",
         "C:/Users/firas/Downloads/SW-BULK/catalog/documents_by_master"]
for c in cands:
    print(c, "exists:", os.path.isdir(c))
    if os.path.isdir(c):
        e = sorted(os.listdir(c))[:8]
        print("  ", len(os.listdir(c)), "entries;", e)
m = json.load(open("C:/Users/firas/Downloads/SW-BULK/catalog/recap_pdfs_manifest.json", encoding="utf-8"))
print("recap_pdfs_manifest type:", type(m).__name__)
s = json.dumps(m)[:600]
print(s)
