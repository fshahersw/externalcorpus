"""Exercise package/search invariants in a wholly synthetic local workspace."""
from contextlib import redirect_stdout
import datetime
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + '\n', encoding='utf-8')


def jsonl(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(v) + '\n' for v in values), encoding='utf-8')


def main():
    build_path = ROOT / 'scripts/build_judge_intelligence_package.py'
    search_path = ROOT / 'scripts/search_judge_intelligence.py'
    code_hashes = {str(p.relative_to(ROOT)): digest(p) for p in [build_path, search_path]}
    b = load('synthetic_package_builder', build_path)
    s = load('synthetic_package_search', search_path)
    fixture = OUT / ('package_review_fixture_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    fixture.mkdir()
    assert fixture.resolve().is_relative_to(OUT.resolve())
    base = fixture / 'delivery/judge_intelligence_20260913'
    audit = fixture / 'reports/judges/focus_20260913'
    official, trellis = base / 'official_profiles', base / 'trellis_profiles'
    state = fixture / 'synthetic_worker'
    for p in [official, trellis, audit, state]:
        p.mkdir(parents=True)
    original = fixture / 'synthetic_original.txt'
    original.write_text('Synthetic fixture original. Name: Bannon Synthetic. Court clerk: 555-000-1111.\n', encoding='utf-8')
    source_hash = digest(original)
    official_rows = []
    for i in range(363):
        ev = {'artifact_path': original.name, 'artifact_sha256': source_hash}
        if i == 0:
            ev = {'artifact_path': '', 'artifact_sha256': ''}
        official_rows.append({'profile_id': str(i), 'observed_name': 'Synthetic Texas ' + str(i), 'state': 'Texas', 'state_code': 'TX', 'courts': ['Synthetic Court'], 'counties': ['Synthetic County'], 'roles': ['Judge'], 'education_facts': [], 'appointment_facts': [], 'service_facts': [], 'biography_facts': [], 'professional_contacts': [], 'current_historical_status': 'unknown', 'source_url': 'https://synthetic.invalid/official', 'capture_times': [], 'facts': [{'value': 'Synthetic fact', 'evidence': [ev]}], 'detail_limitations': []})
    jsonl(official / 'profiles.jsonl', official_rows)
    jsonl(official / 'source_coverage.jsonl', [{'raw_path': original.name, 'raw_sha256': source_hash, 'text_path': None, 'text_sha256': None}])
    jsonl(official / 'state_coverage.jsonl', [{'state': 'Texas', 'state_code': 'TX'}, {'state': 'Arizona', 'state_code': 'AZ'}])
    write(official / 'validation.json', {'issues': 0, 'all_fact_values_reproduced_from_cited_evidence': True})
    write(official / 'summary.json', {'facts': 363})
    profile = {'capture_id': 'fixture', 'source_path': original.name, 'source_sha256': source_hash, 'reported_name': 'Bannon Synthetic', 'reported_state': 'Arizona', 'reported_court': 'AZ - Example Court', 'reported_county': 'Example County', 'reported_county_basis': 'historical judicial career row', 'current_appointment_label': 'Example Court, Department 1', 'education': [], 'appointment_passages': ['Appointed deputy county attorney in 2001.'], 'professional_service_passages': [], 'career_history': [], 'biography': 'Synthetic biography.', 'status': 'parsed_profile', 'source_url': 'https://trellis.law/judge/bannon.synthetic', 'fact_count': 1, 'dashboard_report_links': [], 'directly_reported_analytics': None, 'gaps': []}
    profile['career_history'] = [
        {'Role': 'Deputy County Attorney', 'Employer': 'Synthetic County', 'From': '2001', 'To': '2005'},
        {'Role': 'Judge', 'Employer': 'Example Court', 'From': '2005', 'To': ''},
        {'Role': 'Judge', 'Employer': 'Another Historical Court', 'From': '2005', 'To': '2008'},
        {'Employer': 'Incomplete publisher history row'},
    ]
    jsonl(trellis / 'profiles.jsonl', [profile])
    jsonl(trellis / 'input_manifest.jsonl', [{'path': original.name, 'sha256': source_hash}])
    sealed_trellis_hash = digest(trellis / 'profiles.jsonl')
    write(trellis / 'files.sha256.json', {'profiles.jsonl': {'sha256': sealed_trellis_hash}})
    write(trellis / 'validation.json', {'failure_count': 0, 'originals_unchanged': True, 'all_independent_statistics_null': True})
    write(trellis / 'summary.json', {'distinct_publisher_profile_urls': 1, 'fact_records': 1, 'directly_reported_numeric_analytics': 0, 'dashboard_report_link_records': 0})
    jsonl(trellis / 'facts.jsonl', [{'capture_id': 'fixture', 'fact_id': 'synthetic-contact-fact', 'field': 'public_office_contact', 'value': {'clerk phone': '555-000-1111'}, 'evidence': {'source_path': original.name, 'source_sha256': source_hash}}])
    jsonl(audit / 'trellis_directory_rows.jsonl', [])
    (audit / 'trellis_directory_rows.csv').write_text('name\n', encoding='utf-8')
    for name in ['judge_reports.jsonl', 'trellis_source_audit.jsonl']:
        jsonl(audit / name, [])
    for name in ['schema_audit.json', 'coverage.json', 'summary.json']:
        write(audit / name, {})
    write(audit / 'validation.json', {'issue_count': 0})
    semantic_path = audit / 'official_semantic_audit.json'
    write(semantic_path, {'synthetic_only': True})
    write(state / 'active_run.json', {'status': 'synthetic_fixture_only'})
    b.ROOT, b.BASE, b.AUDIT, b.STATE = fixture, base, audit, state

    def approve_current_components():
        write(audit / 'root_package_approval.json', {
            'approved': True,
            'official_profiles_sha256': digest(official / 'profiles.jsonl'),
            'semantic_audit_sha256': digest(semantic_path),
            'component_sha256': {b.rel(path): b.sha(path) for _, path in b.component_files()},
        })

    def build():
        sys.argv = ['build_judge_intelligence_package.py', '--semantic-audit', str(semantic_path)]
        try:
            with redirect_stdout(io.StringIO()):
                b.main()
            return {'accepted': True}
        except Exception as e:
            return {'accepted': False, 'error': type(e).__name__ + ': ' + str(e)}

    results = {'fixture_root': str(fixture.relative_to(ROOT)), 'reviewed_code_hashes': code_hashes, 'production_sources_read': False, 'network_requests': 0}
    old_argv = sys.argv
    try:
        approve_current_components()
        profile['reported_name'] = 'Changed After Validation Bannon'
        jsonl(trellis / 'profiles.jsonl', [profile])
        results['component_change_after_approval'] = build()
        results['component_change_published_latest'] = (base / 'latest.json').exists()
        profile['reported_name'] = 'Bannon Synthetic'
        jsonl(trellis / 'profiles.jsonl', [profile])
        approve_current_components()
        results['missing_artifact_reference'] = build()
        # Produce a valid-reference fixture for the independent search checks.
        official_rows[0]['facts'][0]['evidence'][0] = {'artifact_path': original.name, 'artifact_sha256': source_hash}
        jsonl(official / 'profiles.jsonl', official_rows)
        approve_current_components()
        results['valid_reference_build'] = build()
        assert results['valid_reference_build']['accepted'], results['valid_reference_build']
        latest = json.loads((base / 'latest.json').read_text(encoding='utf-8'))
        snapshot = fixture / latest['snapshot_path']
        published = [json.loads(x) for x in (snapshot / 'reports.jsonl').read_text(encoding='utf-8').splitlines()]
        tp = next(r for r in published if r['source_class'] == 'trellis_profile')
        results['published_contact_values'] = tp['professional_contacts']
        results['published_status'] = tp['status']
        results['published_parse_status'] = tp.get('parse_status')
        results['career_role_mapping'] = {
            'roles': tp['roles'],
            'current_appointment_label_as_reported': tp['current_appointment_label_as_reported'],
            'all_career_rows_retained': tp['career_history_as_reported'] == profile['career_history'],
            'historical_nonjudicial_limit_retained': any('historical and nonjudicial roles' in x for x in tp['limitations']),
        }
        assert tp['roles'] == ['Deputy County Attorney', 'Judge']
        assert tp['current_appointment_label_as_reported'] == 'Example Court, Department 1'
        assert results['career_role_mapping']['all_career_rows_retained']
        assert results['career_role_mapping']['historical_nonjudicial_limit_retained']
        readme = (snapshot / 'README.md').read_text(encoding='utf-8')
        results['readme_ocr_conditional_and_separate_from_profile_metrics'] = (
            'accepted offline OCR derivatives, when included' in readme
            and 'sample content is not attributed to the profiled judge' in readme
            and 'needs OCR' not in readme)
        assert results['readme_ocr_conditional_and_separate_from_profile_metrics']
        s.ROOT = fixture

        def search(arguments):
            sys.argv = ['search_judge_intelligence.py'] + arguments
            stream = io.StringIO()
            try:
                with redirect_stdout(stream):
                    s.main()
                return {'rows': [json.loads(x) for x in stream.getvalue().splitlines()]}
            except Exception as e:
                return {'error': type(e).__name__ + ': ' + str(e)}

        results['state_source_court_county_filter'] = search(['Bannon', '--state', 'az', '--source', 'trellis_profile', '--court', 'example', '--county', 'example'])
        results['parameterized_court_filter_injection_attempt'] = search(['--court', "' OR 1=1 --"])
        whitespace = search(['   '])
        results['whitespace_only_query'] = {'row_count': len(whitespace.get('rows', [])), 'error': whitespace.get('error')}
        database = snapshot / 'judge_search.sqlite3'
        db = sqlite3.connect(database)
        tp['name'] = 'Altered Sealed Snapshot'
        db.execute('update observations set report_json=? where record_id=?', (json.dumps(tp), tp['record_id']))
        db.commit(); db.close()
        results['search_after_snapshot_database_tamper'] = search(['--state', 'AZ', '--source', 'trellis_profile'])
    except Exception as e:
        results['fixture_error'] = type(e).__name__ + ': ' + str(e)
    finally:
        sys.argv = old_argv
    results['reviewed_scripts_unchanged_during_fixture'] = all(digest(ROOT / p) == h for p, h in code_hashes.items())
    write(OUT / 'package_code_review_fixture_results.json', results)
    print(json.dumps(results, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
