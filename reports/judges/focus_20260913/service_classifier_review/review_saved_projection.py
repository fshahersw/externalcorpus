"""Independently compare the bounded saved biography family, offline only."""
from pathlib import Path
from collections import Counter
import datetime
import hashlib
import importlib.util
import json
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    original_code = OUT / 'baseline_normalize.py'
    revised_code = ROOT / 'delivery/judge_intelligence_20260913/trellis_profiles/normalize.py'
    old = module('independent_prior_service_parser', original_code)
    new = module('independent_revised_service_parser', revised_code)
    revision_hash = sha(revised_code.read_bytes())
    saved_path = OUT / 'saved_regression_cases.json'
    saved = json.loads(saved_path.read_text(encoding='utf-8'))
    assert saved['all_original_and_fragment_hashes_verified'] is True
    cases, issues = [], []
    for case in saved['cases']:
        source = (ROOT / case['source_path']).resolve()
        source.relative_to(ROOT)
        raw = source.read_bytes()
        assert sha(raw) == case['source_sha256']
        data = json.loads(raw)
        html = data.get('data', data)['html']
        ev = case['evidence']
        fragment = html[ev['html_character_start']:ev['html_character_end']]
        assert sha(fragment.encode()) == ev['html_fragment_sha256']
        assert old.plain(fragment) == new.plain(fragment) == ev['literal_text'] == case['value']
        assert sha(case['value'].encode()) == ev['literal_text_sha256']
        before = old.normalize_capture(data, case['source_path'], raw)
        after = new.normalize_capture(data, case['source_path'], raw)
        before_profile, after_profile = before[0], after[0]
        permitted_profile_fields = {'parser_version', 'fact_count', 'professional_service_passages'}
        assert {k: v for k, v in before_profile.items() if k not in permitted_profile_fields} == {
            k: v for k, v in after_profile.items() if k not in permitted_profile_fields
        }, case['source_url']
        before_nonservice = [f for f in before[1] if f['field'] != 'service_or_role_passage']
        after_nonservice = [f for f in after[1] if f['field'] != 'service_or_role_passage']
        assert before_nonservice == after_nonservice, case['source_url']
        assert before[2:] == after[2:], case['source_url']
        assert len(after[1]) == after_profile['fact_count']
        previous = {f['fact_id']: f for f in before[1] if f['field'] == 'service_or_role_passage'}
        revised = {f['fact_id']: f for f in after[1] if f['field'] == 'service_or_role_passage'}
        assert all(previous[k] == v for k, v in revised.items()), case['source_url']
        assert case['fact_id'] in previous
        assert sha(source.read_bytes()) == case['source_sha256']
        cases.append({
            'source_url': case['source_url'], 'source_path': case['source_path'],
            'source_sha256': case['source_sha256'], 'capture_id': case['capture_id'],
            'reported_name': after_profile['reported_name'], 'fact_id': case['fact_id'],
            'literal_value': case['value'], 'evidence': ev,
            'before_service_tag': True, 'after_service_tag': case['fact_id'] in revised,
            'complete_biography_identical': before_profile['biography'] == after_profile['biography'],
            'all_nonservice_facts_identical': before_nonservice == after_nonservice,
            'all_nonfact_outputs_identical': before[2:] == after[2:],
            'removed_fact_ids_for_profile': sorted(set(previous) - set(revised)),
        })
    # Individually inspected saved cases: hobbies/relatives must not be promoted
    # through the negated phrase; unambiguous own service survives the same phrase.
    must_remove = {
        'douglas.p.anderson', 'christopher.d.chiles', 'anna.j.brown',
        'burford.a.cherry', 'charles.e.auslander.iii', 'christian.j.bell',
        'ellen.r.brostrom', 'david.m.jones', 'beverly.j.cannone',
        'andrew.m.lavin', 'cristine.d.silva', 'diane.s.blick',
    }
    must_retain = {'christopher.j.baumann', 'anthony.s.beltrami', 'abigail.e.bartlett'}
    by_slug = {c['source_url'].rstrip('/').rsplit('/', 1)[-1]: c for c in cases}
    for slug in must_remove:
        if by_slug[slug]['after_service_tag']:
            issues.append({'source_url': by_slug[slug]['source_url'], 'issue': 'Personal or third-party-only passage remains service-tagged'})
    for slug in must_retain:
        if not by_slug[slug]['after_service_tag']:
            issues.append({'source_url': by_slug[slug]['source_url'], 'issue': 'Explicit own military/mock-trial/justice-board role loses service tag'})
    assert sha(revised_code.read_bytes()) == revision_hash, 'Normalizer changed during review'
    result = {
        'reviewed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'validated': not issues, 'unresolved_material_findings': len(issues), 'issues': issues,
        'parser_version_before': old.VERSION, 'parser_version_after': new.VERSION,
        'normalizer_path': revised_code.relative_to(ROOT).as_posix(),
        'normalizer_sha256': revision_hash, 'baseline_normalizer_sha256': sha(original_code.read_bytes()),
        'saved_cases_path': saved_path.relative_to(ROOT).as_posix(),
        'saved_cases_sha256': sha(saved_path.read_bytes()),
        'candidate_profiles': len(cases),
        'case_outcomes': dict(Counter('retained_service_tag' if c['after_service_tag'] else 'removed_service_tag' for c in cases)),
        'source_and_fragment_hashes_verified': len(cases),
        'all_complete_biographies_and_nonservice_facts_identical': True,
        'all_other_parser_outputs_identical': True,
        'explicit_saved_semantic_checks': {'negative_cases': len(must_remove), 'positive_cases': len(must_retain)},
        'cases': cases,
        'scope_limits': [
            'Bounded review of saved negated-presiding paragraphs, not certification of every biography or role.',
            'Source passages remain literal publisher assertions; service tags do not establish current judicial assignments.',
            'No network, source edits, production normalization, index changes, or publication occurred in this reviewer.',
        ],
    }
    target = OUT / 'independent_projection_review.json'
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in {'cases', 'scope_limits'}}, indent=2))
    if issues:
        sys.exit(1)


if __name__ == '__main__':
    main()
