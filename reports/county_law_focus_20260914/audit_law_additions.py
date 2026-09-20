"""Read-only independent audit of completed official-law additions after 03:40 UTC."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'official_law_additions_after_0340'
CUTOFF = '2026-09-14T03:40:00+00:00'
COLLECTIONS = ['corpus/official_law_resume_quick_20260914', 'corpus/official_law_resume_pass3_20260913']
DERIVATIVE_MANIFEST = 'corpus/official_law_resume_quick_20260914/offline_docx_pass2/manifest.jsonl'


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def sha_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def checked_path(relative, prefix=None):
    p = (ROOT / relative).resolve()
    assert p.is_relative_to(ROOT.resolve()), f'Escaping reference {relative}'
    if prefix:
        assert p.is_relative_to((ROOT / prefix).resolve()), f'Wrong collection reference {relative}'
    assert p.is_file(), f'Missing file {relative}'
    return p


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def save_jsonl(path, rows):
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def snapshot(collection):
    path = checked_path(collection + '/corpus.sqlite3')
    before = sha_file(path)
    source = sqlite3.connect('file:' + path.as_posix() + '?mode=ro', uri=True)
    memory = sqlite3.connect(':memory:')
    source.backup(memory)
    source.close()
    memory.row_factory = sqlite3.Row
    resources = [dict(r) for r in memory.execute('SELECT * FROM resources ORDER BY id')]
    fetches = {r['id']: dict(r) for r in memory.execute('SELECT * FROM fetches')}
    contexts = {r['id']: dict(r) for r in memory.execute('SELECT * FROM contexts')}
    associations = defaultdict(set)
    for r in memory.execute('SELECT resource_id,context_id FROM resource_contexts'):
        associations[r[0]].add(r[1])
    runs = [dict(r) for r in memory.execute('SELECT id,started_at,ended_at,stop_reason,processed FROM runs ORDER BY started_at')]
    integrity = memory.execute('PRAGMA quick_check').fetchone()[0]
    memory.close()
    assert integrity == 'ok'
    return {'collection': collection, 'source_database_path': path.relative_to(ROOT).as_posix(),
            'source_database_sha256_before': before, 'snapshot_at': now(), 'resources': resources,
            'fetches': fetches, 'contexts': contexts, 'associations': associations, 'runs': runs,
            'resources_canonical_sha256': digest(canonical(resources)), 'quick_check': integrity}


def audit_capture(snap, row):
    collection = snap['collection']
    fetch = snap['fetches'][row['last_fetch_id']]
    assert fetch['resource_id'] == row['id'] and fetch['id'] == row['last_fetch_id']
    for key in ['status', 'raw_path', 'text_path', 'metadata_path', 'sha256', 'byte_count', 'raw_complete', 'extraction_status', 'error']:
        assert row[key] == fetch[key], f'Resource/fetch mismatch: {collection}:{row["id"]}:{key}'
    assert row['last_http_status'] == fetch['http_status']
    raw_path = checked_path(collection + '/' + row['raw_path'], collection + '/raw')
    meta_path = checked_path(collection + '/' + row['metadata_path'], collection + '/metadata')
    raw_sha = sha_file(raw_path)
    assert raw_sha == row['sha256']
    assert raw_path.stat().st_size == row['byte_count']
    meta_raw = meta_path.read_bytes()
    meta = json.loads(meta_raw.decode('utf-8'))
    assert meta == json.loads(fetch['response_json']), 'Metadata file differs from saved fetch response'
    assert meta['fetch_id'] == fetch['id'] and meta['run_id'] == fetch['run_id']
    assert any(r['id'] == fetch['run_id'] for r in snap['runs'])
    assert meta['requested_url'] == row['url']
    assert meta['fetched_at'] == fetch['fetched_at']
    for key in ['status', 'raw_path', 'text_path', 'sha256', 'byte_count', 'raw_complete', 'extraction_status']:
        assert meta.get(key) == row.get(key), f'Metadata mismatch: {key}'
    assert meta['http_status'] == row['last_http_status'] and meta['queue_status'] == row['status']
    assert row['raw_complete'] == 1
    for cx in meta.get('contexts', []):
        assert cx['context_id'] in snap['associations'][row['id']]
        stored = snap['contexts'][cx['context_id']]
        assert cx['seed_url'] == stored['seed_url']
        assert cx['source_family'] == stored['source_family']
        assert cx['category'] == stored['category']
        assert cx['jurisdiction'] == json.loads(stored['jurisdiction_json'])
    text, text_sha, text_bytes = None, None, None
    if row['text_path']:
        text_path = checked_path(collection + '/' + row['text_path'], collection + '/text')
        text_raw = text_path.read_bytes()
        text = text_raw.decode('utf-8')
        text_sha, text_bytes = digest(text_raw), len(text_raw)
        assert text_sha == meta['text_sha256']
        assert len(text) == meta['text_char_count']
    elif meta.get('text_path') or meta.get('text_sha256'):
        raise AssertionError('Unexpected metadata-only text reference')
    flags = {k: v for k, v in meta.items() if any(word in k.lower() for word in ['truncat', 'page', 'ocr'])}
    raw_nonempty = raw_path.stat().st_size > 0
    text_nonempty = bool(text and text.strip())
    page_flag_consistent = meta.get('pages_extracted') == meta.get('page_count') if 'page_count' in meta else None
    issues = []
    if not raw_nonempty:
        issues.append('empty_response_body')
    if row['status'] == 'downloaded' and row['extraction_status'] == 'extracted' and not text_nonempty:
        issues.append('extracted_flag_without_nonempty_text')
    if page_flag_consistent is False:
        issues.append('collector_reports_partial_page_extraction')
    if text_nonempty and len(text.strip()) < 80:
        issues.append('short_text_review_candidate')
    return {'capture_id': collection + ':' + str(row['id']), 'collection': collection,
            'resource_id': row['id'], 'fetch_id': fetch['id'], 'run_id': fetch['run_id'],
            'source_url': row['url'], 'retrieved_at': fetch['fetched_at'], 'status': row['status'],
            'http_status': row['last_http_status'], 'extraction_status': row['extraction_status'],
            'raw_path': raw_path.relative_to(ROOT).as_posix(), 'raw_sha256': raw_sha,
            'raw_bytes': raw_path.stat().st_size, 'raw_complete': True, 'raw_nonempty': raw_nonempty,
            'metadata_path': meta_path.relative_to(ROOT).as_posix(), 'metadata_sha256': digest(meta_raw),
            'metadata_bytes': len(meta_raw), 'fetch_response_canonical_sha256': digest(canonical(meta)),
            'text_path': collection + '/' + row['text_path'] if row['text_path'] else None,
            'text_sha256': text_sha, 'text_bytes': text_bytes, 'text_characters': len(text) if text is not None else None,
            'text_nonempty': text_nonempty, 'detected_type': meta['detected_type'], 'title': meta.get('title'),
            'contexts': meta.get('contexts', []), 'collector_extraction_flags': flags,
            'collector_page_counts_equal': page_flag_consistent, 'quality_flags': issues,
            'integrity_validated': True, 'usable_legal_content_claim': row['status'] == 'downloaded' and text_nonempty,
            'text_semantics_or_all_page_coverage_independently_certified': False}


def audit_docx(captures):
    manifest_path = checked_path(DERIVATIVE_MANIFEST)
    raw = manifest_path.read_bytes()
    rows = [json.loads(line) for line in raw.decode('utf-8').splitlines() if line.strip()]
    parents = {r['capture_id']: r for r in captures if r['status'] == 'downloaded'}
    audited = []
    for line, d in enumerate(rows, 1):
        key = COLLECTIONS[0] + ':' + str(d['resource_id'])
        if d['parent_retrieved_at'] < CUTOFF:
            continue
        assert key in parents and d['status'] == 'extracted'
        p = parents[key]
        assert d['source_url'] == p['source_url']
        for left, right in [('parent_raw_path','raw_path'), ('parent_raw_sha256','raw_sha256'),
                            ('parent_metadata_path','metadata_path'), ('parent_metadata_sha256','metadata_sha256'),
                            ('parent_byte_count','raw_bytes'), ('parent_fetch_id','fetch_id'), ('parent_retrieved_at','retrieved_at')]:
            assert d[left] == p[right], f'DOCX parent mismatch: {left}'
        assert d['parent_extraction_status'] == p['extraction_status'] == 'unsupported_format'
        assert d['detected_format'] == 'docx'
        assert d['parent_sha256_verified'] and d['literal_text_conservation_verified'] and d['paragraph_coverage_verified']
        assert d['source_contexts'] == p['contexts']
        text_path = checked_path(d['text_path'], COLLECTIONS[0] + '/offline_docx_pass2/text')
        content = text_path.read_bytes()
        text = content.decode('utf-8')
        assert digest(content) == d['text_sha256']
        assert len(content) == d['text_bytes'] and len(text) == d['text_characters'] and bool(text.strip())
        assert d['network_requests'] == 0 and d['originals_modified'] is False
        assert d['extraction_method'] and d['extractor_version'] and d['limitations']
        inv = checked_path(d['package_inventory_path'], COLLECTIONS[0] + '/offline_docx_pass2/metadata')
        audited.append({'parent_capture_id': key, 'source_url': d['source_url'], 'parent_raw_path': d['parent_raw_path'],
                        'parent_raw_sha256': d['parent_raw_sha256'], 'parent_metadata_path': d['parent_metadata_path'],
                        'parent_metadata_sha256': d['parent_metadata_sha256'], 'manifest_path': DERIVATIVE_MANIFEST,
                        'manifest_sha256': digest(raw), 'manifest_line': line, 'manifest_record_sha256': digest(canonical(d)),
                        'text_path': d['text_path'], 'text_sha256': digest(content), 'text_bytes': len(content),
                        'text_characters': len(text), 'text_nonempty': True, 'extractor_version': d['extractor_version'],
                        'extraction_method': d['extraction_method'], 'package_inventory_path': d['package_inventory_path'],
                        'package_inventory_sha256': sha_file(inv), 'paragraphs_as_reported': d['text_paragraphs'],
                        'prior_literal_conservation_check': d['literal_text_conservation_verified'],
                        'prior_paragraph_coverage_check': d['paragraph_coverage_verified'],
                        'fresh_parent_metadata_text_hash_validation': True, 'limitations': d['limitations'],
                        'xml_reextracted_by_this_audit': False})
        p['verified_docx_derivative'] = {'manifest_path': DERIVATIVE_MANIFEST, 'manifest_line': line,
                                        'text_path': d['text_path'], 'text_sha256': d['text_sha256'],
                                        'text_nonempty': True}
        p['usable_legal_content_claim'] = True
    assert len(audited) == 111
    receipt_paths = [DERIVATIVE_MANIFEST,
                     COLLECTIONS[0] + '/offline_docx_pass2/validation_receipt.json',
                     COLLECTIONS[0] + '/offline_docx_pass2/per_file_validation.jsonl',
                     COLLECTIONS[0] + '/offline_docx_pass2/summary.json',
                     'reports/remaining_resume_20260913/docx_pass2_root_validation_20260914.json']
    prior_receipts = [{'path': rel, 'sha256': sha_file(checked_path(rel)), 'bytes': checked_path(rel).stat().st_size} for rel in receipt_paths]
    prior = json.loads(checked_path(receipt_paths[1]).read_text(encoding='utf-8'))
    assert prior['manifest_sha256'] == digest(raw)
    return audited, prior_receipts


def main():
    started = now()
    OUT.mkdir(parents=True, exist_ok=True)
    snapshots = [snapshot(c) for c in COLLECTIONS]
    captures, failed_integrity = [], []
    for snap in snapshots:
        for row in snap['resources']:
            f = snap['fetches'].get(row['last_fetch_id'])
            if not f or f['fetched_at'] < CUTOFF:
                continue
            try:
                captures.append(audit_capture(snap, row))
            except Exception as exc:
                failed_integrity.append({'collection': snap['collection'], 'resource_id': row['id'], 'source_url': row['url'],
                                         'exception_type': type(exc).__name__, 'error': str(exc)})
    derivatives, prior_receipts = audit_docx(captures)
    states = Counter()
    for c in captures:
        if c['status'] == 'downloaded':
            for state, category in {(x.get('jurisdiction', {}).get('state'), x.get('category')) for x in c['contexts']}:
                states[(state, category, c['detected_type'])] += 1
    gaps = []
    snapshot_receipts = []
    for snap in snapshots:
        selected = [c for c in captures if c['collection'] == snap['collection']]
        for row in snap['resources']:
            if row['status'] != 'downloaded':
                gaps.append({'collection': snap['collection'], 'resource_id': row['id'], 'source_url': row['url'],
                             'status': row['status'], 'attempts': row['attempts'], 'error': row['error'],
                             'last_http_status': row['last_http_status'], 'next_attempt_at': row['next_attempt_at'],
                             'updated_at': row['updated_at'], 'raw_path': row['raw_path'], 'metadata_path': row['metadata_path'],
                             'gap_class': 'scope_exclusion' if row['status'] == 'out_of_scope' else 'acquisition_gap',
                             'source_database': snap['source_database_path'], 'no_retry_or_policy_change_by_audit': True})
        snap_file = OUT / (Path(snap['collection']).name + '_resources_snapshot.jsonl')
        save_jsonl(snap_file, snap['resources'])
        after = sha_file(checked_path(snap['source_database_path']))
        stable = after == snap['source_database_sha256_before']
        if not stable:
            failed_integrity.append({'collection': snap['collection'], 'error': 'Source database changed during audit; snapshot is bounded but refresh needed'})
        snapshot_receipts.append({k: snap[k] for k in ['collection', 'source_database_path', 'source_database_sha256_before', 'snapshot_at', 'resources_canonical_sha256', 'quick_check']} | {
            'source_database_sha256_after': after, 'source_database_stable': stable,
            'snapshot_path': snap_file.relative_to(ROOT).as_posix(), 'snapshot_sha256': sha_file(snap_file),
            'resource_counts': dict(Counter(r['status'] for r in snap['resources'])),
            'post_cutoff_audited_counts': dict(Counter(c['status'] for c in selected)),
            'runs': snap['runs'],
            'historical_unclosed_run_rows': sum(r['ended_at'] is None for r in snap['runs']),
            'unclosed_run_note': 'Historical null-ended run rows are retained; they are not evidence of a live collector. The source owner reports both collectors stopped.'})
    extraction_gaps = [c for c in captures if c['status'] == 'downloaded' and (not c['usable_legal_content_claim'] or c['quality_flags'])]
    save_jsonl(OUT / 'captures_audited.jsonl', captures)
    save_jsonl(OUT / 'docx_derivatives_audited.jsonl', derivatives)
    save_jsonl(OUT / 'frontier_gaps.jsonl', gaps)
    save_jsonl(OUT / 'extraction_gaps.jsonl', extraction_gaps)
    save_jsonl(OUT / 'integrity_issues.jsonl', failed_integrity)
    summary = {'audit_started_at': started, 'audit_completed_at': now(), 'cutoff_utc': CUTOFF,
               'selection': 'Latest completed fetches with fetched_at >= cutoff in the two explicitly scoped read-only SQLite snapshots.',
               'validated': not failed_integrity, 'status': 'passed' if not failed_integrity else 'issues_found',
               'source_collections': COLLECTIONS, 'snapshots': snapshot_receipts,
               'counts': {'successful_captures_after_cutoff': sum(c['status'] == 'downloaded' for c in captures),
                          'failed_response_captures_after_cutoff': sum(c['status'] != 'downloaded' for c in captures),
                          'fresh_raw_metadata_receipts': len(captures),
                          'nonempty_collector_text_for_successes': sum(c['status'] == 'downloaded' and c['text_nonempty'] for c in captures),
                          'verified_nonempty_docx_derivatives': len(derivatives),
                          'successful_captures_with_text_direct_or_derivative': sum(c['status'] == 'downloaded' and c['usable_legal_content_claim'] for c in captures),
                          'empty_successful_response_bodies': sum(c['status'] == 'downloaded' and not c['raw_nonempty'] for c in captures),
                          'extraction_or_thin_text_review_gaps': len(extraction_gaps), 'integrity_issues': len(failed_integrity),
                          'remaining_frontier_states': dict(Counter(g['status'] for g in gaps)),
                          'collector_reported_pdf_pages': sum(c['collector_extraction_flags'].get('page_count', 0) for c in captures if c['status'] == 'downloaded'),
                          'successful_raw_bytes': sum(c['raw_bytes'] for c in captures if c['status'] == 'downloaded'),
                          'direct_successful_text_bytes': sum(c['text_bytes'] or 0 for c in captures if c['status'] == 'downloaded'),
                          'docx_derivative_text_bytes': sum(c['text_bytes'] for c in derivatives)},
               'state_category_format_counts': [{'state': k[0], 'category': k[1], 'format': k[2], 'captures': n} for k, n in sorted(states.items())],
               'prior_docx_validation_receipts_rehashed': prior_receipts,
               'network_requests': 0, 'collector_launches': 0, 'original_source_mutations': 0, 'ocr_or_xml_reextraction': False,
               'limitations': ['File integrity and nonempty saved text are verified; semantic correctness, complete page text, images, automatic numbering, diagram/table reconstruction and source legal completeness are not certified.',
                               'PDF pages_extracted/page_count equality is a saved collector flag check, not independent page-by-page OCR or completeness certification.',
                               'DOCX parent/text and saved receipt hashes are freshly verified; prior XML literal/paragraph coverage work is referenced, not rerun.',
                               'The one HTTP 404 response is retained as acquisition evidence and is never counted as a successful legal content capture.',
                               'An exhausted finite queue is not proof of nationwide or state-family completeness. County local acquisition is separate.']}
    save_json(OUT / 'summary.json', summary)
    summary['output_sha256'] = {p.name: sha_file(p) for p in sorted(OUT.glob('*.jsonl'))} | {'summary.json': sha_file(OUT / 'summary.json')}
    save_json(OUT / 'validation.json', summary)
    print(json.dumps({'validated': summary['validated'], 'counts': summary['counts'], 'state_category_format_counts': summary['state_category_format_counts'], 'output': OUT.relative_to(ROOT).as_posix()}, ensure_ascii=True))


if __name__ == '__main__':
    main()
