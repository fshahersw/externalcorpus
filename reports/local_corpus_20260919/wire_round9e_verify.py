"""Round 9e: the live verifier gains the checks for the open-source enrichment layers (one verifier, not two). Idempotent."""
P = 'C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/verify_round2.py'
t = open(P, encoding='utf-8').read()
anchor = "    status, _, body = fetch('/usmap.js')\n"
block = (
    "    # --- round 9: open-source enrichment layers ---\n"
    "    for area, minimum in (('citation-guide', 2400), ('limitation-periods', 459), ('citation-index', 50000)):\n"
    "        listing = get_json(f'/api/area/{area}?limit=2')\n"
    "        detail = get_json(f'/api/area/{area}/item?id=' + urllib.request.quote(listing['results'][0]['id'], safe=''))\n"
    "        check(f'Generic area {area}: listing, filters, detail', listing['available'] and listing['total'] >= minimum and listing['filters'] and detail.get('title') and detail.get('facts'), {'total': listing['total']})\n"
    "    court = get_json('/api/area/courts/item?id=njd')\n"
    "    check('Court registry detail carries the citation abbreviation and the seal by court id', any(f[0] == 'Cited as' and f[1] == 'D.N.J.' for f in court['facts']) and court['sections'][0]['heading'] == 'Court seal')\n"
    "    status, headers, body = fetch('/supplement-files/court_reference/njd')\n"
    "    check('Court seal served as a PNG that matches its recorded hash', status == 200 and body[:4] == b'\\x89PNG', {'bytes': len(body)})\n"
    "    resolved = get_json('/api/court-resolve?q=' + urllib.request.quote('United States District Court for the Southern District of Texas'))\n"
    "    check('Court name resolver names S.D. Tex. for a district-court caption', resolved['available'] and [r['id'] for r in resolved['results']] == ['txsd'])\n"
    "    cardozo = [p for p in get_json('/api/people?q=Cardozo&limit=5')['items'] if p.get('photo_url')]\n"
    "    status, headers, body = fetch(cardozo[0]['photo_url']) if cardozo else (0, {}, b'')\n"
    "    check('Biography portrait attached by CourtListener person id and served as JPEG', bool(cardozo) and status == 200 and body[:2] == b'\\xff\\xd8' and 'Free Law Project' in get_json('/api/person?id=' + str(cardozo[0]['id'])).get('photo_credit', ''))\n"
    "    louisiana = (get_json('/api/blocks?state=LA').get('limitation_periods') or {}).get('rows') or []\n"
    "    check('Limitation periods: Louisiana personal injury shows the saved statute disagreeing with the published table', len(louisiana) == 9 and any(r['outcome'] == 'different_wording_found' and r['record_id'] for r in louisiana))\n"
    "    check('Law outline states that Georgia statutes were withdrawn by the publisher', (get_json('/api/law-outline?state=Georgia').get('statute_audit') or {}).get('verdict') == 'withdrawn')\n"
    "    cited = get_json('/api/area/citation-index?q=' + urllib.request.quote('18 U.S.C. 1956') + '&limit=1')['results'][0]\n"
    "    record_id = cited['links'][0]['url'].split('#record/')[1]\n"
    "    back = get_json('/api/citations/record?id=' + urllib.request.quote(record_id))\n"
    "    check('Citation index: a U.S.C. citation opens the saved section and the section lists the documents citing it', cited['cells']['where'] == 'Saved law text' and back['total'] >= 100 and back['results'], {'documents': back['total']})\n"
    "    check('Citation index counts no lab-report strings as cases', get_json('/api/area/citation-index?q=14CO2&limit=1')['total'] == 0)\n"
)
if '# --- round 9: open-source enrichment layers ---' not in t:
    assert t.count(anchor) == 1
    t = t.replace(anchor, block + anchor)
    open(P, 'w', encoding='utf-8', newline='').write(t)
print('verifier extended for round 9')
