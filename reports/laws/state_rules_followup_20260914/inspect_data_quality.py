"""Offline quality-boundary checks; never publish or change collector state."""
from pathlib import Path
import copy, datetime, hashlib, importlib.util, json, re, sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
checks = []


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(name, passed):
    assert passed, name
    checks.append({'name': name, 'passed': True})


files = ['scripts/update_county_local_documents_progress_20260914.py',
         'scripts/build_county_local_package.py', 'reports/laws/reconcile.py',
         'scripts/build_focused_laws.py',
         'sources/official_laws/state_rules_followup_20260914/check_downloads.py']
syntax = []
for filename in files:
    b = (ROOT / filename).read_bytes()
    compile(b, filename, 'exec')
    syntax.append({'path': filename, 'sha256': sha(b), 'syntax_valid': True})

reporter = load('county_quality_reporter', files[0])
packager = load('county_quality_packager', files[1])
law = load('law_quality_reconcile', files[2])
county_path = ROOT / 'reports/counties/local_documents_20260914/resources.jsonl'
county_bytes = county_path.read_bytes()
county_rows = [json.loads(l) for l in county_bytes.splitlines() if l.strip()]
sample = next(r for r in county_rows if r['status'] == 'downloaded' and r['extraction_status'] == 'extracted')
text = sample['text_evidence']
collection = ROOT / sample['collection']
text_path = (ROOT / text['path']).relative_to(collection)
check('actual_saved_county_text_expected_digest_matches', reporter.artifact(text_path, text['expected_sha256'], collection, require_expected_hash=True)['hash_matches'])
for name, expected in [('missing', None), ('empty', ''), ('short', 'a' * 63), ('invalid_hex', 'g' * 64), ('wrong', '0' * 64)]:
    check('strict_text_digest_rejects_' + name, not reporter.artifact(text_path, expected, collection, require_expected_hash=True)['hash_matches'])
check('uppercase_valid_hex_accepted', reporter.artifact(text_path, text['expected_sha256'].upper(), collection, require_expected_hash=True)['hash_matches'])

exports = []
for original in county_rows:
    if original['status'] != 'downloaded':
        continue
    r = copy.deepcopy(original)
    proof = r['text_evidence']
    proof['expected_sha256_valid'] = isinstance(proof.get('expected_sha256'), str) and re.fullmatch('[0-9a-fA-F]{64}', proof['expected_sha256']) is not None
    exports.append(packager.capture_record(r))
check('all_downloaded_county_records_export_once', len(exports) == sum(r['status'] == 'downloaded' for r in county_rows) == len({r['resource_key'] for r in exports}))
check('county_artifact_hash_fields_retained', all(all(k in r for k in ('raw_sha256', 'text_sha256', 'metadata_sha256')) for r in exports))
check('reviewed_resource_kind_only_from_bound_review', all(r['reviewed_resource_kind'] == (r['semantic_review']['actual_resource_kind'] if r['semantic_review']['reviewed'] else None) for r in exports))
check('county_geographic_qualifications_retained', all(r['contexts'] and r['geoid_associations_status'] and all(isinstance(g, str) for g in r['geoid_associations']) for r in exports))
original_by_key = {r['resource_key']: r for r in county_rows}
check('semantic_review_and_categories_preserved', all(r['semantic_review'] == original_by_key[r['resource_key']]['semantic_review'] and r['discovery_categories'] == sorted({c['category'] for c in r['contexts'] if c.get('category')}) for r in exports))
for name, field in [('unbound_text', 'text'), ('not_captured', 'capture')]:
    r = copy.deepcopy(sample)
    r['text_evidence']['expected_sha256_valid'] = field != 'text'
    if field == 'capture': r['public_page_or_document_captured'] = False
    try:
        packager.capture_record(r)
    except RuntimeError:
        check('county_export_rejects_' + name, True)
    else:
        raise AssertionError(name)

