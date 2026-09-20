"""One bounded field-only refresh of the validated 07:49 build; no recrawling."""
from pathlib import Path
from contextlib import ExitStack,redirect_stdout,redirect_stderr
import datetime,hashlib,importlib.util,json,runpy,sqlite3,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'pipeline'));sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(Path(__file__).parent))
from corpus_crawler import run_lock
from rebuild_focused_package import PublicationBackup
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def laws_hashes():return {p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'delivery/focused_legal_corpus/laws').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
def main():
    prior=read(ROOT/'reports/county_law_focus_20260914/rebuilds/20260914T074951Z/receipt.json');assert prior['validated']
    scope_path=ROOT/'reports/remaining_resume_20260913/scope.json';scope_bytes=scope_path.read_bytes();scope=json.loads(scope_bytes);scope_sha=hashlib.sha256(scope_bytes).hexdigest()
    assert scope['reviewed_collections']==prior['collections']
    out=ROOT/'reports/county_law_focus_20260914/rebuilds'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ_county_labels');out.mkdir(parents=True)
    receipt={'validated':False,'source_validated_build':'reports/county_law_focus_20260914/rebuilds/20260914T074951Z/receipt.json','scope':'Exact court-label fields; reuse unchanged validated laws and text index','steps':[]};target=out/'receipt.json'
    def save():target.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    save()
    with ExitStack() as locks:
        for name in scope['reviewed_collections']:locks.enter_context(run_lock(ROOT/name))
        assert sha(ROOT/'delivery/focused_legal_corpus/summary.json')==prior['package_summary_sha256']
        c=sqlite3.connect((ROOT/'delivery/focused_legal_corpus/focused.sqlite3').as_uri()+'?mode=ro',uri=True)
        try:published=set(c.execute("SELECT collection,source_url,raw_sha256 FROM documents WHERE capture_kind='direct_public_capture'"))
        finally:c.close()
        for name in scope['reviewed_collections']:
            c=sqlite3.connect((ROOT/name/'corpus.sqlite3').as_uri()+'?mode=ro',uri=True)
            try:live={(name,*r) for r in c.execute("SELECT url,sha256 FROM resources WHERE status='downloaded'")}
            finally:c.close()
            assert live=={r for r in published if r[0]==name},'Changed capture set requires full rebuild: '+name
        index_sha=sha(ROOT/'catalog/summary.json');law_files=laws_hashes()
        backup=locks.enter_context(PublicationBackup(ROOT,out))
        for name in ['build_county_local_package','build_focused_package','finalize_official_resume_20260913','build_data']:
            assert sha(scope_path)==scope_sha
            src=ROOT/('delivery/ui-sketch/build_data.py' if name=='build_data' else 'scripts/'+name+'.py')
            step={'script':src.relative_to(ROOT).as_posix(),'sha256':sha(src)};receipt['steps'].append(step);save()
            print(json.dumps({'step':name,'status':'started'}),flush=True)
            try:
                with (out/(name+'.log')).open('w',encoding='utf-8') as log,redirect_stdout(log),redirect_stderr(log):
                    if name=='build_county_local_package':module(src,name).build()
                    elif name=='finalize_official_resume_20260913':module(src,name).finalize(scope,persist_scope=False)
                    else:
                        old=sys.argv;sys.argv=[str(src)]
                        try:runpy.run_path(str(src),run_name='__main__')
                        finally:sys.argv=old
                assert sha(src)==step['sha256'];step['passed']=True;save()
            except BaseException as exc:step.update(passed=False,error=str(exc));save();raise
        assert sha(ROOT/'catalog/summary.json')==index_sha and laws_hashes()==law_files
        c=sqlite3.connect((ROOT/'delivery/focused_legal_corpus/focused.sqlite3').as_uri()+'?mode=ro',uri=True)
        try:
            rows=c.execute("SELECT collection,county_court_labels_json,county_geoids_json FROM documents WHERE collection IN ('corpus/county_local_rules_washington_20260914','corpus/county_local_rules_washington_20260914/ocr')").fetchall()
        finally:c.close()
        assert len(rows)==140 and all(json.loads(r[1]) for r in rows)
        direct=[r for r in rows if not r[0].endswith('/ocr')];assert len(direct)==129 and sum(not json.loads(r[2]) for r in direct)==76
        assert sha(scope_path)==scope_sha
        prepared=out/'scope.ready.json';prepared.write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8');prepared.replace(scope_path);backup.record_owned_scope_update()
        receipt.update(validated=True,labels_preserved_in_direct_records=129,labels_preserved_in_ocr_records=11,county_unassigned_direct_records_preserved=76,law_component_and_shared_index_unchanged=True,package_summary_sha256=sha(ROOT/'delivery/focused_legal_corpus/summary.json'),package_manifest_sha256=sha(ROOT/'delivery/focused_legal_corpus/package_files.json'));save()
    print(json.dumps({'validated':True,'receipt':target.relative_to(ROOT).as_posix()}),flush=True)
if __name__=='__main__':main()
