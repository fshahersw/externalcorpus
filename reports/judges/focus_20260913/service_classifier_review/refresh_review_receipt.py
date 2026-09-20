"""Bind the independently checked service correction to the existing review."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    review_path = OUT.parent / 'package_code_review.json'
    prior_path = OUT / 'prior_package_code_review.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    checked_path = OUT / 'independent_projection_review.json'
    checked = json.loads(checked_path.read_text(encoding='utf-8'))
    assert checked['validated'] is True and checked['unresolved_material_findings'] == 0
    expected = {
        'scripts/build_judge_intelligence_package.py': '09d001b0362fc2e3a024b46f86dc4aeb99b5b78dba1255b4089038c400f1219b',
        'scripts/search_judge_intelligence.py': 'ccc80ee6ff8bf92639e215337b9a7b9fffbeb7994c41933f6dfc92d876dd6610',
        'delivery/judge_intelligence_20260913/trellis_profiles/normalize.py': '4174bf6164719d4daddfb9f8683e92d09371a504d22263b43066c7a78d9e169e',
        'delivery/judge_intelligence_20260913/trellis_profiles/test_normalize.py': 'b3a2e1b91997c132406873bb995d64852ef3b27d1e7835a16d5e38b398c2ee41',
        'reports/judges/focus_20260913/review_package_fixtures.py': '1833e1af39787bc801aa189cf446abab03608df9f32806dace42f9bb50c4061e',
    }
    for name, value in expected.items():
        assert digest(ROOT / name) == value, name
    assert checked['normalizer_sha256'] == expected[checked['normalizer_path']]
    result = dict(prior)
    result['reviewed_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['reviewed_files_sha256'] = expected
    result['review_history'] = [{
        'path': prior_path.relative_to(ROOT).as_posix(),
        'sha256': digest(prior_path),
        'reviewed_at_utc': prior['reviewed_at_utc'],
        'retained_findings': ['R' + str(i) for i in range(1, 9)],
    }]
    result['scope']['additional_authorized_fix'] += ' The v1.0.3 service-passage correction was separately reviewed against 56 saved source originals and three observed negated-presiding wording variants.'
    result['resolved_findings'].append({
        'id': 'R9', 'priority': 2,
        'title': 'Do not promote a negated presiding transition or relatives\' roles to judge service',
        'file': 'delivery/judge_intelligence_20260913/trellis_profiles/normalize.py',
        'check': 'Only the three observed negated-presiding transitions lose their presiding signal. Explicit relative-subject sentences are masked for matching within that family; independent own military, mock-trial, and justice-board role evidence survives. Original text is never altered.',
        'evidence_path': checked_path.relative_to(ROOT).as_posix(),
        'evidence_sha256': digest(checked_path),
        'counts': {'saved_profile_candidates': 56, 'removed_service_tags': 51, 'retained_mixed_service_tags': 5},
        'all_candidate_original_and_fragment_hashes_verified': True,
        'all_complete_biographies_and_nonservice_facts_identical': True,
        'all_other_parser_outputs_identical': True,
        'prior_intermediate_fix_not_approved': 'The first 36-case wording-only change missed 20 saved variants and lost a mixed military-service tag; the reviewed v1.0.3 resolves those concrete regressions.',
    })
    result['remaining_material_findings'] = []
    fixture_path = OUT.parent / 'package_code_review_fixture_results.json'
    result['validation']['package_fixture_sha256'] = digest(fixture_path)
    result['validation']['service_projection_evidence'] = checked_path.relative_to(ROOT).as_posix()
    result['validation']['service_projection_evidence_sha256'] = digest(checked_path)
    result['validation']['service_reviewer_script'] = {
        'path': (OUT / 'review_saved_projection.py').relative_to(ROOT).as_posix(),
        'sha256': digest(OUT / 'review_saved_projection.py'),
    }
    result['validation']['parser_fixture_results'][0]['checks'].extend([
        'Three observed negated-presiding transitions, including suffix placement, do not assert service',
        'Explicit spouse/father service is not attributed to the judge within affected passages',
        'Army Reserve veteran, mock-trial coaching and justice-board roles retained in mixed passages',
        'Actual presiding, assignments, judicial committees and Immigration Justice Project roles retained',
    ])
    result['validation']['fixtures_rerun_at_utc'] = result['reviewed_at_utc']
    result['publication_precondition'] = 'Root binds the final stable v1.0.3 normalized component files to fresh source/semantic QA, then rebuilds the legacy base and downstream identity/enrichment snapshots. This review does not itself normalize production data or publish.'
    result['assessment_limits'].append('Service review is bounded to the 56 saved negated-presiding candidate passages plus positive/negative parser fixtures. Remaining service_or_role passages can contain literal civic/volunteer roles; they are not structured proof of current judicial assignments. Relatives and combined clauses outside the reviewed wording family are not comprehensively adjudicated.')
    review_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': review_path.relative_to(ROOT).as_posix(), 'sha256': digest(review_path), 'normalizer_sha256': expected[checked['normalizer_path']], 'remaining_material_findings': 0, 'previous_review_path': prior_path.relative_to(ROOT).as_posix(), 'previous_review_sha256': digest(prior_path)}, indent=2))


if __name__ == '__main__':
    main()
