"""End-to-end checks of the archive-link integration against the running 8769 server."""
import gzip
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8769'
LINKS = ROOT / 'sources/source_archive_links_20260919'
PILOT = ROOT / 'sources/public_law_acquisition_20260919/validation.json'
checks, requests = [], []


def fetch(path):
    started = time.perf_counter()
    try:
        response = urllib.request.urlopen(urllib.request.Request(BASE + path, headers={'Accept-Encoding': 'gzip'}), timeout=60)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read()
        if response.headers.get('Content-Encoding') == 'gzip': body = gzip.decompress(body)
        requests.append({'path': path, 'status': response.status, 'seconds': round(time.perf_counter() - started, 3)})
        return response.status, dict(response.headers), body


def get_json(path):
    status, _, body = fetch(path)
    assert status == 200, (path, status, body[:200])
    return json.loads(body)


def check(name, passed, evidence=None):
    checks.append({'name': name, 'passed': bool(passed), 'evidence': evidence})
    print(('PASS ' if passed else 'FAIL ') + name + (f' {json.dumps(evidence)}' if evidence else ''))


def main():
    gate = json.loads((LINKS / 'validation.json').read_text(encoding='utf-8'))
    counts = gate['counts']
    pilot = json.loads(PILOT.read_text(encoding='utf-8'))['counts']['resources']
    links = {row['source_url']: row for row in map(json.loads, (LINKS / 'links.jsonl').read_text(encoding='utf-8').splitlines()) if row}
    for name in ('app.js', 'styles.css', 'index.html'):
        status, _, body = fetch('/' + name)
        check(f'Live {name} matches disk', status == 200 and body == (ROOT / 'delivery/archive-directory' / name).read_bytes())
    first = get_json('/api/sources?limit=1')
    summary = first['summary']
    check('Archive link summary is live and reconciles with its receipt',
          summary['archive_links']['ready'] and summary['archive_links']['linked_references'] == counts['linked_references'] == len(links)
          and summary['archive_linked_records'] == counts['linked_references'] and summary['saved_content_records'] == pilot,
          {'linked_references': summary['archive_links']['linked_references'], 'pilot_captures': summary['saved_content_records']})
    facets = {f['value']: f['count'] for f in first['facets']['availability']}
    check('Availability facets are distinct and exhaustive',
          facets == {'saved': pilot, 'archived': counts['linked_references'], 'links_only': 9348 - pilot - counts['linked_references']}
          and counts['references_with_pilot_capture'] == 0, facets)
    archived, page, seen = get_json('/api/sources?has=archived&limit=100'), 1, []
    total = archived['total']
    while True:
        seen.extend(archived['items'])
        if len(seen) >= total or not archived['items']: break
        page += 1; archived = get_json(f'/api/sources?has=archived&limit=100&page={page}')
    check('Saved-in-archive filter returns exactly the linked references',
          total == counts['linked_references'] and len(seen) == total and len({i['id'] for i in seen}) == total
          and all(i['has_archive_records'] and i['archive_record_count'] >= 1 for i in seen)
          and {i['url'] for i in seen} == set(links)
          and sum(i['archive_record_count'] for i in seen) == sum(counts['targets'].values()),
          {'total': total, 'target_sum': sum(i['archive_record_count'] for i in seen)})
    check('Pilot captures and link-only counts are unchanged by the new filter',
          get_json('/api/sources?has=saved&limit=1')['total'] == pilot
          and get_json('/api/sources?has=links_only&limit=1')['total'] == 9348 - pilot - counts['linked_references'])
    by_kind = {}
    for item in seen:
        for target in links[item['url']]['targets']:
            key = target['kind'] + ':' + target.get('dataset', target.get('collection', ''))
            by_kind.setdefault(key, item)
    # One detail page per representation class, with its files served safely.
    samples = {'focused': 'directory_record:focused', 'seeger': 'directory_record:seeger', 'federal': 'directory_record:federal'}
    for label, key in samples.items():
        item = by_kind.get(key)
        if not item:
            check(f'{label} sample present', False); continue
        detail = get_json(f'/api/source?id={item["id"]}')
        records = [r for r in detail['archive_records'] if r['kind'] == 'directory_record' and r['dataset'] == label]
        ok = bool(records) and detail['has_archive_records'] and detail['archive_record_count'] == len(detail['archive_records'])
        for record in records[:2]:
            ok = ok and not ({'original_path', 'text_path', 'raw_path'} & set(record)) and record['publication_label']
            if record['original_url']:
                status, headers, body = fetch(record['original_url'])
                ok = ok and status == 200 and len(body) > 0 and headers.get('X-Content-Type-Options') == 'nosniff' and 'sandbox' in headers.get('Content-Security-Policy', '')
            if record['text_url']:
                status, headers, body = fetch(record['text_url'])
                ok = ok and status == 200 and body.strip() != b'' and headers.get('Content-Type', '').startswith('text/plain')
        check(f'Detail page attaches {label} directory records with safely served files', ok,
              {'source': item['url'], 'records': len(records), 'sample_record': records[0]['record_id'] if records else None})
    retained_item = next((i for i in seen if any(t['kind'] == 'retained_capture' for t in links[i['url']]['targets'])), None)
    detail = get_json(f'/api/source?id={retained_item["id"]}')
    target = next(t for t in links[retained_item['url']]['targets'] if t['kind'] == 'retained_capture')
    record = next(r for r in detail['archive_records'] if r['kind'] == 'retained_capture')
    status, headers, body = fetch(record['original_url'])
    ok = status == 200 and hashlib.sha256(body).hexdigest() == target['raw_sha256'] and headers.get('X-Content-Type-Options') == 'nosniff' and 'sandbox' in headers.get('Content-Security-Policy', '')
    if record['text_url']:
        status, _, text = fetch(record['text_url'])
        ok = ok and status == 200 and hashlib.sha256(text).hexdigest() == target['text_sha256']
    check('Retained capture served with exact verified bytes and sandbox headers', ok,
          {'source': retained_item['url'], 'version_id': target['version_id'][:16], 'publication': record['publication']})
    redirect_item = next((i for i in seen if any(t.get('match_basis') == 'exact_final_url' for t in links[i['url']]['targets'])), None)
    if redirect_item:
        detail = get_json(f'/api/source?id={redirect_item["id"]}')
        check('Final-URL matches are labelled as redirect matches', any(r.get('match_basis') == 'exact_final_url' for r in detail['archive_records']), {'source': redirect_item['url']})
    judge_item = next((i for i in seen if any(t['kind'] == 'judge_entity' for t in links[i['url']]['targets'])), None)
    detail = get_json(f'/api/source?id={judge_item["id"]}')
    judges = [r for r in detail['archive_records'] if r['kind'] == 'judge_entity']
    profile = get_json(f'/api/judge?id={judges[0]["record_id"]}')
    check('Judge directory page links resolve to real judge profiles',
          len(judges) == sum(1 for t in links[judge_item['url']]['targets'] if t['kind'] == 'judge_entity') and profile['name'] == judges[0]['name']
          and all(j['profile_route'] == 'judge/' + j['record_id'] for j in judges) and not any(j['current_service_verified'] for j in judges),
          {'source': judge_item['url'], 'judges': len(judges), 'first': judges[0]['name']})
    for token in ('archive:does-not-exist/original', f'archive:{target["version_id"]}/other', f'archive:{target["version_id"]}/../original', '../RUNBOOK.md'):
        status, _, _ = fetch('/source-assets/' + token)
        check(f'Unknown asset fails closed: {token[:40]}', status == 404)
    unlinked = get_json('/api/sources?has=links_only&limit=1')['items'][0]
    detail = get_json(f'/api/source?id={unlinked["id"]}')
    check('Unlinked references carry no archive records and no absence claim',
          detail['archive_records'] == [] and detail['has_archive_records'] is False and 'absence' in summary['qualification'])
    published = get_json('/api/summary')['published']
    pilot_item = get_json('/api/sources?has=saved&limit=1')['items'][0]
    pilot_detail = get_json(f'/api/source?id={pilot_item["id"]}')
    status, _, _ = fetch(pilot_detail['captures'][0]['original_url'])
    check('Main corpus and pilot captures preserved', published['capture_records'] == 16454 and not published['full_corpus_complete'] and status == 200,
          {'capture_records': published['capture_records']})
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'status': 'passed' if all(c['passed'] for c in checks) else 'failed',
              'links_sha256': gate['links_sha256'], 'checks': checks, 'requests': requests}
    (HERE / 'live_verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'requests': len(requests)}))
    sys.exit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__': main()
