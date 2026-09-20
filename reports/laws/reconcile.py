"""Offline, source-preserving jurisdiction/category coverage reconciliation."""
from collections import Counter, defaultdict
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit, urlunsplit

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
ORIGINAL = ROOT / 'sources/official_laws'
FOLLOWUP_COLLECTION = 'corpus/official_law_state_rules_followup_20260914'
FOLLOWUP_ANNOTATIONS = ROOT / 'sources/official_laws/state_rules_followup_20260914/content_annotations.json'
COLLECTIONS = ['corpus/official_law_pages', 'corpus/official_law_recovery_pass_1', 'corpus/official_law_nebraska_chapters', 'corpus/official_law_resume_pass2_20260913', 'corpus/official_law_resume_pass3_20260913', 'corpus/official_law_resume_quick_20260914', FOLLOWUP_COLLECTION]
CATEGORIES = {'statutes', 'constitution', 'court_rules', 'home_rule_act', 'legislative_rules', 'administrative_code'}
INPUTS = {}
STAT_ISSUES = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    INPUTS[path.relative_to(ROOT).as_posix()] = {'sha256': sha(raw), 'bytes': len(raw)}
    return raw


def read_json(path):
    return json.loads(read(path))


def read_jsonl(path):
    return [json.loads(line) for line in read(path).splitlines() if line.strip()]


def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl(name, rows):
    (OUT / name).write_bytes(b''.join(packed(row) + b'\n' for row in rows))


def canonical(url):
    try:
        p = urlsplit(url or '')
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', p.query, '')) if p.scheme in ('http', 'https') else url
    except ValueError:
        return url


def relative(path):
    p = Path(path)
    return str(p.resolve().relative_to(ROOT)).replace('\\', '/') if p.is_absolute() else str(p).replace('\\', '/')


def ro(path):
    c = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('BEGIN')
    return c


