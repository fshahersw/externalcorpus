"""Offline regression fixtures for conservative identity joins."""
from pathlib import Path
import importlib.util
import json
import hashlib
import datetime
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('identity', ROOT / 'scripts/judge_identity_enrichment.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def obs(id, kind, name='Jane A. Doe', court='7th District Court', state='TX', url=None, family=None):
    return {'source_observation_id': id, 'source_class': kind,
            'source_url': url or 'https://example.invalid/' + id,
            'publisher_family_url': family,
            'reported_name': name, 'normalized_full_name': m.normalize_name(name),
            'full_name_eligible': m.full_name_eligible(name),
            'state_code': state, 'state': 'Texas' if state == 'TX' else 'Arizona',
            'explicit_state_consistent': bool(state),
            'reported_courts': [court], 'reported_counties': [],
            'court_keys': [m.normalize_court(court, state, 'Texas' if state == 'TX' else 'Arizona')],
            'specific_court_with_literal_evidence': m.specific_court(m.normalize_court(court, state, 'Texas')),
            'source_record': {'synthetic': True}, 'source_status_as_reported': None}


tests = []
def check(name, observations, groups, links):
    judges, mapping, decisions = m.match(observations)
    assert len(judges) == groups, (name, judges)
    assert sum(d['decision'] == 'confirmed_rule_link' for d in decisions) == links, (name, decisions)
    assert not m.validate(observations, judges, mapping, decisions, [])
    assert {x['source_observation_id'] for x in mapping} == {x['source_observation_id'] for x in observations}
    tests.append(name)
    return judges, mapping, decisions


family = 'https://trellis.law/judge/jane.a.doe'
a = obs('official:a', 'official_observation')
b = obs('trellis-profile:b', 'trellis_profile', court='TX - 7th District Court of Texas', family=family)
c = obs('trellis-directory:c', 'trellis_directory', family=family)
check('exact_full_name_state_specific_court_all_pair_proofs', [a,b,c], 1, 3)
check('same_publisher_link_is_distinct_from_independent_corroboration', [b,c], 1, 1)
check('initial_first_name_not_joined', [obs('a','official_observation',name='J. A. Doe'),obs('b','trellis_profile',name='J. A. Doe',family=family)], 2, 0)
check('missing_middle_initial_not_fuzzy_joined', [a,obs('b','trellis_profile',name='Jane Doe',family=family)], 2, 0)
check('state_conflict_not_joined', [a,obs('b','trellis_profile',state='AZ',family=family)], 2, 0)
check('numbered_court_conflict_not_joined', [a,obs('b','trellis_profile',court='8th District Court',family=family)], 2, 0)
check('generic_court_not_joined', [obs('a','official_observation',court='District Court'),obs('b','trellis_profile',court='District Court',family=family)], 2, 0)
check('competing_profile_urls_prevent_guess', [a,b,obs('trellis-directory:d','trellis_directory',family='https://trellis.law/judge/jane.doe2')], 3, 0)
check('duplicate_official_entries_not_assumed_one_person', [a,obs('official:a2','official_observation',url=a['source_url']),b], 3, 0)
check('incompatible_history_context_blocks_transitive_join', [a,b,obs('official:d','official_observation',court='8th District Court')], 3, 0)
missing = dict(c, specific_court_with_literal_evidence=False)
check('unsupported_competing_court_field_blocks_join', [a,b,missing], 3, 0)
status_a = dict(a, source_status_as_reported='Active')
status_b = dict(b, source_status_as_reported='Retired')
j, _, _ = check('status_conflict_retained_without_current_claim', [status_a,status_b], 1, 1)
assert j[0]['current_judicial_status'] is None and j[0]['conflicting_nonempty_status_claims']
assert m.normalize_name('Hon. Jane A. Doe, Jr.') == 'jane a doe jr'
assert m.normalize_name('Jose Doe') != m.normalize_name('Jos\u00e9 Doe')
assert m.normalize_name('Jane A. Doe') != m.normalize_name('Jane B. Doe')
assert m.normalize_name('Jane Doe Jr.') != m.normalize_name('Jane Doe')
tests.append('honorific_punctuation_only_no_accent_initial_suffix_collapse')
result={'validated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method_version':m.VERSION,'script_sha256':hashlib.sha256((ROOT/'scripts/judge_identity_enrichment.py').read_bytes()).hexdigest(),'passed':len(tests),'tests':tests,'failures':0,'network_requests':0}
(Path(__file__).parent/'identity_parser_fixture_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
