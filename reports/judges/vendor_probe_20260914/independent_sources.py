"""Independent offline census of rendered Context graphs and a public vendor article."""
from pathlib import Path
from collections import Counter
from html import unescape
import hashlib, json, re

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
CONTEXT=ROOT/'sources/judges/vendor_probe_20260914/context'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(encoding='utf-8'))
def snapshot(name): return read(CONTEXT/name)['response']['stdout']
def main():
    original_hashes={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in CONTEXT.glob('*.json')}
    unsafe=[]
    def visit(value, file):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in {'cdpUrl','liveViewUrl','interactiveLiveViewUrl'}: unsafe.append((file,k))
                visit(v,file)
        elif isinstance(value,list):
            for v in value:visit(v,file)
        elif isinstance(value,str) and re.search(r'fc-[a-z0-9]{20,}|(?:cdp|liveview)\.firecrawl\.dev',value,re.I):
            unsafe.append((file,'capability_or_key_pattern'))
    for file in CONTEXT.glob('*.json'):visit(read(file),file.name)
    assert not unsafe
    motions=snapshot('sabraw_motion_browser_final.capture.json')
    assert 'heading "Dana M. Sabraw"' in motions
    matches=list(re.finditer(r'- button "(?P<name>.*?) (?P<count>[\d,]+) Cases(?P<outcome> granted| partial grant| denied)?" \[ref=(?P<ref>\w+)\]',motions))
    expected_motion=[{'motion_type':m['name'],'value':int(m['count'].replace(',','')),'outcome':m['outcome'].strip() if m['outcome'] else None,'ref':m['ref'],'start':m.start(),'end':m.end(),'quote':m.group()} for m in matches]
    totals=[r for r in expected_motion if r['outcome'] is None]
    outcomes=[r for r in expected_motion if r['outcome'] is not None]
    assert len(totals)==116 and len(outcomes)==228
    assert len({r['motion_type'] for r in totals})==116
    total_map={r['motion_type']:r['value'] for r in totals}
    outcome_map={}
    for r in outcomes:outcome_map.setdefault(r['motion_type'],{})[r['outcome']]=r['value']
    assert total_map['motion to dismiss']==542
    assert outcome_map['motion to dismiss']=={'granted':262,'partial grant':156,'denied':124}
    assert outcome_map['motion for remand']=={'granted':38,'denied':33}
    assert all(sum(outcome_map[name].values())==count for name,count in total_map.items())
    assert re.search(r'489\s+cases where Dana M\. Sabraw ruled on a motion to dismiss',motions,re.I)
    citation_expected={}
    for kind,file in [('opinion','sabraw_citation_browser.capture.json'),('judge','sabraw_cited_judges_browser.capture.json')]:
        s=snapshot(file)
        assert 'heading "Dana M. Sabraw"' in s
        items=[{'referenced_entity_type':kind,'referenced_name':m['name'],'value':int(m['count'].replace(',','')),'ref':m['ref'],'start':m.start(),'end':m.end(),'quote':m.group()} for m in re.finditer(r'- button "(?P<name>.*?) cited (?P<count>[\d,]+) times" \[ref=(?P<ref>\w+)\]',s)]
        assert len(items)==(50 if kind=='opinion' else 49)
        citation_expected[kind]=items
    assert [(r['referenced_name'],r['value']) for r in citation_expected['opinion'] if r['referenced_name']=='Andrews v. Cervantes']==[('Andrews v. Cervantes',72),('Andrews v. Cervantes',71)]
    assert next(r['value'] for r in citation_expected['judge'] if r['referenced_name']=='Dana M. Sabraw')==217
    tip=snapshot('sabraw_motion_tooltip_browser.capture.json')
    assert 'Context does not currently detect appellate reversals of trial court motion decisions.' in tip
    raw=read(CONTEXT/'sabraw_overview.firecrawl.json')
    page=json.loads(next(c['text'] for c in raw['tool_result']['content'] if c['type']=='text'))
    html=page['html']
    assert page['metadata']['statusCode']==200
    # Check the exact hidden extra labels so an auditor can ensure they were excluded.
    for name in ['Civil Rights Law','Evidence','Criminal Law & Procedure','Labor & Employment Law','Banking Law']:
        assert name in unescape(html), name
    lex=ROOT/'delivery/judge_vendor_enrichment_20260914/lex_machina'
    analyses=[json.loads(s) for s in (lex/'analyses.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
    assert len(analyses)==1
    a=analyses[0];ev=a['evidence'];source=ROOT/ev['source_path']
    assert sha(source)==ev['source_sha256']
    fragment=source.read_text(encoding='utf-8')[ev['html_character_start']:ev['html_character_end']]
    assert hashlib.sha256(fragment.encode('utf-8')).hexdigest()==ev['html_fragment_sha256']
    literal=' '.join(unescape(fragment).split())
    assert literal=='James Rodney Gilstrap was assigned 2,276 patent-related cases from 2023 through 2025'
    assert a['value']==2276 and a['unit']=='cases' and a['period']['start_year']==2023 and a['period']['end_year']==2025
    assert a['denominator'] is None and a['numerator'] is None
    original_hashes[ev['source_path']]=sha(source)
    expected={'motion_counts':expected_motion,'citation_counts':citation_expected,'separate_motion_result_count':489,'lex_machina_assignment_count':2276}
    (OUT/'independent_expected_counts.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report={'validated':True,'unresolved_material_findings':0,'source_hashes':original_hashes,'counts':{'motion_categories':len(totals),'reported_motion_outcomes':len(outcomes),'cited_opinion_entries':len(citation_expected['opinion']),'cited_judge_entries':len(citation_expected['judge']),'vendor_article_judge_counts':len(analyses)},'checks':{'rendered_native_counts':True,'missing_outcomes_not_invented':True,'motion_chart_and_result_count_distinct':True,'duplicate_citation_labels_preserved':True,'no_capability_urls_or_api_key_patterns':True,'public_article_literal_and_period':True},'validator_sha256':sha(Path(__file__))}
    (OUT/'independent_source_review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'validated':True,'counts':report['counts']}))
if __name__=='__main__':main()
