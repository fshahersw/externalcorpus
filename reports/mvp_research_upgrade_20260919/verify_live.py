from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
import datetime, hashlib, json, time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8769'
checks = []
requests = []

def get(path, raw=False):
    started = time.perf_counter()
    with urlopen(BASE + path, timeout=45) as response:
        data = response.read()
        requests.append({'path':path, 'status':response.status, 'seconds':round(time.perf_counter()-started,3)})
    return data if raw else json.loads(data)

def check(name, passed, evidence=None):
    checks.append({'name':name, 'passed':bool(passed), 'evidence':evidence})

def main():
    for name in ['app.js','styles.css','index.html']:
        body=get('/'+name,True)
        check('Live '+name+' matches disk',body==(ROOT/'delivery/archive-directory'/name).read_bytes(),hashlib.sha256(body).hexdigest())
    for state in ['Kentucky','Pennsylvania']:
        params={'group':'laws','state':state,'category':'rules','availability':'text'}
        hub=get('/api/explore?'+urlencode(params))
        documents=get('/api/documents?'+urlencode(params|{'limit':5}))
        check(state+' navigation and results agree',hub['totals']['total']==documents['total'] and all(x['has_text'] for x in documents['items']),{'total':documents['total'],'hub':hub['totals']})
    registry=get('/api/counties?availability=court_registry&limit=1')
    check('All 374 new county registry entries are filterable',registry['total']==374 and registry['items'][0]['has_court_registry'])
    for geoid,state in [('21001','Kentucky'),('48201','Texas')]:
        row=get('/api/county-registry?geoid='+geoid)
        check('Source registry '+geoid,row['available'] and row['geoid']==geoid and row['state']==state and row['source_as_of']=='2026-08-22' and row['saved_at'] is None and row.get('current_service_verified') is False,{'county':row['county'],'counts':row['counts'],'as_of':row['source_as_of']})
    absent=get('/api/county-registry?geoid=06001')
    check('Uncovered counties are explicitly unavailable',absent['available'] is False and absent['source_as_of'] is None)
    pa=get('/api/judges?has=photo&state=Pennsylvania&limit=60')
    check('PA portrait inventory preserved',pa['total']==29 and all(x.get('photo_url') for x in pa['items']))
    person=get('/api/judge?id='+pa['items'][0]['id'])
    insights=person['library_insights']
    check('Judge insights are explicit derived inventory',insights['kind']=='derived_library_inventory' and insights['analysis_scope']['records']==0 and person['source_as_of'] is None and person['saved_at'] is None and bool(insights['computed_at']),{'name':person['name'],'metrics':insights['metrics'],'gaps':insights['gaps']})
    sample=get('/api/judges?has=photo&q=Breyer&limit=5')
    matching_court=sample['items'][0]['courts'][0]
    check('Court facet counts respect search and photo filters',sample['total']==1 and next(x['count'] for x in sample['courts'] if x['value']==matching_court)==1)
    summary=get('/api/summary')
    photos=get('/api/judges?has=photo&limit=1')
    people=get('/api/people?limit=1')
    check('Existing main collections preserved',summary['published']['capture_records']==16454 and summary['enrichment']['open_us_law']['records']==2978617 and photos['total']==43 and people['total']==15797)
    result={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed' if all(x['passed'] for x in checks) else 'failed','checks':checks,'requests':requests}
    (OUT/'live_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':len(checks),'requests':len(requests),'failed':[x['name'] for x in checks if not x['passed']]}))
    if result['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
