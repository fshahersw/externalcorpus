"""Bounded, entirely local second WA OCR pass; never edits first-pass outputs."""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'pipeline'))
import prepare_court_ocr as ocr

COLLECTION = ROOT / 'corpus/county_local_rules_washington_20260914'
FIRST = COLLECTION / 'ocr'
REPORT_BASE = ROOT / 'reports/counties/local_rules_washington_20260914/ocr'
GAPS = REPORT_BASE / 'remaining_gaps_20260914T0747.json'
WORKER = ROOT / 'sources/official_courts/ocr_worker.cjs'
NODE = 'C:/Users/firas/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return ocr.digest(path)


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def local(value):
    p = Path(value)
    p = (p if p.is_absolute() else ROOT / p).resolve()
    assert p.is_relative_to(ROOT), value
    return p


def frozen_inventory():
    return {rel(p): sha(p) for p in sorted(FIRST.rglob('*')) if p.is_file()}


def prepare(stamp):
    report = REPORT_BASE / 'passes' / stamp
    output = COLLECTION / 'ocr_passes' / stamp
    assert not report.exists() and not output.exists(), 'Use a new timestamp; passes are preserved.'
    report.mkdir(parents=True)
    baseline = frozen_inventory()
    ocr.atomic_json(report / 'first_pass_files_before.json', baseline)
    first = ocr.read_lines(FIRST / 'pdf_ocr_manifest.jsonl')
    assert len(first) == 10 and all(r['ocr_status'] == 'complete' for r in first)
    completed = {r['source_pdf_sha256'] for r in first}
    gaps = json.loads(GAPS.read_text(encoding='utf-8'))
    candidates = [r for r in gaps['items'] if not r['ocr_complete_in_frozen_pass']]
    assert len(candidates) == len({r['sha256'] for r in candidates}) == 26
    assert completed.isdisjoint(r['sha256'] for r in candidates)
    with closing(sqlite3.connect((COLLECTION / 'corpus.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        all_rows = [dict(r) for r in db.execute("SELECT id,url,status,raw_path,text_path,metadata_path,sha256,byte_count,last_fetch_id,extraction_status,last_http_status,raw_complete FROM resources WHERE status='downloaded' AND raw_complete=1")]
    by_url = {r['url']: r for r in all_rows}
    diagnosed = []
    source_hashes = {}
    for candidate in candidates:
        resource = by_url[candidate['url']]
        assert all(resource[k] == candidate[k] for k in ['id','url','sha256','raw_path','metadata_path','extraction_status'])
        raw = COLLECTION / resource['raw_path']
        meta_path = COLLECTION / resource['metadata_path']
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        assert sha(raw) == resource['sha256'] == meta['sha256']
        assert meta['requested_url'] == resource['url'] and meta['fetch_id'] == resource['last_fetch_id']
        assert meta['http_status'] == resource['last_http_status'] == 200 and meta['raw_complete']
        assert not meta.get('extraction_error')
        source_hashes[rel(raw)] = sha(raw)
        source_hashes[rel(meta_path)] = sha(meta_path)
        if resource.get('text_path'):
            text_path = COLLECTION / resource['text_path']
            assert sha(text_path) == meta['text_sha256']
            source_hashes[rel(text_path)] = sha(text_path)
        with ocr.fitz.open(raw) as pdf:
            assert not pdf.needs_pass
            pages = len(pdf)
        diagnosed.append({'resource': resource, 'pdf_pages': pages, 'selection': None})
    selected, total = [], 0
    for item in sorted(diagnosed, key=lambda r: (r['pdf_pages'], r['resource']['url'])):
        if total + item['pdf_pages'] <= 300:
            selected.append(item['resource'])
            total += item['pdf_pages']
            item['selection'] = 'selected_bounded_ocr_pass'
        else:
            item['selection'] = 'deferred_whole_document_page_cap'
    ocr.atomic_lines(report / 'source_diagnoses.jsonl', diagnosed)
    ocr.atomic_json(report / 'source_files_before.json', source_hashes)
    ocr.atomic_lines(report / 'selected_resource_snapshot.jsonl', selected)
    prepared = ocr.prepare(COLLECTION, output, ROOT / 'sources/official_courts/ocr/models', resource_snapshot=selected, snapshot_kind='hash_verified_WA_second_pass_snapshot')
    assert prepared['preparation_errors'] == 0 and prepared['documents_with_incomplete_screening'] == 0
    assert prepared['pdf_pages_in_documents'] == total <= 300 and prepared['pages'] <= 300
    assert frozen_inventory() == baseline
    plan = {'prepared_at_utc': now(), 'output': rel(output), 'report': rel(report), 'candidate_unique_pdfs': len(candidates), 'candidate_pdf_pages': sum(d['pdf_pages'] for d in diagnosed), 'selected_unique_pdfs': len(selected), 'selected_pdf_pages': total, 'queued_ocr_pages': prepared['pages'], 'deferred_unique_pdfs': len(candidates)-len(selected), 'deferred_pdf_pages': sum(d['pdf_pages'] for d in diagnosed)-total, 'max_pdf_pages': 300, 'run_seconds': 600, 'workers': 2, 'model_sha256': prepared['model_sha256'], 'pages_manifest_sha256': sha(output / 'pages.jsonl'), 'documents_manifest_sha256': sha(output / 'documents.jsonl'), 'input_snapshot_sha256': sha(report / 'selected_resource_snapshot.jsonl'), 'gap_inventory_sha256': sha(GAPS), 'worker_sha256': sha(WORKER), 'preparation_script_sha256': sha(ROOT / 'pipeline/prepare_court_ocr.py'), 'pass_script_sha256': sha(Path(__file__)), 'network_requests': 0, 'first_pass_unchanged': True, 'source_originals_modified': False, 'collector_database_modified': False, 'selection_rule': 'Shortest complete PDFs first, at most 300 source PDF pages; exclude all first-pass hashes.'}
    ocr.atomic_json(report / 'run_plan.json', plan)
    print(json.dumps(plan), flush=True)
    env = dict(os.environ, OFFICIAL_OCR_ROOT=str(output), OFFICIAL_OCR_RUN_SECONDS='600', OFFICIAL_OCR_PAGE_TIMEOUT_MS='45000', OFFICIAL_OCR_WORKERS='2')
    with (report / 'worker.stdout.jsonl').open('w', encoding='utf-8') as out, (report / 'worker.stderr.txt').open('w', encoding='utf-8') as err:
        result = subprocess.run([NODE, str(WORKER)], env=env, stdout=out, stderr=err, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert result.returncode == 0, f'Worker exit {result.returncode}'
    validate(stamp)


def validate(stamp):
    report = REPORT_BASE / 'passes' / stamp
    plan = json.loads((report / 'run_plan.json').read_text(encoding='utf-8'))
    output = local(plan['output'])
    assert output == COLLECTION / 'ocr_passes' / stamp and output != FIRST
    for file, key in [('pages.jsonl','pages_manifest_sha256'),('documents.jsonl','documents_manifest_sha256')]:
        assert sha(output / file) == plan[key]
    assert sha(output / 'models/eng.traineddata') == plan['model_sha256']
    assert sha(report / 'selected_resource_snapshot.jsonl') == plan['input_snapshot_sha256']
    assert sha(WORKER) == plan['worker_sha256']
    assert frozen_inventory() == json.loads((report / 'first_pass_files_before.json').read_text(encoding='utf-8'))
    for name, digest in json.loads((report / 'source_files_before.json').read_text(encoding='utf-8')).items():
        assert sha(local(name)) == digest
    docs = ocr.read_lines(output / 'documents.jsonl')
    pages = ocr.read_lines(output / 'pages.jsonl')
    results = ocr.read_lines(output / 'page_results.jsonl')
    manifests = ocr.read_lines(output / 'pdf_ocr_manifest.jsonl')
    first_hashes = {d['source_pdf_sha256'] for d in ocr.read_lines(FIRST / 'pdf_ocr_manifest.jsonl')}
    assert first_hashes.isdisjoint(d['source_pdf_sha256'] for d in docs)
    assert len(docs) == len(manifests) == plan['selected_unique_pdfs']
    assert len(pages) == plan['queued_ocr_pages']
    key = lambda r: (r['source_id'], r['source_pdf_sha256'], r['page_number'], r['image_sha256'])
    expected = {key(p): p for p in pages}
    assert len(expected) == len(pages)
    result_map = {key(r): r for r in results}
    assert set(result_map).issubset(expected)
    verified = []
    for k, page in expected.items():
        assert sha(local(page['image_path'])) == page['image_sha256']
        result = result_map.get(k)
        if not result or result['status'] != 'succeeded':
            continue
        assert result['language_model_sha256'] == plan['model_sha256']
        text = local(result['text_path'])
        tsv = local(result['tsv_path'])
        assert text.is_relative_to(output) and tsv.is_relative_to(output)
        assert sha(text) == result['text_sha256']
        text_content = text.read_text(encoding='utf-8')
        tsv.read_text(encoding='utf-8')
        verified.append({'source_id': page['source_id'], 'source_pdf_sha256': page['source_pdf_sha256'], 'page_number': page['page_number'], 'image_path': rel(page['image_path']), 'image_sha256': page['image_sha256'], 'text_path': rel(text), 'text_sha256': result['text_sha256'], 'tsv_path': rel(tsv), 'tsv_sha256': sha(tsv), 'confidence': result['confidence'], 'text_characters': len(text_content), 'empty_ocr_text': not text_content.strip(), 'status': 'hash_verified_ocr_derivative'})
    manifest_map = {d['source_id']: d for d in manifests}
    verified_docs = []
    for doc in docs:
        assert sha(local(doc['source_pdf_path'])) == doc['source_pdf_sha256']
        assert sha(local(doc['embedded_text_path'])) == doc['embedded_text_sha256']
        coverage = ocr.read_lines(local(doc['page_coverage_path']))
        assert len(coverage) == doc['pdf_pages'] and {p['page_number'] for p in coverage} == set(range(1, doc['pdf_pages'] + 1))
        m = manifest_map[doc['source_id']]
        doc_pages = sorted((r for r in verified if r['source_id'] == doc['source_id']), key=lambda r:r['page_number'])
        assert len(doc_pages) == m['ocr_pages_completed'] <= m['ocr_pages_required'] == doc['ocr_pages_needed']
        assert (m['ocr_status'] == 'complete') == (m['ocr_pages_completed'] == m['ocr_pages_required'])
        combined = local(m['ocr_text_path'])
        assert sha(combined) == m['ocr_text_sha256']
        expected_parts = [f"===== OCR PAGE {p['page_number']} =====\n{local(p['text_path']).read_text(encoding='utf-8')}" for p in doc_pages]
        assert combined.read_text(encoding='utf-8') == '\n\n'.join(expected_parts)
        aliases = []
        for resource in doc['source_resources']:
            mp = COLLECTION / resource['metadata_path']
            meta = json.loads(mp.read_text(encoding='utf-8'))
            assert meta['sha256'] == resource['sha256'] == doc['source_pdf_sha256'] and meta['fetch_id'] == resource['last_fetch_id'] and meta['requested_url'] == resource['url']
            aliases.append({'collection': rel(COLLECTION), 'resource_id': resource['id'], 'url': resource['url'], 'source_metadata_path': rel(mp), 'source_metadata_sha256': sha(mp)})
        verified_docs.append({'source_id': doc['source_id'], 'source_pdf_sha256': doc['source_pdf_sha256'], 'source_pdf_path': rel(doc['source_pdf_path']), 'source_resources': aliases, 'pdf_pages': doc['pdf_pages'], 'ocr_pages_required': m['ocr_pages_required'], 'ocr_pages_completed': m['ocr_pages_completed'], 'ocr_status': m['ocr_status'], 'ocr_text_path': rel(combined), 'ocr_text_sha256': m['ocr_text_sha256'], 'page_coverage_path': rel(doc['page_coverage_path']), 'page_coverage_sha256': sha(local(doc['page_coverage_path'])), 'min_page_confidence': min((p['confidence'] for p in doc_pages), default=None), 'text_correctness_certified': False, 'current_law_status_verified': False})
    ocr.atomic_lines(report / 'verified_pages.jsonl', verified)
    ocr.atomic_lines(report / 'verified_documents.jsonl', verified_docs)
    status = json.loads((output / 'status.json').read_text(encoding='utf-8'))
    receipt = {'validated': True, 'validated_at_utc': now(), 'selected_unique_pdfs': len(docs), 'selected_pdf_pages': sum(d['pdf_pages'] for d in docs), 'queued_ocr_pages': len(pages), 'verified_page_derivatives': len(verified), 'complete_documents': sum(d['ocr_status']=='complete' for d in verified_docs), 'partial_documents': sum(d['ocr_status']=='partial' for d in verified_docs), 'remaining_queued_pages': len(pages)-len(verified), 'deferred_unique_pdfs': plan['deferred_unique_pdfs'], 'deferred_pdf_pages': plan['deferred_pdf_pages'], 'empty_ocr_pages': sum(p['empty_ocr_text'] for p in verified), 'pages_below_70_confidence': sum(p['confidence']<70 for p in verified), 'minimum_page_confidence': min((p['confidence'] for p in verified), default=None), 'worker_elapsed_seconds': status['elapsed_run_seconds'], 'source_files_and_first_pass_unchanged': True, 'collector_database_modified': False, 'network_requests': 0, 'legal_wording_or_currency_certified': False, 'all_pages_visually_verified': False, 'manifest_path': rel(output / 'pdf_ocr_manifest.jsonl'), 'manifest_sha256': sha(output / 'pdf_ocr_manifest.jsonl'), 'files': {rel(p):sha(p) for p in [output / 'documents.jsonl', output / 'pages.jsonl', output / 'page_results.jsonl', output / 'pdf_ocr_manifest.jsonl', report / 'verified_pages.jsonl', report / 'verified_documents.jsonl']}}
    ocr.atomic_json(report / 'validation.json', receipt)
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare-and-run','validate'])
    parser.add_argument('--stamp', required=True)
    args = parser.parse_args()
    assert args.stamp.isalnum(), 'Timestamp must be an alphanumeric directory name.'
    (prepare if args.action == 'prepare-and-run' else validate)(args.stamp)
