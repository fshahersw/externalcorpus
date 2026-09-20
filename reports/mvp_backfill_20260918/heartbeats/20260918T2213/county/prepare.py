"""Prepare one new immutable county heartbeat packet; offline only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, msvcrt, sqlite3, sys
ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
PREPARER=ROOT/'reports/county_law_focus_20260914/heartbeats/20260918T1622/prepare_county_substantive_documents.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
preflight={'checked_at':datetime.now(timezone.utc).isoformat(),'fresh_cim_collector_processes':[],
           'process_check_basis':'PowerShell Get-CimInstance Win32_Process for python/pythonw collector commands returned no processes immediately before this script.',
           'roots':[],'previous_packet_and_receipts_modified':False}
for folder in sorted((ROOT/'corpus').glob('county*')):
 p=folder/'corpus.sqlite3'
 if not p.exists():continue
 c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
 item={'root':folder.relative_to(ROOT).as_posix(),'statuses':dict(c.execute('select status,count(*) from resources group by status')),'locks':{}}
 c.close()
 for name in ['.crawler.lock','collector.lock']:
  lock=folder/name
  if not lock.exists():item['locks'][name]='not_present';continue
  with lock.open('r+b') as stream:
   stream.seek(0)
   try:msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
   except OSError:item['locks'][name]='held';raise RuntimeError('County lock active: '+str(lock))
   else:
    stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1);item['locks'][name]='available'
 preflight['roots'].append(item)
write(OUT/'preflight.json',preflight)
spec=importlib.util.spec_from_file_location('county_heartbeat_preparer',PREPARER)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.LIMIT=30;module.PER_COUNTY=2
old_classify=module.classify
def classify(url,anchor):
 if '/Brevard_Civil_Trial_Dockets/' in url:return None
 return old_classify(url,anchor)
module.classify=classify
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
batch=Path('sources/counties/backfill_20260918/batches')/stamp
sys.argv=[str(__file__),'--output-dir',batch.as_posix()]
module.main()
p=ROOT/batch/'summary.json';summary=json.loads(p.read_text(encoding='utf8'))
summary['selection_order']='Substantive document priority, then county association; at most two per county and 30 URLs. Known Brevard paths from Seminole-associated landing held for identity review.'
write(p,summary)
receipt={'prepared_at':datetime.now(timezone.utc).isoformat(),'batch':batch.as_posix(),
         'parent_preparer':PREPARER.relative_to(ROOT).as_posix(),'parent_preparer_sha256':sha(PREPARER),
         'preflight_sha256':sha(OUT/'preflight.json'),'existing_collections_modified':False,
         'network_requests':0,'selected_urls':summary['selected_unique_urls'],'selected_counties':summary['selected_counties']}
write(OUT/'preparation_receipt.json',receipt)
print(json.dumps(receipt))
