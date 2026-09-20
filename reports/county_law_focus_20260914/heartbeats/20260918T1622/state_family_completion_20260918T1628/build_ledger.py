"""Build this isolated finite-family ledger from saved evidence only."""
from pathlib import Path
from collections import Counter
from urllib.parse import urlsplit
import csv, datetime, hashlib, json, sqlite3

OUT = Path(__file__).resolve().parent
ROOT = next(p for p in OUT.parents if (p / 'pipeline/corpus_crawler.py').is_file())
COLLECTION = ROOT / 'corpus/official_law_state_rules_followup_20260914'
sha = lambda b: hashlib.sha256(b).hexdigest()
packed = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf8')
relative = lambda p: p.resolve().relative_to(ROOT).as_posix()
FAMILIES = {
    ('North Carolina', 'full_statute_chapter_pdf'): ('nc_chapter_pdfs', 342),
    ('Nebraska', 'printer_friendly_rule_chapter_html'): ('ne_rule_exports', 6),
    ('Georgia', 'statewide_uniform_court_rules_pdf'): ('ga_rule_pdfs', 7),
}
SEED_PATHS = [ROOT / 'sources/official_laws/state_rules_followup_20260914/seeds.jsonl',
              ROOT / 'sources/official_laws/state_rules_followup_20260914/continuation_20260914T065424Z/seeds.jsonl']


