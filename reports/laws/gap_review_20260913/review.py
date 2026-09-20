"""Bounded offline review of the 24 zero-verified-text category gaps. No fetching."""
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urljoin, urlsplit, urlunsplit
from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
ORIGINAL = ROOT / 'sources/official_laws'
inputs = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    inputs[str(path.relative_to(ROOT)).replace('\\', '/')] = {'sha256': sha(raw), 'bytes': len(raw)}
    return raw


def read_json(path):
    return json.loads(read(path))


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl(name, rows):
    (OUT / name).write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in rows), encoding='utf-8')


def canon(url):
    try:
        p = urlsplit(url)
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', p.query, '')) if p.scheme in ('http', 'https') else None
    except (ValueError, TypeError):
        return None


def ro(path):
    c = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('BEGIN')
    return c


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    read(ROOT / 'REQUEST.md'); read(ROOT / 'RUNBOOK.md')
    report = read_json(ROOT / 'reports/laws/jurisdiction_coverage.json')
    gaps = {(r['jurisdiction'], r['category']): r for r in report['coverage'] if not r['urls_with_verified_nonempty_text']}
    source_map = read_json(ORIGINAL / 'indexes/source_index.json')
    original_links = read_json(ORIGINAL / 'indexes/discovered_links.json')
    links, dispositions = [], []
    def add(url, state, category, parent, path, label='', relation='saved_link', href=None):
        key = canon(url)
        if not key:
            return
        links.append({'url': key, 'jurisdiction': state, 'category': category, 'source_url': parent,
                      'observed_label': label, 'observed_href': href or url, 'relation': relation,
                      'evidence_path': str(path.relative_to(ROOT)).replace('\\', '/'),
                      'evidence_sha256': inputs[str(path.relative_to(ROOT)).replace('\\', '/')]['sha256']})
    for state, category in gaps:
        entries = [x for x in source_map if (x['jurisdiction'], x['category']) == (state, category)]
        disposition = {'jurisdiction': state, 'category': category,
            'prior_downloaded_urls': gaps[state, category]['downloaded_resource_urls'],
            'prior_verified_nonempty_text_urls': 0, 'evidence': []}
        for entry in entries:
            mp = ORIGINAL / entry['metadata_path']; m = read_json(mp)
            evidence = {'source_url': entry['official_url'], 'saved_status': m['verification_status'],
                        'metadata_path': str(mp.relative_to(ROOT)), 'metadata_sha256': sha(mp.read_bytes()),
                        'http_status': m.get('http_status'), 'error': m.get('error'),
                        'rendered_http_status': m.get('rendered_http_status'),
                        'rendered_text_characters': m.get('rendered_text_characters')}
            disposition['evidence'].append(evidence)
            status = m['verification_status']
            if not status.startswith('retrieved'):
                disposition['disposition'] = ('retained_access_barrier' if '403' in status else
                    'retained_challenge' if 'challenge' in status else 'retained_transport_failure')
                continue
            raw_path = ORIGINAL / m['evidence_path']; raw = read(raw_path)
            evidence['raw_path'] = str(raw_path.relative_to(ROOT)); evidence['raw_sha256'] = sha(raw)
            soup = BeautifulSoup(raw, 'html.parser')
            base = urljoin(m.get('final_url') or entry['official_url'], (soup.find('base') or {}).get('href', ''))
            for a in soup.find_all(['a', 'iframe', 'embed', 'object']):
                attr = 'href' if a.name == 'a' else 'data' if a.name == 'object' else 'src'
                if a.get(attr):
                    add(urljoin(base, a[attr]), state, category, entry['official_url'], raw_path,
                        a.get_text(' ', strip=True), 'html_' + attr, a[attr])
            for meta in soup.find_all('meta'):
                if meta.get('http-equiv', '').lower() == 'refresh':
                    match = re.search(r'url\s*=\s*(.*)', meta.get('content', ''), re.I)
                    if match:
                        add(urljoin(base, match.group(1).strip(' \"\'')), state, category,
                            entry['official_url'], raw_path, 'Saved meta-refresh target', 'meta_refresh', match.group(1))
            for link in m.get('links', []):
                add(link['url'], state, category, entry['official_url'], mp, link.get('label', ''), 'metadata_link')
            rendered_markdown = ''
            if m.get('rendered_evidence_path'):
                rp = ORIGINAL / m['rendered_evidence_path']; render = read_json(rp)
                evidence['rendered_evidence_path'] = str(rp.relative_to(ROOT)); evidence['rendered_evidence_sha256'] = sha(rp.read_bytes())
                for block in render.get('content', []):
                    if block.get('type') != 'text':
                        continue
                    try:
                        data = json.loads(block['text'])
                    except (ValueError, TypeError):
                        continue
                    rendered_markdown = data.get('markdown', '')
                    for url in data.get('links', []):
                        add(url, state, category, entry['official_url'], rp, relation='saved_rendered_link')
                if m.get('rendered_markdown_path'):
                    read(ORIGINAL / m['rendered_markdown_path'])
            disposition['disposition'] = (
                'saved_soft_404_no_document' if 'Error 404' in rendered_markdown else
                'saved_meta_refresh_to_index_not_comprehensive_document' if state == 'New Hampshire' else
                'saved_rule_navigation_not_full_rules' if state == 'Michigan' else
                'saved_statute_search_navigation_not_full_body' if state in {'New Jersey', 'Oklahoma'} else
                'javascript_or_partial_navigation_no_comprehensive_body')
        if not entries:
            disposition['disposition'] = 'saved_recovery_failures_no_new_seed'
        dispositions.append(disposition)
    for link in original_links:
        if (link['jurisdiction'], link['category']) in gaps:
            add(link['official_url'], link['jurisdiction'], link['category'], link['discovered_from'],
                ORIGINAL / 'indexes/discovered_links.json', link.get('label', ''), 'saved_discovered_link_index')
    # Only the three already observed Vermont whole rule PDFs are added from the existing recovery evidence.
    recovery_seeds = ROOT / 'sources/official_laws/recovery_pass_1/seeds.jsonl'
    for line in read(recovery_seeds).splitlines():
        seed = json.loads(line)
        if seed.get('jurisdiction', {}).get('state') == 'Vermont' and seed.get('category') == 'legislative_rules':
            add(seed['url'], 'Vermont', 'legislative_rules', seed.get('discovered_from'), recovery_seeds,
                'Previously selected full legislative rules', 'existing_recovery_seed')
    # Content-category correction: the source context was statutes, but this saved PDF is the constitution.
    wm = ORIGINAL / 'metadata/11658f75929b06d3e63187a8.json'; w = read_json(wm)
    wp = ORIGINAL / w['evidence_path']; wt = ORIGINAL / w['text_path']; wr = read(wp); tr = read(wt)
    assert sha(wr) == w['sha256'] and w['http_status'] == 200
    text = tr.decode('utf-8'); articles = sorted({int(x) for x in re.findall(r'ARTICLE\s+(\d+)', text, re.I)})
    assert 'TITLE 97 - WYOMING CONSTITUTION' in text and articles == list(range(1, 22))
    correction = {'jurisdiction': 'Wyoming', 'saved_provenance_category': 'statutes', 'observed_content_category': 'constitution',
        'source_url': w['source_url'], 'document_title_in_text': 'TITLE 97 - WYOMING CONSTITUTION',
        'pdf_pages': w['pdf_pages'], 'text_characters': len(text), 'article_markers': articles,
        'raw_path': str(wp.relative_to(ROOT)), 'raw_sha256': sha(wr), 'text_path': str(wt.relative_to(ROOT)),
        'text_sha256': sha(tr), 'metadata_path': str(wm.relative_to(ROOT)), 'metadata_sha256': sha(wm.read_bytes()),
        'disposition': 'already_saved_comprehensive_constitution_body_no_download_needed',
        'legal_currency_verified': False, 'source_categories_modified': False}
    add(w['source_url'], 'Wyoming', 'constitution', None, wm, 'The Wyoming Constitution', 'verified_existing_body')
    for d in dispositions:
        if (d['jurisdiction'], d['category']) == ('Wyoming', 'constitution'):
            d['disposition'] = correction['disposition']; d['existing_body_evidence'] = correction
    known = defaultdict(list); db_inventory = []
    for p in sorted(ROOT.rglob('corpus.sqlite3')):
        c = ro(p); rows = [dict(x) for x in c.execute('SELECT id,url,status,attempts FROM resources')]; c.close()
        db_inventory.append({'path': str(p.relative_to(ROOT)), 'resource_rows': len(rows),
            'logical_snapshot_sha256': sha(json.dumps(rows, sort_keys=True).encode())})
        for row in rows:
            known[canon(row['url'])].append({'database': str(p.relative_to(ROOT)), 'resource_id': row['id'],
                                           'status': row['status'], 'attempts': row['attempts']})
    c = ro(ROOT / 'catalog/documents.sqlite3')
    capture_rows = [dict(x) for x in c.execute('SELECT source_url,final_url,collection,raw_sha256 FROM latest_documents')]; c.close()
    for row in capture_rows:
        for key in ('source_url', 'final_url'):
            known[canon(row[key])].append({'saved_capture_collection': row['collection'], 'raw_sha256': row['raw_sha256']})
    for p in (ORIGINAL / 'metadata').glob('*.json'):
        m = json.loads(p.read_bytes())
        for key in ('source_url', 'final_url'):
            if m.get(key):
                known[canon(m[key])].append({'original_metadata': str(p.relative_to(ROOT)), 'status': m.get('verification_status')})
    c = ro(ROOT / 'corpus/_shared_hosts/hosts.sqlite3')
    paused = {x['host']: dict(x) for x in c.execute('SELECT host,pause_reason,cooldown_until,delay_seconds FROM host_state') if x['pause_reason']}; c.close()
    old_pauses = read_json(ORIGINAL / 'indexes/paused_hosts.json')
    by_url = defaultdict(list)
    for link in links:
        by_url[link['url']].append(link)
    candidates, seeds = [], []
    for url, evidence in sorted(by_url.items()):
        label = ' '.join(x['observed_label'] for x in evidence)
        p = urlsplit(url); suffix = Path(p.path).suffix.lower()
        doc = suffix in {'.pdf', '.doc', '.docx', '.epub', '.zip'}
        lead = doc or re.search(r'download|current-rules|default\.aspx|acts/archive|gateway\.dll', url, re.I)
        if not lead:
            continue
        if known.get(url):
            decision = 'excluded_existing_capture_attempt_or_queue'
        elif p.netloc in paused or p.netloc in old_pauses:
            decision = 'excluded_saved_host_barrier'
        elif re.search(r'schedule|calendar|specialevents', url + ' ' + label, re.I):
            decision = 'excluded_ancillary_schedule'
        elif not doc:
            decision = 'deferred_navigation_not_a_comprehensive_document'
        elif not p.hostname.endswith('.gov'):
            decision = 'excluded_unverified_official_document_authority'
        elif re.search(r'constitution|complete|entire|practice.?book|rules', label + ' ' + url, re.I):
            decision = 'staged_observed_comprehensive_document'
            if len(seeds) < 5:
                seeds.append({'url': url, 'source_family': 'offline_gap_review', 'provenance': evidence,
                              'jurisdiction': {'country': 'US', 'level': 'state', 'state': evidence[0]['jurisdiction']},
                              'category': evidence[0]['category'], 'discovery_complete': False})
            else:
                decision = 'deferred_batch_limit'
        else:
            decision = 'excluded_not_established_comprehensive'
        candidates.append({'url': url, 'disposition': decision, 'evidence': evidence,
            'dedup_matches': known.get(url, []), 'saved_host_barrier': paused.get(p.netloc) or old_pauses.get(p.netloc)})
    assert not seeds, 'A new positive lead requires direct model review before staging.'
    for d in dispositions:
        d['candidate_dispositions'] = [{'url': x['url'], 'disposition': x['disposition']} for x in candidates
            if any((e['jurisdiction'], e['category']) == (d['jurisdiction'], d['category']) for e in x['evidence'])]
    summary = {'checked_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        'reviewed_zero_download_categories': sum(not g['downloaded_resource_urls'] for g in gaps.values()),
        'reviewed_zero_verified_text_categories': len(gaps), 'seed_count': 0, 'launchable': False,
        'observed_link_records_reviewed': len(links), 'unique_observed_links': len(by_url),
        'candidate_leads_reviewed': len(candidates), 'candidate_disposition_counts': dict(Counter(x['disposition'] for x in candidates)),
        'category_disposition_counts': dict(Counter(x['disposition'] for x in dispositions)),
        'existing_comprehensive_body_reconciliations': 1, 'remaining_unresolved_or_partial_category_gaps': 23,
        'finding': 'No new unattempted comprehensive official legal document URL qualifies from these saved gaps. Wyoming constitution already exists under statutes provenance; no duplicate fetch is needed.',
        'phase_boundary': 'This review adds no direct-law network batch. Retain access/transport/JavaScript/edition gaps and checkpoint the prepared direct-law work; root owns the separate finite browser review and judge-phase decision.',
        'network_requests': 0, 'source_or_queue_index_controls_modified': False, 'whole_state_completeness_claimed': False}
    write_json('summary.json', summary); write_json('category_dispositions.json', sorted(dispositions, key=lambda x: (x['jurisdiction'], x['category'])))
    write_json('wyoming_constitution_reconciliation.json', correction)
    write_jsonl('candidate_dispositions.jsonl', candidates); write_jsonl('observed_links.jsonl', links); write_jsonl('seeds.jsonl', seeds)
    write_json('input_evidence.json', {'files': inputs, 'corpus_databases': db_inventory,
        'all_index_capture_rows_compared': len(capture_rows), 'known_url_keys': len(known),
        'saved_host_barriers': paused, 'original_host_barriers': old_pauses,
        'dedup_scope': 'Every corpus.sqlite3 resource (any status), all production-index captures, and original-law metadata requests/final URLs. No original/shared data were changed.'})
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
