"""Read-only builder for packets/gap_fill_candidates.jsonl.

Every candidate is an existing reference in sources/public_law_directory_20260919/catalog.json
(selected by exact catalog id, reviewed by hand against the coverage matrix). No URL is invented
and no network request is made. Saved-URL dedupe is exact plus a loose comparison (scheme, www.,
trailing slash, case of host) against the directory DB, the canonical capture index, the pilot
acquisition resources and the source-archive link layer.
"""
import json
import re
import sqlite3

ROOT = 'C:/Users/firas/Downloads/SCRAPE'
OUT = ROOT + '/reports/corpus_upgrade_20260919/understand'

# (catalog id, state, gap_type, priority, caution)
PICKS = [
    # --- publisher-withdrawn statutes (Open US Law has 0 statute rows) ---
    ('pld-d4c37a617395', 'GA', 'statutes_publisher_withdrawn', 1, 'Summary.json lists www.legis.ga.gov/georgia-code as a manifest URL with no indexed record; the official code is hosted by a vendor viewer, so check robots/terms before any packet.'),
    ('pld-63f40d2511fc', 'NC', 'statutes_publisher_withdrawn', 1, ''),
    ('pld-993c4a0f75b4', 'NC', 'statutes_publisher_withdrawn', 3, 'Legacy ncga.state.nc.us host; may redirect to ncleg.gov. 314 official NC chapter PDFs (ncleg.gov ByChapter) are already saved: 261 published + 53 awaiting publication, so the NC gap is mostly publication and section-level structuring, not acquisition.'),
    ('pld-f2944852e17a', 'NC', 'statutes_publisher_withdrawn', 3, 'Session laws, not the codified statutes.'),
    # --- states with zero / absent statewide court rules ---
    ('pld-0890726c6bd5', 'MO', 'court_rules_zero_any_source', 1, 'Directory marks this reference not_verified_in_source.'),
    ('pld-9ec9a7532717', 'OK', 'court_rules_zero_any_source', 1, 'OSCN is a database UI; summary.json shows an earlier OSCN rules URL produced no indexed record.'),
    ('pld-8d1b40d21d14', 'AR', 'court_rules_absent_open_us_law', 1, ''),
    ('pld-376faf1d11aa', 'CO', 'court_rules_absent_open_us_law', 2, 'Portal only; the directory holds no direct Colorado court-rules reference.'),
    ('pld-40038a8d4800', 'KY', 'court_rules_absent_open_us_law', 2, 'Portal only; the directory holds no direct Kentucky court-rules reference.'),
    ('pld-1612d8373ca5', 'NJ', 'court_rules_absent_open_us_law', 2, 'Portal only; the directory holds no Rules Governing the Courts of NJ hub (only the RPC appendix).'),
    ('pld-f46c0e267773', 'NM', 'court_rules_absent_open_us_law', 1, ''),
    ('pld-311a577ad16c', 'SD', 'court_rules_absent_open_us_law', 2, 'Portal only; SD rules of civil procedure and evidence are codified in SDCL titles 15 and 19.'),
    ('pld-76cb10fb6579', 'VT', 'court_rules_absent_open_us_law', 1, ''),
    ('pld-e2b04a5315c3', 'VT', 'court_rules_absent_open_us_law', 2, ''),
    # --- states with no official court-rule capture (Open US Law only) ---
    ('pld-5db83b4e2034', 'DC', 'court_rules_no_official_capture', 2, ''),
    ('pld-e26702412860', 'LA', 'court_rules_no_official_capture', 2, ''),
    ('pld-70b54e3aa18c', 'NH', 'court_rules_no_official_capture', 2, ''),
    ('pld-7f8447e5dc51', 'NC', 'court_rules_no_official_capture', 2, ''),
    ('pld-19e791d91fc8', 'TN', 'court_rules_no_official_capture', 2, ''),
    ('pld-f36954feca0c', 'TN', 'court_rules_no_official_capture', 2, ''),
    ('pld-fbd99746e89c', 'MI', 'court_rules_no_official_capture', 2, 'Summary.json lists this exact URL as a manifest URL with no indexed record (earlier attempt did not yield text).'),
    ('pld-b909e7201ff3', 'CT', 'court_rules_no_official_capture', 3, 'Portal only.'),
    # --- civil procedure / evidence rule sets for mass-tort states ---
    ('pld-bb875280eb27', 'NY', 'civil_procedure_evidence_rules', 2, ''),
    ('pld-e8f3adde33db', 'NY', 'civil_procedure_evidence_rules', 2, ''),
    ('pld-1359137cbfb3', 'NY', 'civil_procedure_evidence_rules', 2, 'Part 202 contains 202.69 (coordination of related actions); no saved record matched "litigation coordinating panel".'),
    ('pld-c4c5b8dcac2a', 'IL', 'civil_procedure_evidence_rules', 2, ''),
    ('pld-6e876eb8dab2', 'IL', 'civil_procedure_evidence_rules', 3, 'Legacy courts.illinois.gov host.'),
    ('pld-67fff7f70aa7', 'FL', 'civil_procedure_evidence_rules', 2, ''),
    ('pld-e1d4b64abbd6', 'FL', 'civil_procedure_evidence_rules', 2, 'Florida Bar-hosted PDF dated April 1, 2026 (publication date in title; not an effective-date finding).'),
    ('pld-17ea219c966d', 'CA', 'local_rules_index', 2, ''),
    ('pld-67df61c4367b', 'WV', 'civil_procedure_evidence_rules', 2, ''),
    ('pld-80ba8eaf0637', 'AL', 'civil_procedure_evidence_rules', 3, ''),
    ('pld-0b13f79e22f9', 'AL', 'civil_procedure_evidence_rules', 3, ''),
    ('pld-ca15c386cd72', 'GA', 'civil_procedure_evidence_rules', 3, ''),
    # --- complex-litigation / mass-tort coordination programs ---
    ('pld-30ed683d1495', 'NJ', 'complex_litigation_program', 1, ''),
    ('pld-a4e45ac43145', 'NJ', 'complex_litigation_program', 1, ''),
    ('pld-346a82441b38', 'PA', 'complex_litigation_program', 1, ''),
    ('pld-3f9b910c4849', 'PA', 'complex_litigation_program', 1, ''),
    ('pld-6f290c940224', 'CA', 'complex_litigation_program', 1, ''),
    ('pld-1b17513c52f3', 'TX', 'complex_litigation_program', 1, ''),
    ('pld-a7d059e8c6fc', 'TX', 'complex_litigation_program', 1, ''),
    ('pld-b1ec3b0a8b5f', 'WV', 'complex_litigation_program', 1, ''),
    ('pld-dc1556930c52', 'WV', 'complex_litigation_program', 2, ''),
    ('pld-fa071038cf85', 'WV', 'complex_litigation_program', 2, ''),
    ('pld-8a55b4a80050', 'WV', 'complex_litigation_program', 2, ''),
    ('pld-8234b24db4c2', 'CT', 'complex_litigation_program', 2, ''),
    ('pld-0775b86331ee', 'NY', 'complex_litigation_program', 3, 'Commercial Division, not the Litigation Coordinating Panel; the directory has no LCP reference.'),
    ('pld-e951f5d8282b', 'FL', 'complex_litigation_program', 3, 'Complex business litigation, not a mass-tort docket.'),
    ('pld-1be89a3ee26b', 'FL', 'complex_litigation_program', 3, 'Complex business litigation rules.'),
    ('pld-6fe939ada1c6', 'FL', 'complex_litigation_program', 3, ''),
    # --- high-volume venue: local rules / forms / clerk / fees ---
    ('pld-a5205c841d48', 'PA', 'venue_philadelphia_local_rules', 1, ''),
    ('pld-5cb50ae53478', 'PA', 'venue_philadelphia_forms', 1, 'About 120 courts.phila.gov documents are already saved in the imported collection without a county link; dedupe by URL/hash before fetching children.'),
    ('pld-713f1512d3c2', 'PA', 'venue_philadelphia_fees', 2, ''),
    ('pld-e7288e8056e9', 'PA', 'venue_philadelphia_manuals', 2, ''),
    ('pld-9c54b287fbc4', 'PA', 'venue_philadelphia_local_rules', 2, ''),
    ('pld-84bec344d424', 'PA', 'venue_philadelphia_publications', 3, ''),
    ('pld-b5602bee0487', 'PA', 'venue_philadelphia_publications', 3, ''),
    ('pld-71145f9ba97d', 'IL', 'venue_cook_orders', 2, 'Judge-filtered orders listing (query string); fetch only as one exact URL.'),
    ('pld-d6a5347255ee', 'NY', 'venue_new_york_forms', 2, ''),
    ('pld-9bd004fa0d42', 'NY', 'venue_new_york_county_court_page', 2, ''),
    ('pld-e5aed275461b', 'MO', 'venue_missouri_circuit_directory', 2, 'Statewide circuit list; the directory has no St. Louis City (22nd Circuit) reference.'),
    ('pld-4300c0698bbd', 'MO', 'statewide_forms_absent', 2, ''),
    # --- administrative regulations absent in every source ---
    ('pld-40ffd7299f49', 'CA', 'regulations_zero_any_source', 2, 'OAL page links to the vendor-hosted CCR; do not crawl the vendor site without a terms/robots review.'),
    ('pld-6457657cca10', 'NY', 'regulations_zero_any_source', 3, 'NYCRR is hosted on govt.westlaw.com; terms/robots review required before any acquisition.'),
    ('pld-e80a8f2269e4', 'NY', 'regulations_zero_any_source', 2, 'Department of Health regulations only.'),
    ('pld-96f4eb650e3d', 'NJ', 'regulations_zero_any_source', 3, 'N.J.A.C. free public access is vendor-hosted (LexisNexis); terms/robots review required.'),
    ('pld-0c39b28ecd39', 'PA', 'regulations_zero_any_source', 2, ''),
    ('pld-8bb767e2b8f2', 'FL', 'regulations_zero_any_source', 2, ''),
    ('pld-58d3b6d92125', 'MO', 'regulations_zero_any_source', 2, ''),
    ('pld-bd0d343b553b', 'MA', 'regulations_zero_any_source', 2, ''),
    ('pld-7335babd117b', 'MI', 'regulations_zero_any_source', 2, ''),
    ('pld-699b3a0410f0', 'NV', 'regulations_zero_any_source', 2, ''),
    ('pld-2085dc8f12f6', 'AL', 'regulations_zero_any_source', 3, ''),
    ('pld-e999d902abe4', 'TN', 'regulations_zero_any_source', 3, ''),
    ('pld-949d31b1057b', 'IN', 'regulations_zero_any_source', 3, ''),
    ('pld-ad00d35e63d3', 'AR', 'regulations_zero_any_source', 3, 'Register, not the codified rules.'),
    ('pld-3fc483c2774f', 'OK', 'regulations_zero_any_source', 3, ''),
    ('pld-cad6c45f12da', 'AZ', 'regulations_zero_any_source', 3, 'Register, not the codified Arizona Administrative Code.'),
    # --- civil jury instructions (products liability, damages, causation) ---
    ('pld-1a28a5dddc0f', 'CA', 'civil_jury_instructions', 2, 'Single large PDF (2026 edition).'),
    ('pld-2ad012a1c1bc', 'CA', 'civil_jury_instructions', 3, ''),
    ('pld-bbdd042433b1', 'NJ', 'civil_jury_instructions', 2, ''),
    ('pld-3432725ad37a', 'NJ', 'civil_jury_instructions', 2, ''),
    ('pld-ddafe36f26c9', 'IL', 'civil_jury_instructions', 2, ''),
    ('pld-79eb7b0db727', 'DE', 'civil_jury_instructions', 2, ''),
    ('pld-c77bc3a26dd7', 'CT', 'civil_jury_instructions', 3, ''),
    ('pld-31e68b4beaf6', 'MA', 'civil_jury_instructions', 3, ''),
    ('pld-48eec9d9fdfb', 'FL', 'civil_jury_instructions', 2, 'Florida Bar-hosted portal.'),
    ('pld-6096352e0cb8', 'MO', 'civil_jury_instructions', 2, ''),
    ('pld-16973ef49e79', 'LA', 'civil_jury_instructions', 3, ''),
    ('pld-9f9ea7be891a', 'SC', 'civil_jury_instructions', 3, ''),
    # --- no official statute capture in the directory (Open US Law only) ---
    ('pld-e202dbb4f1c9', 'NY', 'statutes_no_official_capture', 2, ''),
    ('pld-c90ed12e6cb1', 'NY', 'statutes_no_official_capture', 2, ''),
    ('pld-dbf3cd019cd9', 'NY', 'constitution_no_official_capture', 3, ''),
    ('pld-80856c444147', 'IN', 'statutes_no_official_capture', 3, 'Summary.json lists iga.in.gov/laws as a manifest URL with no indexed record (script-rendered site).'),
    ('pld-cd6244e226a1', 'IN', 'constitution_no_official_capture', 3, 'Same host caveat as the Indiana Code.'),
    ('pld-19bf0fa15cfc', 'NH', 'statutes_no_official_capture', 3, 'Summary.json lists this exact URL as a manifest URL with no indexed record.'),
    ('pld-57c0a8b0fe16', 'SD', 'statutes_no_official_capture', 3, 'Summary.json lists sdlegislature.gov/Statutes as a manifest URL with no indexed record (script-rendered site).'),
    ('pld-60f7939ddbc9', 'SD', 'statutes_no_official_capture', 3, 'SDCL title 15 (civil procedure); same host caveat.'),
    ('pld-30ee3c1476cd', 'SD', 'statutes_no_official_capture', 3, 'SDCL title 20 (personal rights and obligations); same host caveat.'),
    ('pld-24f2e835e551', 'SD', 'statutes_no_official_capture', 3, 'SDCL title 21 (judicial remedies); same host caveat.'),
    ('pld-ae389ae3c743', 'SD', 'statutes_no_official_capture', 3, 'SDCL title 37 (trade regulation); same host caveat.'),
    # --- statewide court forms absent ---
    ('pld-304c4faba33a', 'CT', 'statewide_forms_absent', 2, ''),
    ('pld-41f5dd894f6d', 'MA', 'statewide_forms_absent', 2, ''),
    ('pld-f9bc3e43bb96', 'MI', 'statewide_forms_absent', 2, ''),
    ('pld-118947b5162c', 'NC', 'statewide_forms_absent', 2, ''),
    ('pld-0aa3ed5965cf', 'OK', 'statewide_forms_absent', 2, ''),
    ('pld-420d20b4a846', 'SC', 'statewide_forms_absent', 2, ''),
    ('pld-a290ec002e76', 'TN', 'statewide_forms_absent', 2, ''),
    ('pld-28b54f7360f3', 'GA', 'statewide_forms_absent', 2, ''),
    ('pld-6fa50ca8ec56', 'DC', 'statewide_forms_absent', 2, 'Search form page; save the page only.'),
    ('pld-43313f5a411a', 'ID', 'statewide_forms_absent', 3, 'Self-help forms portal.'),
]


