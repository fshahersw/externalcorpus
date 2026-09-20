"""Build the bounded settlement capture packet.

Read-only on project data (SQLite opened mode=ro). Network use: exactly one robots.txt GET per host,
no retries, 8 workers, 12 s timeout, User-Agent LegalCorpusResearch/1.0. Writes only:
  packets/settlement_urls.jsonl, packets/settlement_robots_check.json
"""
import collections, datetime, hashlib, json, re, sqlite3, ssl, urllib.error, urllib.request, urllib.robotparser
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

UA = 'LegalCorpusResearch/1.0'
OUT = 'C:/Users/firas/Downloads/SCRAPE/reports/corpus_upgrade_20260919/understand/packets/'
CAT = 'C:/Users/firas/Downloads/Court-Document-Library/07-Settlement-References/catalog/catalog.json'
PLD = 'C:/Users/firas/Downloads/SCRAPE/sources/public_law_directory_20260919/catalog.json'
DBS = [('C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/directory.sqlite3', 'records'),
       ('C:/Users/firas/Downloads/SCRAPE/catalog/documents.sqlite3', 'versions')]

P = 'class_action_product'
G = 'government_enforcement_refund'
A = 'class_action_antitrust'
M = 'mdl_class_settlement'
CATALOG_PICKS = {
 'a5c5bf': ('mdl_global_settlement', 'NFL concussion program; MDL/court metadata to be confirmed from captured documents'),
 '320d3a': (M, 'JUUL class settlement'), '9af8ef': (M, 'sartan economic-loss settlement'),
 'e23b1f': ('class_action', 'metformin'), 'dae14e': (M, 'generic drugs end-payer; previously reviewed; one order PDF already saved'),
 '6cfbc5': (A, 'Tracleer'), '5237ba': (A, 'QVAR'),
 'e2858b': (A, 'pork; previously reviewed; prior PDF request returned 403 - page only, do not retry documents'),
 '6ca8e1': (A, 'beef'), 'cd7e3d': (A, 'Deere repair'), '7b6b58': (A, 'RealPage'), 'e1c8a9': (A, 'homebuyer commissions'),
 '1e447d': (A, 'NCAA volunteer coach'), '2508b9': (M, 'Hyundai/Kia ACU'), '4e58ed': (M, 'Toyota ACU'), '43f10f': (M, 'Hyundai/Kia theft'),
 '664744': (P, ''), '1ddba0': (P, ''), '06e635': (P, ''), 'e6f173': (P, ''), '751f39': (P, ''),
 '0ec324': ('bankruptcy_trust', 'Zonolite attic insulation (ZAI) program; trust status to be confirmed from captured page'),
 '5920ab': (P, ''), '1af58a': (P, ''), '6c6cd0': (P, ''), 'a8c59b': (P, ''), '63496c': (P, ''), 'f943f1': (P, ''),
 'b377fd': (P, ''), '50c970': (P, ''), 'ec855b': (P, ''), 'df75ea': (P, ''), 'af40d9': ('class_action_medical', ''),
 'c3f004': ('class_action_environmental', ''), '370fdd': ('class_action_environmental', ''), '44896e': ('class_action', ''),
 'c25718': (P, ''), '0f785f': (P, ''), '4e47c0': (P, ''), '4e9b6f': (P, ''), '470036': (P, ''), '32fe30': (P, ''),
 'c4c650': (P, ''), 'fd75c7': (P, ''), 'c29a6c': (P, ''), 'b73558': (P, ''),
 '268c8a': ('class_action', 'previously reviewed; class notice PDF already saved'),
 'c0cc43': ('class_action_data_breach', 'previously reviewed; notice + claim form PDFs already saved from cw.simpluris.com'),
 '4542ed': ('class_action_wage', 'previously reviewed; prior PDF request returned 403 - page only'),
 '72d1a1': ('class_action_privacy', 'previously reviewed; prior PDF request returned 403 - page only'),
 '416115': (G, 'previously reviewed; administrator order previously failed TLS - page only'),
 '981aed': (G, ''), '6ce615': (G, ''), '6c4ced': (G, ''), 'c73687': (G, ''), 'a1a93d': (G, ''),
 '1920d2': (G, ''), '154480': (G, ''), '141d6b': (G, ''), 'b50fbb': (G, ''),
 'c5ce31': (G, 'SEC fair fund'), 'dda4bc': (G, 'SEC fair fund'), '84f1e6': (G, 'SEC fair fund list'),
 'c2c7f5': ('state_ag_settlement', ''), '15e0ba': ('government_refund_program', ''),
}
HELD_CATALOG = {'b45016': 'AmTrust: prior review preserved reference-use/AI-training reservation signals; excluded',
                'be4026': 'Heckathorn/Farmers: prior attempts ended in TLS/connection resets; excluded from first packet',
                '2b87f2': 'Prestige Feed: official URL is a law-firm site, not an administrator/court/government host'}

