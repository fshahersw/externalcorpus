"""Exercise the live directory, exact bindings and every pilot attachment."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode, quote
from urllib.error import HTTPError
import datetime
import hashlib
import json
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8769'
checks, requests = [], []


def get(path, raw=False):
    started = time.perf_counter()
    with urlopen(BASE + path, timeout=45) as response:
        data, headers = response.read(), dict(response.headers)
        requests.append({'path': path, 'status': response.status, 'seconds': round(time.perf_counter()-started, 3)})
    return (data, headers) if raw else json.loads(data)


def check(name, condition, evidence=None):
    checks.append({'name': name, 'passed': bool(condition), 'evidence': evidence})


def main():
    for filename in ('app.js', 'styles.css', 'index.html'):
        data, _ = get('/'+filename, True)
        check('Live '+filename+' matches disk', data == (ROOT/'delivery/archive-directory'/filename).read_bytes())
    listing = get('/api/sources?limit=1')
    check('Full reconciled source map live', listing['ready'] and listing['total'] == 9348 and listing['summary']['unique_urls'] == 9348)
    check('Historical claims remain dated and qualified', listing['summary']['historical_verified_claims'] == 8349 and listing['summary']['source_as_of'] == '2026-08-19' and listing['summary']['freshly_verified'] == 0 and listing['summary']['draft'])
    api, bulk = get('/api/sources?access_method=api&limit=100'), get('/api/sources?api_bulk=1&limit=100')
    check('API and API/bulk references stay distinct', api['total'] == 16 and bulk['total'] == 62 and all(r['access_method'] == 'api' for r in api['items']))
    context=listing['summary']['api_context']
    check('API context counts are separate and qualified', context['ready'] and context['mapped_references']==109 and context['live_documentation_reviews']==9 and context['api_calls_performed']==0)
    refs = get('/api/sources?'+urlencode({'q':'https://docs.openstates.org/api-v3/','limit':1}))
    reviewed=get('/api/source?'+urlencode({'id':refs['items'][0]['id']}))
    reference=reviewed['api_reference']
    check('Reviewed access requirements appear on the exact source', reviewed['url']=='https://docs.openstates.org/api-v3/' and reference['access_requirements']['status']=='key_required' and reference['requirements_reviewed_at'] and reference['live_api_query_performed'] is False)
    name, code = get('/api/sources?jurisdiction=Texas&limit=1'), get('/api/sources?jurisdiction=tx&limit=1')
    check('State-name contextual links resolve', name['total'] == code['total'] and name['total'] > 0 and name['items'] == code['items'], {'Texas': name['total']})
    saved = get('/api/sources?has=saved&limit=100')
    unlinked = get('/api/sources?has=links_only&limit=1')
    manifest = [json.loads(line) for line in (ROOT/'sources/public_law_acquisition_20260919/resources.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    captures = {r['source_url']: r for r in manifest}
    check('Capture availability is exact and complete', saved['total'] == len(captures) and saved['summary']['saved_content_records'] == len(captures) and saved['total'] + unlinked['total'] == 9348 and {r['url'] for r in saved['items']} == set(captures) and all(r['has_saved_content'] for r in saved['items']) and not unlinked['items'][0]['has_saved_content'], {'saved_pages': saved['total'], 'unlinked_references': unlinked['total']})
    all_assets, source_bindings = [], []
    for row in saved['items']:
        detail = get('/api/source?'+urlencode({'id': row['id']}))
        item = captures[row['url']]
        attached = detail['captures']
        source_bindings.append(len(attached) == 1 and attached[0]['publisher_url'] == row['url'] and detail['source_record'] and detail['observations'])
        for field, digest in [('original_url', item['raw_sha256']), ('text_url', item['text_sha256'])]:
            data, headers = get(attached[0][field], True)
            valid = hashlib.sha256(data).hexdigest() == digest and headers.get('X-Content-Type-Options') == 'nosniff'
            if field == 'original_url' and item['mime_type'] == 'text/html':
                valid = valid and headers.get('Content-Type') == 'application/octet-stream' and 'attachment' in headers.get('Content-Disposition', '') and 'sandbox' in headers.get('Content-Security-Policy','')
            if field == 'text_url': valid = valid and bool(data.decode('utf-8').strip()) and headers.get('Content-Type','').startswith('text/plain')
            all_assets.append(valid)
    check('Every saved source binds original entry and observations', all(source_bindings) and len(source_bindings) == len(captures))
    check('Every original and cleaned text served with exact bytes and safe headers', all(all_assets) and len(all_assets) == 2*len(captures), {'assets': len(all_assets)})
    for bad in ('/source-assets/../RUNBOOK.md', '/source-assets/missing/original', '/api/source?id=does-not-exist'):
        try: get(bad); valid=False
        except HTTPError as error: valid=error.code == 404
        check('Unknown path fails closed: '+bad, valid)
    baseline = get('/api/summary')
    judges = get('/api/judges?has=photo&limit=1')
    counties = get('/api/counties?availability=court_registry&limit=1')
    check('Main corpus, portraits and county registry preserved', baseline['published']['capture_records'] == 16454 and baseline['enrichment']['open_us_law']['records'] == 2978617 and judges['total'] == 43 and counties['total'] == 374)
    output = {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'passed' if all(r['passed'] for r in checks) else 'failed', 'checks': checks, 'requests': requests}
    (OUT/'live_verification.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps({'status': output['status'], 'checks': len(checks), 'requests': len(requests), 'failed': [r['name'] for r in checks if not r['passed']]}))
    if output['status'] != 'passed': raise SystemExit(1)


if __name__ == '__main__': main()
