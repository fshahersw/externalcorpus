import json, collections
base = r"C:/Users/firas/Downloads/returnedfiles"
cross = collections.defaultdict(collections.Counter)
sec_counter = collections.Counter()
subsec_counter = collections.Counter()
with open(base + '/doj_state_sources.jsonl', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        row=json.loads(line)
        sec = row.get('section') or ''
        sub = row.get('subsection') or ''
        cross[sec][sub]+=1
        sec_counter[sec]+=1
        subsec_counter[sub]+=1
for sec, subs in cross.items():
    print('SECTION:', sec)
    for sub, cnt in subs.most_common():
        print('   ', sub, cnt)
