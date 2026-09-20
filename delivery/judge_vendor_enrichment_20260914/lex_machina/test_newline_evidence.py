"""Offline regression: contract LF offsets and independent original byte spans."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import sys
from lxml import html
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
spec=importlib.util.spec_from_file_location('lm_newlines',OUT/'build.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
sha=lambda b:hashlib.sha256(b).hexdigest()

for original in ['x\r\ny\rz\n','\r\n\r\n','A\u2028B\u2029C','α\r\n<p>Judge A\r\nwas assigned 2 cases.</p>\rTail']:
    raw=original.encode('utf-8')
    expected=io.TextIOWrapper(io.BytesIO(raw),encoding='utf-8',newline=None).read()
    actual,boundaries=build.universal_lf_with_original_boundaries(original)
    assert actual==expected and len(boundaries)==len(actual)+1
    assert boundaries[0]==0 and boundaries[-1]==len(original)
    for a in range(len(actual)):
        for b in range(a+1,len(actual)+1):
            original_slice=original[boundaries[a]:boundaries[b]]
            assert io.StringIO(original_slice,newline=None).read()==actual[a:b]

history=ROOT/'sources/judges/vendor_probe_20260914/lex_machina/evidence_lf_fix_20260914'
checks=[]
for name in ['facts.jsonl','analyses.jsonl']:
    previous=[json.loads(x) for x in (history/name).read_text().splitlines()]
    current=[json.loads(x) for x in (OUT/name).read_text().splitlines()]
    assert len(previous)==len(current)==1
    for old,row in zip(previous,current):
        assert {k:v for k,v in old.items() if k!='evidence'}=={k:v for k,v in row.items() if k!='evidence'}
        e=row['evidence'];path=ROOT/e['source_path'];raw=path.read_bytes();normalized=path.read_text(encoding='utf-8')
        assert sha(raw)==e['source_sha256']
        fragment=normalized[e['html_character_start']:e['html_character_end']]
        assert sha(fragment.encode())==e['html_fragment_sha256']
        actual=' '.join(html.fragment_fromstring('<span>'+fragment+'</span>').text_content().split())
        assert actual==e['literal_text'] and sha(actual.encode())==e['literal_text_sha256']
        raw_fragment=raw[e['raw_byte_start']:e['raw_byte_end']]
        assert sha(raw_fragment)==e['raw_fragment_sha256']
        assert io.TextIOWrapper(io.BytesIO(raw_fragment),encoding='utf-8',newline=None).read()==fragment
        assert e['raw_byte_start']==old['evidence']['raw_byte_start'] and e['raw_byte_end']==old['evidence']['raw_byte_end']
        checks.append({'file':name,'original_sha256':e['source_sha256'],'old_html_start':old['evidence']['html_character_start'],
            'lf_html_start':e['html_character_start'],'original_byte_start':e['raw_byte_start'],'original_byte_end':e['raw_byte_end'],
            'unchanged_raw_byte_span':True,'independent_lxml_literal_verified':True})
assert (OUT/'observations.jsonl').read_bytes()==(history/'observations.jsonl').read_bytes()
validation=json.loads((OUT/'validation.json').read_text())
for name,digest in validation['output_sha256'].items():assert sha((OUT/name).read_bytes())==digest
result={'validated':True,'issues':[],'synthetic_newline_fixtures':4,'actual_claims_checked':len(checks),
    'claim_values_and_observation_unchanged':True,'original_sources_unchanged':True,
    'normalizer_sha256':sha((OUT/'build.py').read_bytes()),'component_validation_sha256':sha((OUT/'validation.json').read_bytes()),
    'checks':checks}
(history/'lf_fix_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
