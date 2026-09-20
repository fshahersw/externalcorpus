"""Run only the frozen 30-URL county packet with existing crawler locks/pacing."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BATCH=ROOT/'sources/counties/backfill_20260918/batches/20260918T212813275333Z'
TARGET=ROOT/'corpus/county_local_backfill_20260918'
ENGINE=ROOT/'pipeline/corpus_crawler.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
    review=json.loads((BATCH/'root_review.json').read_text(encoding='utf8'))
    assert review['validated'] and review['selected_urls']==30
    assert all(sha(BATCH/name)==digest for name,digest in review['input_sha256'].items())
    cfg=json.loads((BATCH/'config.json').read_text(encoding='utf8'))
    assert cfg['respect_robots'] and not cfg['follow_links'] and not cfg['follow_external_allowed_links']
    assert cfg['max_depth']==0 and cfg['max_retries']==0 and cfg['per_host_delay']>=2
    assert cfg['shared_host_dir']=='corpus/_shared_hosts' and cfg['pause_host_on_access_block']
    receipt={'started_at':now(),'process_id':os.getpid(),'status':'running','batch':BATCH.relative_to(ROOT).as_posix(),
             'data_root':TARGET.relative_to(ROOT).as_posix(),'maximum_resource_attempts':30,'dispatch_budget_seconds':300,
             'maximum_transfer_seconds':cfg['max_transfer_seconds'],'seeds_sha256':sha(BATCH/'seeds.jsonl'),
             'packet_config_sha256':sha(BATCH/'config.json'),'crawler_sha256':sha(ENGINE),
             'publication_modified':False,'prior_collections_modified':False,
             'command':[sys.executable,str(__file__)]}
    path=OUT/'job_receipt.json'
    path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    try:
        with (OUT/'collector.stdout.log').open('a',encoding='utf8') as output,(OUT/'collector.stderr.log').open('a',encoding='utf8') as error:
            if not (TARGET/'corpus.sqlite3').exists():
                result=subprocess.run([sys.executable,str(ENGINE),'--root',str(TARGET),'ingest','--seeds',str(BATCH/'seeds.jsonl'),'--config',str(BATCH/'config.json')],cwd=ROOT,stdout=output,stderr=error)
                if result.returncode:raise RuntimeError('Ingest exit %d'%result.returncode)
            else:
                # Any repeat invocation can consume only this already-reviewed finite queue.
                import sqlite3
                with sqlite3.connect((TARGET/'corpus.sqlite3').as_uri()+'?mode=ro',uri=True) as c:
                    stored={json.loads(r[0])['url'] for r in c.execute('select seed_json from contexts')}
                expected={json.loads(line)['url'] for line in (BATCH/'seeds.jsonl').read_text(encoding='utf8').splitlines()}
                assert stored==expected
            result=subprocess.run([sys.executable,str(ENGINE),'--root',str(TARGET),'run','--max-pages','30','--max-seconds','300'],cwd=ROOT,stdout=output,stderr=error)
            if result.returncode:raise RuntimeError('Crawler exit %d'%result.returncode)
            receipt['status']='exited'
    except Exception as exc:
        receipt['status']='failed';receipt['error']=str(exc);raise
    finally:
        receipt['ended_at']=now()
        if (TARGET/'summary.json').is_file():receipt['summary_path']=(TARGET/'summary.json').relative_to(ROOT).as_posix()
        path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt))
if __name__=='__main__':main()