# Exact official URLs that are NOT in the source directory but were observed as anchors on a
# saved official hub page (raw HTML parsed locally with lxml; nothing fetched).
HUB = 'https://www.courtswv.gov/legal-community/court-rules'
HUB_LINKS = [
    ('https://www.courtswv.gov/legal-community/court-rules/rules-civil-procedure-contents', 'West Virginia Rules of Civil Procedure', 'WV', 'civil_procedure_evidence_rules', 2),
    ('https://www.courtswv.gov/legal-community/court-rules/rules-evidence-contents', 'Rules of Evidence', 'WV', 'civil_procedure_evidence_rules', 2),
    ('https://www.courtswv.gov/legal-community/court-rules/rules-appellate-procedure', 'Rules of Appellate Procedure', 'WV', 'civil_procedure_evidence_rules', 3),
    ('https://www.courtswv.gov/legal-community/court-rules/wv-trial-court-rules-contents', 'West Virginia Trial Court Rules', 'WV', 'complex_litigation_program', 2),
    ('https://www.courtswv.gov/lower-courts/mass-litigation-panel', 'Mass Litigation Panel', 'WV', 'complex_litigation_program', 1),
]


def loose(u):
    u = (u or '').strip()
    u = re.sub(r'^https?://', '', u, flags=re.I)
    u = re.sub(r'^www\.', '', u, flags=re.I)
    host, _, rest = u.partition('/')
    return host.lower() + '/' + rest.rstrip('/')


