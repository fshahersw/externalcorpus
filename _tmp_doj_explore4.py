import json, collections
base = r"C:/Users/firas/Downloads/returnedfiles"
url_counts = collections.Counter()
bad = []
n=0
with open(base + '/doj_sweep_urls.jsonl', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        line=line.strip()
        if not line: continue
        n+=1
        try:
            row=json.loads(line)
        except Exception as e:
            bad.append((i, str(e)))
            continue
        u = row.get('url')
        url_counts[u]+=1
        if not u or not (u.startswith('http://') or u.startswith('https://')):
            bad.append((i, u))
print('n', n, 'bad', len(bad), bad[:10])
dupes = {k:v for k,v in url_counts.items() if v>1}
print('dupe urls', len(dupes))
print(list(dupes.items())[:5])

# state_sources malformed check
bad2=[]
n2=0
with open(base + '/doj_state_sources.jsonl', encoding='utf-8') as f:
    for i, line in enumerate(f,1):
        line=line.strip()
        if not line: continue
        n2+=1
        row=json.loads(line)
        u = row.get('url')
        if not u or not (u.startswith('http://') or u.startswith('https://')):
            bad2.append((i,u))
print('state_sources n', n2, 'bad', len(bad2), bad2[:10])
