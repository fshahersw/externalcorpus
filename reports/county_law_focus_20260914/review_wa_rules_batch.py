"""Independent original-byte, source-link and county-label checks for WA PDFs."""
from pathlib import Path
from urllib.parse import urljoin,urldefrag,urlsplit
from html.parser import HTMLParser
from collections import Counter
import argparse,datetime,hashlib,json,re,sqlite3
ROOT=Path(__file__).resolve().parents[2]
BATCH=ROOT/'sources/counties/local_documents_20260914/batches/wa_local_rules_20260914T065327354995Z'
DEST='corpus/county_local_rules_washington_20260914'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
class Anchors(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a' and dict(attrs).get('href'):self.hrefs.append(dict(attrs)['href'])
def main():
    global BATCH
    ap=argparse.ArgumentParser();ap.add_argument('--batch',type=Path);args=ap.parse_args()
    if args.batch:BATCH=args.batch.resolve();BATCH.relative_to(ROOT)
    seeds=[json.loads(x) for x in (BATCH/'seeds.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    cfg=read(BATCH/'config.json');summary=read(BATCH/'summary.json');baseline={r['geoid']:r for r in read(ROOT/'sources/official_courts/datasets/counties_50_plus_dc.json')}
    assert len(seeds)==len({s['url'] for s in seeds})==summary['selected_unique_urls'] and 1<=len(seeds)<=100
    assert cfg['respect_robots'] and cfg['pause_host_on_access_block'] and not cfg['follow_links'] and not cfg['follow_external_allowed_links'] and cfg['max_depth']==0
    assert cfg['shared_host_dir']=='corpus/_shared_hosts' and cfg['per_host_delay']>=2 and cfg['workers']<=3
    cons={};existing=set();parsed={};verified={};county=Counter();unassigned=0;checks=0
    for db in (ROOT/'corpus').glob('*/corpus.sqlite3'):
        c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
        existing.update(r[0] for r in c.execute('SELECT url FROM resources'));cons[db.relative_to(ROOT).as_posix()]=c
    for s in seeds:
        u=urlsplit(s['url']);assert u.scheme=='https' and u.netloc=='www.courts.wa.gov' and u.path.startswith('/court_rules/pdf/LCR/') and u.path.endswith('.pdf') and not u.query and not u.fragment
        assert s['url'] not in existing and s['scope']=={'host':u.netloc,'path_prefixes':[u.path]}
        assert any(a['host']==u.netloc and u.path in a['path_prefixes'] for a in cfg['allow'])
        assert s['site_authority_verified'] is True and s['court_fips_association_verified'] is False and s['category']=='local_rules'
        j=s['jurisdiction'];assert j['state']=='Washington' and j['state_fips']=='53'
        if j.get('geoid'):
            b=baseline[j['geoid']];assert all(j[k]==b[k] for k in ['state','state_fips','county_fips','geoid']) and j['county']==b['name']
            # Seven official Superior Court labels omit the literal suffix County.
            label_name=b['name'].removesuffix(' County') if 'Superior Court' in s['court_label'] else b['name']
            assert re.search(r'(?<!\w)'+re.escape(label_name)+r'(?!\w)',s['court_label'],re.I)
            assert s['county_geography_association_verified'] is True;county[j['geoid']]+=1
        else:
            assert not j.get('county') and not j.get('county_fips') and not s['county_geography_association_verified'];unassigned+=1
        assert s['provenance']
        for e in s['provenance']:
            c=cons[e['database']];link=c.execute('SELECT * FROM links WHERE id=?',(e['link_id'],)).fetchone();assert link
            assert link['target_url']==s['url']==e['target_url'] and link['raw_href']==e['raw_href'] and link['anchor_text']==s['court_label']==e['anchor_text']
            assert link['fetch_id']==e['source_fetch_id'] and link['source_id']==e['source_resource_id']
            f=c.execute('SELECT * FROM fetches WHERE id=?',(e['source_fetch_id'],)).fetchone();assert f and f['status']=='downloaded' and f['raw_complete'] and f['sha256']==e['parent_raw_sha256']
            for pk,hk in [('parent_raw_path','parent_raw_sha256'),('parent_metadata_path','parent_metadata_sha256')]:
                p=(ROOT/e[pk]).resolve();p.relative_to(ROOT);verified[e[pk]]=sha(p);assert verified[e[pk]]==e[hk]
            assert (ROOT/e['database']).parent/f['raw_path']==ROOT/e['parent_raw_path']
            assert (ROOT/e['database']).parent/f['metadata_path']==ROOT/e['parent_metadata_path']
            if e['parent_raw_path'] not in parsed:
                h=Anchors();h.feed((ROOT/e['parent_raw_path']).read_text(encoding='utf-8-sig'));parsed[e['parent_raw_path']]=h.hrefs
            assert e['raw_href'] in parsed[e['parent_raw_path']] and urldefrag(urljoin(e['parent_url'],e['raw_href']))[0]==s['url'];checks+=1
    for c in cons.values():c.close()
    assert sum(county.values())==summary['selected_county_assigned_pdfs'] and len(county)==summary['selected_county_associations'] and unassigned==summary['selected_county_unassigned_pdfs']
    inputs=['seeds.jsonl','config.json','summary.json','validation.json']
    if (BATCH/'merged_collection_config.json').exists():
        base=read(BATCH/'prior_collection_config_snapshot.json');merged=read(BATCH/'merged_collection_config.json')
        assert sha(ROOT/DEST/'config.json')==sha(BATCH/'prior_collection_config_snapshot.json')
        assert {k:v for k,v in base.items() if k!='allow'}=={k:v for k,v in merged.items() if k!='allow'}
        def paths(c):return {(a['host'],p) for a in c['allow'] for p in a['path_prefixes']}
        assert paths(merged)==paths(base)|paths(cfg)
        inputs+=['merged_collection_config.json','prior_collection_config_snapshot.json']
    result={'validated':True,'unresolved_material_findings':0,'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'collection_root':DEST,'selected_urls':len(seeds),'county_assigned_pdfs':sum(county.values()),'distinct_assigned_counties':len(county),'county_unassigned_pdfs':unassigned,'exact_saved_anchor_checks':checks,'source_original_hashes':verified,'input_sha256':{n:sha(BATCH/n) for n in inputs},'reviewer_sha256':sha(Path(__file__)),'network_requests':0,'court_territorial_jurisdiction_verified':False,'legal_currency_or_national_completeness_verified':False}
    (BATCH/'root_review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if 'sha256' not in k and k!='source_original_hashes'},indent=2))
if __name__=='__main__':main()
