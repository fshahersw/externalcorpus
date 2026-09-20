"""Independent evidence and scope review of prepared county-local URL seeds."""
from pathlib import Path
from urllib.parse import urlsplit,urljoin,urldefrag
from html import unescape
from html.parser import HTMLParser
from collections import Counter
import argparse,datetime,hashlib,json,sqlite3

ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
class Anchors(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.hrefs=[]
    def handle_starttag(self,t,a):
        if t=='a' and dict(a).get('href'):self.hrefs.append(dict(a)['href'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--batch',type=Path,default=ROOT/'sources/counties/local_documents_20260914');ap.add_argument('--expected-count',type=int,default=200);args=ap.parse_args();batch=args.batch.resolve();batch.relative_to(ROOT)
    seeds=rows(batch/'seeds.jsonl');config=read(batch/'config.json');summary=read(batch/'summary.json')
    baseline={r['geoid']:r for r in read(ROOT/'sources/official_courts/datasets/counties_50_plus_dc.json')}
    assert 0<args.expected_count<=200
    assert len(baseline)==3144 and len(seeds)==len({r['url'] for r in seeds})==args.expected_count
    assert config['respect_robots'] and config['pause_host_on_access_block'] and not config['follow_links'] and not config['follow_external_allowed_links'] and config['max_depth']==0
    assert (ROOT/config['shared_host_dir']).resolve()==ROOT/'corpus/_shared_hosts'
    assert 1<=config['workers']<=8 and config['per_host_delay']>=2
    owned_db={};existing=set()
    for p in (ROOT/'corpus').glob('*/corpus.sqlite3'):
        con=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
        existing.update(r[0] for r in con.execute('SELECT url FROM resources'));owned_db[p.relative_to(ROOT).as_posix()]=con
    verified={};parsed={};evidence_checks=0;per_county=Counter();categories=Counter();source_urls=set();www_alias_links=[]
    for s in seeds:
        u=urlsplit(s['url']);assert u.scheme in ('http','https') and u.hostname and not u.username and not u.password and not u.fragment
        assert s['url'] not in existing
        j=s['jurisdiction'];b=baseline[j['geoid']]
        assert all(j[k]==b[k] for k in ['state','state_fips','county_fips','geoid']) and j['county']==b['name']
        assert s['site_authority_verified'] is False and s['court_fips_association_verified'] is False
        assert j['association_status']==s['source_association_strength']
        assert s['scope']=={'host':u.netloc,'path_prefixes':[u.path or '/']}
        assert any(a['host']==u.netloc and (u.path or '/') in a['path_prefixes'] for a in config['allow'])
        assert s['provenance'];per_county[j['geoid']]+=1;categories[s['category']]+=1
        for e in s['provenance']:
            con=owned_db[e['database']];l=con.execute('SELECT * FROM links WHERE id=?',(e['link_id'],)).fetchone();assert l
            assert l['target_url']==s['url']==e['target_url'] and l['raw_href']==e['raw_href'] and l['anchor_text']==e['anchor_text']
            assert l['source_id']==e['source_resource_id'] and l['fetch_id']==e['source_fetch_id']
            parent_host=urlsplit(e['parent_url']).netloc
            assert parent_host==u.netloc or parent_host.removeprefix('www.')==u.netloc.removeprefix('www.')
            if parent_host!=u.netloc:www_alias_links.append({'parent_url':e['parent_url'],'target_url':s['url'],'basis':'Exact observed href between bare and www hostname; website authority remains unverified.'})
            f=con.execute('SELECT * FROM fetches WHERE id=?',(e['source_fetch_id'],)).fetchone();assert f and f['status']=='downloaded' and f['raw_complete']
            source_root=ROOT/e['collection'];raw=(source_root/f['raw_path']).resolve();meta=(source_root/f['metadata_path']).resolve();raw.relative_to(source_root);meta.relative_to(source_root)
            assert raw==ROOT/e['parent_raw_path'] and meta==ROOT/e['parent_metadata_path']
            for p,d in [(raw,e['parent_raw_sha256']),(meta,e['parent_metadata_sha256'])]:
                key=p.relative_to(ROOT).as_posix()
                if key not in verified:verified[key]=sha(p)
                assert verified[key]==d
            assert f['sha256']==e['parent_raw_sha256']
            if e['parent_raw_path'] not in parsed:
                parser=Anchors();parser.feed(raw.read_text(encoding='utf-8-sig'));parsed[e['parent_raw_path']]=parser.hrefs
            assert e['raw_href'] in parsed[e['parent_raw_path']]
            assert urldefrag(urljoin(e.get('observed_link_base_url',e['parent_url']),e['raw_href']))[0]==s['url']
            # Exact saved link graph plus source bytes is the parent evidence; no guessed endpoint.
            c=con.execute('SELECT * FROM contexts WHERE id=?',(e['source_context_id'],)).fetchone();assert c
            assert con.execute('SELECT 1 FROM resource_contexts WHERE resource_id=? AND context_id=?',(e['source_resource_id'],e['source_context_id'])).fetchone()
            source_urls.add(e['parent_url']);evidence_checks+=1
    assert max(per_county.values())<=3
    extra_inputs=[]
    if (batch/'merged_collection_config.json').is_file():
        base=read(batch/'prior_collection_config_snapshot.json');merged=read(batch/'merged_collection_config.json')
        assert sha(ROOT/'corpus/county_local_documents_20260914/config.json')==sha(batch/'prior_collection_config_snapshot.json')
        assert {k:v for k,v in base.items() if k!='allow'}=={k:v for k,v in merged.items() if k!='allow'}
        def paths(c):return {(a['host'],p) for a in c['allow'] for p in a['path_prefixes']}
        assert paths(merged)==paths(base)|paths(config)
        extra_inputs=['merged_collection_config.json','prior_collection_config_snapshot.json']
    for con in owned_db.values():con.close()
    report={'validated':True,'unresolved_material_findings':0,'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'batch_path':batch.relative_to(ROOT).as_posix(),'input_sha256':{n:sha(batch/n) for n in ['seeds.jsonl','config.json','validation.json','summary.json']},'reviewer_sha256':sha(Path(__file__)),'selected_urls':len(seeds),'selected_counties':len(per_county),'categories':dict(categories),'source_parent_pages':len(source_urls),'source_graph_context_checks':evidence_checks,'original_and_metadata_hashes':verified,'observed_www_alias_links':www_alias_links,'checks':{'every_url_literal_observed_link':True,'every_parent_complete_successful_capture':True,'county_baseline_mapping_preserved':True,'unverified_authority_not_promoted':True,'same_host_or_observed_www_alias_and_exact_scopes':True,'already_queued_urls_excluded':True,'shared_pacing_and_access_controls_preserved':True},'network_requests':0,'full_county_content_complete':False}
    report['input_sha256'].update({n:sha(batch/n) for n in extra_inputs})
    (batch/'root_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['original_and_metadata_hashes','input_sha256']},indent=2))
if __name__=='__main__':main()
