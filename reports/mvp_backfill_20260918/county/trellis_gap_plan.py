"""Compute the observed Trellis profile URL denominator, not Census coverage."""
from pathlib import Path
from urllib.parse import urlsplit
import sqlite3,json,hashlib
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def ro(p):
 c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;return c
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((ROOT/'sources/official_courts/datasets/counties_50_plus_dc.json').read_text(encoding='utf8'))
states={r['state'].lower().replace(' ','-') for r in baseline}
def profile(url):
 p=urlsplit(url);parts=p.path.strip('/').split('/')
 return p.scheme=='https' and p.netloc=='trellis.law' and not p.query and not p.fragment and len(parts)==3 and parts[0]=='coverage' and parts[1] in states
catalog_path=ROOT/'sources/trellis/catalog/catalog.sqlite3'
proofs={};saved={};pages={};excluded=[]
with ro(catalog_path) as c:
 pages={r['url']:dict(r) for r in c.execute('select * from pages')}
 for r in c.execute("select * from links where category='coverage_county' order by url,source_url"):
  if profile(r['url']):proofs.setdefault(r['url'],dict(r))
 for r in c.execute('select * from counties'):
  if profile(r['url']):saved[r['url']]=dict(r)
  else:excluded.append({'url':r['url'],'reason':'Saved county table row outside exact state/DC county-profile URL shape'})
frontier_path=ROOT/'sources/trellis/worker/frontier.sqlite3'
with ro(frontier_path) as c:
 frontier={r['url']:dict(r) for r in c.execute("select url,status,attempts,error,discovered_from from frontier where category='county' and in_scope=1")}
known=set(proofs)|set(saved)
gaps=[]
for url in sorted(known-set(saved)):
 p=proofs.get(url);f=frontier.get(url,{})
 row={'url':url,'status':f.get('status','not_in_frontier'),'attempts':f.get('attempts',0),'error':f.get('error'),
      'observed_link':p,'source_page_record':pages.get(p['source_url']) if p else None,
      'scope':'Observed state/DC county-profile URL; no claim of unique Census county identity or paid document access.'}
 gaps.append(row)
# Favor unattempted explicit County/Parish labels with a saved source page. Leave
# earlier error URLs and ambiguous labels for review rather than blind retries.
next_rows=[r for r in gaps if r['status']=='pending' and r['attempts']==0 and r['source_page_record'] and
           any(w in (r['observed_link'].get('label') or '').lower() for w in ['county','parish'])][:10]
for r in next_rows:
 page=r['source_page_record'];p=(ROOT/page['source_path']).resolve()
 r['saved_parent_receipt']={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'artifact_kind':'Saved provider source JSON, not browser session cookies'}
 r['browser_capture_instruction']='Open this literal observed profile URL in the authorized browser, capture visible county profile fields and official website href only, then checkpoint. Stop on login, CAPTCHA, 403, 429 or subscription barrier to requested fields. Do not open cases, paginate, submit forms or clear blocked crawler controls.'
def write(name,data):
 (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),encoding='utf8')
write('trellis_observed_county_profile_gaps.jsonl',gaps)
write('trellis_next_10_browser_profiles.jsonl',next_rows)
write('trellis_excluded_noncounty_catalog_rows.jsonl',excluded)
summary={'generated_at':datetime.now(timezone.utc).isoformat(),'denominator':'Distinct state/DC county-profile URLs observed as saved coverage_county links or already saved profiles; not Census counties and not all Trellis URLs.',
 'observed_county_profile_urls':len(known),'saved_profile_urls':len(saved),'remaining_observed_profile_urls':len(gaps),
 'saved_percent_of_observed_profile_urls':round(100*len(saved)/len(known),2),
 'states_or_dc_with_saved_profiles':len({urlsplit(u).path.split('/')[2] for u in saved}),
 'frontier_county_rows':len(frontier),'frontier_rows_outside_observed_valid_profile_set':len(set(frontier)-known),
 'excluded_catalog_noncounty_rows':excluded,'next_browser_batch_count':len(next_rows),
 'next_browser_batch_path':'reports/mvp_backfill_20260918/county/trellis_next_10_browser_profiles.jsonl',
 'browser_public_profile_access_currently_observed':True,'paid_case_document_entitlement_verified':False,
 'http_or_provider_barriers_cleared':False,'network_requests':0}
(OUT/'trellis_gap_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=True))
print('NEXT',[r['url'] for r in next_rows])
