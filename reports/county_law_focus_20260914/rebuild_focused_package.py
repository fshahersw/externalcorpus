"""Refresh completed official additions while holding every reviewed collector lock."""
from pathlib import Path
from contextlib import ExitStack,redirect_stdout,redirect_stderr
import argparse,datetime,hashlib,importlib.util,json,runpy,shutil,sys,time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'pipeline'))
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from corpus_crawler import run_lock
from rebuild_checkpoint_cache import CheckpointCache
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class PublicationBackup:
    """Restore the prior published package after any failed coordinated rebuild."""
    def __init__(self,root,out):self.root=root.resolve();self.out=out.resolve();self.package=self.root/'delivery/focused_legal_corpus';self.files={};self.owned_scope_sha=None
    def __enter__(self):
        self.out.relative_to(self.root);assert self.package.resolve()==self.root/'delivery/focused_legal_corpus'
        self.backup=self.out/'previous_published_package';shutil.copytree(self.package,self.backup)
        for name in ['README.md','reports/remaining_resume_20260913/scope.json','delivery/ui-sketch/data.js']:
            p=self.root/name;self.files[name]=p.read_bytes() if p.exists() else None
        return self
    def record_owned_scope_update(self):
        self.owned_scope_sha=sha(self.root/'reports/remaining_resume_20260913/scope.json')
    def __exit__(self,kind,error,tb):
        if kind is None:return False
        # Both resolved rename endpoints are inside this exact workspace. Keep
        # the failed build as evidence; do not recursively delete either tree.
        assert self.package.resolve()==self.root/'delivery/focused_legal_corpus'
        failed=self.out/'failed_build_package';failed.resolve().relative_to(self.root)
        if self.package.exists():self.package.rename(failed)
        self.backup.rename(self.package)
        for name,data in self.files.items():
            p=self.root/name;p.resolve().relative_to(self.root)
            if name=='reports/remaining_resume_20260913/scope.json':
                # Preserve a concurrent new user scope. Revert only the scope
                # update this build's finalizer explicitly recorded as its own.
                if self.owned_scope_sha is None or not p.exists() or sha(p)!=self.owned_scope_sha:continue
            if data is not None:p.write_bytes(data)
            elif p.is_file():p.unlink()
        (self.out/'publication_rollback.json').write_text(json.dumps({'restored_at':now(),'restored_previous_published_package':True,'failure':str(error),'failed_build_preserved':str(failed.relative_to(self.root)),'shared_index_note':'The shared index is append-only for capture versions and text; newly indexed additions may remain, while the prior focused selection is restored.'},indent=2)+'\n',encoding='utf-8')
        return False
