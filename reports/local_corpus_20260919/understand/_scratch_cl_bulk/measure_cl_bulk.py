import bz2, csv, io, json, os, sys, time

BULK = "C:/Users/firas/Downloads/returnedfiles/bulk"
OUT = os.path.dirname(os.path.abspath(__file__))

def open_bz2_text(path):
    f = bz2.open(path, mode="rt", encoding="utf-8", newline="")
    return f

def csv_reader(path):
    f = open_bz2_text(path)
    r = csv.reader(f, escapechar="\\", doublequote=False, strict=False)
    return f, r

def count_and_header(fname, max_seconds=55, sample_rows=3):
    path = os.path.join(BULK, fname)
    t0 = time.time()
    f, r = csv_reader(path)
    header = next(r, None)
    n = 0
    samples = []
    timed_out = False
    for row in r:
        n += 1
        if len(samples) < sample_rows:
            samples.append(row)
        if n % 200000 == 0 and (time.time() - t0) > max_seconds:
            timed_out = True
            break
    f.close()
    return {"file": fname, "header": header, "ncols": len(header) if header else None,
            "rows_counted": n, "timed_out": timed_out, "elapsed_s": round(time.time()-t0,1),
            "sample_rows": samples}

files = [
    "people-db-people-2026-06-30.csv.bz2",
    "people-db-positions-2026-06-30.csv.bz2",
    "people-db-educations-2026-06-30.csv.bz2",
    "people-db-schools-2026-06-30.csv.bz2",
    "people-db-political-affiliations-2026-06-30.csv.bz2",
    "people-db-races-2026-06-30.csv.bz2",
    "people_db_race-2026-06-30.csv.bz2",
    "people-db-retention-events-2026-06-30.csv.bz2",
    "courts-2026-06-30.csv.bz2",
    "courthouses-2026-06-30.csv.bz2",
    "court-appeals-to-2026-06-30.csv.bz2",
    "search_opinioncluster_panel-2026-06-30.csv.bz2",
    "search_opinion_joined_by-2026-06-30.csv.bz2",
    "search_opinioncluster_non_participating_judges-2026-06-30.csv.bz2",
    "financial-disclosures-2026-06-30.csv.bz2",
    "financial-disclosures-agreements-2026-06-30.csv.bz2",
    "financial-disclosures-debts-2026-06-30.csv.bz2",
    "financial-disclosures-gifts-2026-06-30.csv.bz2",
    "financial-disclosures-non-investment-income-2026-06-30.csv.bz2",
    "financial-disclosures-positions-2026-06-30.csv.bz2",
    "financial-disclosures-reimbursements-2026-06-30.csv.bz2",
    "financial-disclosures-spousal-income-2026-06-30.csv.bz2",
]

out = {}
for fn in files:
    try:
        out[fn] = count_and_header(fn)
        print(fn, "->", out[fn]["rows_counted"], "timed_out=", out[fn]["timed_out"], "cols=", out[fn]["ncols"])
    except Exception as e:
        out[fn] = {"error": str(e)}
        print(fn, "ERROR", e)

with open(os.path.join(OUT, "basic_counts.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, default=str)
print("DONE")
