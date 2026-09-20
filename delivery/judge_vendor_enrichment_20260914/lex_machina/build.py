"""Offline extraction of one evidenced public Lex Machina judge count."""
from pathlib import Path
import csv
import datetime
import hashlib
import html
import json
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SOURCE=ROOT/'sources/judges/vendor_probe_20260914/lex_machina'
VERSION='lex-machina-public-article-1.0.1'


def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def rel(p):return p.relative_to(ROOT).as_posix()
def write(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def lines(name,value):(OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in value),encoding='utf-8')


def universal_lf_with_original_boundaries(original):
    """Return the universal-LF view and its original code-point boundaries."""
    normalized=[];boundaries=[0];i=0
    while i<len(original):
        if original[i]=='\r':
            normalized.append('\n')
            i+=2 if original[i:i+2]=='\r\n' else 1
        else:
            normalized.append(original[i]);i+=1
        boundaries.append(i)
    return ''.join(normalized),boundaries


def main():
    manifest=SOURCE/'current_public_fetches.jsonl'
    attempted=rows(manifest);documents=[r for r in attempted if r['status']=='downloaded_public_html']
    assert len(documents)==5 and len({r['url'] for r in documents})==5
    verified={}
    for r in attempted+rows(SOURCE/'fetches.jsonl'):
        for path_field,hash_field in [('raw_path','raw_sha256'),('text_path','text_sha256'),('metadata_path','metadata_sha256')]:
            if r.get(path_field):
                path=ROOT/r[path_field]
                assert sha(path.read_bytes())==r[hash_field],path
                verified[r[path_field]]=r[hash_field]
    r=next(d for d in documents if d['document_id']=='patent_trends_2026')
    assert r['http_status']==200 and r['tls_verified'] is True and r['credentials_or_cookies_supplied'] is False
    raw=(ROOT/r['raw_path']).read_bytes();original_decoded=raw.decode('utf-8')
    decoded,original_boundaries=universal_lf_with_original_boundaries(original_decoded)
    assert decoded==(ROOT/r['raw_path']).read_text(encoding='utf-8')
    pattern=r'(?P<name>James Rodney Gilstrap) was assigned (?P<count>2,276)&nbsp;patent-related cases&nbsp;from (?P<start>2023) through (?P<end>2025)'
    matches=list(re.finditer(pattern,decoded));assert len(matches)==1
    match=matches[0]
    assert 'August 11, 2026' in (ROOT/r['text_path']).read_text(encoding='utf-8')
    assert 'federal district courts' in html.unescape(decoded)
    name=match['name'];value=int(match['count'].replace(',',''))
    assert value==2276

    def evidence(start,end):
        fragment=decoded[start:end]
        text=' '.join(html.unescape(fragment).split())
        original_start=original_boundaries[start];original_end=original_boundaries[end]
        byte_start=len(original_decoded[:original_start].encode('utf-8'))
        byte_end=len(original_decoded[:original_end].encode('utf-8'))
        original_fragment=raw[byte_start:byte_end]
        assert original_fragment==original_decoded[original_start:original_end].encode('utf-8')
        assert universal_lf_with_original_boundaries(original_fragment.decode('utf-8'))[0]==fragment
        return {'source_url':r['url'],'source_path':r['raw_path'],'source_sha256':r['raw_sha256'],
            'html_character_start':start,'html_character_end':end,
            'html_fragment_sha256':sha(fragment.encode('utf-8')),
            'literal_text':text,'literal_text_sha256':sha(text.encode('utf-8')),
            'raw_byte_start':byte_start,'raw_byte_end':byte_end,
            'raw_fragment_sha256':sha(original_fragment),
            'offset_basis':'Zero-based Python Unicode code points in UTF-8 HTML after universal CRLF/CR-to-LF conversion, end exclusive; equivalent to Path.read_text(encoding=utf-8)',
            'raw_offset_basis':'Independent zero-based offsets in the unchanged original bytes, end exclusive; raw_fragment_sha256 hashes that exact byte slice',
            'literal_text_method':'HTML character-reference decoding followed by Unicode whitespace collapse; selected fragment contains no tags'}

    identity='public-article:'+r['raw_sha256'][:20]+':james-rodney-gilstrap'
    observation={'source_observation_id':identity,'name':name,'subject_type':'judge','record_class':'vendor_published',
        'source_class':'lex_machina_public_article','publisher':'LexisNexis / Lex Machina',
        'judge_system':'federal','judge_system_basis':'Explicit federal district-court patent litigation context in the same article; a specific court or state is not assigned from adjacent venue counts',
        'state_code':None,'state':None,'courts':[],'counties':[],
        'source_url':r['url'],'final_url':r['final_url'],'source_path':r['raw_path'],'source_sha256':r['raw_sha256'],
        'text_path':r['text_path'],'text_sha256':r['text_sha256'],
        'metadata_path':r['metadata_path'],'metadata_sha256':r['metadata_sha256'],
        'captured_at':r['ended_at_utc'],'source_published_at':'2026-08-11',
        'current_status':None,'current_service_verified':False,'identity_resolution':'source_specific_no_cross_source_merge',
        'source_record_kind':'public_vendor_article_named_judge_aggregate',
        'biography':None,'court_assignment_verified':False,
        'limits':['This is a historical vendor-reported case-assignment count, not a judge profile or a litigation outcome rate.',
                  'No case-level cohort or roster was acquired; name-only matching to other judge observations is forbidden.',
                  'No state or court is inferred from the article\'s separate venue rankings.']}
    facts=[{'fact_id':identity+':name','source_observation_id':identity,'field':'reported_name','value':name,
        'source_reported':True,'evidence':evidence(match.start('name'),match.end('name'))}]
    analyses=[{'analysis_id':identity+':patent-assigned-2023-2025','source_observation_id':identity,
        'metric_subject_type':'judge',
        'analysis_type':'vendor_reported_case_assignment_count','metric':'assigned_patent_related_cases',
        'label':'Patent-related cases assigned to the named judge','value':value,'unit':'cases',
        'period':{'label':'2023 through 2025','start_year':2023,'end_year':2025,'precision':'calendar_year'},
        'numerator':None,'denominator':None,'scale_minimum':None,'scale_maximum':None,
        'cohort':'patent-related cases',
        'cohort_scope_note':'Assigned to the named judge during the reported period; the article discusses federal district-court patent litigation. Underlying case IDs were not acquired.',
        'methodology_url':None,'underlying_report':'Lex Machina 2026 Patent Litigation Report (not acquired)',
        'underlying_report_request_url':'https://www.lexisnexis.com/en-us/products/lex-machina/reports.page',
        'source_reported':True,'independently_computed':False,'evidence':evidence(match.start(),match.end()),
        'limitations':['Count is reported by the vendor; the underlying case IDs, exact assignment-date definition and cohort deduplication method are not provided in the saved article.',
                       'This is not a grant rate, win rate, performance rating or current caseload.',
                       'The adjacent comparison to the next busiest judge is not converted into an inferred numeric denominator or ratio.']}]
    for item in facts+analyses:
        ev=item['evidence'];fragment=decoded[ev['html_character_start']:ev['html_character_end']]
        assert sha(fragment.encode())==ev['html_fragment_sha256']
        assert ' '.join(html.unescape(fragment).split())==ev['literal_text']
        assert item['source_observation_id']==identity
    lines('observations.jsonl',[observation]);lines('facts.jsonl',facts);lines('analyses.jsonl',analyses)
    lines('source_documents.jsonl',documents)
    write('methodology.json',{'parser_version':VERSION,'source_type':'Public publisher-authored article, directly retrieved HTTP 200',
        'source_byte_limit':5242880,'network_during_normalization':0,'capture_credentials_used':False,
        'selection':'Exactly one fully stated named-judge assignment count with an explicit period. Generic vendor capabilities and unrelated case/court totals are excluded.',
        'evidence':'HTML character offsets and fragment hashes use universal-newline LF decoded text. Original byte offsets and raw_fragment_sha256 independently bind the unchanged original bytes; full original/text/metadata hashes, source URL and capture time are retained.',
        'authority':'Publisher assertion, not independently recalculated or certified court statistics.',
        'unknowns':['Current service','Specific court/state','Underlying case list','Rate denominator','Deduplication and reassignment handling'],
        'excluded_sources':'Older indexed PDF tables have no locally retrieved original bytes and are kept only as candidates outside this component.'})
    summary={'built_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parser_version':VERSION,
        'source_observations':1,'facts':1,'analyses':1,'source_documents_downloaded':len(documents),
        'downloaded_public_html_bytes':sum(x['bytes'] for x in documents),'public_pdf_originals_downloaded':0,
        'native_source_files_rehashed':len(verified),'unique_current_judges':None,'full_judge_corpus_complete':False,
        'licensed_feed_acquired':False,'identity_merges':0,'independent_outcome_statistics':0,
        'source_fetch_manifest':rel(manifest),'source_fetch_manifest_sha256':sha(manifest.read_bytes()),
        'observation_source_url':r['url'],'input_original_sha256':r['raw_sha256']}
    write('summary.json',summary)
    write('validation.json',{'validated':True,'validated_at_utc':summary['built_at_utc'],'issues':[],
        'source_observation_ids_unique':True,'all_claims_own_observation_id':True,'all_claims_cite_exact_parent_original':True,
        'all_literal_html_and_text_hashes_verified':True,'all_unknown_rates_and_denominators_null':True,
        'original_sha256':verified,'network_requests_during_build':0,
        'output_sha256':{n:sha((OUT/n).read_bytes()) for n in ['observations.jsonl','facts.jsonl','analyses.jsonl','source_documents.jsonl','methodology.json','summary.json']},
        'parser_sha256':sha(Path(__file__).read_bytes()),'cross_source_identity_merge_count':0})
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