def main(argv=()):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force',action='store_true',help='Run all seven steps even if the byte-verified checkpoint is unchanged.')
    parser.add_argument('--no-rebuild-cache',action='store_true',help='Run the normal full workflow without checking or establishing a no-change baseline.')
    options=parser.parse_args(argv)
    scope_path=ROOT/'reports/remaining_resume_20260913/scope.json'
    scope_bytes=scope_path.read_bytes();scope=json.loads(scope_bytes)
    frozen_scope_sha=hashlib.sha256(scope_bytes).hexdigest()
    assert scope['latest_user_direction']=='Continue official sources only'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=ROOT/'reports/county_law_focus_20260914/rebuilds'/stamp;out.mkdir(parents=True,exist_ok=False)
    receipt={'started_at':now(),'scope':'official state laws and county local documents','scope_input_sha256':frozen_scope_sha,'collections':scope['reviewed_collections'],'steps':[],'validated':False}
    target=out/'receipt.json'
    def save():target.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    save()
    with ExitStack() as locks:
        for name in scope['reviewed_collections']:
            p=(ROOT/name).resolve();p.relative_to(ROOT/'corpus');assert (p/'corpus.sqlite3').is_file();locks.enter_context(run_lock(p))
        assert '| Location |' in (ROOT/'README.md').read_text(encoding='utf-8'), 'Root guide preflight failed'
        cache=CheckpointCache(ROOT)
        cache_before=None
        if not options.no_rebuild_cache:
            receipt['checkpoint_cache']=({'hit':False,'reason':'forced_full_build'} if options.force else cache.check());save()
            if receipt['checkpoint_cache']['hit']:
                assert sha(scope_path)==frozen_scope_sha, 'Scope changed during checkpoint verification'
                receipt.update(ended_at=now(),validated=True,publication_action='unchanged_validated_snapshot_reused',
                    package_summary_sha256=sha(ROOT/'delivery/focused_legal_corpus/summary.json'),
                    package_manifest_sha256=sha(ROOT/'delivery/focused_legal_corpus/package_files.json'))
                save();print(json.dumps({'validated':True,'skipped_unchanged':True,'receipt':target.relative_to(ROOT).as_posix()}),flush=True)
                return
            try:cache_before=cache.inventory(inputs_only=True)
            except (OSError,ValueError,RuntimeError) as exc:
                receipt['cache_baseline']={'written':False,'reason':'input_inventory_unavailable','error_type':type(exc).__name__};save()
        publication=locks.enter_context(PublicationBackup(ROOT,out))
        steps=[('scripts/build_document_index.py',['build']),('scripts/build_focused_laws.py',[]),('scripts/build_focused_counties.py',[]),('scripts/build_county_local_package.py',[]),('scripts/build_focused_package.py',[]),('scripts/finalize_official_resume_20260913.py',[]),('delivery/ui-sketch/build_data.py',[])]
        for script,args in steps:
            src=ROOT/script;name=src.stem;step={'script':script,'started_at':now(),'source_sha256':sha(src),'stdout':(out/(name+'.stdout.log')).relative_to(ROOT).as_posix(),'stderr':(out/(name+'.stderr.log')).relative_to(ROOT).as_posix()};receipt['steps'].append(step);save()
            assert sha(scope_path)==frozen_scope_sha, 'Scope changed during locked build; publication cancelled'
            print(json.dumps({'event':'step_started','script':script}),flush=True)
            step_clock=time.perf_counter()
            try:
                with (ROOT/step['stdout']).open('w',encoding='utf-8') as stdout,(ROOT/step['stderr']).open('w',encoding='utf-8') as stderr,redirect_stdout(stdout),redirect_stderr(stderr):
                    prior_argv=sys.argv;sys.argv=[str(src),*args]
                    try:
                        if name=='finalize_official_resume_20260913':
                            spec=importlib.util.spec_from_file_location('official_finalize',src);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                            module.finalize(scope,persist_scope=False)
                        elif name=='build_county_local_package':
                            spec=importlib.util.spec_from_file_location('county_local_package',src);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                            module.build()
                        else:
                            try:runpy.run_path(str(src),run_name='__main__')
                            except SystemExit as exc:
                                if exc.code not in (None,0):raise
                    finally:sys.argv=prior_argv
                step['exit_code']=0
            except BaseException as exc:
                step['exit_code']=1;step['error']=type(exc).__name__+': '+str(exc);step['ended_at']=now();save();raise
            assert sha(src)==step['source_sha256']
            step['ended_at']=now();step['elapsed_seconds']=round(time.perf_counter()-step_clock,6);save();print(json.dumps({'event':'step_completed','script':script}),flush=True)
        assert sha(scope_path)==frozen_scope_sha, 'Scope changed before publication; publication cancelled'
        pending_scope=out/'scope.ready.json';pending_scope.write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8');pending_scope.replace(scope_path)
        publication.record_owned_scope_update()
        receipt.update(ended_at=now(),validated=True,publication_action='full_seven_step_rebuild',package_summary_sha256=sha(ROOT/'delivery/focused_legal_corpus/summary.json'),package_manifest_sha256=sha(ROOT/'delivery/focused_legal_corpus/package_files.json'))
        save()
        # Cache bookkeeping is outside the signed receipt to keep its digest
        # stable. Cache failure does not invalidate a passing full publication.
        if cache_before is not None:
            try:cache_result=cache.remember(target,cache_before)
            except (OSError,ValueError,KeyError,TypeError,RuntimeError) as exc:
                cache_result={'written':False,'reason':'baseline_not_established','error_type':type(exc).__name__}
            (out/'checkpoint_cache_result.json').write_text(json.dumps(cache_result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'validated':True,'receipt':target.relative_to(ROOT).as_posix()}),flush=True)
if __name__=='__main__':main(sys.argv[1:])
