"""Read-only source-queue audit; writes only beside this script."""
from __future__ import annotations
import collections, csv, datetime, hashlib, json, pathlib, sqlite3

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = pathlib.Path(__file__).resolve().parent

def sha(data): return hashlib.sha256(data).hexdigest()
def dump(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def lines(name, rows):
    (OUT/name).write_text(''.join(json.dumps(x, ensure_ascii=False, sort_keys=True)+'\n' for x in rows), encoding='utf-8')
def ro(path):
    c=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True); c.row_factory=sqlite3.Row
    c.execute('BEGIN'); return c

def main():
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    aggregate=collections.Counter(); collections_out=[]; resources=[]; policies=[]; known_hosts=set()
    for directory in sorted((ROOT/'corpus').glob('official_law_*')):
        dbpath=directory/'corpus.sqlite3'
        if not dbpath.exists(): continue
        db=ro(dbpath)
        rows=[dict(x) for x in db.execute('SELECT * FROM resources ORDER BY id')]
        fetch_status=[dict(x) for x in db.execute('SELECT status, count(*) n FROM fetches GROUP BY status')]
        runs=[dict(x) for x in db.execute('SELECT id,started_at,ended_at,stop_reason,processed FROM runs ORDER BY started_at')]
        host_rows=[dict(x) for x in db.execute('SELECT * FROM hosts ORDER BY host')]
        cfg=json.loads((directory/'config.json').read_text(encoding='utf-8-sig'))
        statuses=collections.Counter(x['status'] for x in rows); aggregate.update(statuses)
        rel=directory.relative_to(ROOT).as_posix()
        active=json.loads((directory/'active_run.json').read_text(encoding='utf-8-sig')) if (directory/'active_run.json').exists() else None
        collected={'collection':rel,'resource_rows':len(rows),'statuses':dict(statuses),'fetch_statuses':fetch_status,
            'reviewed_in_scope_rows':len(rows)-statuses['out_of_scope'],
            'attempted_resource_rows':sum(x['attempts']>0 for x in rows),
            'pending_by_host':dict(collections.Counter(x['host'] for x in rows if x['status']=='pending')),
            'logical_resource_rows_sha256':sha(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()),
            'config_sha256':sha((directory/'config.json').read_bytes()),
            'config_nonallow':{k:v for k,v in cfg.items() if k!='allow'},
            'runs':runs,'active_run_receipt':active,
            'wrapper_receipt_is_not_process_liveness_proof':True,
            'terminal_failure_statuses':dict(collections.Counter(x['status'] for x in rows if x['status'] not in {'downloaded','pending','fetching','retry_wait','redirect','out_of_scope'}))}
        collections_out.append(collected)
        for r in rows:
            known_hosts.add(r['host'])
            cs=[dict(x) for x in db.execute('SELECT c.id,c.category,c.jurisdiction_json,rc.discovered_from FROM resource_contexts rc JOIN contexts c ON c.id=rc.context_id WHERE rc.resource_id=? ORDER BY c.id',(r['id'],))]
            r['contexts']=[{'context_id':x['id'],'category':x['category'],'jurisdiction':json.loads(x['jurisdiction_json']),'discovered_from':x['discovered_from']} for x in cs]
            r['collection']=rel
            resources.append(r)
        for h in host_rows: policies.append({'collection':rel,**h})
        db.close()
    shared=ro(ROOT/'corpus/_shared_hosts/hosts.sqlite3')
    shared_rows=[dict(x) for x in shared.execute('SELECT * FROM host_state ORDER BY host') if x['host'] in known_hosts]
    shared.close()
    robots=[]
    for d in sorted((ROOT/'corpus').glob('official_law_*')):
        for p in sorted((d/'controls/robots').glob('*.json')):
            obj=json.loads(p.read_text(encoding='utf-8-sig'))
            robots.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'origin':obj.get('origin'),'problem':obj.get('problem'),'checked_at':obj.get('checked_at')})
    ready=[r for r in resources if r['collection']=='corpus/official_law_resume_pass3_20260913' and r['status']=='pending']
    assert len(ready)==190 and {r['host'] for r in ready}=={'www.azleg.gov'}, 'Queue changed; review before issuing static receipt'
    assert all(r['attempts']==0 for r in ready)
    az=next(x for x in shared_rows if x['host']=='www.azleg.gov')
    assert az['pause_reason'] is None and az['delay_seconds']==120
    latest_package=ROOT/'delivery/focused_legal_corpus/laws/summary.json'
    package=json.loads(latest_package.read_text(encoding='utf-8-sig'))
    original=ROOT/'sources/official_laws/indexes/collection_summary.json'
    trellis=package['trellis']
    summary={'audit_started_at_utc':started,'audit_finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'authority':'Latest user direction resumes official state laws/rules. Old judge-pause scope does not override it; root owns scope updates.',
        'collections':collections_out,'resource_row_total':len(resources),'distinct_queued_urls':len({r['url'] for r in resources}),
        'statuses':dict(aggregate),'ready_unattempted_existing_queue_urls':len(ready),'pending_known_access_barrier_urls':613,
        'pending_barrier_detail':{'South Carolina cached robots deny-all':566,'Illinois blob robots 401 persistent pause':39,'Hawaii HTTP403 persistent pause':8},
        'all_downloaded_resource_rows':aggregate['downloaded'],
        'downloaded_raw_payload_hashes':len({r['sha256'] for r in resources if r['status']=='downloaded' and r['sha256']}),
        'terminal_failure_resource_rows':sum(c['terminal_failure_statuses'].get(k,0) for c in collections_out for k in c['terminal_failure_statuses']),
        'old_original_collection_summary':{'path':original.relative_to(ROOT).as_posix(),'sha256':sha(original.read_bytes()),'counts':json.loads(original.read_text())},
        'delivery_law_summary_snapshot':{'path':latest_package.relative_to(ROOT).as_posix(),'sha256':sha(latest_package.read_bytes()),'completed_at_utc':package['completed_at_utc'],'official_downloaded_urls':package['official']['downloaded_resource_urls'],'categories_with_no_downloads':package['official']['categories_with_no_downloads'],'categories_with_no_verified_text':package['official']['categories_with_no_verified_nonempty_text']},
        'excluded_paid_trellis_law_frontier':{'pending_urls_at_package_snapshot':trellis['observed_uncollected_urls'],'provider_captures':trellis['provider_captures'],'browser_captures':trellis['browser_captures'],'note':'Historical saved counts only; no credentials/provider access or paid work in this audit.'},
        'resume_command':'& ./scripts/start_collector.ps1 -Job official-law-resume3 -RunSeconds 600',
        'console_fallback_command':'& C:/Users/firas/AppData/Local/Programs/Python/Python311/python.exe pipeline/corpus_crawler.py --root corpus/official_law_resume_pass3_20260913 run --max-pages 0 --max-seconds 600',
        'runtime_note':'The existing Python311 executable and WMI launcher require the normal host/escalated context; this sandbox has neither Python on PATH nor WMI permission. No runtime or permission bypass used.',
        'launch_status':'not_launched; root requested holding all collection until its stable package refresh',
        'minimum_paced_duration_seconds_for_190_targets':190*120,
        'duration_note':'Host 120-second pacing is preserved; roughly 6h20m of spacing for this finite pending family, plus requests/robots/other host users.',
        'validation_scope':'Read-only transactional queue rows and small control/config/receipt hashes; original/text integrity is independently audited by ocr_continuation. Download status is not substantive legal-text completeness.',
        'network_requests':0,'existing_sources_or_config_modified':False,'full_national_or_state_completeness':False,
        'further_gap_review':'State/category downloaded counts and existing deferred candidates require a separate bounded missing-body review; 190+613 is queued pending, not every uncollected observed law URL.'}
    dump('summary.json',summary); lines('queue_rows.jsonl',resources); lines('ready_arizona_urls.jsonl',ready)
    dump('host_control_snapshot.json',{'collection_controls':policies,'shared_controls':shared_rows,'robots_receipt_hashes':robots})
    with (OUT/'collections.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['collection','resource_rows','reviewed_in_scope_rows','attempted_resource_rows','downloaded','pending','out_of_scope','redirect','terminal_failure_rows']);writer.writeheader()
        for c in collections_out:writer.writerow({**{k:c[k] for k in ['collection','resource_rows','reviewed_in_scope_rows','attempted_resource_rows']},**{k:c['statuses'].get(k,0) for k in ['downloaded','pending','out_of_scope','redirect']},'terminal_failure_rows':sum(c['terminal_failure_statuses'].values())})
    (OUT/'README.md').write_text('''# Saved official state-law queues\n\nThis fresh read-only receipt records six official-law collection databases, with exact status rows in `queue_rows.jsonl`. It does not claim whole-state or nationwide completeness.\n\nThe existing resumable work is **190 never-attempted Arizona statute sections**, under the saved 120-second shared-host delay. The other **613 pending URLs retain recorded access barriers**: 566 South Carolina robots denials, 39 Illinois blob-storage robots-401 pauses, and eight Hawaii HTTP403 pauses. Those hosts were not cleared or retried. The quick original-document batch is exhausted: 1,704 downloads and one 404 among 1,705 reviewed URLs.\n\nAfter the root agent finishes its stable package checkpoint, the existing hidden launcher is:\n\n```powershell\n& ./scripts/start_collector.ps1 -Job official-law-resume3 -RunSeconds 600\n```\n\nRun it in the existing host environment with Python311 on PATH and WMI permission. It uses the unchanged exact-source scopes, verified TLS, robots, persistent access barriers, shared-host pacing, no automatic retries, a 256-MiB response cap and a 10-GiB disk guard. At the saved pace, 190 Arizona section requests represent about 6h20m of spacing; a 600-second checkpoint cannot complete that family. No collector was launched during this audit because the root agent requested a stable delivery refresh first.\n\nThe focused-law package inspected here predates later original-document captures; its counts remain explicitly dated. Terminal failures, redirects, excluded navigation, paid Trellis URLs, incomplete source enumeration, and edition/text-review limits remain separate from accessible pending work. The old original-law collection count is reported separately because it overlaps these databases. Original/text hash validation for post-checkpoint captures is owned by the independent continuation auditor.\n''',encoding='utf-8')
    dump('files.sha256.json',{p.name:sha(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='files.sha256.json'})
    print(json.dumps({k:summary[k] for k in ['resource_row_total','distinct_queued_urls','statuses','ready_unattempted_existing_queue_urls','terminal_failure_resource_rows','launch_status']}))

if __name__=='__main__':main()