def classify_followup_chapter(r):
    """Recognize reviewed chapter families without certifying extent or currency."""
    r.pop('content_review', None)
    observations = [o for o in r['observations'] if o['collection'] == FOLLOWUP_COLLECTION]
    if not observations or not r['captures']:
        return None
    contexts = [c for o in observations for c in o.get('source_contexts', [])]
    p = urlsplit(r['url'])
    chapter = None
    kind = None
    if p.hostname == 'www.ncleg.gov':
        match = re.fullmatch(r'/EnactedLegislation/Statutes/PDF/ByChapter/Chapter_([0-9A-Za-z]+)\.pdf', p.path)
        if match and any(c.get('resource_kind') == 'full_statute_chapter_pdf' and c.get('jurisdiction') == 'North Carolina' and c.get('category') == 'statutes' for c in contexts):
            chapter, kind = match.group(1), 'North Carolina statute PDF'
    elif p.hostname == 'nebraskajudicial.gov':
        node = p.path.removeprefix('/book/export/html/') if p.path.startswith('/book/export/html/') else ''
        chapters = {'8577': '1', '8670': '2', '8710': '3', '8933': '4', '8974': '5', '9050': '6'}
        if node in chapters and any(c.get('resource_kind') == 'printer_friendly_rule_chapter_html' and c.get('jurisdiction') == 'Nebraska' and c.get('category') == 'court_rules' for c in contexts):
            chapter, kind = chapters[node], 'Nebraska Supreme Court rule chapter HTML export'
    if chapter is None:
        return None
    historical_label = kind == 'North Carolina statute PDF' and any(re.search(r'\[(?:recodified|repealed|expired|reserved)', label, re.I) for label in r.get('labels', []))
    annotations = read_json(FOLLOWUP_ANNOTATIONS)['notices']
    raw_hashes = {c['raw_sha256'] for c in r['captures'].values() if c.get('raw_hash_verified')}
    for text in r['texts'].values():
        if text.get('raw_sha256') not in raw_hashes:
            continue
        try:
            path = (ROOT / text['text_path']).resolve()
            path.relative_to(ROOT.resolve())
            raw = path.read_bytes()
            if sha(raw) != text['text_sha256']:
                continue
            body = raw.decode('utf-8')
        except (OSError, ValueError, UnicodeError):
            continue
        annotation = next((a for a in annotations if a['source_url'] == r['url'] and a['raw_sha256'] == text['raw_sha256'] and a['text_sha256'] == sha(raw)), None)
        if annotation:
            r['content_review'] = {**annotation, 'annotation_path': relative(FOLLOWUP_ANNOTATIONS),
                'annotation_file_sha256': INPUTS[relative(FOLLOWUP_ANNOTATIONS)]['sha256']}
            return (annotation['content_kind'], annotation['classification_basis'])
        heading = re.search(r'\bChapter\s+' + re.escape(chapter) + r'\b', body, re.I)
        section = re.search(r'(?:G\.S\.|§)\s*' + re.escape(chapter) + r'[-–]\d+', body)
        if not historical_label and len(body.strip()) >= 200 and heading and section:
            return ('law_chapter_body', f'Reviewed {kind} family; hash-verified indexed text contains its chapter heading and section citations. Extent, legal correctness, and current edition are not certified; prior-version sections may remain.')
    if historical_label:
        return ('law_document_title_evidence_needs_review', 'The preserved publisher label indicates recodification, repeal, expiration or reservation. A historical notice has not been matched to the reviewed raw/text hashes, so active statutory body status is not inferred.')
    return ('law_document_title_evidence_needs_review', f'Reviewed {kind} source family; no matching hash-verified chapter-body indicators established in the current index. Download status alone does not verify legal text or currency.')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    read(ROOT / 'REQUEST.md'); read(ROOT / 'RUNBOOK.md')
    source_map = read_json(ORIGINAL / 'indexes/source_index.json')
    state_names = sorted({r['jurisdiction'] for r in source_map})
    assert len(state_names) == 51 and len(source_map) == 153
    original_rows = source_map + read_json(ORIGINAL / 'indexes/document_manifest.json') + read_json(ORIGINAL / 'indexes/supplemental_sources_manifest.json')
    meta_by_url = {}
    for path in sorted((ORIGINAL / 'metadata').glob('*.json')):
        m = read_json(path)
        meta_by_url[canonical(m.get('source_url'))] = (m, path)
    resources = {}
    def resource(url):
        key = canonical(url)
        if key not in resources:
            resources[key] = {'url': key, 'contexts': set(), 'observations': [], 'captures': {},
                              'texts': {}, 'derivatives': [], 'labels': set(), 'edition_observations': [],
                              'source_entries': [], 'ocr': {}}
        return resources[key]
    def capture(r, path, digest, size, collection, verified=False):
        key = (relative(path), digest)
        old = r['captures'].get(key, {})
        r['captures'][key] = {'raw_path': key[0], 'raw_sha256': digest, 'bytes': size,
                              'collection': old.get('collection', collection), 'raw_hash_verified': verified or old.get('raw_hash_verified', False)}
    def dates(r, m, evidence):
        values = {k: m[k] for k in ('document_title', 'source_document_title', 'source_document_description',
                  'retrieved_at_utc', 'fetched_at', 'derived_at_utc', 'opf_metadata') if m.get(k)}
        if m.get('headers', {}).get('last-modified'):
            values['http_last_modified_not_legal_edition'] = m['headers']['last-modified']
        if values:
            r['edition_observations'].append({'evidence': evidence, 'observed_values': values,
                'legal_currency_verified': False, 'note': 'Retrieval/generation/HTTP dates are not effective-date or current-edition certification.'})
    for original in original_rows:
        url = original.get('official_url') or original.get('source_url')
        r = resource(url)
        if original.get('jurisdiction') in state_names:
            r['contexts'].add((original['jurisdiction'], original['category']))
        m, path = meta_by_url.get(canonical(original.get('source_url') or url), (original, None))
        label = original.get('label') or m.get('document_title') or ''
        if label:
            r['labels'].add(label)
        status = m.get('verification_status', 'unknown')
        evidence = relative(path) if path else 'sources/official_laws/indexes/document_manifest.json'
        raw_path = ORIGINAL / m['evidence_path'] if m.get('evidence_path') else None
        accepted = status.startswith('retrieved') and 200 <= m.get('http_status', 0) < 300
        if accepted and raw_path and raw_path.is_file() and m.get('sha256'):
            capture(r, raw_path, m['sha256'], m.get('bytes'), 'official_laws')
        obs = {'collection': 'official_laws', 'status': status, 'http_status': m.get('http_status'),
               'metadata_path': evidence, 'metadata_sha256': INPUTS.get(evidence, {}).get('sha256'),
               'retrieved_at': m.get('retrieved_at_utc'), 'error': m.get('error'),
               'discovered_from': original.get('discovered_from'), 'source_evidence_path': original.get('source_evidence_path'),
               'redirect_url': canonical(m.get('final_url')) if m.get('final_url') != m.get('source_url') else None}
        if obs not in r['observations']:
            r['observations'].append(obs)
        dates(r, m, evidence)
        if original in source_map:
            r['source_entries'].append({'jurisdiction': original['jurisdiction'], 'category': original['category'],
                'official_url': original['official_url'], 'discovery_method': original.get('discovery_method'),
                'discovered_from': original.get('discovered_from'), 'saved_status': status, 'metadata_path': evidence,
                'completeness': original.get('completeness'), 'document_title': m.get('document_title')})
    database_snapshots = []
    for collection in COLLECTIONS:
        base = ROOT / collection
        db = ro(base / 'corpus.sqlite3')
        contexts = {}
        for c in db.execute('SELECT * FROM contexts'):
            seed = json.loads(c['seed_json'])
            j = json.loads(c['jurisdiction_json'])
            contexts[c['id']] = {'state': j.get('state'), 'category': c['category'], 'seed': seed}
        links = defaultdict(list)
        for link in db.execute('SELECT * FROM resource_contexts'):
            links[link['resource_id']].append(dict(link))
        rows = [dict(x) for x in db.execute('SELECT * FROM resources ORDER BY id')]
        db.close()
        database_snapshots.append({'database': collection + '/corpus.sqlite3', 'resource_count': len(rows),
            'status_counts': dict(Counter(x['status'] for x in rows)), 'logical_resource_rows_sha256': sha(packed(rows))})
        for row in rows:
            r = resource(row['url'])
            provenance = []
            for link in links[row['id']]:
                c = contexts[link['context_id']]
                if c['state'] in state_names:
                    r['contexts'].add((c['state'], c['category']))
                seed = c['seed']
                provenance.append({'context_id': link['context_id'], 'jurisdiction': c['state'], 'category': c['category'],
                    'discovered_from': link.get('discovered_from') or seed.get('discovered_from'),
                    'authority_basis': seed.get('authority_basis'), 'discovery_complete': seed.get('discovery_complete', False),
                    'resource_kind': seed.get('resource_kind'), 'source_family': seed.get('source_family')})
                if collection == FOLLOWUP_COLLECTION and seed.get('edition', {}).get('source_label'):
                    r['labels'].add(seed['edition']['source_label'])
                for p in seed.get('provenance', []):
                    if p.get('observed_label'):
                        r['labels'].add(p['observed_label'])
            if row['title']:
                r['labels'].add(row['title'])
            m = read_json(base / row['metadata_path']) if row.get('metadata_path') else {}
            if row['status'] == 'downloaded' and row['raw_complete'] and row.get('sha256'):
                capture(r, base / row['raw_path'], row['sha256'], row['byte_count'], collection)
            evidence = collection + '/' + row['metadata_path'] if row.get('metadata_path') else collection + '/corpus.sqlite3'
            r['observations'].append({'collection': collection, 'resource_id': row['id'], 'status': row['status'],
                'http_status': row['last_http_status'], 'attempts': row['attempts'], 'fetch_id': row['last_fetch_id'],
                'metadata_path': evidence, 'metadata_sha256': INPUTS.get(evidence, {}).get('sha256'),
                'retrieved_at': m.get('fetched_at'), 'error': row['error'], 'redirect_url': row['redirect_url'],
                'extraction_status': row['extraction_status'], 'source_contexts': provenance})
            dates(r, m, evidence)
    # Reuse the production index's hash verification only when its size/mtime fingerprint still matches.
    idx = ro(ROOT / 'catalog/documents.sqlite3')
    file_cache = {x['path']: dict(x) for x in idx.execute('SELECT * FROM file_cache')}
    latest_build = dict(idx.execute('SELECT * FROM builds WHERE completed_at IS NOT NULL ORDER BY completed_at DESC LIMIT 1').fetchone())
    latest_build['summary_json'] = json.loads(latest_build['summary_json'])
    indexed = [dict(x) for x in idx.execute('''SELECT d.*,c.characters AS indexed_characters FROM latest_documents d
        LEFT JOIN contents c ON c.id=d.content_id WHERE d.collection LIKE 'official_laws%'
        OR d.collection LIKE 'corpus/official_law_%' ''')]
    idx.close()
    verified_paths = {}
    def verified(path, digest):
        if not path or not digest:
            return False
        path = relative(path)
        if (path, digest) in verified_paths:
            return verified_paths[path, digest]
        cache = file_cache.get(path)
        try:
            stat = (ROOT / path).stat()
            good = bool(cache and cache['sha256'] == digest and stat.st_size == cache['size'] and stat.st_mtime_ns == cache['mtime_ns'])
        except OSError:
            good = False
        verified_paths[path, digest] = good
        if not good:
            STAT_ISSUES.append({'path': path, 'expected_sha256': digest, 'issue': 'No unchanged production-index verification fingerprint; not counted as currently verified.'})
        return good
    verified_derivatives = set()
    for row in indexed:
        r = resource(row['source_url'])
        for state in json.loads(row['jurisdictions_json']):
            for category in json.loads(row['categories_json']):
                if state in state_names and category in CATEGORIES:
                    r['contexts'].add((state, category))
        if row['title']:
            r['labels'].add(row['title'])
        raw_ok = verified(row['raw_path'], row['raw_sha256'])
        if raw_ok:
            capture(r, row['raw_path'], row['raw_sha256'], row['raw_bytes'], row['collection'], True)
        text_ok = raw_ok and row['index_text_status'] == 'searchable' and verified(row['text_path'], row['text_file_sha256'])
        if text_ok:
            r['texts'][row['text_file_sha256']] = {'text_path': row['text_path'], 'text_sha256': row['text_file_sha256'],
                'indexed_text_sha256': row['indexed_text_sha256'], 'characters': row['indexed_characters'],
                'collection': row['collection'], 'capture_kind': row['capture_kind'], 'raw_sha256': row['raw_sha256'],
                'index_version_id': row['version_id'], 'indexed_at': row['indexed_at'],
                'verification_basis': 'Existing index SHA256 validation plus unchanged current size/mtime fingerprint'}
            if row['capture_kind'] == 'document_text_derivative':
                verified_derivatives.add((r['url'], row['raw_sha256'], relative(row['text_path'])))
    derivative_counts = Counter()
    document_manifests = [('corpus/official_law_pages', family) for family in ('document_derivatives', 'xml_document_derivatives', 'epub_document_derivatives')]
    document_manifests.append(('corpus/official_law_resume_quick_20260914', 'offline_docx'))
    document_manifests.append(('corpus/official_law_resume_quick_20260914', 'offline_docx_pass2'))
    for collection, family in document_manifests:
        path = ROOT / collection / family / 'manifest.jsonl'
        for d in read_jsonl(path):
            if d.get('status') != 'extracted':
                continue
            r = resource(d['source_url'])
            ok = (r['url'], d['parent_raw_sha256'], relative(d['text_path'])) in verified_derivatives
            body_scope_verified = bool(ok and (d.get('literal_text_conservation_verified') and d.get('paragraph_coverage_verified')
                or d.get('detected_format') == 'epub' and d.get('extracted_spine_items') == d.get('spine_items') and not d.get('skipped_unsupported_spine_parts')))
            info = {'family': family, 'status': d['status'], 'current_index_verification_retained': ok,
                    'body_or_book_coverage_verified': body_scope_verified, 'parent_raw_sha256': d['parent_raw_sha256'],
                    'text_sha256': d['text_sha256'], 'text_bytes': d['text_bytes'], 'text_paragraphs': d['text_paragraphs'],
                    'detected_format': d.get('detected_format'), 'declared_format': d.get('declared_format'),
                    'extractor_version': d['extractor_version'], 'extraction_method': d['extraction_method'],
                    'limitations': d['limitations'], 'manifest': relative(path)}
            r['derivatives'].append(info)
            derivative_counts[family] += ok
            dates(r, d, relative(path))
    archive_summary = read_json(ROOT / 'corpus/official_law_pages/document_derivatives/archive_member_reconciliation.summary.json')
    reconciled_archives = {canonical(x['archive_url']) for x in archive_summary['archives']
                           if set(x['counts']) <= {'already_saved_exact_payload', 'non_document_members'}}
    for path in [ORIGINAL / 'ocr/pdf_ocr_manifest.jsonl'] + [ROOT / c / 'ocr/pdf_ocr_manifest.jsonl' for c in COLLECTIONS[:2]]:
        for o in read_jsonl(path):
            for url in o.get('source_urls', [o.get('source_url')]):
                if canonical(url) not in resources:
                    continue
                r = resources[canonical(url)]
                if o['source_pdf_sha256'] not in {c['raw_sha256'] for c in r['captures'].values()}:
                    continue
                r['ocr'][o['source_pdf_sha256']] = {'pdf_sha256': o['source_pdf_sha256'], 'pdf_pages': o['pdf_pages'],
                    'screening_complete': o['screening_complete'], 'ocr_status': o['ocr_status'],
                    'ocr_pages_required': o['ocr_pages_required'], 'ocr_pages_completed': o['ocr_pages_completed'],
                    'manual_review_pages': len(o.get('manual_review_page_numbers', [])),
                    'low_confidence_pages': o.get('pages_below_70_confidence'), 'manifest': relative(path),
                    'screening_status_counts': o.get('screening_status_counts'), 'screening_note': o.get('screening_note')}
    original_pauses = read_json(ORIGINAL / 'indexes/paused_hosts.json')
    constraint_report = read_json(ROOT / 'reports/law_source_constraints.json')
    constraints = {r['host']: r for r in constraint_report['hosts']}
    shared = ro(ROOT / 'corpus/_shared_hosts/hosts.sqlite3')
    shared_rows = {r['host']: dict(r) for r in shared.execute('SELECT host,delay_seconds,cooldown_until,pause_reason,updated_at FROM host_state')}
    shared.close()
    def redirect_resolved(url, visited=None):
        visited = set() if visited is None else visited
        url = canonical(url)
        if url in visited or url not in resources:
            return None
        r = resources[url]
        if r['captures']:
            return url
        visited.add(url)
        for o in r['observations']:
            if o.get('redirect_url'):
                found = redirect_resolved(o['redirect_url'], visited)
                if found:
                    return found
        return None
    resource_rows, gap_rows, edition_rows = [], [], []
    for r in resources.values():
        p = urlsplit(r['url'])
        labels = sorted(r['labels'])
        lowered = (r['url'] + ' ' + ' '.join(labels)).lower()
        followup_chapter = classify_followup_chapter(r)
        if re.search(r'/weekly_schedule/|/alispdfs/(?:billtolaw|hbillaw)\.pdf|/sunset_review\.pdf', r['url'], re.I):
            role, basis = 'ancillary', 'Observed Arizona schedules, legislative-process or sunset-review material; not substantive constitution/statute body.'
        elif p.hostname == 'www.azleg.gov' and p.path.rstrip('/').lower() in {'/arsdetail', '/constitution', '/constitution/constitution'}:
            role, basis = 'legal_inventory_navigation', 'Saved Arizona title/article landing pages are navigation, not full statute/constitution body.'
        elif r['url'] in reconciled_archives:
            role, basis = 'reconciled_duplicate_archive', 'All legal archive members hash-match saved standalone payloads; archive container is not an extra law document.'
        elif followup_chapter and followup_chapter[0].startswith('historical_'):
            role, basis = followup_chapter
        elif any(d['current_index_verification_retained'] for d in r['derivatives']):
            role, basis = 'verified_law_document_derivative', 'Explicit saved DOCX/Word XML/EPUB legal document parser and indexed parent/text validation.'
        elif any(o['collection'] == 'corpus/official_law_nebraska_chapters' for o in r['observations']) and r['captures']:
            role, basis = 'law_chapter_body', 'Reviewed Nebraska full statutory chapter family; ordinary HTML extraction, not independently certified full text.'
        elif followup_chapter:
            role, basis = followup_chapter
        elif p.hostname == 'www.azleg.gov' and p.path.lower() == '/const/preamble.htm':
            role, basis = 'law_text_fragment', 'Saved Arizona constitution preamble only.'
        elif any(h in lowered for h in ('adoptedrulesofthe57thlegislature', 'senaterules2025-2026')):
            role, basis = 'legislative_procedural_rules', 'Legislative chamber rules; source constitution/statute context does not change their content category.'
        elif any(c['raw_path'].lower().endswith('.pdf') for c in r['captures'].values()) and re.search(r'\b(?:constitution|statutes|revised statutes|century code|rules|code of)\b', ' '.join(labels), re.I):
            role, basis = 'law_document_title_evidence_needs_review', 'Saved title/anchor identifies law-related material; content and completeness were not manually certified.'
        else:
            role, basis = 'needs_content_review', 'Source category is provenance, not proof of substantive legal body or complete text.'
        if r['captures']:
            effective = 'downloaded'
            resolved = None
        else:
            resolved = redirect_resolved(r['url'])
            statuses = {o['status'] for o in r['observations']}
            effective = 'resolved_to_saved_target' if resolved else ('pending' if statuses & {'pending', 'retry_wait', 'fetching'} else ('unresolved_redirect' if any(o.get('redirect_url') for o in r['observations']) else 'unresolved_failure_or_exclusion'))
        host_policy = shared_rows.get(p.netloc, {})
        blocked = bool(host_policy.get('pause_reason') or p.netloc in original_pauses or p.netloc == 'www.sccourts.org')
        output = {'url': r['url'], 'contexts': [{'jurisdiction': j, 'category': c} for j, c in sorted(r['contexts'])],
            'effective_status': effective, 'resolved_target': resolved, 'downloaded': bool(r['captures']),
            'content_role': role, 'classification_basis': basis, 'content_review': r.get('content_review'), 'labels': labels,
            'captures': list(r['captures'].values()), 'verified_texts': list(r['texts'].values()),
            'document_derivatives': r['derivatives'], 'ocr_screenings': list(r['ocr'].values()),
            'observations': r['observations'], 'source_entries': r['source_entries'],
            'known_host_constraint': constraints.get(p.netloc, {}).get('observed_condition'),
            'host_pause': host_policy.get('pause_reason') or original_pauses.get(p.netloc, {}).get('reason'),
            'host_delay_seconds': host_policy.get('delay_seconds'),
            'pending_known_access_block': effective == 'pending' and blocked,
            'full_legal_text_correctness_verified': None, 'whole_jurisdiction_completeness': 'not_established'}
        resource_rows.append(output)
        for e in r['edition_observations']:
            edition_rows.append({'url': r['url'], 'contexts': output['contexts'], **e})
        if effective.startswith('unresolved') or effective == 'pending':
            gap_rows.append({'url': r['url'], 'contexts': output['contexts'], 'gap': effective,
                'recorded_statuses': dict(Counter(o['status'] for o in r['observations'])),
                'host_constraint': output['known_host_constraint'], 'host_pause': output['host_pause'],
                'pending_known_access_block': output['pending_known_access_block'],
                'evidence_paths': sorted({o['metadata_path'] for o in r['observations']})})
    # Retain the exact saved Arizona compilation statements; they are not current-law certifications.
    for url, kind in [('https://www.azleg.gov/constitution/', 'constitution_inventory_and_stale_compilation_notice'),
                      ('https://www.azleg.gov/arsDetail/?title=1', 'statute_title_inventory_compilation_notice')]:
        r = resources.get(url)
        if not r:
            continue
        paths = [ROOT / x['text_path'] for x in r['texts'].values()]
        if not paths and url in meta_by_url and meta_by_url[url][0].get('text_path'):
            paths = [ORIGINAL / meta_by_url[url][0]['text_path']]
        for path in paths[:1]:
            text = path.read_text(encoding='utf-8')
            excerpts = [line for line in text.splitlines() if re.search(r'updated to include|next update|compilation|legislative drafting', line, re.I)]
            edition_rows.append({'url': url, 'contexts': [{'jurisdiction': 'Arizona', 'category': 'constitution' if '/constitution/' in url else 'statutes'}],
                'evidence': relative(path), 'evidence_sha256': sha(path.read_bytes()), 'kind': kind,
                'observed_values': {'saved_compilation_statements': excerpts}, 'legal_currency_verified': False})
    by_context = defaultdict(list)
    for r in resource_rows:
        for c in r['contexts']:
            by_context[c['jurisdiction'], c['category']].append(r)
    def counts(rows):
        downloaded = [r for r in rows if r['downloaded']]
        payloads = {c['raw_sha256']: c['bytes'] for r in downloaded for c in r['captures']}
        texts = {t['text_sha256']: t['characters'] for r in rows for t in r['verified_texts']}
        screens = {o['pdf_sha256']: o for r in rows for o in r['ocr_screenings']}
        return {'observed_resource_urls': len(rows), 'downloaded_resource_urls': len(downloaded),
            'unique_downloaded_payloads': len(payloads), 'unique_downloaded_payload_bytes': sum(x or 0 for x in payloads.values()),
            'downloaded_urls_with_current_index_verified_raw': sum(any(c['raw_hash_verified'] for c in r['captures']) for r in downloaded),
            'urls_with_verified_nonempty_text': sum(bool(r['verified_texts']) for r in rows),
            'unique_verified_text_artifacts': len(texts), 'unique_verified_text_characters': sum(x or 0 for x in texts.values()),
            'verified_document_parser_resources': sum(any(d['current_index_verification_retained'] for d in r['document_derivatives']) for r in rows),
            'body_or_book_parser_coverage_verified_resources': sum(any(d['body_or_book_coverage_verified'] for d in r['document_derivatives']) for r in rows),
            'verified_text_content_correctness_resources': None,
            'known_ancillary_downloaded_urls': sum(r['downloaded'] and r['content_role'] == 'ancillary' for r in rows),
            'legal_inventory_navigation_downloaded_urls': sum(r['downloaded'] and r['content_role'] == 'legal_inventory_navigation' for r in rows),
            'downloaded_content_needing_review_urls': sum(r['downloaded'] and r['content_role'] in {'needs_content_review', 'law_document_title_evidence_needs_review'} for r in rows),
            'reconciled_duplicate_archive_urls': sum(r['content_role'] == 'reconciled_duplicate_archive' for r in rows),
            'resolved_redirect_or_prior_failure_urls': sum(r['effective_status'] == 'resolved_to_saved_target' for r in rows),
            'pending_urls': sum(r['effective_status'] == 'pending' for r in rows),
            'pending_known_access_block_urls': sum(r['pending_known_access_block'] for r in rows),
            'unresolved_redirect_urls': sum(r['effective_status'] == 'unresolved_redirect' for r in rows),
            'unresolved_failure_or_exclusion_urls': sum(r['effective_status'] == 'unresolved_failure_or_exclusion' for r in rows),
            'screened_unique_pdfs': len(screens), 'screened_pdf_pages': sum(o['pdf_pages'] for o in screens.values()),
            'selected_ocr_pages_required': sum(o['ocr_pages_required'] for o in screens.values()),
            'selected_ocr_pages_completed': sum(o['ocr_pages_completed'] for o in screens.values()),
            'sparse_or_other_manual_review_pdf_pages': sum(o['manual_review_pages'] for o in screens.values())}
    category_rows = []
    baseline = {(r['jurisdiction'], r['category']) for r in source_map}
    for state, category in sorted(baseline | set(by_context)):
        rows = by_context[state, category]
        metrics = counts(rows)
        specific = []
        if not metrics['downloaded_resource_urls']:
            specific.append('No accepted downloaded resource recorded for this saved source category.')
        if not metrics['urls_with_verified_nonempty_text']:
            specific.append('No nonempty text artifact with retained production-index verification.')
        if metrics['pending_urls'] or metrics['unresolved_redirect_urls'] or metrics['unresolved_failure_or_exclusion_urls']:
            specific.append('Unresolved observed URLs remain; exact URLs/statuses/source evidence are in resource_gaps.jsonl.')
        if metrics['sparse_or_other_manual_review_pdf_pages']:
            specific.append('Sparse/vector or other flagged PDF pages remain for text-quality review; completed OCR is not a correctness guarantee.')
        if state == 'Arizona' and category == 'constitution':
            specific.append('Saved whole-constitution entry is navigation with an outdated compilation notice; only the preamble body is identified. The 29 article redirect targets remain uncollected; no whole-constitution body was found in the audited law sources.')
        if state == 'Arizona' and category == 'statutes':
            specific.append('arsDetail title pages are chapter/section navigation listings, not full statute bodies; ancillary legislature PDFs are separate.')
        if state == 'Iowa' and category == 'statutes':
            specific.append('Extracted EPUB identifies itself as 2022 Code of Iowa. Saved MOBI remains unparsed and is not assumed equivalent or current.')
        specific.append('The whole jurisdiction/category is not fully enumerated; expected total and legal currency remain unknown.')
        category_rows.append({'jurisdiction': state, 'category': category, 'source_map_slots': sum(r['jurisdiction'] == state and r['category'] == category for r in source_map),
            **metrics, 'effective_status_counts': dict(Counter(r['effective_status'] for r in rows)),
            'downloaded_content_role_counts': dict(Counter(r['content_role'] for r in rows if r['downloaded'])),
            'unresolved_hosts': dict(Counter(urlsplit(r['url']).netloc for r in rows if r['effective_status'] in {'pending', 'unresolved_redirect', 'unresolved_failure_or_exclusion'})),
            'source_entries': [e for r in rows for e in r['source_entries'] if e['jurisdiction'] == state and e['category'] == category],
            'specific_gaps': specific, 'expected_full_corpus_resource_count': None, 'enumeration_complete': False,
            'whole_category_complete': False, 'edition_currency_verified': False})
    jurisdiction_rows = []
    for state in state_names:
        rows = [r for r in resource_rows if any(c['jurisdiction'] == state for c in r['contexts'])]
        jurisdiction_rows.append({'jurisdiction': state, **counts(rows), 'categories': [r['category'] for r in category_rows if r['jurisdiction'] == state],
                                  'whole_state_complete': False, 'expected_full_corpus_resource_count': None})
    summary = {'snapshot_started_at_utc': started, 'snapshot_completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'scope': 'Original official law map/captures; official-law pages; recovery; Nebraska chapters; reviewed official-law continuation passes; completed document and OCR derivatives. Trellis/court/county collections excluded.',
        'jurisdictions': 51, 'original_source_map_slots': 153, 'jurisdiction_category_rows': len(category_rows),
        'totals_deduplicated_across_jurisdictions_and_categories': counts(resource_rows),
        'verified_document_derivatives_by_family': dict(derivative_counts),
        'collection_database_snapshots': database_snapshots,
        'production_index_build': {k: latest_build[k] for k in ('build_id', 'started_at', 'completed_at', 'builder_version')},
        'production_index_file_reference_issues_at_build': latest_build['summary_json'].get('validation_file_reference_issues'),
        'retained_index_fingerprint_issue_count': len(STAT_ISSUES),
        'definitions': {'downloaded_resource_urls': 'Distinct observed source URLs with an accepted successful saved payload; includes ancillary and navigation captures.',
            'urls_with_verified_nonempty_text': 'Distinct resource URLs with a nonempty direct or derivative text verified by the existing production index; current file fingerprints still match. Not semantic completeness.',
            'verified_document_parser_resources': 'Resources with an indexed parent/hash-verified completed DOCX, Word XML or EPUB parser derivative.',
            'body_or_book_parser_coverage_verified_resources': 'Word XML literal-text/paragraph coverage or complete EPUB spine extraction with verified artifacts; parser scope and formatting limits still apply.',
            'verified_text_content_correctness_resources': 'Null: no human/certified full-legal-text correctness count is established.',
            'category_attribution': 'Saved source/seed context, preserved even where a discovered ancillary link is not that kind of law.',
            'dedup': 'URLs normalized only for scheme/host casing and fragments; query order and path spelling retained. Payloads and text artifacts deduplicated by SHA256. Derivatives attach to parent URLs; archives do not add member documents.',
            'editions': 'Observed titles, generation statements, OPF metadata, retrieval and HTTP modification dates retained separately; retrieval/generation dates are not legal effective dates.'},
        'whole_state_complete_count': 0, 'full_corpus_complete': False, 'network_requests': 0,
        'source_manifests_index_workers_modified': False, 'jurisdiction_totals': jurisdiction_rows, 'coverage': category_rows}
    write_json('jurisdiction_coverage.json', summary)
    scalar_fields = ['jurisdiction', 'category', 'source_map_slots'] + list(counts([])) + ['expected_full_corpus_resource_count', 'enumeration_complete', 'whole_category_complete', 'edition_currency_verified']
    with (OUT / 'jurisdiction_coverage.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=scalar_fields)
        writer.writeheader()
        writer.writerows({key: r.get(key) for key in scalar_fields} for r in category_rows)
    write_jsonl('resource_inventory.jsonl', sorted(resource_rows, key=lambda r: r['url']))
    write_jsonl('resource_gaps.jsonl', sorted(gap_rows, key=lambda r: r['url']))
    write_jsonl('edition_observations.jsonl', edition_rows)
    write_json('source_map_snapshot.json', source_map)
    write_json('input_evidence.json', {'snapshot_started_at_utc': started, 'files': INPUTS,
        'database_snapshots': database_snapshots, 'shared_host_policy_snapshot': shared_rows,
        'production_index_build': latest_build, 'retained_index_fingerprint_issues': STAT_ISSUES,
        'consistency': 'Each SQLite database read in a read-only transaction; snapshots are sequential while Arizona collection may advance. No blanket payload/text rehash, collection, OCR or indexing was run.'})
    print(json.dumps({k: v for k, v in summary.items() if k not in {'coverage', 'jurisdiction_totals', 'definitions'}}, indent=2))


if __name__ == '__main__':
    main()
