"""Read-only county publication/backfill inventory; no crawler controls changed."""
from pathlib import Path
import json, sqlite3, hashlib
from collections import Counter
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def db(path):
    c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    c.execute('pragma query_only=ON');return c
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def jsonl(path,records):
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf8')

with db(ROOT/'delivery/focused_legal_corpus/focused.sqlite3') as c:
    published={(r['collection'],r['source_url'],r['raw_sha256']) for r in c.execute("select collection,source_url,raw_sha256 from documents where collection like 'corpus/county%'")}
collections=[];gaps=[]
for folder in sorted((ROOT/'corpus').glob('county*')):
    path=folder/'corpus.sqlite3'
    if not path.exists():continue
    with db(path) as c:
        status=dict(c.execute('select status,count(*) from resources group by status').fetchall())
        item={'collection':folder.relative_to(ROOT).as_posix(),'statuses':status,'publication_missing_downloaded':0}
        for r in c.execute("select * from resources where status='downloaded' and raw_complete=1"):
            if (item['collection'],r['url'],r['sha256']) in published:continue
            item['publication_missing_downloaded']+=1
            raw=(folder/r['raw_path']).resolve();metadata=(folder/r['metadata_path']).resolve()
            evidence={'raw_sha256_verified':raw.is_file() and sha(raw)==r['sha256'],'metadata_exists':metadata.is_file()}
            text=(folder/r['text_path']).resolve() if r['text_path'] else None
            meta=json.loads(metadata.read_text(encoding='utf8')) if metadata.is_file() else {}
            text_sha=sha(text) if text and text.is_file() else None
            evidence['text_exists']=bool(text and text.is_file())
            evidence['text_expected_sha256']=meta.get('text_sha256')
            evidence['text_sha256_matches_metadata']=bool(text_sha and meta.get('text_sha256')==text_sha)
            contexts=[]
            for cx in c.execute('select c.seed_json from contexts c join resource_contexts rc on c.id=rc.context_id where rc.resource_id=?',(r['id'],)):
                seed=json.loads(cx[0]);contexts.append({k:seed[k] for k in ['jurisdiction','category','source_family','source_association_strength','court_label','candidate_county_association'] if k in seed})
            gaps.append({'collection':item['collection'],'resource_id':r['id'],'source_url':r['url'],'raw_sha256':r['sha256'],
                'raw_path':raw.relative_to(ROOT).as_posix(),'text_path':text.relative_to(ROOT).as_posix() if text else None,
                'text_sha256':text_sha,'metadata_path':metadata.relative_to(ROOT).as_posix(),'metadata_sha256':sha(metadata),
                'title':r['title'],'extraction_status':r['extraction_status'],'contexts':contexts,'validation':evidence,
                'quality':'Saved original awaiting coordinated publication validation; county association remains as recorded.'})
        item['active_run']=json.loads((folder/'active_run.json').read_text(encoding='utf8')) if (folder/'active_run.json').exists() else None
        collections.append(item)
with db(ROOT/'sources/trellis/worker/frontier.sqlite3') as c:
    trellis_status=dict(c.execute("select status,count(*) from frontier where category='county' and in_scope=1 group by status").fetchall())
    trellis_gaps=[dict(r) for r in c.execute("select url,status,attempts,error,discovered_from,state from frontier where category='county' and in_scope=1 and status not in ('downloaded','captured_elsewhere') order by priority,url")]
with db(ROOT/'sources/trellis/catalog/catalog.sqlite3') as c:
    county_count,state_count=c.execute('select count(*),count(distinct state) from counties').fetchone()
    website_status=dict(c.execute('select website_validation_status,count(*) from counties group by website_validation_status').fetchall())
    saved_urls={r[0] for r in c.execute('select url from counties')}
for r in trellis_gaps:
    r['catalog_already_has_url']=r['url'] in saved_urls
    r['queue_row_is_not_validated_county_identity']=True
    r['selection_note']='Must validate exact county URL/identity before browser backfill; queue includes malformed or noncounty discoveries.'
jsonl(OUT/'unpublished_county_captures.jsonl',gaps)
jsonl(OUT/'trellis_county_frontier_gaps.jsonl',trellis_gaps)
summary={'audited_at':datetime.now(timezone.utc).isoformat(),'collections':collections,'unpublished_downloaded_captures':len(gaps),
 'unpublished_raw_hashes_valid':sum(r['validation']['raw_sha256_verified'] for r in gaps),
 'unpublished_text_with_matching_expected_digest':sum(r['validation']['text_sha256_matches_metadata'] for r in gaps),
 'trellis_county_frontier_statuses':trellis_status,'trellis_catalog_counties':county_count,'trellis_catalog_states':state_count,
 'trellis_official_website_statuses':website_status,'trellis_frontier_gap_rows':len(trellis_gaps),
 'note':'Queue counts are observed URL counts, not all-US county completeness. Public profile access differs from paid case-document entitlement.',
 'network_requests':0,'publication_modified':False}
(OUT/'audit.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in summary.items() if k!='collections'},ensure_ascii=True))