def ro(path):
    return sqlite3.connect('file:' + path + '?mode=ro', uri=True)


def main():
    ent = {e['id']: e for e in json.load(open(ROOT + '/sources/public_law_directory_20260919/catalog.json', encoding='utf-8'))['entries']}
    matrix = json.load(open(OUT + '/_work/coverage_matrix_stage1.json', encoding='utf-8'))['states']

    saved_exact, saved_loose = set(), set()
    c = ro(ROOT + '/delivery/archive-directory/directory.sqlite3')
    for (u,) in c.execute("select source_url from records where source_url is not null and source_url<>''"):
        saved_exact.add(u)
    d = ro(ROOT + '/catalog/documents.sqlite3')
    for (u,) in d.execute('select source_url from records'):
        saved_exact.add(u)
    for (u,) in d.execute("select distinct final_url from versions where final_url is not null"):
        saved_exact.add(u)
    try:
        for line in open(ROOT + '/sources/public_law_acquisition_20260919/resources.jsonl', encoding='utf-8'):
            r = json.loads(line)
            for k in ('url', 'source_url', 'final_url'):
                if r.get(k):
                    saved_exact.add(r[k])
    except OSError:
        pass
    saved_loose = {loose(u) for u in saved_exact}
    linked = set()
    for line in open(ROOT + '/sources/source_archive_links_20260919/links.jsonl', encoding='utf-8'):
        linked.add(json.loads(line)['source_id'])

    def evidence(state, gap):
        r = matrix[state]
        O = r['open_us_law']
        D = r['directory']
        fl = D['focused_laws']
        if gap.startswith('statutes_publisher_withdrawn'):
            return 'Open US Law v2026.08 statute rows=%d (publisher withdrew GA/NC statutes); official statute captures in directory: body=%d, unreviewed=%d; awaiting publication=%d.' % (
                O.get('statutes', 0), fl.get('statutes', {}).get('body', 0), fl.get('statutes', {}).get('unreviewed_page', 0), D['pending_publication'].get('statutes', 0))
        if gap.startswith('court_rules') or gap in ('civil_procedure_evidence_rules', 'local_rules_index'):
            s = r['open_us_law_court_rule_sets']
            return 'Open US Law court-rule rows=%d (civil-labelled %d, evidence-labelled %d, appellate-labelled %d); official court-rule captures: body=%d, unreviewed pages=%d; imported rule/order documents=%d.' % (
                O.get('court_rules', 0), s['civil_label_rows'], s['evidence_label_rows'], s['appellate_label_rows'],
                fl.get('court_rules', {}).get('body', 0), fl.get('court_rules', {}).get('unreviewed_page', 0), D['seeger'].get('court_rule_or_order', 0))
        if gap == 'regulations_zero_any_source':
            return 'Open US Law regulation rows=%d; official administrative-code captures in directory=%d.' % (
                O.get('regulations', 0), sum(fl.get('regulations', {}).values()))
        if gap.startswith('statutes_no_official') or gap.startswith('constitution_no_official'):
            return 'Official statute captures in directory=%d, constitution captures=%d; only Open US Law third-party rows exist (statutes=%d, constitution=%d).' % (
                sum(fl.get('statutes', {}).values()), sum(fl.get('constitution', {}).values()), O.get('statutes', 0), O.get('constitutions', 0))
        if gap == 'statewide_forms_absent':
            return 'Imported statewide form documents for this state=%d; county-level form records=%d.' % (
                D['seeger'].get('court_form_or_other_document', 0), D['county_records'].get('local_forms_fees', 0))
        if gap == 'complex_litigation_program':
            t = r['topics_open_us_law'].get('complex_coordination', {})
            return 'Coordination-rule phrase hits in Open US Law: statutes=%d, court rules=%d; directory full-text hits for the program name are limited to a handful of imported forms (see report section 5).' % (
                t.get('statutes', 0), t.get('court_rules', 0))
        if gap == 'civil_jury_instructions':
            return 'No saved record in the directory is classified as jury instructions for this state; source directory holds %d jury-instruction references.' % (
                r['source_directory']['by_category'].get('jury_instructions', 0))
        if gap.startswith('venue_'):
            cr = D['county_records']
            return 'State county-layer totals: local rules=%d, forms/fees=%d, clerk pages=%d; venue county has 0-3 county-linked records (see report section 6).' % (
                cr.get('local_rules', 0), cr.get('local_forms_fees', 0), cr.get('clerk_pages', 0))
        return ''

    rows, skipped = [], []
    seen = set()
    for pid, state, gap, prio, caution in PICKS:
        e = ent.get(pid)
        if not e:
            skipped.append({'id': pid, 'reason': 'id_not_in_catalog'})
            continue
        url = e['url']
        if url in seen:
            skipped.append({'id': pid, 'reason': 'duplicate_url_in_picks'})
            continue
        seen.add(url)
        already = 'exact' if url in saved_exact else ('loose' if loose(url) in saved_loose else '')
        if already or pid in linked:
            skipped.append({'id': pid, 'url': url, 'state': state, 'gap_type': gap,
                            'reason': 'already_saved_' + (already or 'linked_record')})
            continue
        vc = e.get('verification_claim') or {}
        rows.append({
            'priority': prio, 'state': state, 'gap_type': gap, 'url': url, 'title': e['title'],
            'source_directory_id': pid, 'directory_jurisdiction': e['jurisdiction'],
            'directory_category': e['category'], 'content_kind': e['content_kind'], 'host': e['host'],
            'access_requirements': e['access_requirements'],
            'directory_verification': {'status': e['verification_status'], 'verified_date': vc.get('verified_date'),
                                       'http_status': vc.get('http_status'),
                                       'note': 'historical directory claim, not a fresh check'},
            'saved_url_match': 'none (exact and loose comparison)',
            'evidence': evidence(state, gap),
            'caution': (caution + (' Source directory recorded historical HTTP status %s for this URL (possible bot barrier); do not retry around it.' % vc.get('http_status') if vc.get('http_status') not in (None, '', '200') else '')).strip(),
        })
    hub_sha = d.execute('select v.raw_sha256 from records r join versions v on v.version_id=r.latest_version_id '
                        'where r.source_url=? limit 1', (HUB,)).fetchone()
    for url, title, state, gap, prio in HUB_LINKS:
        if url in seen:
            continue
        seen.add(url)
        already = 'exact' if url in saved_exact else ('loose' if loose(url) in saved_loose else '')
        if already:
            skipped.append({'url': url, 'state': state, 'gap_type': gap, 'reason': 'already_saved_' + already})
            continue
        rows.append({
            'priority': prio, 'state': state, 'gap_type': gap, 'url': url, 'title': title,
            'source_directory_id': None, 'directory_jurisdiction': None, 'directory_category': None,
            'content_kind': 'page', 'host': 'www.courtswv.gov', 'access_requirements': 'unknown',
            'directory_verification': None,
            'observed_on_saved_hub': {'hub_url': HUB, 'hub_raw_sha256': hub_sha[0] if hub_sha else None,
                                      'note': 'anchor href parsed from the saved hub HTML; link liveness not checked'},
            'saved_url_match': 'none (exact and loose comparison)',
            'evidence': evidence(state, gap) + ' The saved hub page itself is an index with no rule text.',
            'caution': 'Not a source-directory reference; add it to the directory before acquisition.',
        })
    rows.sort(key=lambda r: (r['priority'], r['gap_type'], r['state'], r['url']))
    for i, r in enumerate(rows, 1):
        r['rank'] = i
    with open(OUT + '/packets/gap_fill_candidates.jsonl', 'w', encoding='utf-8', newline='\n') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    json.dump({'kept': len(rows), 'skipped': skipped}, open(OUT + '/_work/candidate_selection_log.json', 'w', encoding='utf-8'), indent=1)
    print('kept', len(rows), 'skipped', len(skipped))
    for s in skipped:
        print(s)
    import collections
    print(collections.Counter(r['gap_type'] for r in rows).most_common())
    print(collections.Counter(r['priority'] for r in rows))
    print(collections.Counter(r['host'] for r in rows).most_common(8))


if __name__ == '__main__':
    main()
