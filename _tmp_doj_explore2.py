import json, collections
base = r"C:/Users/firas/Downloads/returnedfiles"
by_state_domain = collections.defaultdict(collections.Counter)
with open(base + '/doj_sweep_urls.jsonl', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        row=json.loads(line)
        by_state_domain[row.get('sources')][row.get('domain')]+=1
for st, c in by_state_domain.items():
    print(st, c.most_common(5))
