"""Validate this heartbeat's saved county artifacts without publishing them."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
import json,hashlib,sqlite3
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
TARGET=ROOT/'corpus/county_local_backfill_20260918T2213'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ro(p):
 c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;return c
def write(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def local(p):
 p=p.resolve();assert p.is_relative_to(TARGET.resolve()) and p.is_file();return p
def rel(p):return p.relative_to(ROOT).as_posix()
receipt=json.loads((OUT/'job_receipt.json').read_text(encoding='utf8'));assert receipt['status']=='exited'
existing=defaultdict(list)
for p in (ROOT/'corpus').glob('*/corpus.sqlite3'):
 if p.parent==TARGET:continue
 c=ro(p)
 for r in c.execute("select url,sha256 from resources where status='downloaded' and sha256 is not null"):
  existing[r['sha256']].append({'collection':rel(p.parent),'url':r['url']})
 c.close()
c=ro(TARGET/'corpus.sqlite3');all_rows=[dict(r) for r in c.execute('select * from resources order by url')]
resources=[];errors=[]
for row in all_rows:
 if row['status']!='downloaded':continue
 try:
  raw=local(TARGET/row['raw_path']);meta_path=local(TARGET/row['metadata_path']);meta=json.loads(meta_path.read_text(encoding='utf8'))
  fetch=dict(c.execute('select * from fetches where id=?',(row['last_fetch_id'],)).fetchone())
  assert row['raw_complete']==meta['raw_complete']==fetch['raw_complete']==1
  assert row['last_http_status']==meta['http_status']==fetch['http_status']==200
  assert row['status']==meta['status']==fetch['status']=='downloaded'
  assert row['url']==meta['requested_url'] and row['last_fetch_id']==meta['fetch_id']==fetch['id']
  for key in ['sha256','raw_path','text_path','byte_count','extraction_status']:assert row[key]==meta[key]==fetch[key]
  assert sha(raw)==row['sha256'] and raw.stat().st_size==row['byte_count']
  with raw.open('rb') as f:pdf_signature=f.read(5)==b'%PDF-'
  assert pdf_signature,'Unexpected content format for selected document URL'
  text=local(TARGET/row['text_path']) if row['text_path'] else None
  text_sha=sha(text) if text else None;body=text.read_bytes().decode('utf8') if text else ''
  assert not text or (len(meta.get('text_sha256',''))==64 and text_sha==meta['text_sha256'])
  seed_contexts=[]
  for context in c.execute('select x.* from contexts x join resource_contexts rc on x.id=rc.context_id where rc.resource_id=?',(row['id'],)):
   seed=json.loads(context['seed_json']);seed_contexts.append(seed)
   match=[x for x in meta['contexts'] if x['context_id']==context['id']]
   assert len(match)==1 and match[0]['jurisdiction']==seed['jurisdiction']
  states={x['jurisdiction'].get('state') for x in seed_contexts};counties={x['jurisdiction'].get('county') for x in seed_contexts}
  categories={x['category'] for x in seed_contexts};key=[rel(TARGET),row['url'],row['sha256']]
  resources.append({'id':'county_heartbeat_'+hashlib.sha256(json.dumps(key,separators=(',',':')).encode()).hexdigest()[:28],
   'collection':rel(TARGET),'resource_id':row['id'],'source_url':row['url'],'title':row['title'] or row['url'],
   'state':next(iter(states)) if len(states)==1 else None,'county':next(iter(counties)) if len(counties)==1 else None,
   'county_geoids':sorted({s['jurisdiction']['geoid'] for s in seed_contexts}),
   'resource_kind':next(iter(categories)) if len(categories)==1 else 'unreviewed_resource','group':'counties',
   'raw_path':rel(raw),'sha256':row['sha256'],'raw_bytes':row['byte_count'],'text_path':rel(text) if text else None,
   'text_sha256':text_sha,'text_characters':len(body),'native_text_nonempty':bool(body.strip()),'strict_utf8_valid':bool(text),
   'text_replacement_character_count':body.count('\ufffd'),
   'metadata_path':rel(meta_path),'metadata_sha256':sha(meta_path),'captured_at':meta['fetched_at'],
   'extraction_status':row['extraction_status'],'quality':'Awaiting publication validation; county context is not verified court territory',
   'metadata':{'fetch_id':row['last_fetch_id'],'contexts':seed_contexts,'source_metadata_path':rel(meta_path),
               'raw_and_metadata_binding_verified':True,'original_pdf_signature_verified':True,
               'prior_identical_raw_captures':existing.get(row['sha256'],[]),'legal_currency_verified':False,
               'text_quality_note':'Native extraction preserves observed output; UTF-8/hash validity does not certify transcription accuracy.'}})
 except Exception as exc:errors.append({'url':row['url'],'error':type(exc).__name__+': '+str(exc)})
statuses=dict(Counter(r['status'] for r in all_rows));c.close()
manifest=OUT/'resources.jsonl';manifest.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in resources),encoding='utf8')
blocked=[{k:r[k] for k in ['url','status','last_http_status','error']} for r in all_rows if r['status']!='downloaded']
summary={'validated_at':datetime.now(timezone.utc).isoformat(),'status':'passed' if not errors else 'failed','data_root':rel(TARGET),
 'status_counts':statuses,'downloaded':statuses.get('downloaded',0),'validated_pdf_captures':len(resources),
 'with_nonempty_native_text':sum(r['native_text_nonempty'] for r in resources),'empty_or_missing_native_text':sum(not r['native_text_nonempty'] for r in resources),
 'distinct_raw_payloads':len({r['sha256'] for r in resources}),'captures_identical_to_prior_corpus_payload':sum(bool(r['metadata']['prior_identical_raw_captures']) for r in resources),
 'pending_or_fetching':sum(statuses.get(x,0) for x in ['pending','retry_wait','fetching']),
 'county_associations':len({g for r in resources for g in r['county_geoids']}),'resources_sha256':sha(manifest),
 'errors':errors,'unresolved_resources':blocked,
 'terminal_failures_or_exclusions':[r for r in blocked if r['status'] not in ['pending','fetching','retry_wait']],
 'publication_modified':False,'pending_projection_modified':False,'full_county_content_complete':False}
write(OUT/'validation.json',summary);write(OUT/'summary.json',summary)
print(json.dumps(summary,ensure_ascii=True))
if errors:raise SystemExit(1)
