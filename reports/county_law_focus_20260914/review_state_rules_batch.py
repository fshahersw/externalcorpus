"""Independently verify the 100 exact saved official PDF links before ingestion."""
from pathlib import Path
from urllib.parse import urlsplit,urljoin,urldefrag
from html.parser import HTMLParser
from collections import Counter
import datetime,hashlib,json,sqlite3
ROOT=Path(__file__).resolve().parents[2]
BATCH=ROOT/'sources/official_laws/state_rules_followup_20260914'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
class Hrefs(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a' and dict(attrs).get('href'):self.hrefs.append(dict(attrs)['href'])
def main():
    seeds=rows(BATCH/'seeds.jsonl');cfg=read(BATCH/'config.json');assert len(seeds)==len({s['url'] for s in seeds})==100
    assert Counter(s['jurisdiction']['state'] for s in seeds)=={'Georgia':7,'North Carolina':93}
    assert not cfg['follow_links'] and not cfg['follow_external_allowed_links'] and cfg['max_depth']==0 and cfg['respect_robots'] and cfg['pause_host_on_access_block']
    assert (ROOT/cfg['shared_host_dir']).resolve()==ROOT/'corpus/_shared_hosts'
    connections={};existing=set()
    for p in (ROOT/'corpus').glob('*/corpus.sqlite3'):
        if p.parent.name=='official_law_state_rules_followup_20260914':continue
        c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row;existing.update(r[0] for r in c.execute('SELECT url FROM resources'));connections[p.relative_to(ROOT).as_posix()]=c
    verified={};parsed={};checks=0
    for s in seeds:
        assert s['url'] not in existing;u=urlsplit(s['url']);assert u.scheme=='https' and not u.username and not u.fragment and u.path.endswith('.pdf')
        assert u.netloc in {'www.gasupreme.us','www.ncleg.gov'}
        assert s['scope']=={'host':u.netloc,'path_prefixes':[u.path]}
        assert any(a['host']==u.netloc and u.path in a['path_prefixes'] for a in cfg['allow'])
        assert not s['edition']['current_edition_verified']
        for e in s['provenance']:
            c=connections[e['source_database']];link=c.execute('SELECT * FROM links WHERE id=?',(e['link_id'],)).fetchone();assert link and link['target_url']==s['url']==e['observed_url'] and link['raw_href']==e['raw_href']
            fetch=c.execute('SELECT * FROM fetches WHERE id=?',(e['fetch_id'],)).fetchone();assert fetch and fetch['id']==link['fetch_id'] and fetch['status']=='downloaded' and fetch['raw_complete']
            for pk,hk in [('parent_raw_path','parent_raw_sha256'),('parent_metadata_path','parent_metadata_sha256')]:
                p=(ROOT/e[pk]).resolve();p.relative_to(ROOT);actual=sha(p);assert actual==e[hk];verified[e[pk]]=actual
            assert fetch['sha256']==e['parent_raw_sha256']
            if e['parent_raw_path'] not in parsed:
                h=Hrefs();h.feed((ROOT/e['parent_raw_path']).read_text(encoding='utf-8-sig'));parsed[e['parent_raw_path']]=h.hrefs
            assert e['raw_href'] in parsed[e['parent_raw_path']]
            assert urldefrag(urljoin(e['source_url'],e['raw_href']))[0]==s['url'];checks+=1
    for c in connections.values():c.close()
    report={'validated':True,'unresolved_material_findings':0,'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_urls':100,'selected_state_counts':{'Georgia':7,'North Carolina':93},'exact_saved_anchor_and_fetch_checks':checks,'source_original_hashes':verified,'input_sha256':{n:sha(BATCH/n) for n in ['seeds.jsonl','config.json','summary.json','validation.json']},'reviewer_sha256':sha(Path(__file__)),'network_requests':0,'legal_currency_and_completeness_verified':False}
    (BATCH/'root_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
