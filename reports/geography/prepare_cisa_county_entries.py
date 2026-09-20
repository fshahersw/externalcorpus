"""Prepare an offline .gov county-domain entry queue, without asserting county FIPS."""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import urllib.parse

from reconcile_counties import now, url_value, write_table

DEFAULT_ROOT=Path(__file__).resolve().parents[2]
REGISTRY='sources/official_courts/datasets/cisa_county_government_domains.json'
SUCCESS={'retrieved','downloaded','captured','succeeded','redirect','no_content'}
ACTIVE={'pending','fetching','queued','in_progress','in-progress','retry_wait','running'}


def load_records(path):
    raw=path.read_bytes()
    if path.suffix=='.jsonl':records=[json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    else:
        value=json.loads(raw.decode('utf-8-sig'))
        if isinstance(value,list):records=value
        elif isinstance(value,dict):
            records=next((value[key] for key in ('sources','documents','records','entries','pages','results') if isinstance(value.get(key),list)),[])
            if not records and any(key in value for key in ('url','official_url','source_url')):records=[value]
        else:records=[]
    return records,hashlib.sha256(raw).hexdigest()


def record_urls(record):
    values=set()
    for key in ('url','official_url','source_url','requested_url','final_url'):
        value,_=url_value(record.get(key))
        if value:values.add(value)
    return values


def collect_exclusions(root):
    captured=collections.defaultdict(list)
    active=collections.defaultdict(list)
    paused=collections.defaultdict(list)
    inspected=[]
    snapshot=[]
    paths=[]
    sources=root/'sources'
    for source in sorted(sources.glob('official*')) if sources.exists() else []:
        for folder,pattern in (('manifests','*.jsonl'),('indexes','*.json'),('continuation','*url_manifest.jsonl')):
            directory=source/folder
            if directory.exists():paths.extend(sorted(directory.glob(pattern)))
    for path in paths:
        relative=path.relative_to(root).as_posix()
        records,sha=load_records(path)
        inspected.append({'path':relative,'sha256':sha,'records_read':len(records)})
        for number,row in enumerate(records,1):
            if not isinstance(row,dict):continue
            status=str(row.get('verification_status') or row.get('status') or '').lower()
            http=row.get('http_status') or row.get('status_code')
            try:http=int(http) if http is not None else None
            except (ValueError,TypeError):http=None
            ref={'path':relative,'record_number':number,'status':status,'http_status':http}
            urls=record_urls(row)
            successful=status in SUCCESS or (http is not None and 200<=http<300 and bool(row.get('raw_path') or row.get('evidence_path') or row.get('sha256')))
            for url in urls:
                if successful:captured[url].append(ref)
                elif status in ACTIVE:active[url].append(ref)
            # Historical fetch attempts do not establish a current host pause.
            if path.name!='fetches.jsonl' and (row.get('pause_reason') or status in {'forbidden','unauthorized','challenge','host_paused','blocked_host','http_403','http_401'} or http in (401,403)):
                hosts={urllib.parse.urlsplit(url).netloc for url in urls}
                if row.get('host'):hosts.add(str(row['host']).lower())
                for host in hosts:paused[host].append({**ref,'pause_reason':row.get('pause_reason') or status or f'http_{http}'})
    database_paths=set()
    corpus=root/'corpus'
    if corpus.exists():
        for directory in corpus.iterdir():
            if directory.is_dir() and ('official' in directory.name or 'county' in directory.name):
                database_paths.update(directory.glob('corpus.sqlite3'))
    for source in sorted(sources.glob('official*')) if sources.exists() else []:
        database_paths.update(source.glob('corpus.sqlite3'))
    for path in sorted(database_paths):
        relative=path.relative_to(root).as_posix()
        con=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
        con.row_factory=sqlite3.Row
        try:
            con.execute('BEGIN')
            tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'resources' not in tables:continue
            columns={r[1] for r in con.execute('PRAGMA table_info(resources)')}
            selected=[column for column in ('id','url','status','updated_at','last_http_status','raw_complete') if column in columns]
            rows=[dict(row) for row in con.execute('SELECT '+','.join(selected)+' FROM resources')]
            hosts=[dict(row) for row in con.execute('SELECT * FROM hosts WHERE pause_reason IS NOT NULL AND pause_reason<>\'\'')] if 'hosts' in tables else []
            content=json.dumps({'resources':rows,'paused_hosts':hosts},sort_keys=True,separators=(',',':')).encode()
            inspected.append({'path':relative,'read_mode':'read-only SQLite transaction','selected_rows_sha256':hashlib.sha256(content).hexdigest(),'resource_rows_read':len(rows),'paused_hosts_read':len(hosts)})
            for row in rows:
                url,_=url_value(row.get('url'))
                if not url:continue
                ref={'path':relative,'table':'resources','id':row.get('id'),'status':row.get('status'),'updated_at':row.get('updated_at')}
                if row['status'] in SUCCESS:captured[url].append(ref)
                elif row['status'] in ACTIVE:active[url].append(ref)
            for row in hosts:paused[row['host'].lower()].append({'path':relative,'table':'hosts','pause_reason':row.get('pause_reason'),'updated_at':row.get('updated_at')})
        finally:
            con.rollback();con.close()
    for kind,mapping in (('captured_exact_url',captured),('active_queue_exact_url',active),('known_paused_or_access_denied_host',paused)):
        for value,refs in sorted(mapping.items()):snapshot.append({'kind':kind,'value':value,'evidence':refs})
    return captured,active,paused,inspected,snapshot


def make_queue(registry,registry_sha,captured,active,paused):
    grouped=collections.defaultdict(list)
    invalid=[]
    for number,row in enumerate(registry,1):
        domain=str(row.get('domain','')).strip().lower().rstrip('.')
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.gov',domain) or '..' in domain:
            invalid.append({'registry_record_number':number,'domain':domain,'decision':'invalid_or_non_gov_registered_domain','registry_record':row})
            continue
        grouped[domain].append((number,row))
    seeds=[];decisions=[];hosts=set()
    for domain,records in sorted(grouped.items()):
        url='https://'+domain+'/'
        pair=sorted({domain,'www.'+domain})
        reason=None;evidence=[]
        blocked=[host for host in pair if host in paused]
        if blocked:
            reason='known_paused_host_in_registered_www_pair'
            evidence=[{'host':host,'evidence':paused[host]} for host in blocked]
        elif url in captured:reason='already_captured_exact_url';evidence=captured[url]
        elif url in active:reason='already_in_active_queue_exact_url';evidence=active[url]
        states=sorted({str(row.get('usps','')) for _,row in records if row.get('usps')})
        organizations=sorted({str(row.get('organization','')) for _,row in records if row.get('organization')})
        decision={'domain':domain,'entry_url':url,'allowed_registered_www_hosts':pair,'registry_records':len(records),'registry_record_numbers':[number for number,_ in records],'organizations':organizations,'registry_state_codes':states,'decision':reason or 'included_registry_derived_entry','exclusion_evidence':evidence,'county_name_association':'UNREVIEWED','court_fips_association_verified':False}
        decisions.append(decision)
        if reason:continue
        hints=[{'candidate_geoid':row.get('candidate_geoid'),'candidate_county_name':row.get('candidate_county_name'),'upstream_match_status':row.get('county_match_status'),'assessment':'UNREVIEWED; not assigned as a verified jurisdiction'} for _,row in records]
        seed={'url':url,'source_family':'official_cisa_county_gov_domain_registry','source_category':'registry-derived-site-entry','category':'county_government_entry_unreviewed','jurisdiction':{'country':'US','registry_state_codes':states,'county_name_association':'UNREVIEWED'},'discovered_from':records[0][1].get('discovered_from'),'entry_url_derivation':'HTTPS root entry formed from the registered domain; no claim that this exact entry URL was observed on a fetched website','domain_registration_status':'official_registration_verified_website_not_tested','authority_classification':'official_government_domain_registration','county_name_association':'UNREVIEWED','court_fips_association_verified':False,'registered_domain':domain,'allowed_registered_www_hosts':pair,'redirect_review_policy':'Record every redirect. Destinations outside this seed host pair require review; they never establish a verified county/FIPS mapping. The shared crawler allowlist enforces only the global registered-domain set.','registry_organizations':organizations,'unreviewed_registry_county_hints':hints,'provenance':{'registry_dataset':REGISTRY,'registry_dataset_sha256':registry_sha,'registry_record_numbers':[number for number,_ in records],'official_registry_sources':sorted({str(row.get('discovered_from')) for _,row in records if row.get('discovered_from')}),'registry_evidence_paths':sorted({str(row.get('discovery_evidence_path')) for _,row in records if row.get('discovery_evidence_path')})}}
        seeds.append(seed);hosts.update(pair)
    config={'allow':[{'host':host,'path_prefixes':['/']} for host in sorted(hosts)],'workers':3,'per_host_delay':2.0,'timeout_seconds':30,'max_transfer_seconds':120,'max_response_bytes':16777216,'max_extract_chars':4194304,'min_free_bytes':2147483648,'max_depth':0,'max_retries':1,'backoff_base_seconds':30,'max_backoff_seconds':900,'respect_robots':True,'follow_links':False,'follow_external_allowed_links':False,'pause_host_on_access_block':True,'user_agent':'LegalCorpusResearch/1.0'}
    return seeds,decisions,invalid,config


def prepare(root=DEFAULT_ROOT):
    root=Path(root).resolve();out=root/'reports'/'geography'/'cisa_county_entries'
    out.mkdir(parents=True,exist_ok=True)
    registry,sha=load_records(root/REGISTRY)
    captured,active,paused,inspected,snapshot=collect_exclusions(root)
    seeds,decisions,invalid,config=make_queue(registry,sha,captured,active,paused)
    for name,rows in (('seeds',seeds),('domain_decisions',decisions),('invalid_registry_rows',invalid),('exclusion_snapshot',snapshot)):
        write_table(out,name,rows)
    (out/'config.json').write_text(json.dumps(config,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    summary={'generated_at':now(),'network_requests':0,'registry_dataset':REGISTRY,'registry_dataset_sha256':sha,'registry_records':len(registry),'unique_valid_registered_domains':len(decisions),'duplicate_registry_rows':len(registry)-len(invalid)-len(decisions),'invalid_registry_rows':len(invalid),'ready_entry_urls':len(seeds),'allowed_hosts':len(config['allow']),'decisions':dict(collections.Counter(row['decision'] for row in decisions)),'captured_exact_url_exclusion_set_size':len(captured),'active_queue_exact_url_exclusion_set_size':len(active),'known_paused_or_denied_host_set_size':len(paused),'seed_entry_urls_per_registered_domain':1,'follow_links':False,'max_depth':0,'county_name_association':'UNREVIEWED','court_fips_association_verified':False,'independent_from_trellis_census_match_queue':True,'redirect_limitation':'Registered/www pairs are retained per seed. The unchanged crawler enforces a global allowlist, so cross-pair redirects to another globally allowed registered domain are possible and must be reviewed. Redirects outside the global allowlist are recorded but not fetched.','queue_snapshot_note':'Exclusions reflect captured files and active SQLite queues at preparation time. Re-run preparation immediately before ingestion to refresh them; no workers were started.','full_corpus_complete':False,'inspected_collections':inspected}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({key:value for key,value in summary.items() if key!='inspected_collections'},indent=2))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,default=DEFAULT_ROOT)
    prepare(parser.parse_args().workspace)