annotations_path = ROOT / 'sources/official_laws/state_rules_followup_20260914/content_annotations.json'
annotations_bytes = annotations_path.read_bytes()
annotations = json.loads(annotations_bytes)['notices']
for a in annotations:
    raw = (ROOT / a['raw_path']).read_bytes()
    tb = (ROOT / a['text_path']).read_bytes()
    check(a['chapter'] + '_annotation_binds_actual_saved_raw_and_text', sha(raw) == a['raw_sha256'] and sha(tb) == a['text_sha256'])
    r = {'url': a['source_url'], 'labels': [a['observed_source_label']],
         'observations': [{'collection': law.FOLLOWUP_COLLECTION, 'source_contexts': [{'jurisdiction': 'North Carolina', 'category': 'statutes', 'resource_kind': 'full_statute_chapter_pdf'}]}],
         'captures': {'x': {'raw_sha256': a['raw_sha256'], 'raw_hash_verified': True}},
         'texts': {'x': {'raw_sha256': a['raw_sha256'], 'text_sha256': a['text_sha256'], 'text_path': a['text_path']}}}
    check(a['chapter'] + '_historical_notice_classified_without_active_body_claim', law.classify_followup_chapter(r)[0] == a['content_kind'])
    check(a['chapter'] + '_current_law_and_extent_uncertified', r['content_review']['current_edition_verified'] is False and r['content_review']['whole_body_complete'] is None)
    changed = copy.deepcopy(r)
    changed['texts']['x']['text_sha256'] = '0' * 64
    check(a['chapter'] + '_changed_text_cannot_inherit_review', law.classify_followup_chapter(changed)[0] == 'law_document_title_evidence_needs_review' and changed.get('content_review') is None)
    changed = copy.deepcopy(r)
    changed['texts']['x']['raw_sha256'] = changed['captures']['x']['raw_sha256'] = '0' * 64
    check(a['chapter'] + '_changed_original_cannot_inherit_review', law.classify_followup_chapter(changed)[0] == 'law_document_title_evidence_needs_review' and changed.get('content_review') is None)

fixture = OUT / 'historical_label_fixture.txt'
fixture.write_text('Chapter 17A\n\u00a7 17A-1.\n' + 'Synthetic body-shape test; not acquired legal data. ' * 8, encoding='utf8')
historical = next(a for a in annotations if a['chapter'] == '17A')
changed = copy.deepcopy(r)
changed.update(url=historical['source_url'], labels=[historical['observed_source_label']])
changed['texts']['x'].update(text_path=fixture.relative_to(ROOT).as_posix(), text_sha256=sha(fixture.read_bytes()))
check('unreviewed_recodified_label_cannot_be_promoted_by_long_body_heuristic', law.classify_followup_chapter(changed)[0] == 'law_document_title_evidence_needs_review')

seed_paths = [ROOT / 'sources/official_laws/state_rules_followup_20260914/seeds.jsonl', ROOT / 'sources/official_laws/state_rules_followup_20260914/continuation_20260914T065424Z/seeds.jsonl']
labels = [json.loads(l).get('edition', {}).get('source_label', '') for p in seed_paths for l in p.read_text(encoding='utf8').splitlines() if l.strip()]
suspect = [label for label in labels if any(token in label for token in ('\ufffd', '\u00e2\u20ac', '\u00c3\u00a2', '\u00ef\u00bf\u00bd'))]
check('source_label_utf8_has_no_reviewed_mojibake_markers', not suspect)
check('first_bound_seed_unchanged', sha(seed_paths[0].read_bytes()) == '855d7a1b1b466f4ebda6d55dd8e481357fcc0c2c2adf55d6dea7d5c3a18e686f')
check('continuation_seed_unchanged', sha(seed_paths[1].read_bytes()) == '40039903427f735c3d2ca3fe16ae154057293c41286bcce23ec5afdc9281d4ff')

result = {'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
          'syntax': syntax, 'checks': checks, 'passed_checks': len(checks), 'issues': [],
          'county_snapshot': {'path': county_path.relative_to(ROOT).as_posix(), 'sha256': sha(county_bytes), 'rows': len(county_rows), 'downloaded_records_exported_in_memory': len(exports), 'semantic_reviews_retained': sum(r['semantic_review']['reviewed'] for r in exports)},
          'annotations': {'path': annotations_path.relative_to(ROOT).as_posix(), 'sha256': sha(annotations_bytes), 'notices': len(annotations)},
          'source_labels_checked': len(labels), 'full_builders_or_reporter_main_run': False,
          'collector_configuration_or_queue_modified': False, 'original_artifacts_modified': False}
(OUT / 'data_quality_inspection_receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
print(json.dumps(result, indent=2))
