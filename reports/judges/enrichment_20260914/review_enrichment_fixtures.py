"""Bounded helper and sealed-reader fixtures; never run the production builder."""
from pathlib import Path
from contextlib import redirect_stdout
import ast
import datetime
import hashlib
import importlib.util
import io
import json
import sqlite3
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj)
    return obj


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj) + '\n', encoding='utf-8')


def main():
    build = ROOT / 'scripts/build_judge_enrichment.py'
    search = ROOT / 'scripts/search_judge_enrichment.py'
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in [build, search]}
    b, s = load('enrichment_build_review', build), load('enrichment_search_review', search)
    checks = []
    for court, state, wanted in [
        ('CO - U.S. District Court for the District of Colorado','CO','federal'),
        ('United States Court of Appeals for the Ninth Circuit','CA','federal'),
        ('Los Angeles Immigration Court','CA','administrative'),
        ('Cochise County Superior Court','AZ','state'),
        ('Unspecified tribunal',None,'unknown'),
        ('District Court',None,'unknown'),
    ]:
        assert b.reported_system({'courts':[court],'state_code':state})[0] == wanted
    checks.append('reported_system_explicit_labels_and_unknowns')
    function = next(x for x in ast.walk(ast.parse(build.read_text(encoding='utf-8'))) if isinstance(x,ast.FunctionDef) and x.name=='scan_originals')
    calls = []
    ns = {'verify_original': lambda path, digest: calls.append((path,digest))}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(build),'exec'),ns)
    for pk, hk in [('source_path','source_sha256'),('artifact_path','artifact_sha256'),('raw_path','raw_sha256'),('text_path','text_sha256'),('narrative_path','narrative_sha256')]:
        for bad in [{pk:'original',hk:None},{pk:None,hk:'digest'}]:
            try: ns['scan_originals']({'nested':[bad]})
            except ValueError: pass
            else: raise AssertionError('One-sided citation accepted: '+pk)
    ns['scan_originals']({'source_path':'original','source_sha256':'digest'})
    assert calls == [('original','digest')]
    ns['scan_originals']({'source_path':None,'source_sha256':None})
    checks.append('all_recognized_one_sided_original_pairs_rejected')
    fixture = OUT / ('fixture_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    fixture.mkdir()
    folder = fixture / 'component'; folder.mkdir()
    target = folder / 'observations.jsonl'; target.write_text('{}\n',encoding='utf-8')
    binding = {'output_sha256':{'observations.jsonl':sha(target)}}
    b.bound_outputs(folder,binding,['observations.jsonl'])
    target.write_text('{"changed":true}\n',encoding='utf-8')
    try: b.bound_outputs(folder,binding,['observations.jsonl'])
    except ValueError: pass
    else: raise AssertionError('Post-validation semantic change accepted')
    checks.append('semantic_output_hash_binding_rejects_changed_file')
    base = fixture / 'delivery/judge_enrichment_20260914'
    snap = base / 'snapshots/synthetic'; snap.mkdir(parents=True)
    database = snap / 'judge_corpus.sqlite3'
    db = sqlite3.connect(database)
    db.executescript('''CREATE TABLE judges(judge_id TEXT,name TEXT,payload TEXT);
        CREATE TABLE observations(observation_id TEXT,judge_id TEXT,source_class TEXT,judge_system TEXT,state_code TEXT,name TEXT,courts TEXT,payload TEXT);
        CREATE TABLE facts(fact_id TEXT,judge_id TEXT,payload TEXT);
        CREATE TABLE analyses(analysis_id TEXT,judge_id TEXT,observation_id TEXT,analysis_type TEXT,payload TEXT);
        CREATE VIRTUAL TABLE observation_search USING fts5(observation_id UNINDEXED,name,details);''')
    for oid,jid,name,state,system,source,court in [
        ('co:1','judge-co','Jane Example','CO','state','state_evaluations','1st Judicial District Court'),
        ('fjc:2','judge-fjc','John Example',None,'federal','federal_biographies','U.S. District Court')]:
        obj={'source_observation_id':oid,'judge_id':jid,'name':name,'source_class':source,'judge_system':system,'state_code':state,'courts':[court]}
        db.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?)',(oid,jid,source,system,state,name,json.dumps([court]),json.dumps(obj)))
        db.execute('INSERT INTO judges VALUES(?,?,?)',(jid,name,json.dumps({'judge_id':jid,'name':name})))
        db.execute('INSERT INTO observation_search VALUES(?,?,?)',(oid,name,'Synthetic professional history'))
    db.execute('INSERT INTO analyses VALUES(?,?,?,?,?)',('analysis:1','judge-co','co:1','commission_vote',json.dumps({'source_observation_id':'co:1','denominator':None,'value':10})))
    db.commit(); db.close()
    dbkey=database.relative_to(fixture).as_posix()
    manifest=snap/'files.sha256.json'; write(manifest,{dbkey:{'sha256':sha(database),'bytes':database.stat().st_size}})
    review=fixture/'reports/judges/enrichment_20260914/independent_review.json'
    approved={'validated':True,'unresolved_material_findings':0,'snapshot_path':snap.relative_to(fixture).as_posix(),'manifest_sha256':sha(manifest)}
    def set_review(obj):
        write(review,obj)
        write(base/'latest.json',{'snapshot_path':snap.relative_to(fixture).as_posix(),'manifest_sha256':sha(manifest),'independent_review_path':review.relative_to(fixture).as_posix(),'independent_review_sha256':sha(review)})
    s.ROOT, s.BASE = fixture, base
    old_argv = sys.argv
    def query(args):
        stream=io.StringIO(); sys.argv=['search_judge_enrichment.py']+args
        try:
            with redirect_stdout(stream): s.main()
            return {'result':json.loads(stream.getvalue())}
        except Exception as e: return {'error':type(e).__name__+': '+str(e)}
    try:
        set_review(approved)
        result=query(['Jane','--state','co','--source','state_evaluations','--system','state','--has-analysis','--analysis-type','commission_vote'])
        assert len(result['result'])==1 and result['result'][0]['observation_id']=='co:1'
        assert len(query(['   '])['result'])==2
        assert len(query(['--system','federal'])['result'])==1
        assert not query(['--court',"' OR 1=1 --"])['result']
        assert query(['--report','judge-co'])['result']['analysis'][0]['denominator'] is None
        checks.append('search_filters_null_analysis_context_report_and_whitespace')
        for changes in [{'snapshot_path':'delivery/judge_enrichment_20260914/snapshots/another'}, {'manifest_sha256':'0'*64}, {'validated':False}, {'unresolved_material_findings':1}]:
            set_review({**approved,**changes})
            bad=query([])
            assert 'error' in bad, ('Unbound or failed review accepted',changes,bad)
        checks.append('reader_requires_exact_successful_review_binding')
        set_review(approved)
        with sqlite3.connect(database) as db: db.execute('UPDATE observations SET name=? WHERE observation_id=?',('Changed','co:1'))
        assert 'error' in query([])
        checks.append('reader_rejects_changed_database')
    finally:
        sys.argv=old_argv
    assert all(sha(ROOT/path)==h for path,h in hashes.items()),'Code changed during fixture'
    result={'validated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewed_code_sha256':hashes,'checks':checks,'passed':len(checks),'failure_count':0,'fixture_path':fixture.relative_to(ROOT).as_posix(),'production_builder_runs':0,'network_requests':0}
    write(OUT/'code_fixture_results.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
