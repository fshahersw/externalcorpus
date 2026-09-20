"""In-memory field preservation against the independently verified WA mapping."""
from collections import defaultdict
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[3]
COLLECTION = 'corpus/county_local_rules_washington_20260914'
MAPPING = ROOT / 'reports/counties/local_rules_washington_20260914/court_labels/20260914T075835637370Z/court_labels.jsonl'
EXPECTED_MAPPING_SHA256 = '2da5505fe241fbe1450b048c1fd247242f969fdd916f57bc8a65cd1ca0d18c7c'


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    reporter_path = 'scripts/update_county_local_documents_progress_20260914.py'
    package_path = 'scripts/build_county_local_package.py'
    reporter = load('court_label_reporter_fixture', reporter_path)
    package = load('court_label_package_fixture', package_path)
    mapping_bytes = MAPPING.read_bytes()
    assert hashlib.sha256(mapping_bytes).hexdigest() == EXPECTED_MAPPING_SHA256
    mapping = {(row['collection'], row['source_url'], row['raw_sha256']): row for row in (json.loads(line) for line in mapping_bytes.decode('utf-8').splitlines())}
    with closing(sqlite3.connect((ROOT / COLLECTION / 'corpus.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
        contexts = {}
        for source in db.execute('SELECT * FROM contexts'):
            row = dict(source)
            row['seed'] = json.loads(row['seed_json'])
            row['jurisdiction'] = json.loads(row['jurisdiction_json'])
            row['collection'] = COLLECTION
            contexts[row['id']] = row
        associations = defaultdict(list)
        for row in db.execute('SELECT * FROM resource_contexts'):
            associations[row['resource_id']].append({'collection': COLLECTION, **dict(row)})
    saved_bytes = (ROOT / 'reports/counties/local_documents_20260914/resources.jsonl').read_bytes()
    resources = [row for row in (json.loads(line) for line in saved_bytes.decode('utf-8').splitlines()) if row['collection'] == COLLECTION]
    source_before = json.dumps(contexts, sort_keys=True)
    assigned = unassigned = checked = label_count = 0
    for saved in resources:
        expected = mapping[(saved['collection'], saved['url'], saved['raw_evidence']['sha256'])]
        output = deepcopy(saved)
        output['contexts'] = [reporter.context_record(contexts[link['context_id']], link) for link in associations[saved['resource_id']]]
        previous = {row['context_id']: row for row in saved['contexts']}
        expected_labels = {row['context_id']: row for row in expected['labels']}
        for context in output['contexts']:
            old = previous[context['context_id']]
            assert all(context[key] == value for key, value in old.items())
            label = expected_labels[context['context_id']]
            assert context['court_label'] == label['court_label']
            assert context['provenance'] == label['provenance']
            assert context['source_seed_evidence']['sha256'] == label['seed_json_sha256']
            assert context['source_seed_evidence']['record_locator'] == COLLECTION + '/corpus.sqlite3#contexts/' + context['context_id']
            assert context['jurisdiction'] == label['jurisdiction']
            assert context['court_fips_association_verified'] is False
        capture = package.capture_record(output)
        assert capture['court_labels'] == expected['court_labels']
        assert capture['geoid_associations'] == expected['geoid_associations']
        assert capture['contexts'] == output['contexts']
        if capture['geoid_associations']:
            assigned += 1
        else:
            unassigned += 1
            assert all(row['jurisdiction'].get('geoid') is None for row in capture['contexts'])
        checked += 1
        label_count += len(capture['court_labels'])
    assert (checked, assigned, unassigned, label_count) == (129, 53, 76, 129)
    assert json.dumps(contexts, sort_keys=True) == source_before

    # The same evidence preservation applies outside WA; names never assign a county.
    synthetic = deepcopy(next(iter(contexts.values())))
    synthetic['collection'] = 'corpus/county_local_documents_20260914'
    synthetic['seed']['court_label'] = 'Observed Municipal Court'
    synthetic['seed']['jurisdiction']['geoid'] = None
    synthetic['jurisdiction']['geoid'] = None
    link = {'collection': synthetic['collection'], 'depth': 0, 'discovered_from': 'https://fixture.invalid/index'}
    result = reporter.context_record(synthetic, link)
    assert result['court_label'] == 'Observed Municipal Court' and result['jurisdiction']['geoid'] is None
    assert result['provenance'] == synthetic['seed']['provenance']
    assert result['source_seed_evidence']['record_locator'].startswith(synthetic['collection'] + '/')
    del synthetic['seed']['court_label']
    result = reporter.context_record(synthetic, link)
    assert 'court_label' not in result and 'source_seed_evidence' not in result
    no_label_resource = deepcopy(resources[0]); no_label_resource['contexts'] = [result]
    assert package.capture_record(no_label_resource)['court_labels'] == []
    assert package.capture_record(no_label_resource)['geoid_associations'] == []

    receipt = {'verified_at_utc': datetime.now(timezone.utc).isoformat(), 'valid': True, 'actual_records_checked': checked, 'observed_labels_preserved': label_count, 'county_assigned_preserved': assigned, 'county_unassigned_preserved': unassigned, 'all_source_provenance_preserved_exactly': True, 'all_original_context_fields_preserved': True, 'original_seed_inputs_unchanged': True, 'other_collection_label_check': True, 'missing_label_and_null_geoid_check': True, 'mapping_sha256': EXPECTED_MAPPING_SHA256, 'reporter_input_snapshot_sha256': hashlib.sha256(saved_bytes).hexdigest(), 'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (reporter_path, package_path)}, 'reporter_main_or_builders_run': False, 'delivery_or_collection_mutations': 0, 'network_requests': 0}
    output_path = Path(__file__).with_name('court_label_export_verification.json')
    output_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
