"""Preserve the draft and create a semantically reviewed, robots-screened packet."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter,defaultdict
from urllib.parse import urlsplit
import json,hashlib,shutil,urllib.robotparser
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines()]
def write(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8')
def jsonl(p,r):p.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True)+'\n' for x in r),encoding='utf8')
draft=ROOT/read(OUT/'preparation_receipt.json')['batch']
seeds=rows(draft/'seeds.jsonl');assert len(seeds)==30
robot_roots=[ROOT/'corpus/county_local_backfill_20260918']
rules={}
for collection in robot_roots:
 for p in (collection/'controls/robots').glob('*.json'):
  record=read(p)
  for observation in record.get('observations',[]):
   if observation.get('http_status')==200 and observation.get('raw_complete'):
    raw=collection/observation['raw_path'];assert sha(raw)==observation['sha256']
    parser=urllib.robotparser.RobotFileParser();parser.parse(raw.read_text(encoding='utf8').splitlines())
    rules[record['origin']]={'parser':parser,'control_path':p.relative_to(ROOT).as_posix(),'control_sha256':sha(p),'raw_path':raw.relative_to(ROOT).as_posix(),'raw_sha256':sha(raw)}
review=[];accepted=[];excluded={}
for s in seeds:
 url=s['url'];parts=urlsplit(url);origin=parts.scheme+'://'+parts.netloc;rule=rules.get(origin)
 label=s['provenance'][0]['anchor_text'];decision='accept';notes=[];basis=None
 if label=='Ordinances Help':decision='exclude';basis='Saved label and filename identify online-library help, not substantive ordinance text.'
 elif rule and not rule['parser'].can_fetch('LegalCorpusResearch/1.0',url):decision='exclude';basis='Already-saved robots policy disallows this exact URL for the collector user agent; no network retry.'
 if s['category']=='local_rules':notes.append('Administrative-order version retained; current validity/supersession not established.')
 if s['category']=='court_forms_filing_documents':notes.append('Public circuit docket/calendar; not a pleading. Month-only filename does not establish year; county context remains unverified.')
 if s['category']=='local_laws_codes':notes.append('Ordinance/resolution source document; enactment, amendments and current force require body/date review.')
 notes.append('Original county/source association remains qualified; no court-territory claim added.')
 item={'url':url,'anchor':label,'category':s['category'],'county_context':s['jurisdiction'],
       'parent_titles':sorted({p['parent_page_title'] for p in s['provenance']}),'decision':decision,'reason':basis,
       'qualifications':notes,'robots_evidence':{k:v for k,v in rule.items() if k!='parser'} if rule else None}
 review.append(item)
 if decision=='accept':accepted.append(s)
 else:excluded[url]=item
assert len(accepted)==26 and len(excluded)==4
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');batch=ROOT/'sources/counties/backfill_20260918/batches'/stamp
batch.mkdir(parents=True)
config=read(draft/'config.json');allow=defaultdict(set)
for s in accepted:allow[s['scope']['host']].update(s['scope']['path_prefixes'])
config['allow']=[{'host':h,'path_prefixes':sorted(paths)} for h,paths in sorted(allow.items())]
write(batch/'config.json',config);jsonl(batch/'seeds.jsonl',accepted)
candidates=rows(draft/'all_candidates.jsonl')
for r in candidates:
 if r['url'] in excluded and r['selection_status']=='selected':
  r['selection_status']='deferred_reviewed_robots_or_nonlegal_help';r['reviewed_exclusion']=excluded[r['url']]['reason']
jsonl(batch/'all_candidates.jsonl',candidates);jsonl(batch/'deferred.jsonl',[r for r in candidates if r['selection_status']!='selected'])
counts=Counter(s['jurisdiction']['geoid'] for s in accepted)
ledger=rows(draft/'county_ledger.jsonl')
for r in ledger:
 r['selected_this_batch']=counts[r['geoid']]
 r['selection_statuses']=dict(Counter(c['selection_status'] for c in candidates if c['county_geoid']==r['geoid']))
 if not r['selected_this_batch'] and r['status']=='selected_batch_pending_acquisition':r['status']='all_selected_candidates_deferred_after_review'
jsonl(batch/'county_ledger.jsonl',ledger)
prior=draft/'prior_collection_config_snapshot.json';shutil.copyfile(prior,batch/prior.name)
merged=read(prior);all_allow=defaultdict(set)
for a in merged['allow']+config['allow']:all_allow[a['host']].update(a['path_prefixes'])
merged['allow']=[{'host':h,'path_prefixes':sorted(v)} for h,v in sorted(all_allow.items())];write(batch/'merged_collection_config.json',merged)
validation=read(draft/'validation.json');validation.update(selected_unique_urls=len(accepted),selected_counties=len(counts),prior_saved_robots_rules_checked=True,manual_anchor_review=True)
write(batch/'validation.json',validation)
summary=read(draft/'summary.json');summary.update(selected_unique_urls=len(accepted),selected_counties=len(counts),selected_categories=dict(Counter(s['category'] for s in accepted)),
 selected_association_strengths=dict(Counter(s['source_association_strength'] for s in accepted)),selected_previously_targeted_counties=len(counts),
 selection_status_counts=dict(Counter(r['selection_status'] for r in candidates)),reviewed_draft=draft.relative_to(ROOT).as_posix())
summary['config_merge'].update(snapshot_path=(batch/prior.name).relative_to(ROOT).as_posix(),merged_config_path=(batch/'merged_collection_config.json').relative_to(ROOT).as_posix(),merged_config_sha256=sha(batch/'merged_collection_config.json'))
summary['outputs']={p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in batch.iterdir() if p.is_file()}
write(batch/'summary.json',summary)
write(OUT/'manual_review.json',{'reviewed_at':datetime.now(timezone.utc).isoformat(),'draft':draft.relative_to(ROOT).as_posix(),'all_anchors_reviewed':30,'accepted':len(accepted),'excluded':len(excluded),'rows':review})
write(OUT/'reviewed_packet.json',{'batch':batch.relative_to(ROOT).as_posix(),'selected_urls':len(accepted),'selected_counties':len(counts),
 'manual_review_sha256':sha(OUT/'manual_review.json'),'draft_preserved':True})
print(json.dumps(read(OUT/'reviewed_packet.json')))
