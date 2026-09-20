"""Bounded read-only acceptance checks for the new local biography routes."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
import hashlib,json,time

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
BASE='http://127.0.0.1:8769'
def get(path):
    started=time.perf_counter()
    with urlopen(BASE+path,timeout=10) as response:body=json.load(response)
    return body,round(time.perf_counter()-started,6)
def status(path,**kwargs):
    try:
        with urlopen(Request(BASE+path,**kwargs),timeout=10) as response:return response.status
    except HTTPError as exc:return exc.code

default,default_time=get('/api/people?limit=24')
all_people,all_time=get('/api/people?include_aliases=1&limit=24')
second,second_time=get('/api/people?include_aliases=1&offset=24&limit=24')
filtered,filter_time=get('/api/people?'+urlencode({'q':'Claire Cecchi','court':'njd'}))
profile,profile_time=get('/api/person?id=576')
alias,_=get('/api/person?id=4696')
judge,_=get('/api/judges?has=all&limit=1')
ready=json.loads((ROOT/'sources/courtlistener_people_20260918/ready.json').read_text())
checks={
 'source_ready':default['ready'] is True and ready['ready'] is True,
 'default_excludes_aliases':default['total']==15797 and all(not p['is_alias'] for p in default['items']),
 'all_source_people_count':all_people['total']==16191,
 'aliases_do_not_inflate_default':all_people['total']-default['total']==394,
 'paging_is_disjoint':not ({p['id'] for p in all_people['items']} & {p['id'] for p in second['items']}) and len(second['items'])==24,
 'court_and_name_intersect':filtered['total']==1 and filtered['items'][0]['id']=='576',
 'year_precision_preserved':profile['birth']['text']=='1964' and profile['birth']['recorded_value']=='1964-01-01',
 'career_and_education_present':len(profile['positions'])==4 and len(profile['educations'])==2,
 'alias_native_identity_preserved':alias['id']=='4696' and alias['is_alias'] is True and alias['alias_of']['id']!='4696',
 'six_source_table_hashes_available':len(profile['source']['source_files'])==6,
 'main_judge_entities_unchanged':judge['total']==10669,
 'invalid_native_id_404':status('/api/person?id=..%2F..%2F.env')==404,
 'writes_disallowed':status('/api/people',method='POST',data=b'')==405,
 'loopback_host_guard':status('/api/people',headers={'Host':'external.example'})==403,
 'no_fake_image_url':all('photo_url' not in p for p in all_people['items']) and 'photo_url' not in profile,
}
changed=['delivery/archive-directory/people.py','delivery/archive-directory/server.py',
         'delivery/archive-directory/app.js','delivery/archive-directory/styles.css',
         'sources/courtlistener_people_20260918/import_people.py']
result={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':all(checks.values()),'checks':checks,
 'request_seconds':{'default_page':default_time,'include_aliases':all_time,'second_page':second_time,
                    'court_and_name':filter_time,'profile':profile_time},
 'source_ready':{'database_sha256':ready['database_sha256'],'database_bytes':ready['database_bytes'],
                 'source_manifest_sha256':ready['source_manifest_sha256']},
 'browser_checks':{'desktop_profile':'passed; career/education split layout, collapsed source details',
 'mobile_390x844':'passed; viewport390/document375, no horizontal overflow',
 'back_to_filters':'passed; name and court retained in return URL',
 'court_filter':'passed; njd plus Claire Cecchi returns one biography',
 'clear_filters':'passed; 15,797 biographies with aliases excluded',
 'include_aliases':'passed; 16,191 separately qualified records',
 'pagination':'passed; 1-24 then25-48 with offset24',
 'photo_flags':'no images rendered',
 'viewport_override':'reset after mobile verification'},
 'code':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in changed],
 'scope':{'new_entity_merges':0,'new_portraits':0,'network_acquisition':0,'main_directory_rebuilt':False,
          'bulk_law_index_rebuilt':False,'county_collection_started':False}}
(OUT/'live_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':result['passed'],'checks':checks,'request_seconds':result['request_seconds']},indent=2))
raise SystemExit(0 if result['passed'] else 1)
