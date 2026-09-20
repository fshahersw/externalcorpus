"""Bounded syntax and chapter-classification checks; no full package rebuild."""
import ast,copy,hashlib,importlib.util,json,sqlite3,sys,datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
scripts=[ROOT/'reports/laws/reconcile.py',ROOT/'scripts/build_focused_laws.py']
syntax=[]
for p in scripts:
 b=p.read_bytes();compile(b,str(p),'exec');syntax.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(b),'syntax_valid':True})
sp=importlib.util.spec_from_file_location('law_reconcile',scripts[0]);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
assert 'corpus/official_law_state_rules_followup_20260914' in m.COLLECTIONS
assert 'corpus/official_law_state_rules_followup_20260914' in scripts[1].read_text()
collection=ROOT/'corpus/official_law_state_rules_followup_20260914';c=sqlite3.connect((collection/'corpus.sqlite3').resolve().as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
row=dict(c.execute("select * from resources where url=? and status='downloaded'",('https://www.ncleg.gov/EnactedLegislation/Statutes/PDF/ByChapter/Chapter_1.pdf',)).fetchone());c.close()
meta=json.loads((collection/row['metadata_path']).read_bytes());raw=(collection/row['raw_path']).read_bytes();tb=(collection/row['text_path']).read_bytes()
assert sha(raw)==row['sha256']==meta['sha256'];assert sha(tb)==meta['text_sha256']
r={'url':row['url'],'observations':[{'collection':m.FOLLOWUP_COLLECTION,'source_contexts':[{'jurisdiction':'North Carolina','category':'statutes','resource_kind':'full_statute_chapter_pdf'}]}],
 'captures':{'x':{'raw_sha256':sha(raw),'raw_hash_verified':True}},'texts':{'x':{'raw_sha256':sha(raw),'text_path':(collection/row['text_path']).relative_to(ROOT).as_posix(),'text_sha256':sha(tb)}}}
checks=[]
def check(name,record,expected):
 result=m.classify_followup_chapter(record);actual=result[0] if result else None;assert actual==expected,(name,result)
 checks.append({'name':name,'expected_role':expected,'observed_role':actual,'passed':True})
check('actual_saved_nc_chapter_1_with_fresh_raw_and_text_hashes',r,'law_chapter_body')
x=copy.deepcopy(r);x['texts']={};check('no_verified_text_is_not_observed_body',x,'law_document_title_evidence_needs_review')
x=copy.deepcopy(r);x['texts']['x']['text_sha256']='0'*64;check('changed_text_digest_rejected',x,'law_document_title_evidence_needs_review')
x=copy.deepcopy(r);x['captures']['x']['raw_hash_verified']=False;check('unverified_raw_capture_rejected',x,'law_document_title_evidence_needs_review')
x=copy.deepcopy(r);x['observations'][0]['source_contexts'][0]['category']='court_rules';check('wrong_jurisdiction_category_context_rejected',x,None)
x=copy.deepcopy(r);x['observations'][0]['collection']='another_collection';check('unreviewed_collection_does_not_acquire_body_role',x,None)
x=copy.deepcopy(r);x['captures']={};check('download_missing_does_not_acquire_body_role',x,None)
fixture=OUT/'classification_fixture.txt';fixture.write_text('CHAPTER 6: TRIAL COURTS\n§ 6-101. Time for disposition.\n'+'Synthetic procedure text for classification boundary test only. '*8,encoding='utf8')
x=copy.deepcopy(r);x['url']='https://nebraskajudicial.gov/book/export/html/9050';x['observations'][0]['source_contexts'][0]={'jurisdiction':'Nebraska','category':'court_rules','resource_kind':'printer_friendly_rule_chapter_html'};x['texts']['x'].update(text_path=fixture.relative_to(ROOT).as_posix(),text_sha256=sha(fixture.read_bytes()))
check('synthetic_nebraska_chapter_export_shape',x,'law_chapter_body')
x=copy.deepcopy(x);x['url']='https://nebraskajudicial.gov/book/export/html/999999';check('unreviewed_nebraska_export_node_rejected',x,None)
source=scripts[1].read_text();assert "'observed_chapter_text_extent_and_currency_unverified' if followup" in source
summary={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'syntax':syntax,'classification_checks':checks,'check_count':len(checks),'issues':[],'full_package_builders_run':False,'collector_config_or_queue_modified':False,'classification_scope':'Source-kind/jurisdiction plus verified raw/text and chapter/section indicators; no whole-document, legal correctness or current-edition certification.','real_sample_url':row['url'],'real_sample_raw_sha256':sha(raw),'real_sample_text_sha256':sha(tb),'fixture_is_synthetic':True,'builder_version':'1.0.5','new_collection_in_both_explicit_lists':True,'followup_whole_document_status':'observed_chapter_text_extent_and_currency_unverified'}
(OUT/'integration_inspection_receipt.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8');print(json.dumps(summary,indent=2))
