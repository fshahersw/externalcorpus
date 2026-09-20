"""Persist scope and verified launch facts without changing collector queues."""
from pathlib import Path
import datetime,hashlib,json,sqlite3
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,r):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
def main():
    jobs={'official-law-resume3':'corpus/official_law_resume_pass3_20260913','official-law-state-rules':'corpus/official_law_state_rules_followup_20260914','county-local-documents':'corpus/county_local_documents_20260914','county-wa-rules':'corpus/county_local_rules_washington_20260914'}
    packets=[('sources/counties/local_documents_20260914','county-local-documents'),('sources/counties/local_documents_20260914/batches/20260914T070014424407Z','county-local-documents'),('sources/counties/local_documents_20260914/batches/wa_local_rules_20260914T065327354995Z','county-wa-rules'),('sources/counties/local_documents_20260914/batches/wa_local_rules_20260914T070412008149Z','county-wa-rules'),('sources/official_laws/state_rules_followup_20260914','official-law-state-rules'),('sources/official_laws/state_rules_followup_20260914/continuation_20260914T065424Z','official-law-state-rules')]
    packets.append(('sources/counties/local_documents_20260914/batches/20260914T075036205099Z','county-local-documents'))
    packets.append(('sources/counties/local_documents_20260914/batches/20260918T163032097064Z','county-local-documents'))
    db=sqlite3.connect((ROOT/'delivery/focused_legal_corpus/focused.sqlite3').as_uri()+'?mode=ro',uri=True)
    try:indexed=set(db.execute("SELECT collection,source_url,raw_sha256 FROM documents WHERE capture_kind='direct_public_capture'"))
    finally:db.close()
    unpublished=[]
    progress={}
    for job,name in jobs.items():
        base=ROOT/name;c=sqlite3.connect((base/'corpus.sqlite3').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
        try:
            statuses={r[0]:r[1] for r in c.execute('SELECT status,count(*) FROM resources GROUP BY status')}
            latest=c.execute('SELECT id,started_at,ended_at,stop_reason,processed FROM runs ORDER BY started_at DESC LIMIT 1').fetchone()
            unpublished.extend({'collection':name,'source_url':r[0],'raw_sha256':r[1]} for r in c.execute("SELECT url,sha256 FROM resources WHERE status='downloaded'") if (name,r[0],r[1]) not in indexed)
        finally:c.close()
        active=read(base/'active_run.json')
        progress[job]={'collection':name,'resource_statuses':statuses,'latest_run':dict(latest) if latest else None,'wrapper_process_id':active['process_id'],'wrapper_reported_status':active['status'],'wrapper_started_at':active['started_at_utc'],'config_sha256':sha(base/'config.json')}
    receipts=[]
    for folder,job in packets:
        batch=ROOT/folder;review=read(batch/'root_review.json');assert review['validated'] and review.get('unresolved_material_findings',0)==0
        for name,digest in review['input_sha256'].items():assert sha(batch/name)==digest
        seeds=[json.loads(x) for x in (batch/'seeds.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        c=sqlite3.connect((ROOT/jobs[job]/'corpus.sqlite3').as_uri()+'?mode=ro',uri=True)
        try:
            count=sum(c.execute('SELECT 1 FROM resources WHERE url=?',(s['url'],)).fetchone() is not None for s in seeds)
            db_seeds={json.dumps(json.loads(r[0]),sort_keys=True,separators=(',',':')) for r in c.execute('SELECT seed_json FROM contexts')}
            bound=sum(json.dumps(s,sort_keys=True,separators=(',',':')) in db_seeds for s in seeds)
        finally:c.close()
        assert count==bound==len(seeds)
        receipt={'verified_at':now(),'packet':folder,'collection':jobs[job],'review_receipt_sha256':sha(batch/'root_review.json'),'reviewed_input_sha256':review['input_sha256'],'expected_seed_urls':len(seeds),'ingested_urls_verified':count,'exact_seed_payloads_verified':bound,'job':job,'launch_observation':progress[job],'network_requests_by_verifier':0}
        write(batch/'root_ingest_checkpoint.json',receipt);receipts.append(folder+'/root_ingest_checkpoint.json')
    result={'observed_at':now(),'jobs':progress,'ingest_checkpoints':receipts,'quality_requirements':'reports/county_law_focus_20260914/DATA_QUALITY.md','latest_published_aggregate':read(ROOT/'delivery/focused_legal_corpus/summary.json'),'new_downloads_are_not_yet_in_that_published_snapshot':True,'next_reviewed_state_packet':'sources/official_laws/state_rules_followup_20260914/continuation_20260914T065424Z/root_review.json','new_state_packet_ingested':True,'full_national_content_complete':False}
    result.update(new_downloads_are_not_yet_in_that_published_snapshot=bool(unpublished),unpublished_captures=unpublished)
    write(HERE/'execution_checkpoint.json',result)
    scope=read(HERE/'scope.json');scope.update(quality_requirements=result['quality_requirements'],latest_execution_checkpoint='reports/county_law_focus_20260914/execution_checkpoint.json',active_collections=list(jobs.values()),next_reviewed_state_packet=result['next_reviewed_state_packet']);write(HERE/'scope.json',scope)
    legacy=ROOT/'reports/remaining_resume_20260913/scope.json';r=read(legacy)
    for name in jobs.values():
        if name not in r['reviewed_collections']:r['reviewed_collections'].append(name)
    r.update(superseded_at=None,superseded_by=None,collector_restart_authorized_during_judge_focus=False,latest_scope_path='reports/county_law_focus_20260914/scope.json',latest_process_observation=now(),current_process_manifest='reports/county_law_focus_20260914/execution_checkpoint.json',stable_snapshot_pending=True,stable_snapshot_instruction='Let healthy finite collectors stop. Acquire all eight reviewed collection locks for the coordinated rebuild. Include the county-local supplement and state follow-up collection. Resume remaining reviewed eligible work only after the validated checkpoint. Do not restart old judge/vendor or Trellis jobs.');write(legacy,r)
    print(json.dumps({'checkpoint':'reports/county_law_focus_20260914/execution_checkpoint.json','jobs':progress,'verified_packets':len(receipts)},indent=2))
if __name__=='__main__':main()
