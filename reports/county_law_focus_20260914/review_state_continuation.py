"""Review exact source evidence and additive scope of the 255-URL continuation."""
from pathlib import Path
from urllib.parse import urlsplit,urljoin,urldefrag
from html.parser import HTMLParser
from collections import Counter
import datetime,hashlib,json,sqlite3
ROOT=Path(__file__).resolve().parents[2]
BATCH=ROOT/'sources/official_laws/state_rules_followup_20260914/continuation_20260914T065424Z'
DEST=ROOT/'corpus/official_law_state_rules_followup_20260914'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def paths(c):return {(a['host'],p) for a in c['allow'] for p in a['path_prefixes']}
class Anchors(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.hrefs=[]
    def handle_starttag(self,t,a):
        if t=='a' and dict(a).get('href'):self.hrefs.append(dict(a)['href'])
def main():
    seeds=[json.loads(x) for x in (BATCH/'seeds.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    cfg=read(BATCH/'config.merged.json');base=read(BATCH/'base_config.snapshot.json')
    assert sha(DEST/'config.json')==sha(BATCH/'base_config.snapshot.json')
    assert len(seeds)==len({s['url'] for s in seeds})==255
    assert Counter(s['jurisdiction']['state'] for s in seeds)=={'North Carolina':249,'Nebraska':6}
    assert {k:v for k,v in cfg.items() if k!='allow'}=={k:v for k,v in base.items() if k!='allow'}
    assert cfg['respect_robots'] and cfg['pause_host_on_access_block'] and not cfg['follow_links'] and not cfg['follow_external_allowed_links'] and cfg['max_depth']==0 and (ROOT/cfg['shared_host_dir']).resolve()==ROOT/'corpus/_shared_hosts' and cfg['per_host_delay']>=2
    expected={(urlsplit(s['url']).netloc,urlsplit(s['url']).path) for s in seeds}
    assert paths(cfg)==paths(base)|expected and not paths(base)&expected
    cons={};existing=set();parsed={};verified={};checks=0
    for db in (ROOT/'corpus').glob('*/corpus.sqlite3'):
        c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
        existing.update(r[0] for r in c.execute('SELECT url FROM resources'));cons[db.relative_to(ROOT).as_posix()]=c
    for s in seeds:
        u=urlsplit(s['url']);assert s['url'] not in existing and u.scheme=='https' and not u.query and not u.fragment
        assert u.netloc in {'www.ncleg.gov','nebraskajudicial.gov'}
        assert (u.netloc=='www.ncleg.gov' and u.path.startswith('/EnactedLegislation/Statutes/PDF/ByChapter/') and u.path.endswith('.pdf')) or (u.netloc=='nebraskajudicial.gov' and u.path in {'/book/export/html/'+str(n) for n in [8577,8670,8710,8933,8974,9050]})
        assert not s['edition']['current_edition_verified'] and s['scope']=={'host':u.netloc,'path_prefixes':[u.path]}
        for e in s['provenance']:
            c=cons[e['source_database']];l=c.execute('SELECT * FROM links WHERE id=?',(e['link_id'],)).fetchone();assert l and l['target_url']==s['url']==e['observed_url'] and l['raw_href']==e['raw_href'] and l['fetch_id']==e['fetch_id']
            f=c.execute('SELECT * FROM fetches WHERE id=?',(e['fetch_id'],)).fetchone();assert f and f['status']=='downloaded' and f['raw_complete'] and f['sha256']==e['parent_raw_sha256']
            for pk,hk in [('parent_raw_path','parent_raw_sha256'),('parent_metadata_path','parent_metadata_sha256')]:
                p=(ROOT/e[pk]).resolve();p.relative_to(ROOT);verified[e[pk]]=sha(p);assert verified[e[pk]]==e[hk]
            assert (ROOT/e['source_database']).parent/f['raw_path']==ROOT/e['parent_raw_path'] and (ROOT/e['source_database']).parent/f['metadata_path']==ROOT/e['parent_metadata_path']
            if e['parent_raw_path'] not in parsed:
                h=Anchors();h.feed((ROOT/e['parent_raw_path']).read_text(encoding='utf-8-sig'));parsed[e['parent_raw_path']]=h.hrefs
            assert e['raw_href'] in parsed[e['parent_raw_path']] and urldefrag(urljoin(e['source_url'],e['raw_href']))[0]==s['url'];checks+=1
    for c in cons.values():c.close()
    result={'validated':True,'unresolved_material_findings':0,'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_original_hashes':verified,'input_sha256':{n:sha(BATCH/n) for n in ['seeds.jsonl','config.merged.json','base_config.snapshot.json','summary.json','validation.json']},'reviewer_sha256':sha(Path(__file__)),'selected_urls':255,'state_counts':{'North Carolina':249,'Nebraska':6},'literal_source_anchor_checks':checks,'required_base_config_sha256':sha(BATCH/'base_config.snapshot.json'),'execution_condition':'Ingest only after the active worker exits and the source/base config hashes still match. Use config.merged.json, not additive config.json. Preserve all shared host controls.','network_requests':0,'national_completeness_verified':False}
    (BATCH/'root_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if 'sha256' not in k and k!='source_original_hashes'},indent=2))
if __name__=='__main__':main()