PLD_PICKS = {
 'https://www.ftc.gov/enforcement/refunds': 'government_enforcement_refund_index',
 'https://www.ftc.gov/enforcement/recent-ftc-cases-resulting-refunds/how-ftc-provides-refunds': 'government_enforcement_refund_index',
 'https://www.naag.org/news-resources/research-data/multistate-settlements-database/': 'state_ag_multistate_index',
 'https://www.naag.org/issues/antitrust/state-antitrust-litigation-and-settlement-database/': 'state_ag_multistate_index',
 'https://epa.gov/enforcement/cases-and-settlements': 'government_enforcement_index',
 'https://epa.gov/enforcement/civil-and-cleanup-enforcement-cases-and-settlements': 'government_enforcement_index',
 'https://www.jpml.uscourts.gov/pending-mdls-0': 'mdl_index',
 'https://www.jpml.uscourts.gov/panel-orders': 'mdl_index',
 'https://www.jpml.uscourts.gov/pending-mdl-reports-archive': 'mdl_index',
 'https://www.jpml.uscourts.gov/sites/jpml/files/Pending_MDL_Dockets_By_District-August-3-2026.pdf': 'mdl_index',
 'https://www.hrsa.gov/vaccine-compensation': 'government_compensation_program',
 'https://www.hrsa.gov/vaccine-compensation/data': 'government_compensation_program',
}

KNOWLEDGE = [
 ('https://www.pfaswatersettlement.com/', 'PFAS public water system settlements (3M, DuPont) - AFFF MDL 2873, D.S.C.', 'mdl_global_settlement'),
 ('https://nationalopioidsettlement.com/', 'National opioid settlements', 'state_ag_multistate_settlement'),
 ('https://www.tribalopioidsettlements.com/', 'Tribal opioid settlements', 'state_ag_multistate_settlement'),
 ('https://www.officialflintwatersettlement.com/', 'Flint Water Cases settlement - E.D. Mich.', 'mass_tort_class_settlement'),
 ('https://www.eastpalestinetrainsettlement.com/', 'East Palestine train derailment settlement - N.D. Ohio', 'mass_tort_class_settlement'),
 ('https://www.firevictimtrust.com/', 'PG&E Fire Victim Trust', 'bankruptcy_trust'),
 ('https://www.scoutingsettlementtrust.com/', 'BSA Scouting Settlement Trust', 'bankruptcy_trust'),
 ('https://www.takataairbaginjurytrust.com/', 'Takata airbag tort compensation trust fund', 'bankruptcy_trust'),
 ('https://www.bcbssettlement.com/', 'Blue Cross Blue Shield antitrust settlement - MDL 2406, N.D. Ala.', M),
 ('https://www.paymentcardsettlement.com/', 'Payment card interchange fee settlement - MDL 1720, E.D.N.Y.', M),
 ('https://www.realestatecommissionlitigation.com/', 'Real estate commission antitrust settlements', A),
 ('https://www.equifaxbreachsettlement.com/', 'Equifax data breach settlement - MDL 2800, N.D. Ga.', M),
 ('https://www.vcf.gov/', 'September 11th Victim Compensation Fund', 'government_compensation_program'),
 ('https://www.cornseedsettlement.com/', 'Syngenta MIR162 corn settlement - MDL 2591, D. Kan.', 'mdl_global_settlement'),
 ('https://www.vwcourtsettlement.com/', 'Volkswagen clean diesel settlements - MDL 2672, N.D. Cal.', M),
 ('https://www.deepwaterhorizoneconomicsettlement.com/', 'Deepwater Horizon economic and property damages settlement - MDL 2179, E.D. La.', M),
 ('https://www.gmignitionswitcheconomicsettlement.com/', 'GM ignition switch economic loss settlement - MDL 2543, S.D.N.Y.', M),
 ('https://www.ecodieselsettlement.com/', 'FCA EcoDiesel settlement - MDL 2777, N.D. Cal.', M),
 ('https://www.facebookuserprivacysettlement.com/', 'Facebook consumer privacy user profile settlement - MDL 2843, N.D. Cal.', M),
 ('https://restructuring.ra.kroll.com/purduepharma/', 'Purdue Pharma chapter 11 claims agent docket', 'bankruptcy_plan'),
]

