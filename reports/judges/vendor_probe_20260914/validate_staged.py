"""Independent full-file, native-record and SQLite audit of the vendor add-on."""
from pathlib import Path
from collections import Counter
from html import unescape
from urllib.parse import quote
import argparse,csv,datetime,hashlib,json,re,sqlite3

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'delivery/judge_vendor_enrichment_20260914'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):return [json.loads(s) for s in path.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def path(value,within=ROOT):
    p=(ROOT/value).resolve();p.relative_to(within.resolve());assert p.is_file();return p
def rel(p):return p.resolve().relative_to(ROOT).as_posix()
def canon(component,native,kind=None):return 'vendor:'+component+(':'+kind if kind else '')+':'+quote(native,safe='-_.~')
def pointer(value,location):
    if location=='':return value
    assert location.startswith('/')
    for segment in location[1:].split('/'):
        key=segment.replace('~1','/').replace('~0','~')
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value
def main():
    ap=argparse.ArgumentParser();ap.add_argument('snapshot',type=Path);args=ap.parse_args()
    snap=args.snapshot.resolve();snap.relative_to((BASE/'snapshots').resolve())
    manifest=read(snap/'files.sha256.json')
    for name,item in manifest.items():
        p=path(name,snap);assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
    actual={rel(p) for p in snap.rglob('*') if p.is_file() and p.name!='files.sha256.json'}
    assert actual==set(manifest)
    originals=read(snap/'verified_originals.json')
    for name,item in originals.items():assert sha(path(name))==sha(path(item['snapshot_path'],snap))==item['sha256']
    inputs=read(snap/'component_inputs.json')
    for name,digest in inputs.items():
        original=path(name);frozen=snap/'components'/original.relative_to(BASE)
        assert sha(original)==sha(frozen)==digest
    code={name:sha(ROOT/name) for name in ['scripts/build_judge_vendor_addon.py','scripts/query_judge_vendor_addon.py','delivery/judge_vendor_enrichment_20260914/SCHEMA.md']}
    for name,digest in code.items():
        frozen=snap/'SCHEMA.md' if name.endswith('SCHEMA.md') else snap/'pipeline'/Path(name).name
        assert sha(frozen)==digest
    data={name:rows(snap/(name+'.jsonl')) for name in ['observations','facts','analyses','candidates']}
    obs={r['source_observation_id']:r for r in data['observations']}
    assert len(obs)==len(data['observations'])==2
    all_evidence=[]
    for component in ['context','lex_machina']:
        folder=snap/'components'/component
        native_obs=rows(folder/'observations.jsonl')
        projected=[r for r in data['observations'] if r['component']==component]
        assert Counter(json.dumps(r,sort_keys=True) for r in native_obs)==Counter(json.dumps(r['native_record'],sort_keys=True) for r in projected)
        for o in projected:
            native=o['native_record'];assert o['source_observation_id']==canon(component,native.get('native_id',native['source_observation_id']))
            assert o['record_class']==native['record_class'] and o['name']==native['name']
            assert o['current_service_verified'] is False and o['identity_merge_performed'] is False
            assert o['identity_resolution']=='source_specific_no_cross_source_merge'
        for name,idkey,kind in [('facts','fact_id','fact'),('analyses','analysis_id','analysis')]:
            native_rows=rows(folder/(name+'.jsonl'));projected=[r for r in data[name] if r['component']==component]
            assert Counter(json.dumps(r,sort_keys=True) for r in native_rows)==Counter(json.dumps(r['native_record'],sort_keys=True) for r in projected)
            for r in projected:
                native=r['native_record'];o=obs[r['source_observation_id']]
                assert r[idkey]==canon(component,native[idkey],kind)
                assert r['source_observation_id']==canon(component,next(v.get('native_id',v['source_observation_id']) for v in native_obs if v['source_observation_id']==native['source_observation_id']))
                assert r['record_class']==o['record_class'] and r['value']==native['value']
                owned={o['source_path']:o['source_sha256']}
                for v in o.get('additional_sources') or []:owned[v['source_path']]=v['source_sha256']
                evidence=r['evidence'] if isinstance(r['evidence'],list) else [r['evidence']]
                for e in evidence:
                    assert owned[e['source_path']]==e['source_sha256']==originals[e['source_path']]['sha256']
                    source=path(e['source_path'])
                    selected=pointer(read(source),e['json_pointer']) if 'json_pointer' in e else source.read_text(encoding='utf-8-sig')
                    if 'embedded_json_pointer' in e:selected=pointer(json.loads(selected),e['embedded_json_pointer'])
                    assert isinstance(selected,str)
                    if 'html_character_start' in e:
                        fragment=selected[e['html_character_start']:e['html_character_end']]
                        assert hashlib.sha256(fragment.encode('utf8')).hexdigest()==e['html_fragment_sha256']
                        assert ' '.join(unescape(re.sub(r'<[^>]*>','',fragment)).split())==' '.join(e['literal_text'].split())
                        if 'raw_byte_start' in e:assert source.read_bytes()[e['raw_byte_start']:e['raw_byte_end']]==fragment.encode('utf8')
                    else:assert selected[e['start']:e['end']]==e['quote']
                    all_evidence.append(e)
                if name=='analyses':
                    assert r['source_reported'] is True and r['independently_computed'] is False
                    assert r['metric_subject_type']==o['subject_type']==r['subject_type']=='judge'
                    assert r['numerator'] is None and r['denominator'] is None
                    if component=='context':assert r['period'] is None
    assert len([o for o in obs.values() if o['record_class']=='public_ui_preview'])==1
    assert len([o for o in obs.values() if o['record_class']=='vendor_published'])==1
    # Independent source census provides the native source graph expectations.
    source_review=read(OUT/'independent_source_review.json');assert source_review['validated'] is True
    for name,digest in source_review['source_hashes'].items():assert sha(path(name))==digest
    expected=read(OUT/'independent_expected_counts.json')
    cx=[r for r in data['analyses'] if r['component']=='context']
    assert len(cx)==449
    areas=[r for r in cx if r['metric']=='opinions_by_area_of_law']
    assert len(areas)==5
    assert sorted(r['value'] for r in areas)==[844,948,991,1211,2023]
    separate=[r for r in cx if r['metric']=='motion_case_result_list_count']
    assert len(separate)==1 and separate[0]['value']==489
    # Bind the count/value to each exact native source graph button independently.
    rendered_values=[]
    for r in cx:
        for e in (r['evidence'] if isinstance(r['evidence'],list) else [r['evidence']]):
            text=e.get('quote',e.get('literal_text',''))
            motion=re.search(r'(.*?) ([\d,]+) Cases( granted| partial grant| denied)?(?=["\n]|$)',text)
            citation=re.search(r'(.*?) cited ([\d,]+) times',text)
            if motion and ('motion ' in motion[1] or 'compound' in motion[1]):
                label=re.sub(r'^.*?button "','',motion[1]);value=int(motion[2].replace(',',''))
                assert value==r['value'];rendered_values.append(('motion',label,value,(motion[3] or '').strip() or None))
            elif citation:
                label=re.sub(r'^.*?button "','',citation[1]);value=int(citation[2].replace(',',''))
                assert value==r['value'];kind='judge' if 'cited_judges' in e['source_path'] else 'opinion'
                rendered_values.append((kind,label,value,None))
    graph_expected=[('motion',r['motion_type'],r['value'],r['outcome']) for r in expected['motion_counts']]
    for kind,items in expected['citation_counts'].items():graph_expected += [(kind,r['referenced_name'],r['value'],None) for r in items]
    assert Counter(rendered_values)==Counter(graph_expected)
    lm=[r for r in data['analyses'] if r['component']=='lex_machina'];assert len(lm)==1 and lm[0]['value']==2276
    assert lm[0]['period']['start_year']==2023 and lm[0]['period']['end_year']==2025
    for file,selection in [('vendor_published_judge_measures',lambda r:r['record_class']=='vendor_published' and r['subject_type']=='judge'),('public_ui_preview_measures',lambda r:r['record_class']=='public_ui_preview'),('historical_illustrations',lambda r:r['record_class']=='historical_illustration'),('non_judge_context_measures',lambda r:r['subject_type']!='judge')]:
        assert rows(snap/(file+'.jsonl'))==[r for r in data['analyses'] if selection(r)]
    con=sqlite3.connect((snap/'vendor_addon.sqlite').as_uri()+'?mode=ro',uri=True);con.execute('PRAGMA query_only=ON')
    assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not con.execute('PRAGMA foreign_key_check').fetchall()
    for table,key in [('observations','source_observation_id'),('facts','fact_id'),('analyses','analysis_id'),('candidates','candidate_id')]:
        assert {r[0]:json.loads(r[1]) for r in con.execute('SELECT id,record_json FROM '+table)}=={r[key]:r for r in data[table]}
    assert con.execute('SELECT COUNT(*) FROM vendor_published_judge_measures').fetchone()[0]==1
    assert con.execute('SELECT COUNT(*) FROM public_ui_preview_measures').fetchone()[0]==len(cx)
    assert con.execute('SELECT COUNT(*) FROM historical_illustrations').fetchone()[0]==0
    con.close()
    summary=read(snap/'summary.json')
    for name in data:assert summary[name]==len(data[name])
    assert summary['identity_merges']==summary['independently_computed_outcome_rates']==summary['network_requests']==0
    report={'validated':True,'unresolved_material_findings':0,'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot_path':rel(snap),'manifest_sha256':sha(snap/'files.sha256.json'),'reviewed_code_sha256':code,'counts':{name:len(values) for name,values in data.items()},'all_snapshot_files_rehashed':len(manifest),'all_originals_and_copies_rehashed':len(originals),'native_records_preserved':True,'component_ownership_and_classes_preserved':True,'independent_rendered_count_comparisons':len(graph_expected),'source_review_path':rel(OUT/'independent_source_review.json'),'source_review_sha256':sha(OUT/'independent_source_review.json'),'validator_path':rel(Path(__file__)),'validator_sha256':sha(Path(__file__)),'sqlite_integrity_and_exact_projection':True,'unknown_preview_period_and_denominators_null':True,'cross_source_merges':0}
    (OUT/'independent_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
