SRC = "C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/verify2/section.md"
DST = "C:/Users/firas/Downloads/SCRAPE/reports/local_corpus_20260919/INTEGRATION_PLAN.md"
s = open(SRC, encoding="utf-8").read()
before = len(open(DST, encoding="utf-8").read())
with open(DST, "a", encoding="utf-8", newline="") as f:
    f.write(s)
after = len(open(DST, encoding="utf-8").read())
print("before", before, "after", after, "appended", after - before)
print("has Verification 2:", "## Verification 2" in open(DST, encoding="utf-8").read())