def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def main():
    inputs = []
    seeds, seed_refs = {}, {}
    for path in SEED_PATHS:
        b = path.read_bytes()
        inputs.append({'path': relative(path), 'sha256': sha(b)})
        for line, raw in enumerate(b.splitlines(), 1):
            if not raw.strip(): continue
            seed = json.loads(raw)
            assert seed['url'] not in seeds
            seeds[seed['url']] = seed
            seed_refs[seed['url']] = {'seed_packet': relative(path), 'seed_line': line, 'seed_packet_sha256': sha(b), 'seed_object_sha256': sha(packed(seed))}
    assert len(seeds) == 355
    checker_path = ROOT / 'sources/official_laws/state_rules_followup_20260914/check_downloads.py'
    annotation_path = ROOT / 'sources/official_laws/state_rules_followup_20260914/content_annotations.json'
    for path in [checker_path, annotation_path, OUT / 'checks/resources.jsonl', OUT / 'checks/summary.json', COLLECTION / 'config.json']:
        inputs.append({'path': relative(path), 'sha256': sha(path.read_bytes())})
    checks = {r['url']: r for l in (OUT / 'checks/resources.jsonl').read_bytes().splitlines() if l.strip() for r in [json.loads(l)]}
    check_summary = json.loads((OUT / 'checks/summary.json').read_bytes())
    assert set(checks) == set(seeds) and check_summary['issue_count'] == 0
    with sqlite3.connect((COLLECTION / 'corpus.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        snapshot = [dict(r) for r in db.execute('SELECT * FROM resources ORDER BY id')]
        context_pairs = [(r['url'], json.loads(r['seed_json'])) for r in db.execute('SELECT r.url,c.seed_json FROM resources r JOIN resource_contexts rc ON rc.resource_id=r.id JOIN contexts c ON c.id=rc.context_id')]
        runs = [dict(r) for r in db.execute('SELECT id,started_at,ended_at,stop_reason,processed FROM runs ORDER BY rowid')]
    resources = {r['url']: r for r in snapshot}
    assert set(resources) == set(seeds)
    contexts = {}
    for url, seed in context_pairs: contexts.setdefault(url, []).append(seed)
    ledger = []
    for url, seed in seeds.items():
        r, check = resources[url], checks[url]
        assert seed in contexts[url] and r['status'] == check['queue_status']
        family, _ = FAMILIES[(seed['jurisdiction']['state'], seed['resource_kind'])]
        historical = check.get('content_review')
        downloaded = r['status'] == 'downloaded'
        native = False
        if downloaded:
            assert not check['issues'] and check['raw_sha256'] == r['sha256'] and check['fetch_id'] == r['last_fetch_id']
            meta_path = COLLECTION / r['metadata_path']
            metadata = json.loads(meta_path.read_bytes())
            assert sha(meta_path.read_bytes()) == check['metadata_sha256']
            native = bool(check.get('text_characters', 0) and metadata.get('text_sha256') == check['text_sha256'] and metadata['extraction_status'] == 'extracted' and metadata['detected_type'] in ('pdf', 'html') and Path(r['text_path']).parts[0] == 'text')
            assert native
        if downloaded and historical: bucket = 'downloaded_native_historical_notice'
        elif downloaded and native: bucket = 'downloaded_native_body_indicators'
        elif r['status'] in ('pending', 'fetching', 'retry_wait'): bucket = 'pending'
        else: bucket = 'access_barrier_or_exclusion'
        ledger.append({
            'source_url': url, 'family_id': family, 'state': seed['jurisdiction']['state'],
            'source_resource_kind': seed['resource_kind'], 'source_category': seed['category'],
            'observed_source_label': seed.get('edition', {}).get('source_label'),
            'observed_from_url': seed['discovered_from'], **seed_refs[url],
            'resource_id': r['id'], 'queue_status': r['status'], 'attempts': r['attempts'],
            'http_status': r['last_http_status'], 'fetch_id': r['last_fetch_id'],
            'completion_bucket': bucket, 'downloaded': downloaded, 'usable_native_text': native,
            'historical_notice_kind': historical['content_kind'] if historical else None,
            'historical_annotation_sha256': historical.get('annotation_file_sha256') if historical else None,
            'barrier_status': r['status'] if bucket == 'access_barrier_or_exclusion' else None,
            'barrier_detail': r['error'] if bucket == 'access_barrier_or_exclusion' else None,
            'raw_path': check.get('raw_path'), 'raw_sha256': check.get('raw_sha256'),
            'raw_bytes': check.get('raw_bytes', 0), 'raw_complete': check.get('raw_complete', False),
            'text_path': check.get('text_path'), 'text_sha256': check.get('text_sha256'),
            'text_characters': check.get('text_characters', 0),
            'metadata_path': check.get('metadata_path'), 'metadata_sha256': check.get('metadata_sha256'),
            'extraction_status': r['extraction_status'], 'pdf_pages': check.get('pdf_page_count'),
            'body_indicators': check.get('body_indicators'), 'validation_issues': check['issues'],
            'current_edition_verified': False, 'substantive_legal_correctness_verified': False,
            'full_state_corpus_completeness': 'not_established',
        })
    ledger.sort(key=lambda r: (r['family_id'], r['source_url']))
    assert len(ledger) == len({r['source_url'] for r in ledger}) == 355
    families = []
    for (state, kind), (family, denominator) in FAMILIES.items():
        rows = [r for r in ledger if r['family_id'] == family]
        assert len(rows) == denominator
        downloaded = sum(r['downloaded'] for r in rows)
        families.append({'family_id': family, 'state': state, 'source_resource_kind': kind,
            'reviewed_url_denominator': denominator, 'downloaded_originals': downloaded,
            'usable_native_texts_including_historical': sum(r['usable_native_text'] for r in rows),
            'native_body_indicator_records': sum(r['completion_bucket'] == 'downloaded_native_body_indicators' for r in rows),
            'historical_notices': sum(r['historical_notice_kind'] is not None for r in rows),
            'historical_kind_counts': dict(Counter(r['historical_notice_kind'] for r in rows if r['historical_notice_kind'])),
            'pending': sum(r['completion_bucket'] == 'pending' for r in rows),
            'barriers_or_exclusions': sum(r['completion_bucket'] == 'access_barrier_or_exclusion' for r in rows),
            'queue_status_counts': dict(Counter(r['queue_status'] for r in rows)),
            'finite_family_download_percent': round(100 * downloaded / denominator, 2),
            'raw_bytes': sum(r['raw_bytes'] for r in rows), 'text_characters': sum(r['text_characters'] for r in rows),
            'pdf_pages': sum(r['pdf_pages'] or 0 for r in rows),
            'current_edition_verified': False, 'complete_laws_of_state': False})
    (OUT / 'url_family_ledger.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in ledger), encoding='utf8')
    csv_fields = ['family_id','state','source_url','completion_bucket','queue_status','usable_native_text','historical_notice_kind','barrier_status','raw_sha256','text_sha256','metadata_sha256','raw_bytes','text_characters','pdf_pages','current_edition_verified','seed_packet','seed_line','seed_packet_sha256']
    with (OUT / 'url_family_ledger.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=csv_fields); w.writeheader()
        for row in ledger: w.writerow({k: row.get(k) for k in csv_fields})
    summary = {'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'scope': 'Exactly the already-reviewed 355 statewide source-family URLs; no expansion.',
        'source_collection': relative(COLLECTION), 'reviewed_urls': 355, 'families': families,
        'total_downloaded': sum(r['downloaded'] for r in ledger), 'total_native_texts': sum(r['usable_native_text'] for r in ledger),
        'total_historical_notices': sum(r['historical_notice_kind'] is not None for r in ledger),
        'total_pending': sum(r['completion_bucket'] == 'pending' for r in ledger),
        'total_barriers_or_exclusions': sum(r['completion_bucket'] == 'access_barrier_or_exclusion' for r in ledger),
        'database_resource_snapshot_sha256': sha(packed(snapshot)), 'database_snapshot_rows': len(snapshot),
        'queue_statuses_match_checked_snapshot': True, 'complete_seed_payloads_match_database_contexts': True,
        'resource_checker_at_utc': check_summary['checked_at_utc'], 'runs': runs, 'inputs': inputs,
        'notes': ['Denominators measure these reviewed source URLs, not all laws, local rules or filings in a state.',
                  'NC 342 is the reviewed chapter-PDF family; previously excluded publisher-labeled reserved/repealed chapter URLs are not added back into this denominator.',
                  'Native text means the collector original PDF/HTML extraction, separately hash verified and nonempty; no OCR derivative is counted here.',
                  'Historical notices are a subset of downloaded usable native text, not additional downloads. Body indicators establish recognizable text, not current legal effect.',
                  'Nebraska exports can include prior versions; chapter 6 has an observed prior-version heading.',
                  'Access barriers are unresolved acquisition outcomes. A terminal queue status is not successful collection.',
                  'No state-law or national corpus completeness or legal currency is certified.'],
        'network_requests': 0, 'queue_config_source_or_shared_output_changes': False,
        'validation': {'passed': True, 'issues': [], 'unique_url_rows': len(ledger), 'family_denominators_verified': True}}
    write('summary.json', summary)
    (OUT / 'README.md').write_text('''# Reviewed statewide source-family completion ledger

This snapshot contains exactly 355 previously reviewed URLs: 342 North Carolina chapter PDFs, six Nebraska rule exports, and seven Georgia uniform-rule PDFs. Each URL appears once in the JSONL and CSV ledger, with its family, outcome, original/text hashes, and seed-packet provenance.

Downloaded records with native text are divided into recognizable chapter/rule text and separately reviewed historical notices. Historical notices are included in the download total. Pending URLs and access exclusions remain explicit. These denominators describe the finite reviewed URL families; they do not establish complete laws of any state or current legal effect.

`summary.json` binds both seed files, the annotation version, checker output, current configuration, and the read-only database resource snapshot. `checks/` preserves the underlying original/text integrity checks. All collection originals and shared outputs remain unchanged.
''', encoding='utf8')
    write('files.sha256.json', {'files': [{'path': relative(p), 'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'files.sha256.json']})
    print(json.dumps({'summary': relative(OUT / 'summary.json'), 'families': families, 'validation': summary['validation']}, indent=2))


if __name__ == '__main__': main()
