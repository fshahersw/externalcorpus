"""Live checks for the corpus-upgrade integration: facets in the document listing, research areas, sidebar gating."""
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
AD = ROOT / 'delivery/archive-directory'
checks, requests = [], []


def fetch(path):
    started = time.perf_counter()
    try:
        response = urllib.request.urlopen(urllib.request.Request(BASE + path, headers={'Accept-Encoding': 'gzip'}), timeout=120)
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
    print(('PASS ' if passed else 'FAIL ') + name + (f' {json.dumps(evidence)[:260]}' if evidence else ''))


def main():
    for name in ('app.js', 'areas.js', 'styles.css', 'index.html'):
        status, _, body = fetch('/' + name)
        check(f'Live {name} matches disk', status == 200 and body == (AD / name).read_bytes())
    index = (AD / 'index.html').read_text(encoding='utf-8')
    check('Sidebar is three hubs with an in-page tab bar; Library hub retired', index.count('data-hub=') == 3 and 'data-hub="library"' not in index and 'id="hub-tabs"' in index)
    rodgers = get_json('/api/judges?has=all&limit=2&q=Casey%20Rodgers')
    check('Alias search finds Judge Rodgers and her MDLs are linked by native id', rodgers['total'] == 1 and rodgers['items'][0]['entity_id'] == 'judge-entity-24222174cb13b7162bfcfcbc'
          and {m['mdl_number'] for m in get_json('/api/judge?id=judge-entity-24222174cb13b7162bfcfcbc')['mdls']['results']} >= {2885, 3140})
    for area, minimum in (('settlements', 800), ('courts', 5000), ('counsel', 2000), ('urls', 400000), ('uscourts', 1400), ('federal-register', 1000000),
                          ('court-documents', 50000), ('state-proceedings', 1400), ('judge-disclosures', 20000), ('agency-documents', 900), ('saved-pages', 15000), ('indiana-code', 80000), ('public-laws', 2000), ('state-codes', 2),
                          ('mdl-documents', 35000), ('mdl-activity', 26000), ('mdl-cases', 4000), ('mdl-appearances', 800), ('sd-statutes', 70),
                          ('counsel-directory', 2000), ('verdict-reports', 3000), ('expert-rulings', 2000), ('cpsc-injury-data', 400000), ('source-documents', 900)):
        listing = get_json(f'/api/area/{area}?limit=2')
        detail = get_json(f'/api/area/{area}/item?id=' + urllib.request.quote(listing['results'][0]['id'], safe=''))
        check(f'Generic area {area}: listing, filters, detail', listing['available'] and listing['total'] >= minimum and listing['filters'] and listing['columns'] and detail.get('title') and detail.get('facts'), {'total': listing['total']})
    harris = get_json('/api/county-filing?fips=48201')
    check('County page carries official rules, forms and filing sources', harris.get('available') and harris['coverage_level'] == 'rules_and_filing' and any(i['kind'] == 'local_rules' for g in harris['groups'] for i in g['items']), {'groups': [g['scope_label'] for g in harris.get('groups', [])][:4]})
    filing = get_json('/api/county-filing/coverage')
    check('County filing coverage: at least 80% of counties have a rules source plus a filing source', filing.get('available') and filing['counts']['percent_with_rules_any_scope_and_filing'] >= 80 and filing['counts']['counties'] == 3144,
          {k: filing['counts'].get(k) for k in ('percent_with_any', 'percent_with_rules_any_scope_and_filing', 'percent_with_local_rules')})
    status, _, body = fetch('/assets/us-counties-albers-10m.json')
    geometry = json.loads(body) if status == 200 else {}
    check('Map geometry served: 51 states and 3,142 counties', status == 200 and len(geometry.get('objects', {}).get('states', {}).get('geometries', [])) == 51 and len(geometry['objects']['counties']['geometries']) == 3142)
    for module in ('lawreader.js', 'regsui.js', 'judgeui.js', 'statsviz.js'):
        status, _, body = fetch('/' + module)
        check(f'Live {module} matches disk', status == 200 and body == (AD / module).read_bytes())
    outline = get_json('/api/law-outline?state=California')
    top = get_json('/api/law-outline/children?state=CA&kind=statutes&parent=0')
    check('Law outline: California statutes open as 29 named codes', outline.get('available') and outline['collections'][0]['kind'] == 'statutes' and outline['collections'][0]['provisions'] > 150000
          and len(top['nodes']) == 29 and any(n['label'] == 'Code of Civil Procedure (CCP)' for n in top['nodes']), {'provisions': outline['collections'][0]['provisions']})
    ccp = next(n for n in top['nodes'] if n['label'].startswith('Code of Civil Procedure'))
    sections = get_json(f"/api/law-outline/provisions?node={ccp['id']}&limit=5")
    where = get_json('/api/law-outline/context?id=' + urllib.request.quote(sections['results'][1]['id'], safe=''))
    check('Law outline: provisions list in citation order with previous and next', sections['total'] == ccp['direct'] and where.get('available') and where['position'] == 2
          and where['previous']['id'] == sections['results'][0]['id'] and where['next']['id'] == sections['results'][2]['id'], {'first': sections['results'][0]['citation']})
    check('Law outline refuses an unknown jurisdiction', get_json('/api/law-outline?state=Atlantis').get('available') is False)
    hub = get_json('/api/agency-hub')
    fda = get_json('/api/agency-hub/item?key=fda')
    check('Agency overview joins the Federal Register, CFR, safety data, documents and addresses', len(hub) >= 15 and fda['counts']['federal_register_documents'] > 20000 and fda['counts']['safety_records'] > 200000 and fda.get('top_cfr_parts'), {'agencies': len(hub)})
    verdicts = get_json('/api/area/verdict-reports?limit=50')
    check('Verdict reports never print an individual plaintiff name in a caption', all(not r['title'].lower().startswith(('john ', 'jane ')) for r in verdicts['results']) and any(r['title'].startswith('Individual plaintiff') for r in verdicts['results']))
    # --- round 9: open-source enrichment layers ---
    for area, minimum in (('citation-guide', 2400), ('limitation-periods', 459), ('citation-index', 50000)):
        listing = get_json(f'/api/area/{area}?limit=2')
        detail = get_json(f'/api/area/{area}/item?id=' + urllib.request.quote(listing['results'][0]['id'], safe=''))
        check(f'Generic area {area}: listing, filters, detail', listing['available'] and listing['total'] >= minimum and listing['filters'] and detail.get('title') and detail.get('facts'), {'total': listing['total']})
    court = get_json('/api/area/courts/item?id=njd')
    check('Court registry detail carries the citation abbreviation and the seal by court id', any(f[0] == 'Cited as' and f[1] == 'D.N.J.' for f in court['facts']) and court['sections'][0]['heading'] == 'Court seal')
    status, headers, body = fetch('/supplement-files/court_reference/njd')
    check('Court seal served as a PNG that matches its recorded hash', status == 200 and body[:4] == b'\x89PNG', {'bytes': len(body)})
    resolved = get_json('/api/court-resolve?q=' + urllib.request.quote('United States District Court for the Southern District of Texas'))
    check('Court name resolver names S.D. Tex. for a district-court caption', resolved['available'] and [r['id'] for r in resolved['results']] == ['txsd'])
    cardozo = [p for p in get_json('/api/people?q=Cardozo&limit=5')['items'] if p.get('photo_url')]
    status, headers, body = fetch(cardozo[0]['photo_url']) if cardozo else (0, {}, b'')
    check('Biography portrait attached by CourtListener person id and served as JPEG', bool(cardozo) and status == 200 and body[:2] == b'\xff\xd8' and 'Free Law Project' in get_json('/api/person?id=' + str(cardozo[0]['id'])).get('photo_credit', ''))
    louisiana = (get_json('/api/blocks?state=LA').get('limitation_periods') or {}).get('rows') or []
    check('Limitation periods: Louisiana personal injury shows the saved statute disagreeing with the published table', len(louisiana) == 9 and any(r['outcome'] == 'different_wording_found' and r['record_id'] for r in louisiana))
    check('Law outline states that Georgia statutes were withdrawn by the publisher', (get_json('/api/law-outline?state=Georgia').get('statute_audit') or {}).get('verdict') == 'withdrawn')
    cited = get_json('/api/area/citation-index?q=' + urllib.request.quote('18 U.S.C. 1956') + '&limit=1')['results'][0]
    record_id = cited['links'][0]['url'].split('#record/')[1]
    back = get_json('/api/citations/record?id=' + urllib.request.quote(record_id))
    check('Citation index: a U.S.C. citation opens the saved section and the section lists the documents citing it', cited['cells']['where'] == 'Saved law text' and back['total'] >= 100 and back['results'], {'documents': back['total']})
    check('Citation index counts no lab-report strings as cases', get_json('/api/area/citation-index?q=14CO2&limit=1')['total'] == 0)
    status, _, body = fetch('/usmap.js')
    check('Live usmap.js matches disk', status == 200 and body == (AD / 'usmap.js').read_bytes())
    codes = get_json('/api/area/state-codes?state=IN&q=34-20-2-1')
    check('State codes are one collection with a state filter (Indiana citation search)', codes['available'] and codes['total'] == 1 and codes['results'][0]['id'].startswith('IN:'))
    blocks = get_json('/api/blocks?state=NJ')
    check('State page blocks: NJ mass-tort proceedings and saved court documents', (blocks.get('state_proceedings') or {}).get('total') == 40 and (blocks.get('court_documents') or {}).get('total', 0) > 0)
    check('URL directory block for a state', (get_json('/api/urls/block?state=CA')['block'] or {}).get('total', 0) > 10000)
    fr = get_json('/api/regulation?citation=21%20CFR%20314.80').get('fr_history') or {}
    check('Regulation page carries the Federal Register history of its CFR part', fr.get('total', 0) >= 100 and fr.get('first_date', '') < '1995', {'documents': fr.get('total')})
    rodgers_profile = get_json('/api/judge?id=judge-entity-24222174cb13b7162bfcfcbc')
    check('Judge profile carries financial disclosure filings by native person id', (rodgers_profile.get('disclosures') or {}).get('state') == 'filing_with_reportable_holdings')
    check('MDL page names related state proceedings only where the state registry names the MDL', (get_json('/api/mdl?number=2738').get('state_proceedings') or {}).get('total') == 1)
    judges = get_json('/api/judges?role=district&status=active&has=all&limit=1')
    check('Judge evidence filters (FJC status + role) work', judges['total'] == 648 and len(judges['structured_facets']['status']) == 4, {'active_district': judges['total']})
    overlay = get_json('/api/judge?id=judge-entity-85b06ec4ad087308b3f7d0f4').get('structured') or {}
    check('Judge profile carries the structured overlay with a dated FJC status', (overlay.get('fjc') or {}).get('fjc_status', {}).get('as_of') or (overlay.get('fjc_status') or {}).get('as_of'))
    supp = get_json('/api/supplements')
    ready = {i['name'] for i in supp['items'] if i['ready']}
    check('Published supplements verified live', {'record_facets_20260919', 'jpml_mdl_20260919', 'federal_regulations_20260919', 'agency_safety_20260919', 'law_tier_20260919', 'doj_state_resource_map_20260919'} <= ready, {'ready': sorted(n for n in ready if n.endswith('20260919'))})
    docs = get_json('/api/documents?group=all&category=statutes&limit=1&view=sources')
    check('Derived categories drive the document listing', docs['facets_ready'] and docs['source_total'] > 12000 and 'file_type' in docs['facet_options'], {'statutes_source_total': docs['source_total']})
    other = get_json('/api/documents?group=all&category=other&record_type=other&validity=any&limit=1&view=sources')
    check('"Other" no longer swallows reviewed statutes and rules', other['source_total'] < 100, {'other_local': other['source_total']})
    pdf = get_json('/api/documents?group=all&file_type=pdf&review=needs_content_review&limit=3&view=sources')
    check('File-type and review filters work and items carry facets', pdf['total'] > 0 and all(i['facets']['file_type'] == 'pdf' and i['facets']['review_state'] == 'needs_content_review' for i in pdf['items']), {'total': pdf['total']})
    dated = get_json('/api/documents?group=laws&date_type=saved&dfrom=2026-09-13&dto=2026-09-13&undated=0&limit=2&view=sources')
    check('Saved-date range filter works', dated['total'] > 0 and all((i['facets']['dates']['saved_at'] or '').startswith('2026-09-13') for i in dated['items']), {'total': dated['total']})
    parked = get_json('/api/documents?group=counties&validity=parked_redirect&limit=1&view=sources')
    default = get_json('/api/documents?group=counties&limit=1&view=sources')
    every = get_json('/api/documents?group=counties&validity=any&limit=1&view=sources')
    check('Parked/shell captures hidden by default but reachable', parked['total'] > 0 and default['source_total'] < every['source_total'], {'parked': parked['total'], 'default': default['source_total'], 'all': every['source_total']})
    federal = get_json('/api/documents?group=federal&dataset=federal&view=sources&limit=1')
    check('Link-only federal resources still listed', federal['total'] == 591)
    record = get_json('/api/documents?group=laws&q=due%20process&limit=1')['items'][0]
    detail = get_json(f'/api/record?id={record["id"]}')
    check('Record detail carries facets with title basis and derived category', bool(detail.get('facets')) and detail['facets']['derived_category'] == detail['category'] and detail['facets'].get('display_title'))
    hub = get_json('/api/explore?group=laws&state=Pennsylvania')
    q = get_json('/api/documents?group=laws&state=Pennsylvania&category=rules&limit=1')
    check('Explore hub and listing agree on derived categories', next(r for r in hub['categories'] if r['id'] == 'rules')['total'] == q['total'], {'rules_total': q['total']})
    mdls = get_json('/api/mdls?litigation_type=Products%20Liability&limit=3')
    check('MDL registry lists products-liability MDLs as of the JPML report', mdls['available'] and mdls['total'] >= 60 and mdls['as_of'] == '2026-09-01', {'total': mdls['total']})
    m = get_json('/api/mdl?number=3080')
    check('MDL 3080 detail with judge link, snapshots and documents', m['mdl_number'] == 3080 and m['judge_links'] and len(m['snapshots']) >= 3 and m['documents'], {'judge': m['transferee_judge']['name_as_printed'], 'pending': m['actions_pending']})
    judge_id = m['judge_links'][0]['entity_id']
    profile = get_json(f'/api/judge?id={judge_id}')
    check('Judge profile exposes MDL assignments', profile.get('mdls', {}).get('total', 0) >= 1 and any(r['mdl_number'] == 3080 for r in profile['mdls']['results']), {'judge': profile.get('name')})
    doc = m['documents'][0]
    status, headers, body = fetch('/mdl-files/' + (doc.get('id') or doc.get('document_id')))
    check('JPML original served as verified bytes', status == 200 and headers.get('Content-Security-Policy', '').endswith('sandbox') and (not doc.get('sha256') or hashlib.sha256(body).hexdigest() == doc['sha256']), {'bytes': len(body)})
    for bad in ('/api/mdl?number=999999', '/mdl-files/../x', '/api/regulation?citation=garbage', '/api/coverage/state?state=ZZ'):
        status, _, _ = fetch(bad)
        check(f'Bad input rejected: {bad}', status == 404)
    titles = get_json('/api/regulations/titles')
    section = get_json('/api/regulation?citation=21%20CFR%20314.80')
    check('Regulations: titles and a section with two hash-verified texts', titles['total'] == 4 and len(section['texts']) == 2 and all(t.get('text_hash_verified') for t in section['texts'] if t.get('text')), {'section': section['citation']})
    info = get_json('/api/regulations/info')
    check('Regulations info date types are a map (page handles it)', isinstance(info['date_types'], dict) and 'fr_publication_date' in info['date_types'])
    check('Agencies, coverage and DOJ resources still live', get_json('/api/agency/datasets')['status']['records'] == 243682 and len(get_json('/api/coverage/matrix')['rows']) == 56 and get_json('/api/resources/states')['total'] == 56)
    published = get_json('/api/summary')['published']
    check('Main corpus untouched', published['capture_records'] == 16454 and not published['full_corpus_complete'])
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'status': 'passed' if all(c['passed'] for c in checks) else 'failed', 'checks': checks, 'requests': requests}
    (HERE / 'round2_verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'requests': len(requests)}))
    sys.exit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__': main()
