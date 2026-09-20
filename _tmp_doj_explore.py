import json, csv, collections

base = r"C:/Users/firas/Downloads/returnedfiles"

sources_counter = collections.Counter()
kind_counter = collections.Counter()
label_nonempty = 0
n=0
with open(base + '/doj_sweep_urls.jsonl', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        n+=1
        row=json.loads(line)
        sources_counter[row.get('sources')]+=1
        kind_counter[row.get('kind')]+=1
        if row.get('label'): label_nonempty+=1
print('total rows', n)
print('sources', sources_counter)
print('kind', kind_counter)
print('label nonempty', label_nonempty)

n2=0
doc_sources=collections.Counter()
label_nonempty2=0
urls_doc=set()
with open(base + '/doj_sweep_documents.csv', encoding='utf-8', newline='') as f:
    r=csv.DictReader(f)
    for row in r:
        n2+=1
        doc_sources[row.get('sources')]+=1
        if row.get('label'): label_nonempty2+=1
        urls_doc.add(row.get('url'))
print('doc rows', n2, 'unique urls', len(urls_doc))
print('doc sources', doc_sources)
print('doc label nonempty', label_nonempty2)

urls_url=set()
with open(base + '/doj_sweep_urls.jsonl', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        row=json.loads(line)
        urls_url.add(row.get('url'))
print('unique urls in urls.jsonl', len(urls_url))
print('doc urls subset of url list?', urls_doc.issubset(urls_url))
print('doc urls not in url list count', len(urls_doc - urls_url))

# state_sources
n3=0
state_counter=collections.Counter()
with open(base + '/doj_state_sources.jsonl', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if not line: continue
        n3+=1
        row=json.loads(line)
        state_counter[row.get('state')]+=1
print('state_sources rows', n3, 'num states', len(state_counter))
print(sorted(state_counter.keys()))
