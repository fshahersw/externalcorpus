"""One new reviewed packet; normal crawler locks and shared pacing remain active."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
BATCH=ROOT/'sources/counties/backfill_20260918/batches/20260918T221703694232Z'
TARGET=ROOT/'corpus/county_local_backfill_20260918T2213'
ENGINE=ROOT/'pipeline/corpus_crawler.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 review=json.loads((BATCH/'root_review.json').read_text(encoding='utf8'))
 assert review['validated'] and review['selected_urls']==26
 assert all(sha(BATCH/n)==v for n,v in review['input_sha256'].items())
 assert not (TARGET/'corpus.sqlite3').exists(), 'This finite heartbeat must not reingest or rerun an existing queue'
 receipt={'started_at':now(),'process_id':os.getpid(),'status':'running','batch':BATCH.relative_to(ROOT).as_posix(),
          'data_root':TARGET.relative_to(ROOT).as_posix(),'maximum_resource_attempts':26,'dispatch_budget_seconds':120,
          'maximum_transfer_seconds':180,'maximum_requested_run_budget_seconds':300,
          'seeds_sha256':sha(BATCH/'seeds.jsonl'),'packet_config_sha256':sha(BATCH/'config.json'),'crawler_sha256':sha(ENGINE),
          'publication_modified':False,'prior_collections_modified':False,'pending_projection_modified':False,
          'command':[sys.executable,str(__file__)]}
 p=OUT/'job_receipt.json';p.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
 try:
  with (OUT/'collector.stdout.log').open('w',encoding='utf8') as output,(OUT/'collector.stderr.log').open('w',encoding='utf8') as error:
   args=[sys.executable,str(ENGINE),'--root',str(TARGET)]
   r=subprocess.run(args+['ingest','--seeds',str(BATCH/'seeds.jsonl'),'--config',str(BATCH/'config.json')],cwd=ROOT,stdout=output,stderr=error)
   if r.returncode:raise RuntimeError('Ingest exit %d'%r.returncode)
   r=subprocess.run(args+['run','--max-pages','26','--max-seconds','120'],cwd=ROOT,stdout=output,stderr=error)
   if r.returncode:raise RuntimeError('Crawler exit %d'%r.returncode)
   receipt['status']='exited'
 except Exception as e:receipt['status']='failed';receipt['error']=str(e);raise
 finally:
  receipt['ended_at']=now();p.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
 print(json.dumps(receipt))
if __name__=='__main__':main()