BAD_PATH = re.compile(r'login|sign-?in|submit|file-?a?-?claim|claim-?form|/claim\b|dashboard|register|portal', re.I)
CHALLENGE = re.compile(r'just a moment|cf-chl|captcha|access denied|request unsuccessful|incapsula|attention required|are you a human', re.I)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def saved_urls():
    seen = set()
    for path, table in DBS:
        con = sqlite3.connect('file:' + path + '?mode=ro', uri=True)
        for (u,) in con.execute('select source_url from ' + table):
            if u:
                seen.add(u)
        if table == 'versions':
            for (u,) in con.execute('select final_url from versions where final_url is not null'):
                seen.add(u)
        con.close()
    return seen


def fetch_robots(pair):
    scheme, host = pair
    url = '%s://%s/robots.txt' % (scheme, host)
    rec = {'host': host, 'robots_url': url, 'requested_at': now(), 'user_agent': UA}
    text = None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/plain,*/*;q=0.5'})
        with urllib.request.urlopen(req, timeout=12, context=ssl.create_default_context()) as resp:
            body = resp.read(200000)
            rec.update(status=resp.status, final_url=resp.geturl(), content_type=resp.headers.get('Content-Type'),
                       bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            text = body.decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        rec.update(status=e.code, error='HTTPError')
    except Exception as e:  # no retry by design
        rec.update(status=None, error=type(e).__name__ + ': ' + str(e)[:160])
    rec['_text'] = text
    return rec


def main():
    cat = json.load(open(CAT, encoding='utf-8'))
    by_suffix = {r['id'][-6:]: r for r in cat['records']}
    pld = {e['url']: e for e in json.load(open(PLD, encoding='utf-8'))['entries']}
    pld_sha = hashlib.sha256(open(PLD, 'rb').read()).hexdigest()
    cat_sha = hashlib.sha256(open(CAT, 'rb').read()).hexdigest()
    seen = saved_urls()
    cands, held = [], []
    for suf, (family, note) in CATALOG_PICKS.items():
        r = by_suffix[suf]
        pub = r['publisher']
        review = r.get('review') or {}
        cands.append(dict(url=pub['official_settlement_url'], title=review.get('title') or pub['title'],
            source_family='settlement_catalog_official_url', settlement_family=family, expected_page_type='settlement_website_page',
            case_reference=dict(court=review.get('court'), case_number=review.get('case_number'),
                                basis='prior bounded review' if review else 'none - to be extracted from captured page'),
            evidence=dict(kind='local_catalog_record', catalog_path=CAT, catalog_sha256=cat_sha, catalog_record_id=r['id'],
                          publisher_record_sha256=r['publisher_record_sha256'], field='publisher.official_settlement_url',
                          publisher_verification_status=pub['verification_status'], publisher_last_verified=pub['last_verified'],
                          publisher_status=pub['status'], publisher_claim_deadline=pub.get('claim_deadline') or None,
                          publisher_assertions_are_independent_verification=False,
                          prior_independent_review_id=review.get('id')), note=note))
    for suf, why in HELD_CATALOG.items():
        r = by_suffix[suf]
        held.append(dict(url=r['publisher']['official_settlement_url'], reason=why, catalog_record_id=r['id']))
    for u, family in PLD_PICKS.items():
        e = pld.get(u)
        if not e:
            held.append(dict(url=u, reason='not found in source directory catalog; dropped'))
            continue
        cands.append(dict(url=u, title=e.get('title'), source_family='public_law_directory_reference', settlement_family=family,
            expected_page_type='index_or_reference_page', case_reference=None,
            evidence=dict(kind='local_source_directory_entry', catalog_path=PLD, catalog_sha256=pld_sha, entry_id=e['id'],
                          verification_status=e.get('verification_status'), verification_claim=e.get('verification_claim'),
                          source_as_of=e.get('source_as_of')), note=''))
    for u, title, family in KNOWLEDGE:
        cands.append(dict(url=u, title=title, source_family='mass_tort_program_site_candidate', settlement_family=family,
            expected_page_type='settlement_website_page',
            case_reference=dict(basis='model general knowledge; UNVERIFIED until captured documents confirm'),
            evidence=dict(kind='model_general_knowledge_plus_robots_response', local_evidence=None,
                          caveat='Domain and matter description come from general knowledge, not a local record. Confirm court-approved '
                                 'status from the captured page (caption, administrator, order links) before publishing; a live host is not proof.'),
            note=''))
    final, seen_urls = [], set()
    for c in cands:
        s = urlsplit(c['url'])
        if c['url'] in seen or c['url'] in seen_urls:
            held.append(dict(url=c['url'], reason='already saved locally (exact URL) or duplicate'))
            continue
        if BAD_PATH.search(s.path) or s.query:
            held.append(dict(url=c['url'], reason='claim/login/form-like path or query string'))
            continue
        seen_urls.add(c['url'])
        final.append(c)
    uniq = {}
    for c in final:
        s = urlsplit(c['url'])
        uniq.setdefault(s.netloc, s.scheme)
    with ThreadPoolExecutor(max_workers=8) as ex:
        robots = list(ex.map(fetch_robots, [(sch, h) for h, sch in uniq.items()]))
    rob, parsers = {}, {}
    for r in robots:
        text = r.pop('_text')
        r['crawl_delay'] = None
        if r.get('status') == 200 and text is not None:
            if CHALLENGE.search(text[:4000]):
                r['verdict'] = 'challenge_or_block_shell'
            elif '<html' in text[:2000].lower() or '<!doctype' in text[:200].lower():
                r['verdict'] = 'html_returned_no_rules'
            else:
                r['verdict'] = 'parsed'
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(text.splitlines())
                parsers[r['host']] = rp
                try:
                    r['crawl_delay'] = rp.crawl_delay(UA)
                except Exception:
                    pass
        elif r.get('status') in (404, 410):
            r['verdict'] = 'no_robots_file'
        else:
            r['verdict'] = 'unavailable'
        rob[r['host']] = r
    packet = []
    for c in final:
        s = urlsplit(c['url'])
        r = rob[s.netloc]
        allowed = None
        if r['verdict'] == 'parsed':
            allowed = parsers[s.netloc].can_fetch(UA, c['url'])
        elif r['verdict'] in ('no_robots_file', 'html_returned_no_rules'):
            allowed = True
        c['host'] = s.netloc
        c['robots'] = dict(robots_url=r['robots_url'], status=r.get('status'), verdict=r['verdict'], allowed_for_user_agent=allowed,
                           crawl_delay=r.get('crawl_delay'), sha256=r.get('sha256'), requested_at=r['requested_at'], error=r.get('error'))
        c['capture_rules'] = dict(method='GET exact URL only', follow_links=False, forms=False, claim_submission=False,
                                  min_host_delay_seconds=max(2, int(r.get('crawl_delay') or 0)), retries=0,
                                  reject=['soft 404', 'challenge/login shell', 'empty extraction', 'parked-domain page'])
        if allowed:
            packet.append(c)
        else:
            held.append(dict(url=c['url'], source_family=c['source_family'],
                             reason='robots not confirmed: %s (status %s) %s' % (r['verdict'], r.get('status'), r.get('error') or '')))
    with open(OUT + 'settlement_urls.jsonl', 'w', encoding='utf-8', newline='\n') as f:
        for c in packet:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')
    json.dump(dict(generated_at=now(), user_agent=UA, requests=len(rob),
                   policy='one robots.txt GET per host, no retries, 8 workers, 12 s timeout',
                   hosts=sorted(rob.values(), key=lambda x: x['host']), held=held),
              open(OUT + 'settlement_robots_check.json', 'w', encoding='utf-8'), indent=1)
    print('candidates', len(cands), 'after filters', len(final), 'packet', len(packet), 'held', len(held))
    print('hosts in packet', len({c['host'] for c in packet}), 'robots requests', len(rob))
    print('by source_family', dict(collections.Counter(c['source_family'] for c in packet)))
    print('by settlement_family', dict(collections.Counter(c['settlement_family'] for c in packet)))
    print('robots verdicts', dict(collections.Counter(r['verdict'] for r in rob.values())))
    print('crawl delays', {h: r['crawl_delay'] for h, r in rob.items() if r.get('crawl_delay')})
    for h in held:
        print('HELD', h['url'][:90], '|', h['reason'][:120])


main()
