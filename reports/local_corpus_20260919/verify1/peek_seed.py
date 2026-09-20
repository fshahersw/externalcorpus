import gzip, json, io, collections

S = "C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/"
files = [
    S + "court_expansion_seed_v2_4_2026-08-20/court_expansion_anchor_snapshots_v2.jsonl.gz",
    S + "court_expansion_corpus_v2_4_2026-08-20/court_expansion_file_url_corpus_v2.jsonl.gz",
    S + "court_expansion_corpus_v2_4_2026-08-20/court_expansion_graph_nodes_v2.jsonl.gz",
]
for p in files:
    n = 0
    first = None
    try:
        with gzip.open(p, "rt", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    n += 1
                    if first is None:
                        first = json.loads(line)
    except Exception as e:
        print(p, "ERR", e)
        continue
    print("===", p.split("/")[-1], "rows=", n)
    print("keys:", sorted(first.keys()))
    print("sample:", json.dumps(first)[:900])
    print()

p = S + "court_expansion_file_preflight_v2_4_2026-08-20/court_file_preflight_results_v2.jsonl"
n = 0
first = None
with io.open(p, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line:
            n += 1
            if first is None:
                first = json.loads(line)
print("=== court_file_preflight_results_v2.jsonl rows=", n)
print("keys:", sorted(first.keys()))
print("sample:", json.dumps(first)[:900])
