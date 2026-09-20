import io

DST = "C:/Users/firas/Downloads/SCRAPE/reports/local_corpus_20260919/INTEGRATION_PLAN.md"
SRC = "C:/Users/firas/Downloads/SCRAPE/reports/local_corpus_20260919/verify1/section.md"

raw = open(DST, "rb").read()
marker = "## Verification 1 (independent re-measurement, 2026-09-19)".encode("utf-8")
i = raw.find(marker)
print("marker at byte", i, "of", len(raw))
assert i > 0
head = raw[:i]
# trim trailing blank lines back to a single newline separation
head = head.rstrip(b"\r\n") + b"\n"
section = open(SRC, "rb").read()
out = head + section.lstrip(b"\r\n").rjust(0)
out = head + b"\n" + section.lstrip(b"\r\n")
open(DST, "wb").write(out)
print("rewrote, new size", len(out))
txt = io.open(DST, "r", encoding="utf-8").read()
print("lines:", txt.count("\n"))
print("mojibake present:", "\u00e2\u0080" in txt)
print("Verification 2 still present:", "## Verification 2" in txt)
print("Verification 1 present:", "## Verification 1" in txt)
