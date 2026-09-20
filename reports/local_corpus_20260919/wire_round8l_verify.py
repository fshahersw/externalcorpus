"""Round 8l: live checks for the round 8 layers. Idempotent."""
P = 'C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/verify_round2.py'
t = open(P, encoding='utf-8').read()
pairs = [
    ("('mdl-documents', 35000), ('mdl-activity', 26000), ('mdl-cases', 4000), ('mdl-appearances', 800), ('sd-statutes', 70)):",
     "('mdl-documents', 35000), ('mdl-activity', 26000), ('mdl-cases', 4000), ('mdl-appearances', 800), ('sd-statutes', 70),\n"
     "                          ('counsel-directory', 2000), ('verdict-reports', 3000), ('expert-rulings', 2000), ('cpsc-injury-data', 400000), ('source-documents', 900)):"),
    ("    status, _, body = fetch('/usmap.js')\n",
     "    for module in ('lawreader.js', 'regsui.js', 'judgeui.js', 'statsviz.js'):\n"
     "        status, _, body = fetch('/' + module)\n"
     "        check(f'Live {module} matches disk', status == 200 and body == (AD / module).read_bytes())\n"
     "    outline = get_json('/api/law-outline?state=California')\n"
     "    top = get_json('/api/law-outline/children?state=CA&kind=statutes&parent=0')\n"
     "    check('Law outline: California statutes open as 29 named codes', outline.get('available') and outline['collections'][0]['kind'] == 'statutes' and outline['collections'][0]['provisions'] > 150000\n"
     "          and len(top['nodes']) == 29 and any(n['label'] == 'Code of Civil Procedure (CCP)' for n in top['nodes']), {'provisions': outline['collections'][0]['provisions']})\n"
     "    ccp = next(n for n in top['nodes'] if n['label'].startswith('Code of Civil Procedure'))\n"
     "    sections = get_json(f\"/api/law-outline/provisions?node={ccp['id']}&limit=5\")\n"
     "    where = get_json('/api/law-outline/context?id=' + urllib.request.quote(sections['results'][1]['id'], safe=''))\n"
     "    check('Law outline: provisions list in citation order with previous and next', sections['total'] == ccp['direct'] and where.get('available') and where['position'] == 2\n"
     "          and where['previous']['id'] == sections['results'][0]['id'] and where['next']['id'] == sections['results'][2]['id'], {'first': sections['results'][0]['citation']})\n"
     "    check('Law outline refuses an unknown jurisdiction', get_json('/api/law-outline?state=Atlantis').get('available') is False)\n"
     "    hub = get_json('/api/agency-hub')\n"
     "    fda = get_json('/api/agency-hub/item?key=fda')\n"
     "    check('Agency overview joins the Federal Register, CFR, safety data, documents and addresses', len(hub) >= 15 and fda['counts']['federal_register_documents'] > 20000 and fda['counts']['safety_records'] > 200000 and fda.get('top_cfr_parts'), {'agencies': len(hub)})\n"
     "    verdicts = get_json('/api/area/verdict-reports?limit=50')\n"
     "    check('Verdict reports never print an individual plaintiff name in a caption', all(not r['title'].lower().startswith(('john ', 'jane ')) for r in verdicts['results']) and any(r['title'].startswith('Individual plaintiff') for r in verdicts['results']))\n"
     "    status, _, body = fetch('/usmap.js')\n"),
]
for old, new in pairs:
    if new in t:
        continue
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)
open(P, 'w', encoding='utf-8', newline='').write(t)
print('verifier extended')
