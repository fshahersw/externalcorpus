"""Prepare a new offline county-site entry snapshot from reviewed exact matches."""
from __future__ import annotations
import collections, copy, csv, datetime as dt, hashlib, json, sqlite3, subprocess, sys, time
from pathlib import Path
from urllib.parse import urlsplit, urljoin

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
GEO=ROOT/'reports/geography'
sys.path.insert(0,str(ROOT/'pipeline'))
import corpus_crawler as engine

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(path):return [json.loads(s) for s in path.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def jsonl(path,data):path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),encoding='utf-8')
def canon(value):return engine.canonical_url(value or '')
def normalize_host(host):return host.lower().removeprefix('www.')
def digest(raw):return hashlib.sha256(raw).hexdigest()

def main():
    prepared_at=now();snap=OUT/'inputs';snap.mkdir(exist_ok=True)
    input_paths={
      'catalog_summary':ROOT/'sources/trellis/catalog/summary.json',
      'catalog_pages':ROOT/'sources/trellis/catalog/downloaded_pages.jsonl',
      'catalog_county_profiles':ROOT/'sources/trellis/catalog/county_profiles.csv',
      'catalog_website_links':ROOT/'sources/trellis/catalog/official_county_websites.jsonl',
      'geography_summary':GEO/'summary.json',
      'county_reconciliation':GEO/'county_reconciliation.jsonl',
      'county_matches':GEO/'county_matches.jsonl',
      'county_ambiguities':GEO/'county_ambiguities.jsonl',
      'non_census_jurisdictions':GEO/'non_census_jurisdictions.jsonl',
      'website_associations':GEO/'website_associations.jsonl',
      'website_issues':GEO/'website_issues.jsonl',
      'candidate_seeds':GEO/'official_county_website_seeds.jsonl',
      'source_config':GEO/'official_county_websites.config.json',
      'census':GEO/'input_snapshots/census.json',
      'catalog_builder':ROOT/'scripts/build_catalog.py',
      'geography_reconciler':GEO/'reconcile_counties.py',
    }
    inputs={};saved={}
    for key,path in input_paths.items():
        before=path.stat();raw=path.read_bytes();after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('Input changed during snapshot: '+str(path))
        destination=snap/(key+path.suffix);destination.write_bytes(raw);saved[key]=destination
        inputs[key]={'source_path':str(path),'snapshot_path':str(destination),'sha256':digest(raw),'bytes':len(raw),'source_modified_at_utc':dt.datetime.fromtimestamp(after.st_mtime,dt.timezone.utc).isoformat()}
    geo=read(saved['geography_summary']);catalog=read(saved['catalog_summary'])
    assert inputs['catalog_county_profiles']['sha256']==geo['inputs']['county_profiles']['sha256']
    assert inputs['census']['sha256']==geo['inputs']['census']['sha256']
    census={r['geoid']:r for r in read(saved['census'])}
    candidates=rows(saved['candidate_seeds'])
    matches={r['source_url']:r for r in rows(saved['county_matches'])}
    association={(r['source_url'],canon(r['canonical_url'])):r for r in rows(saved['website_associations'])}
    pages={r['url']:r for r in rows(saved['catalog_pages'])}

    # Every resources row is excluded, even failed or inactive rows. A historical
    # failure is not permission to silently requeue a URL in this new-entry batch.
    db_urls=collections.defaultdict(list);official_urls=collections.defaultdict(list);paused=collections.defaultdict(list)
    exclusion_inputs=[]
    listing=subprocess.run(['rg','--files','--hidden','--no-ignore','-g','corpus.sqlite3','-g','!**/.git/**'],cwd=ROOT,capture_output=True,text=True,check=True)
    db_paths=sorted({(ROOT/p).resolve() for p in listing.stdout.splitlines() if p.strip()})
    for number,path in enumerate(db_paths,1):
        with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=15) as con:
            con.row_factory=sqlite3.Row;con.execute('BEGIN')
            tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'resources' not in tables:raise RuntimeError('Unrecognized corpus database: '+str(path))
            resource_rows=[dict(r) for r in con.execute('SELECT id,url,status,attempts,updated_at,last_http_status,raw_path,raw_complete FROM resources ORDER BY id')]
            host_rows=[dict(r) for r in con.execute("SELECT * FROM hosts WHERE (pause_reason IS NOT NULL AND pause_reason!='') OR cooldown_until>? ORDER BY host",(time.time(),))] if 'hosts' in tables else []
            fetch_urls=[]
            if 'fetches' in tables:
                for r in con.execute('SELECT id,response_json FROM fetches ORDER BY id'):
                    d=json.loads(r['response_json'])
                    for field in ('requested_url','source_url','final_url'):
                        u=canon(d.get(field))
                        if u:fetch_urls.append({'fetch_id':r['id'],'field':field,'url':u})
            con.rollback()
        db_snapshot=snap/f'database_{number:02d}.json'
        write(db_snapshot,{'source_database':str(path),'snapshot_at_utc':now(),'resources':resource_rows,'fetch_url_observations':fetch_urls,'paused_or_cooling_hosts':host_rows})
        exclusion_inputs.append({'path':str(path),'read_mode':'read-only SQLite transaction','snapshot_path':str(db_snapshot),'snapshot_sha256':digest(db_snapshot.read_bytes()),'resource_rows':len(resource_rows),'fetch_url_observations':len(fetch_urls),'paused_or_cooling_hosts':len(host_rows)})
        for r in resource_rows:
            u=canon(r['url'])
            if u:db_urls[u].append({'database':str(path),'snapshot_path':str(db_snapshot),'resource_id':r['id'],'status':r['status'],'attempts':r['attempts'],'last_http_status':r['last_http_status']})
        for r in fetch_urls:db_urls[r['url']].append({'database':str(path),'snapshot_path':str(db_snapshot),'fetch_id':r['fetch_id'],'field':r['field']})
        for r in host_rows:paused[normalize_host(r['host'])].append({'path':str(path),'snapshot_path':str(db_snapshot),'host':r['host'],'pause_reason':r.get('pause_reason'),'cooldown_until':r.get('cooldown_until')})

    # Retain original fetch/attempt evidence; do not confuse an unfetched link
    # inventory or government-domain registration with a captured website.
    source_paths=set()
    for source in sorted((ROOT/'sources').glob('official*')):
        source_paths.update(source.glob('metadata/*.json'))
        source_paths.update(source.glob('manifests/*.jsonl'))
        source_paths.update(source.glob('indexes/*manifest*.json'))
        source_paths.update(source.glob('indexes/source_index.json'))
        source_paths.update(source.glob('continuation/*url_manifest.jsonl'))
    source_snapshots=[]
    for path in sorted(source_paths):
        raw=path.read_bytes()
        if path.suffix=='.jsonl':data=[json.loads(s) for s in raw.decode('utf-8-sig').splitlines() if s.strip()]
        else:
            d=json.loads(raw.decode('utf-8-sig'));data=d if isinstance(d,list) else [d]
        source_sha=digest(raw)
        source_snapshots.append({'path':str(path),'sha256':source_sha,'records':len(data)})
        for number,r in enumerate(data,1):
            if not isinstance(r,dict):continue
            status=str(r.get('verification_status') or r.get('status') or '')
            attempted=(path.parent.name=='metadata' or path.name in ('fetches.jsonl','attempted_url_manifest.jsonl','captured_url_manifest.jsonl') or r.get('retrieved_at_utc') or r.get('http_status') or r.get('raw_path') or r.get('evidence_path'))
            if not attempted or status in ('discovered_not_fetched','pending_candidate','unverified_candidate'):continue
            selected={k:r.get(k) for k in ('source_url','requested_url','final_url','official_url','url','verification_status','status','http_status','raw_path','evidence_path','retrieved_at_utc') if r.get(k) is not None}
            ref={'path':str(path),'record_number':number,'file_sha256':source_sha,'record':selected}
            for field in ('source_url','requested_url','final_url','official_url','url'):
                u=canon(r.get(field))
                if u:official_urls[u].append(ref)
    write(snap/'official_source_files.json',source_snapshots)
    exclusion_inputs.append({'kind':'saved_official_sources','file_count':len(source_snapshots),'snapshot_path':str(snap/'official_source_files.json')})

    pause_paths=[]
    for source in sorted((ROOT/'sources').glob('official*')):
        pause_paths.extend(source.glob('indexes/paused_hosts.json'))
        pause_paths.extend(source.glob('continuation/blocked_hosts.json'))
    for path in sorted(pause_paths):
        raw=path.read_bytes();d=json.loads(raw.decode('utf-8-sig'))
        for host,detail in (d.items() if isinstance(d,dict) else ((h,{'reason':'persisted_blocked_host'}) for h in d)):
            paused[normalize_host(host)].append({'path':str(path),'sha256':digest(raw),'host':host,'detail':detail})

    decisions=[];seeds=[]
    for candidate in candidates:
        r=copy.deepcopy(candidate);u=canon(r['url']);source=r['discovered_from'];match=matches.get(source);assoc=association.get((source,u));page=pages.get(source)
        reason=None;evidence=[]
        if not u:reason='invalid_url'
        elif not match or match['match_status']!='matched' or not match['match_method'].startswith(('exact_','explicit_saint_spelling_variant')):reason='no_reviewed_exact_census_match'
        elif r['jurisdiction']['geoid'] not in census:reason='missing_census_geoid'
        elif not assoc or assoc.get('website_validation_status')!='observed_href':reason='not_an_observed_website_href'
        elif not page or not page.get('status') or not 200<=int(page['status'])<300:reason='source_profile_not_successfully_captured'
        elif u in db_urls:reason='already_enqueued_or_fetched_in_corpus_database';evidence=db_urls[u]
        elif u in official_urls:reason='previously_attempted_or_captured_official_source';evidence=official_urls[u]
        elif normalize_host(urlsplit(u).hostname) in paused:reason='persisted_paused_or_cooling_host';evidence=paused[normalize_host(urlsplit(u).hostname)]
        elif any(engine.ACTION_SEGMENT.fullmatch(segment) for segment in urlsplit(u).path.split('/')):reason='account_or_mutating_action_path'
        if not reason:
            county=census[r['jurisdiction']['geoid']]
            assert county['state']==r['jurisdiction']['state'] and county['name']==r['jurisdiction']['county']
            assert r['jurisdiction']['geoid']==r['jurisdiction']['state_fips']+r['jurisdiction']['county_fips']
            assert match['census_geoid']==r['jurisdiction']['geoid']
            assert r['site_authority_verified'] is False and r['authority_classification']=='trellis_reported_government_site'
            website=r['provenance']['website_field']
            hrefs=[x for x in website['candidates'] if x.get('observed_href') and canon(urljoin(source,x['observed_href']))==u and x.get('method') in ('html_website_field_href','markdown_website_field_link')]
            if not hrefs:reason='no_matching_observed_href_in_provenance'
            else:
                evidence_paths=[ROOT/page[k] for k in ('source_path','html_path','markdown_path') if page.get(k)]
                assert all(path.exists() for path in evidence_paths)
                assert digest((ROOT/page['source_path']).read_bytes())==page['content_sha256'],'Source provider artifact changed since catalog snapshot: '+source
                r['url']=u;r['scope']={'host':urlsplit(u).netloc,'path_prefixes':['/']}
                r['batch_id']=OUT.name
                r['provenance']['entry_batch_snapshot']={'directory':str(OUT),'prepared_at_utc':prepared_at,'catalog_generated_at':catalog['updated_at'],'geography_generated_at':geo['generated_at'],'candidate_seed_snapshot':str(saved['candidate_seeds']),'candidate_seed_snapshot_sha256':inputs['candidate_seeds']['sha256'],'reconciliation_snapshot':str(saved['county_reconciliation']),'reconciliation_snapshot_sha256':inputs['county_reconciliation']['sha256'],'census_snapshot':str(saved['census']),'census_snapshot_sha256':inputs['census']['sha256']}
                r['provenance']['source_profile_evidence']={'source_url':source,'provider_response_path':str(ROOT/page['source_path']),'provider_response_sha256':page['content_sha256'],'extracted_html_path':str(ROOT/page['html_path']) if page.get('html_path') else None,'extracted_markdown_path':str(ROOT/page['markdown_path']) if page.get('markdown_path') else None,'provider':page.get('provider'),'observed_at':page.get('observed_at')}
                r['authority_note']='Exact Census name matching verifies geography association only. This remains a Trellis-reported website; site ownership and authority have not been independently verified.'
                seeds.append(r)
        decisions.append({'url':u or r['url'],'source_profile_url':source,'geoid':r['jurisdiction']['geoid'],'state':r['jurisdiction']['state'],'county':r['jurisdiction']['county'],'match_method':r.get('match_method'),'decision':reason or 'included_new_observed_href','exclusion_evidence':evidence,'authority_classification':r['authority_classification'],'site_authority_verified':r['site_authority_verified']})

    allowed=sorted({r['scope']['host'] for r in seeds})
    config=read(saved['source_config'])
    config.update(allow=[{'host':h,'path_prefixes':['/']} for h in allowed],workers=3,per_host_delay=2.0,max_retries=1,backoff_base_seconds=30,max_backoff_seconds=900,min_free_bytes=10737418240,follow_links=False,max_depth=0)
    cfg=engine.Config.from_dict(config)
    assert len({(r['url'],r['jurisdiction']['geoid']) for r in seeds})==len(seeds)
    for r in seeds:
        assert cfg.allowed(r['url'],r['scope'])==(True,'allowed')
        assert r['url'] not in db_urls and r['url'] not in official_urls
        assert normalize_host(urlsplit(r['url']).hostname) not in paused
    jsonl(OUT/'seeds.jsonl',seeds);write(OUT/'config.json',config);jsonl(OUT/'decisions.jsonl',decisions)
    jsonl(OUT/'excluded.jsonl',[r for r in decisions if r['decision']!='included_new_observed_href'])
    write(OUT/'input_manifest.json',inputs)
    jsonl(OUT/'exclusion_urls.snapshot.jsonl',[{'url':u,'kind':kind,'evidence':refs} for kind,mapping in (('corpus_database_resource_or_fetch',db_urls),('saved_official_source_attempt_or_capture',official_urls)) for u,refs in sorted(mapping.items())])
    write(OUT/'paused_hosts.snapshot.json',paused)
    states=[]
    for state in sorted({r['jurisdiction']['state'] for r in candidates}):
        picked=[r for r in seeds if r['jurisdiction']['state']==state]
        all_rows=[r for r in decisions if r['state']==state]
        states.append({'state':state,'candidate_associations':len(all_rows),'new_seed_associations':len(picked),'new_unique_urls':len({r['url'] for r in picked}),'new_unique_geoids':len({r['jurisdiction']['geoid'] for r in picked}),'decisions':dict(collections.Counter(r['decision'] for r in all_rows))})
    write(OUT/'state_counts.json',states)
    with (OUT/'state_counts.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=['state','candidate_associations','new_seed_associations','new_unique_urls','new_unique_geoids'];writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(states)
    summary={'prepared_at_utc':prepared_at,'finished_at_utc':now(),'batch_id':OUT.name,'network_requests':0,'collector_launches':0,'source_catalog_generated_at':catalog['updated_at'],'source_geography_generated_at':geo['generated_at'],'catalog_processed_new_files':catalog['processed_this_pass'],'source_county_profiles':geo['observed_county_profiles'],'source_exactly_matched_profiles':geo['matched_profiles'],'source_ambiguous_profiles_preserved':geo['ambiguous_profiles'],'source_non_census_court_scopes_preserved':geo['non_census_jurisdictions'],'candidate_seed_associations':len(candidates),'candidate_unique_urls':len({r['url'] for r in candidates}),'new_seed_associations':len(seeds),'new_unique_urls':len({r['url'] for r in seeds}),'new_unique_geoids':len({r['jurisdiction']['geoid'] for r in seeds}),'new_states':len({r['jurisdiction']['state'] for r in seeds}),'allowed_exact_hosts':len(allowed),'decision_counts':dict(collections.Counter(r['decision'] for r in decisions)),'authority_classifications':dict(collections.Counter(r['authority_classification'] for r in seeds)),'government_namespace_signals':dict(collections.Counter(r['government_namespace_signal'] for r in seeds)),'site_authority_verified_count':0,'unique_corpus_database_url_exclusions':len(db_urls),'unique_saved_official_source_url_exclusions':len(official_urls),'normalized_paused_or_cooling_host_exclusions':len(paused),'corpus_database_count':len(db_paths),'database_overlap_in_ready_seeds':0,'saved_official_source_overlap_in_ready_seeds':0,'follow_links':False,'max_depth':0,'full_corpus_complete':False,'input_manifest_path':str(OUT/'input_manifest.json'),'exclusion_inputs':exclusion_inputs,'notes':['Only exact reviewed geography associations and actual observed Website-field hrefs are included. No CISA-derived entry URLs are added to this delta.','Every resource URL already enqueued in any workspace corpus.sqlite3 database is excluded, including inactive, failed, and offline validation queues.','Original ambiguous and non-Census court scopes are retained in the immutable input snapshots; no historical-to-current crosswalk is inferred.','URL exclusions use exact canonical URLs without conflating http/https or www/non-www URLs. Host-block exclusion conservatively groups www and bare host names.','The config is scoped to this new batch. Do not replace an active collection config with it without merging its existing allowlist.','All authority labels remain Trellis-reported and unverified. A Census match does not verify website ownership or court authority.']}
    write(OUT/'summary.json',summary)
    write(OUT/'artifact_hashes.json',{name:digest((OUT/name).read_bytes()) for name in ('seeds.jsonl','config.json','summary.json','decisions.jsonl','input_manifest.json')})
    print(json.dumps({k:v for k,v in summary.items() if k not in ('exclusion_inputs','notes')},indent=2))

if __name__=='__main__':main()
