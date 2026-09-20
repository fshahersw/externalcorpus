"""Live checks for the corpus-upgrade scaffolding: static assets, supplements route, filters, record deep link."""
import gzip
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
AD = ROOT / 'delivery/archive-directory'
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
    print(('PASS ' if passed else 'FAIL ') + name + (f' {json.dumps(evidence)[:300]}' if evidence else ''))


def main():
    for name in ('app.js', 'areas.js', 'styles.css', 'index.html'):
        status, headers, body = fetch('/' + name)
        check(f'Live {name} matches disk', status == 200 and body == (AD / name).read_bytes() and headers.get('X-Content-Type-Options') == 'nosniff')
    index = (AD / 'index.html').read_text(encoding='utf-8')
    check('index.html loads areas.js after app.js and lists the research areas', index.index('app.js') < index.index('areas.js') and 'data-view="mdls"' in index and 'data-view="coverage"' in index)
    supp = get_json('/api/supplements')
    check('Supplements route reports readiness honestly', supp['total'] >= 10 and 0 < supp['ready'] <= supp['total'] and 'legal currency' in supp['qualification']
          and all(set(i) >= {'name', 'envelope', 'ready', 'status', 'data_files', 'issues'} for i in supp['items'])
          and not any('C:\\' in json.dumps(i) or 'C:/' in json.dumps(i) for i in supp['items']), {'total': supp['total'], 'ready': supp['ready']})
    doj = get_json('/api/supplements?name=doj_state_resource_map_20260919')
    check('Uniform envelope is hash-verified live', doj['envelope'] == 'uniform' and doj['ready'] and all(f['verified'] for f in doj['data_files']), {'files': len(doj['data_files'])})
    status, _, _ = fetch('/api/supplements?name=../secret')
    check('Supplement lookup rejects traversal', status == 404)
    src = get_json('/api/sources?limit=1&task_family=complex-litigation')
    facets = src['facets']
    check('Source directory type filters and facets are live', src['total'] == 68 and all(k in facets for k in ('layers', 'task_families', 'content_kinds', 'source_types', 'access_requirements'))
          and sum(f['count'] for f in facets['content_kinds']) == 9348, {'complex_litigation': src['total']})
    check('Combined type filters intersect', 0 < get_json('/api/sources?limit=1&content_kind=pdf&source_type=official')['total'] < 1676)
    check('Archive links still live', get_json('/api/sources?limit=1&has=archived')['total'] == 554)
    docs = get_json('/api/documents?group=laws&q=due%20process&limit=1')
    record = get_json(f'/api/record?id={docs["items"][0]["id"]}')
    check('Record detail exposes saved_at with its evidence field (retrieved_at accepted)', record.get('saved_at') is not None or record.get('date_evidence', {}).get('saved_at_field') in (None, 'captured_at', 'retrieved_at'),
          {'saved_at': record.get('saved_at'), 'field': record.get('date_evidence', {}).get('saved_at_field')})
    focused = get_json('/api/documents?group=laws&dataset=focused&limit=5')
    dated = 0
    for item in focused['items'][:5]:
        detail = get_json(f'/api/record?id={item["id"]}')
        if detail.get('saved_at') and detail.get('date_evidence', {}).get('saved_at_field') == 'retrieved_at': dated += 1
    check('Focused records now carry a saved date from retrieved_at', dated >= 1, {'sampled': min(5, len(focused['items'])), 'dated_via_retrieved_at': dated})
    published = get_json('/api/summary')['published']
    check('Main corpus untouched', published['capture_records'] == 16454 and not published['full_corpus_complete'])
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'status': 'passed' if all(c['passed'] for c in checks) else 'failed', 'checks': checks, 'requests': requests}
    (HERE / 'scaffold_verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'requests': len(requests)}))
    sys.exit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__': main()
