"""Verify the live judge addition without rebuilding the main document catalog."""
from pathlib import Path
from urllib.request import urlopen
import datetime, hashlib, json

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8769'

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))

def lines(path):
    return [json.loads(s) for s in (ROOT / path).read_text(encoding='utf-8-sig').splitlines() if s.strip()]

def get(path, raw=False):
    with urlopen(BASE + path, timeout=30) as response:
        assert response.status == 200
        body = response.read()
    return body if raw else json.loads(body)

def main():
    checks = []
    def check(name, ok, evidence=None):
        checks.append(dict(name=name, passed=bool(ok), evidence=evidence))

    for name in ['app.js', 'styles.css', 'index.html']:
        body = get('/'+name, True)
        check('Live asset matches disk: '+name, body == (ROOT/'delivery/archive-directory'/name).read_bytes(), hashlib.sha256(body).hexdigest())
    profiles = lines('sources/pa_judge_portraits_20260919/official_profiles.jsonl')
    image_rows = lines('sources/pa_judge_portraits_20260919/images.jsonl')
    old_images = lines('sources/judge_presentation_20260918/portraits.jsonl')
    summary = read('sources/judge_presentation_20260918/summary.json')
    all_profiles = get('/api/judges?has=all&limit=1')
    photo_profiles = get('/api/judges?has=photo&limit=60')
    check('Combined browse count is 10669 entities plus 29 source profiles', all_profiles['total'] == 10698, all_profiles['total'])
    check('Existing entity bytes unchanged', summary['source_entities_sha256'] == hashlib.sha256((ROOT/'sources/judge_entities_20260918/entities.jsonl').read_bytes()).hexdigest())
    check('No identity merges added', summary['identity_merges_added'] == 0)
    check('Live photo count reconciles', photo_profiles['total'] == len(old_images) + len(image_rows) == summary['profiles_with_photos'], photo_profiles['total'])
    pa = [x for x in photo_profiles['items'] if x.get('profile_layer') == 'official_source']
    expected = {x['source_profile_id']:x for x in profiles}
    image_by_hash = {x['sha256']:x for x in old_images + image_rows}
    delivered = []
    for item in photo_profiles['items']:
        body = get(item['photo_url'], True)
        digest = hashlib.sha256(body).hexdigest()
        image_row = image_by_hash.get(digest)
        ok = bool(image_row) and body == (ROOT/image_row['path']).read_bytes()
        delivered.append({'name':item['name'], 'sha256':digest, 'bytes':len(body), 'passed':ok})
    check('Every portrait endpoint delivers its verified local bytes', all(x['passed'] for x in delivered), delivered)
    verified = []
    for item in pa:
        source = expected[item['source_profile_id']]
        detail = get('/api/judge?id='+item['id'])
        ok = (detail['name'] == source['name'] and detail.get('entity_id') is None
              and detail.get('profile_layer') == 'official_source'
              and not detail.get('record_id') and not detail.get('provenance_url')
              and detail['profile_heading_as_published'] == source['profile_heading_as_published']
              and detail['term_as_published'] == source['term_as_published']
              and detail.get('current_service_verified') is False)
        verified.append({'name':item['name'], 'id':item['id'], 'passed':ok})
    check('Official profiles retain source identity and saved dates', len(verified) == len(image_rows) and all(x['passed'] for x in verified), verified)
    people = get('/api/people?limit=1')
    check('Separate biography collection remains live', people['ready'] is True and people['total'] == 15797)
    county = get('/api/counties?limit=1')
    check('County inventory preserved', county['total'] == 3144)
    live = get('/api/summary')
    check('Main publication unchanged', live['published']['capture_records'] == 16454 and live['published']['searchable_texts'] == 15837)
    check('Bulk law reader remains ready', live['enrichment']['open_us_law']['ready'] is True and live['enrichment']['open_us_law']['records'] == 2978617)
    trellis = get('/api/documents?dataset=trellis_browser_counties&view=sources&limit=10')
    check('Trellis integration wording reflects live state', trellis['total'] == 6 and all('awaiting directory integration' not in (x.get('quality') or '') for x in trellis['items']))
    report = {'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status':'passed' if all(x['passed'] for x in checks) else 'failed', 'checks':checks}
    (OUT/'deployment_verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status':report['status'], 'checks':len(checks), 'profiles':all_profiles['total'], 'photos':photo_profiles['total'], 'failed':[x['name'] for x in checks if not x['passed']]}))
    if report['status'] != 'passed': raise SystemExit(1)

if __name__ == '__main__': main()
