# -*- coding: utf-8 -*-
import bz2, csv, json, os, time

BULK = "C:/Users/firas/Downloads/returnedfiles/bulk"
OUT = os.path.dirname(os.path.abspath(__file__))

def reader(fname):
    f = bz2.open(os.path.join(BULK, fname), mode="rt", encoding="utf-8", newline="")
    r = csv.reader(f, escapechar="\\", doublequote=False, strict=False)
    return f, r

result = {}

def sampled_count(fname, max_seconds=50):
    f, r = reader(fname)
    header = next(r)
    t0 = time.time()
    n = 0
    sample = None
    timed_out = False
    for row in r:
        n += 1
        if sample is None and len(row) == len(header):
            sample = dict(zip(header, row))
        if n % 500000 == 0 and (time.time() - t0) > max_seconds:
            timed_out = True
            break
    f.close()
    return {"header": header, "ncols": len(header), "rows_counted": n, "timed_out": timed_out,
            "elapsed_s": round(time.time() - t0, 1), "sample": sample}

for fn in ["originating-court-information-2026-06-30.csv.bz2",
           "financial-disclosure-investments-2026-06-30.csv.bz2",
           "citations-2026-06-30.csv.bz2"]:
    r = sampled_count(fn)
    result[fn] = r
    print(fn, r["rows_counted"], "timed_out=", r["timed_out"], "elapsed=", r["elapsed_s"], "cols=", r["ncols"])

with open(os.path.join(OUT, "measure3.json"), "w", encoding="utf-8") as fh:
    json.dump(result, fh, indent=2, default=str)
print("DONE")
