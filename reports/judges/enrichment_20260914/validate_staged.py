"""Read-only integration audit of one exact staged judge enrichment snapshot."""
from pathlib import Path
from collections import Counter, defaultdict
import datetime
import hashlib
import importlib.util
import json
import sqlite3
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):
    with path.open(encoding='utf-8-sig') as f:
        return [json.loads(x) for x in f if x.strip()]
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for x in iter(lambda:f.read(1048576),b''): h.update(x)
    return h.hexdigest()
def safe(value):
    p=(ROOT/value).resolve();p.relative_to(ROOT);return p


def main():
    snap=safe(sys.argv[1]);snap.relative_to(ROOT/'delivery/judge_enrichment_20260914/snapshots')
    manifest_path=snap/'files.sha256.json'; manifest_digest=sha(manifest_path); manifest=read(manifest_path)
    hashes={}
    for name,item in manifest.items():
        p=safe(name);p.relative_to(snap)
        hashes[name]=sha(p)
        if hashes[name]!=item['sha256'] or p.stat().st_size!=item['bytes']: raise ValueError('Snapshot seal mismatch: '+name)
    code_review=read(OUT/'code_review.json')
    assert code_review['validated'] is True and code_review['unresolved_material_findings']==0
    for name,digest in code_review['reviewed_code_sha256'].items():
        assert sha(ROOT/name)==digest==sha(snap/'pipeline'/Path(name).name)
    spec=importlib.util.spec_from_file_location('reviewed_enrichment',ROOT/'scripts/build_judge_enrichment.py')
    b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    originals=read(snap/'verified_originals.json')
    for name,digest in originals.items():
        if sha(safe(name))!=digest: raise ValueError('Cited original changed: '+name)
    inputs=read(snap/'component_inputs.json')
    for name,item in inputs.items():
        assert sha(safe(name))==item['sha256']==hashes[item['snapshot_path']],name
    components={}
    for name in ['state_evaluations','federal_biographies','identity']:
        folder=snap/'components'/name;validation=read(folder/'validation.json')
        assert validation.get('validated') is True
        for filename,digest in validation['output_sha256'].items():
            assert sha(folder/filename)==digest,(name,filename)
        components[name]=validation
    colorado_path=OUT/'colorado_independent_audit.json'; colorado=read(colorado_path)
    assert colorado['validated'] is True and colorado['unresolved_findings']==0 and not colorado['issues']
    colorado_copies=0
    for name,digest in colorado['component_sha256'].items():
        src=safe(name); relative=src.relative_to(ROOT/'delivery/judge_enrichment_20260914/state_evaluations')
        assert sha(src)==digest==sha(snap/'components/state_evaluations'/relative),name
        colorado_copies+=1
    # This stage adds the final 999-profile batch and the reviewed service-tag
    # correction. Bind its separate source audit to the exact frozen component.
    trellis_audit_path=OUT/'trellis_added_sample_audit.json';trellis_audit=read(trellis_audit_path)
    assert trellis_audit['validated'] is True and trellis_audit['unresolved_findings']==0 and not trellis_audit['issues']
    stage_summary=read(snap/'summary.json');sealed_base=safe(stage_summary['base_snapshot'])
    sealed_base.relative_to(ROOT/'delivery/judge_intelligence_20260913/snapshots')
    assert sha(sealed_base/'files.sha256.json')==sha(snap/'components/base/original_manifest.json')
    sealed_base_manifest=read(snap/'components/base/original_manifest.json')
    for name,item in sealed_base_manifest.items():
        p=safe(name);p.relative_to(sealed_base)
        assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes'],name
    trellis_copies=0
    for name,digest in trellis_audit['component_hashes'].items():
        src=safe(name);relative=src.relative_to(ROOT/'delivery/judge_intelligence_20260913/trellis_profiles')
        assert sha(src)==digest,name
        frozen=sealed_base/'trellis_profiles'/relative
        if frozen.exists():
            assert sha(frozen)==digest,name
            trellis_copies+=1
        else:
            assert relative.as_posix() in {'normalize.py','test_normalize.py','files.sha256.json'},name
    service_path=ROOT/'reports/judges/focus_20260913/service_classifier_review/independent_projection_review.json'
    service=read(service_path)
    assert service['validated'] is True and service['unresolved_material_findings']==0
    legacy_review_path=ROOT/'reports/judges/focus_20260913/package_code_review.json';legacy_review=read(legacy_review_path)
    assert legacy_review['remaining_material_findings']==[]
    for name,digest in legacy_review['reviewed_files_sha256'].items(): assert sha(safe(name))==digest
    assert service['normalizer_sha256']==legacy_review['reviewed_files_sha256'][service['normalizer_path']]
    approval=read(sealed_base/'root_package_approval.json')
    assert approval['approved'] is True and approval['package_code_review_sha256']==sha(legacy_review_path)
    final_trellis_profiles=rows(sealed_base/'trellis_profiles/profiles.jsonl')
    assert len(final_trellis_profiles)==trellis_audit['final_component_profiles']
    assert all(p['parser_version']==service['parser_version_after'] for p in final_trellis_profiles)
    final_trellis_facts=rows(snap/'components/base/trellis_profiles/facts.jsonl')
    final_service_ids={f['fact_id'] for f in final_trellis_facts if f['field']=='service_or_role_passage'}
    final_biography={(f['capture_id'],f['value']) for f in final_trellis_facts if f['field']=='biography_passage'}
    for case in service['cases']:
        assert (case['fact_id'] in final_service_ids)==case['after_service_tag']
        assert (case['capture_id'],case['literal_value']) in final_biography
        assert originals[case['source_path']]==case['source_sha256']
    observations=rows(snap/'source_observations.jsonl'); lookup={o['source_observation_id']:o for o in observations}
    assert len(lookup)==len(observations)
    base=rows(snap/'components/base/reports.jsonl');base_ids={r['record_id'] for r in base}
    for r in base:
        o=lookup[r['record_id']]
        assert o['native_record']==r and o['name']==r['name'] and o['source_url']==r['source_url']
        assert o['state_code']==r.get('state_code') and o['courts']==r.get('courts',[])
        assert o['judge_system']==b.reported_system(r)[0]
    component_ids={}
    for name in ['state_evaluations','federal_biographies']:
        native=rows(snap/'components'/name/'observations.jsonl')
        component_ids[name]={r['source_observation_id'] for r in native}
        assert len(component_ids[name])==len(native)
        for p in native:
            o=lookup[p['source_observation_id']]
            assert o['native_record']==p and o['name']==p['name'] and o['source_class']==name
            assert o['state_code']==p.get('state_code') and o['courts']==p.get('courts',[])
            expected=p['judge_system']
            if expected not in {'state','federal','administrative','unknown'}: expected=b.reported_system(p)[0]
            assert o['judge_system']==expected
    assert base_ids|component_ids['state_evaluations']|component_ids['federal_biographies']==set(lookup)
    crosswalk=rows(snap/'components/identity/observation_identity.jsonl'); mapping={r['source_observation_id']:r for r in crosswalk}
    assert len(mapping)==len(crosswalk) and set(mapping)==base_ids
    identity_source=read(snap/'components/identity/summary.json')['source_snapshot']
    summary=read(snap/'summary.json')
    assert identity_source['snapshot_path']==summary['base_snapshot']
    assert identity_source['manifest_sha256']==sha(snap/'components/base/original_manifest.json')
    for oid in base_ids: assert lookup[oid]['judge_id']==mapping[oid]['judge_id']
    for component,ids in component_ids.items():
        for oid in ids:
            o=lookup[oid];native=o['native_record']
            anchor=native.get('source_record_id') if component=='federal_biographies' else oid
            assert o['judge_id']==b.ident('source-judge:',anchor or oid)
            if component=='federal_biographies': assert oid.startswith(anchor+':csv:')
    groups=rows(snap/'judges.jsonl');members=defaultdict(list)
    for o in observations:
        members[o['judge_id']].append(o['source_observation_id'])
        assert o['current_service_verified'] is False
    assert len(groups)==len(members)
    for g in groups:
        assert sorted(g['source_observation_ids'])==sorted(members[g['judge_id']])
        assert g['current_service_verified'] is False
    fact_native={}
    for group in ['official_profiles','trellis_profiles']:
        p=snap/'components/base'/group/'facts.jsonl';fact_native[p.relative_to(ROOT).as_posix()]=rows(p)
    for group in component_ids:
        p=snap/'components'/group/'facts.jsonl';fact_native[p.relative_to(ROOT).as_posix()]=rows(p)
    facts=rows(snap/'facts.jsonl');analyses=rows(snap/'analyses.jsonl');context=rows(snap/'context_analyses.jsonl')
    assert len({f['fact_id'] for f in facts})==len(facts)
    for f in facts:
        native=fact_native[f['evidence']['file']][f['evidence']['line']-1]
        assert native==f['native_record'] and f['value']==native.get('value')
        owner=lookup[f['source_observation_id']]
        assert f['judge_id']==owner['judge_id']
        if owner['source_class'] in component_ids:
            assert f['source_observation_id'] in component_ids[owner['source_class']]
            assert '/components/'+owner['source_class']+'/' in f['evidence']['file']
            assert f['source_observation_id']==native['source_observation_id']
            assert f['field']==(native.get('field') or native.get('predicate'))
        elif owner['source_class']=='official_observation':
            assert f['source_observation_id']=='official:'+native['profile_id'] and f['field']==native['category']
        else:
            assert f['source_observation_id']=='trellis-profile:'+native['capture_id'] and f['field']==native['field']
    analysis_native=rows(snap/'components/state_evaluations/analyses.jsonl')
    assert len(analyses)==len(analysis_native) and len({a['analysis_id'] for a in analyses})==len(analyses)
    preserved=['analysis_type','metric','label','value','unit','numerator','denominator','scale_minimum','scale_maximum','period','cohort','methodology_url']
    for a in analyses:
        native=analysis_native[a['evidence']['line']-1]
        assert native==a['native_record']
        assert a['source_observation_id']==native['source_observation_id'] in component_ids['state_evaluations']
        assert a['judge_id']==lookup[a['source_observation_id']]['judge_id']
        assert all(a[k]==native.get(k) for k in preserved)
        if a['analysis_type']=='survey_overall_rating':
            assert a['numerator'] is None and a['denominator'] is None and a['scale_minimum'] is None
    context_native=rows(snap/'components/state_evaluations/context_analyses.jsonl')
    assert len(context)==len(context_native)
    for a in context:
        assert a['native_record']==context_native[a['evidence']['line']-1]
        assert a['source_observation_id'] is None and a['judge_id'] is None and a['aggregation_scope']=='statewide_cycle'
    counts={'source_observations':len(observations),'identity_groups':len(groups),'fact_claims':len(facts),'analysis_records':len(analyses),'separate_aggregate_context_records':len(context)}
    assert all(summary[k]==v for k,v in counts.items())
    assert summary['full_national_corpus_complete'] is False and summary['unique_current_judges'] is None
    database=snap/'judge_corpus.sqlite3';db=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    for table,expected in [('observations',len(observations)),('judges',len(groups)),('facts',len(facts)),('analyses',len(analyses)),('context_analyses',len(context)),('observation_search',len(observations))]:
        assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==expected
    for table in ['facts','analyses']:
        assert db.execute('SELECT count(*) FROM '+table+' a LEFT JOIN observations o ON a.observation_id=o.observation_id WHERE o.observation_id IS NULL OR a.judge_id<>o.judge_id').fetchone()[0]==0
    assert db.execute("SELECT count(*) FROM analyses a JOIN observations o ON a.observation_id=o.observation_id WHERE o.source_class<>'state_evaluations'").fetchone()[0]==0
    by_system=dict(db.execute('SELECT judge_system,count(*) FROM observations GROUP BY judge_system'))
    by_source=dict(db.execute('SELECT source_class,count(*) FROM observations GROUP BY source_class'))
    assert by_source==dict(Counter(o['source_class'] for o in observations))
    sample=next(o for o in observations if o['source_class']=='state_evaluations')
    token=sample['name'].split()[0].replace('"','""')
    assert db.execute('SELECT count(*) FROM observation_search WHERE observation_search MATCH ?',('"'+token+'"',)).fetchone()[0]>0
    db.close()
    assert sha(database)==hashes[database.relative_to(ROOT).as_posix()]
    assert sha(manifest_path)==manifest_digest
    for name,digest in code_review['reviewed_code_sha256'].items(): assert sha(ROOT/name)==digest
    result={'validated':True,'unresolved_material_findings':0,'reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'snapshot_path':snap.relative_to(ROOT).as_posix(),'manifest_sha256':manifest_digest,
        'reviewed_code_sha256':code_review['reviewed_code_sha256'],'code_review_path':'reports/judges/enrichment_20260914/code_review.json','code_review_sha256':sha(OUT/'code_review.json'),
        'validator_path':Path(__file__).relative_to(ROOT).as_posix(),'validator_sha256':sha(Path(__file__)),
        'snapshot_files_hash_verified':len(manifest),'input_copies_hash_verified':len(inputs),'originals_freshly_rehashed':len(originals),
        'counts':counts,'observations_by_source':by_source,'observations_by_reported_system':by_system,
        'checks':{'all_base_native_records_preserved':True,'all_external_native_records_preserved':True,'all_fact_values_and_source_attributions_verified':True,'all_analysis_fields_and_null_context_preserved':True,'all_claim_foreign_keys_and_component_ownership_verified':True,'aggregate_context_has_no_judge_identity':True,'identity_crosswalk_exact_base_binding_and_complete_mapping':True,'external_source_native_ids_only_no_name_merges':True,'sqlite_integrity_and_row_counts':True,'sealed_pipeline_matches_reviewed_current_code':True,'full_national_completeness_not_claimed':True},
        'colorado_independent_audit':{'path':colorado_path.relative_to(ROOT).as_posix(),'sha256':sha(colorado_path),'validated':True,'unresolved_findings':0,'component_files_bound_to_frozen_copies':colorado_copies,'source_auditor_checks':colorado['checks'],'preserved_publication_uncertainties':colorado['preserved_publication_uncertainties']},
        'trellis_added_sample_audit':{'path':trellis_audit_path.relative_to(ROOT).as_posix(),'sha256':sha(trellis_audit_path),'validated':True,'unresolved_material_findings':0,'component_files_bound_to_sealed_base':trellis_copies,'sealed_base_snapshot':sealed_base.relative_to(ROOT).as_posix(),'sealed_base_manifest_sha256':sha(sealed_base/'files.sha256.json'),'sealed_base_files_freshly_rehashed':len(sealed_base_manifest),'final_profile_count':len(final_trellis_profiles),'new_profile_urls':trellis_audit['new_profile_urls'],'sample_names':trellis_audit['sample_names']},
        'trellis_service_correction':{'path':service_path.relative_to(ROOT).as_posix(),'sha256':sha(service_path),'validated':True,'normalizer_sha256':service['normalizer_sha256'],'candidate_profiles':service['candidate_profiles'],'case_outcomes':service['case_outcomes'],'all_56_biographies_retained_in_final_component':True,'every_reviewed_service_tag_disposition_matches_final_component':True,'legacy_review_sha256':sha(legacy_review_path),'legacy_approval_binds_exact_review':True},
        'limits':['Integration verification of all emitted native claims and provenance; original field extraction relies on the separately bound source audits.','Colorado is the saved 116-profile 2024 ballot-evaluation package, not every eligible/evaluated judge.','FJC professional biography observations and source IDs include historical service and do not establish current office.','Canonical groups include unresolved singletons and repeated source representations; no certified distinct-current-judge total.','Official performance evaluations are not litigation outcome rates or causal judge quality scores.'],
        'source_mutations':0,'snapshot_mutations':0,'network_requests':0,'production_builder_runs':0}
    (OUT/'independent_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['validated','snapshot_path','manifest_sha256','snapshot_files_hash_verified','originals_freshly_rehashed','counts','observations_by_reported_system']},indent=2))


if __name__=='__main__':main()
