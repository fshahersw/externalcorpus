"""Assemble coverage_matrix.json (final) and the generated tables for state_county_gaps.md.

Read-only on every project database; writes only inside reports/corpus_upgrade_20260919/understand/.
"""
import collections
import hashlib
import json
import re
import sqlite3

ROOT = 'C:/Users/firas/Downloads/SCRAPE'
OUT = ROOT + '/reports/corpus_upgrade_20260919/understand'

VENUES = [
    # fips, label, state abbr, trellis slug, tier, host patterns for statewide/venue court documents
    ('42101', 'Philadelphia County, PA', 'PA', 'pennsylvania/philadelphia', 'primary', ['courts.phila.gov']),
    ('17031', 'Cook County, IL', 'IL', 'illinois/cook', 'primary', ['cookcountycourt.org', 'cookcountyclerkofcourt.org']),
    ('06037', 'Los Angeles County, CA', 'CA', 'california/losangeles', 'primary', ['//www.lacourt.org', '//lacourt.org', 'lacourt.ca.gov', 'lascpubstorage.blob.core.windows.net']),
    ('29510', 'St. Louis City, MO', 'MO', 'missouri/st.louiscity', 'primary', ['stlcitycircuitcourt.com']),
    ('17119', 'Madison County, IL', 'IL', 'illinois/madison', 'primary', ['madisoncountyil.gov', 'co.madison.il.us']),
    ('17163', 'St. Clair County, IL', 'IL', 'illinois/st.clair', 'primary', ['co.st-clair.il.us', 'stclaircountycourts']),
    ('34023', 'Middlesex County, NJ', 'NJ', 'new-jersey/middlesex', 'primary', ['njcourts.gov/courts/vicinages/middlesex']),
    ('34001', 'Atlantic County, NJ', 'NJ', 'new-jersey/atlantic', 'primary', ['njcourts.gov/courts/vicinages/atlantic']),
    ('36061', 'New York County, NY', 'NY', 'new-york/newyork', 'primary', ['nycourts.gov/courts/1jd', 'nycourts.gov/legacypdfs/courts/1jd']),
    ('48201', 'Harris County, TX', 'TX', 'texas/harris', 'primary', ['justex.net', 'hcdistrictclerk.com']),
    ('34003', 'Bergen County, NJ', 'NJ', 'new-jersey/bergen', 'secondary', ['njcourts.gov/courts/vicinages/bergen']),
    ('29189', 'St. Louis County, MO', 'MO', 'missouri/st.louis', 'secondary', ['stlcountycourts.com']),
    ('06075', 'San Francisco County, CA', 'CA', 'california/sanfrancisco', 'secondary', ['sfsuperiorcourt.org', 'sf.courts.ca.gov']),
    ('06001', 'Alameda County, CA', 'CA', 'california/alameda', 'secondary', ['alameda.courts.ca.gov']),
    ('12086', 'Miami-Dade County, FL', 'FL', 'florida/miami-dade', 'secondary', ['jud11.flcourts.org', 'miamidadeclerk.gov']),
    ('32003', 'Clark County, NV', 'NV', 'nevada/clark', 'secondary', ['clarkcountycourts.us']),
    ('10003', 'New Castle County, DE', 'DE', 'delaware/newcastle', 'secondary', ['courts.delaware.gov/superior']),
    ('22071', 'Orleans Parish, LA', 'LA', 'louisiana/orleansparish', 'secondary', ['orleanscivilclerk.com', 'orleanscdc.com']),
    ('54039', 'Kanawha County, WV', 'WV', 'west-virginia/kanawha', 'secondary', ['courtswv.gov/lower-courts/mass-litigation-panel']),
    ('42003', 'Allegheny County, PA', 'PA', 'pennsylvania/allegheny', 'secondary', ['alleghenycourts.us']),
    ('39035', 'Cuyahoga County, OH', 'OH', 'ohio/cuyahoga', 'secondary', ['cp.cuyahogacounty']),
    ('13121', 'Fulton County, GA', 'GA', 'georgia/fulton', 'secondary', ['fultoncourt.org', 'fultonclerk.org']),
    ('48113', 'Dallas County, TX', 'TX', 'texas/dallas', 'secondary', ['dallascounty.org']),
    ('36047', 'Kings County, NY', 'NY', 'new-york/kings', 'secondary', ['nycourts.gov/courts/2jd']),
    ('26163', 'Wayne County, MI', 'MI', 'michigan/wayne', 'secondary', ['3rdcc.org']),
    ('25025', 'Suffolk County, MA', 'MA', 'massachusetts/suffolk', 'secondary', ['mass.gov/locations/suffolk']),
    ('27053', 'Hennepin County, MN', 'MN', 'minnesota/hennepin', 'secondary', ['mncourts.gov/find-courts/hennepin']),
    ('29095', 'Jackson County, MO', 'MO', 'missouri/jackson', 'secondary', ['16thcircuit.org']),
]


def ro(path):
    return sqlite3.connect('file:' + path + '?mode=ro', uri=True)


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    stage = json.load(open(OUT + '/_work/coverage_matrix_stage1.json', encoding='utf-8'))
    M = stage['states']
    c = ro(ROOT + '/delivery/archive-directory/directory.sqlite3')
    d = ro(ROOT + '/catalog/documents.sqlite3')
    t = ro(ROOT + '/sources/trellis/catalog/catalog.sqlite3')
    cat = json.load(open(ROOT + '/sources/public_law_directory_20260919/catalog.json', encoding='utf-8'))['entries']

    obs = set(u for (u,) in t.execute("select distinct url from links where category='coverage_county'"))
    saved = set(u for (u,) in t.execute("select url from pages where category='coverage_county' and status=200"))

    venues = []
    for fips, label, ab, slug, tier, hosts in VENUES:
        turl = 'https://trellis.law/coverage/' + slug
        kinds = collections.Counter()
        for ds, kind, n in c.execute(
                'select r.dataset,r.kind,count(*) from record_counties rc join records r on r.id=rc.record_id '
                'where rc.geoid=? group by 1,2', (fips,)):
            kinds[ds + ':' + kind] += n
        ids_dir, ids_cap = set(), set()
        for h in hosts:
            for (rid,) in c.execute("select id from records where source_url like ?", ('%' + h + '%',)):
                ids_dir.add(rid)
            for (rk,) in d.execute("select record_key from records where source_url like ?", ('%' + h + '%',)):
                ids_cap.add(rk)
        rx = re.compile('|'.join(re.escape(h) for h in hosts), re.I)
        refs = [e for e in cat if rx.search(e['url'])]
        w = t.execute('select official_website,case_links,judge_links from counties where url=?', (turl,)).fetchone()
        has_rules = any(k.endswith(':local_rules') for k in kinds)
        has_forms = any('court_forms_filing_documents' in k for k in kinds)
        has_clerk = any('court_clerk_office' in k for k in kinds)
        venues.append({
            'fips': fips, 'venue': label, 'state': ab, 'tier': tier,
            'trellis_profile_url': turl,
            'trellis_profile_status': 'saved' if turl in saved else ('observed_not_saved' if turl in obs else 'not_observed'),
            'trellis_reported_county_website': (w[0] if w else None),
            'trellis_case_links': (w[1] if w else None), 'trellis_judge_links': (w[2] if w else None),
            'county_linked_directory_records': dict(kinds), 'county_linked_total': sum(kinds.values()),
            'county_linked_local_rules': has_rules, 'county_linked_forms': has_forms, 'county_linked_clerk_page': has_clerk,
            'host_patterns_checked': hosts,
            'directory_records_on_court_hosts_not_county_linked': len(ids_dir),
            'capture_index_records_on_court_hosts': len(ids_cap),
            'source_directory_references_on_court_hosts': [{'id': e['id'], 'url': e['url'], 'category': e['category']} for e in refs][:12],
            'source_directory_reference_count': len(refs),
        })

    # topical search in the local directory index (coordination programmes)
    dq = {
        'nj_multicounty_litigation': '"multicounty litigation" OR "multi-county litigation"',
        'ca_jccp_coordination': '"coordination proceeding" OR "coordination proceedings" OR JCCP OR "judicial council coordination"',
        'mass_tort_or_complex_litigation_center': '"mass tort" OR "mass torts" OR "complex litigation center"',
        'ny_litigation_coordinating_panel': '"litigation coordinating panel"',
        'wv_mass_litigation_panel': '"mass litigation panel"',
        'medical_monitoring': '"medical monitoring"',
        'mdl_case_management_forms': '"short form complaint" OR "master complaint" OR "plaintiff fact sheet"',
    }
    directory_topics = {}
    for k, q in dq.items():
        rows = c.execute(
            'select b.dataset,b.group_name,b.state,count(*) from search s join browse b on b.id=s.id '
            'where search match ? group by 1,2,3 order by 4 desc', (q,)).fetchall()
        directory_topics[k] = {
            'query': q, 'total': sum(r[3] for r in rows),
            'law_or_federal_hits': [{'dataset': r[0], 'group': r[1], 'state': r[2], 'n': r[3]} for r in rows if r[1] in ('laws', 'federal', 'counties')],
        }

    # text size of "unreviewed" official law pages (characters from the capture index contents table)
    chars = dict(d.execute('select id,characters from contents'))
    name2ab = {r['state']: a for a, r in M.items()}
    size_tot = collections.Counter()
    for a in M:
        M[a]['directory']['unreviewed_text_size'] = {}
    sql = ("select state,content_id,payload from records where dataset='focused' and group_name='laws' and "
           "(kind like '%needs_content_review%' or kind like '%law_document_title_evidence%')")
    for state, cid, pl in c.execute(sql):
        a = name2ab.get(state)
        if not a:
            continue
        catg = json.loads(pl).get('category') or ''
        n = chars.get(cid)
        b = 'no_text' if n is None else ('lt_2k' if n < 2000 else ('2k_to_20k' if n < 20000 else 'ge_20k'))
        for tok in ('statutes', 'court_rules', 'constitution'):
            if tok in catg:
                U = M[a]['directory']['unreviewed_text_size'].setdefault(tok, {})
                U[b] = U.get(b, 0) + 1
                size_tot[tok + ':' + b] += 1

    cand = [json.loads(l) for l in open(OUT + '/packets/gap_fill_candidates.jsonl', encoding='utf-8')]
    sel = json.load(open(OUT + '/_work/candidate_selection_log.json', encoding='utf-8'))

    totals = collections.Counter()
    for a, r in M.items():
        O = r['open_us_law']
        for k in ('statutes', 'constitutions', 'regulations', 'court_rules', 'guidance'):
            totals['open_us_law_' + k] += O.get(k, 0)
        for k, v in r['directory']['county_records'].items():
            totals['county_' + k] += v
        totals['trellis_observed'] += r['trellis_county_profiles']['observed']
        totals['trellis_saved'] += r['trellis_county_profiles']['saved']
        totals['seeger_forms'] += r['directory']['seeger'].get('court_form_or_other_document', 0)
    flag_index = collections.defaultdict(list)
    for a, r in M.items():
        for f in r['flags']:
            flag_index[f].append(a)

    final = {
        'generated_at': stage['generated_at'],
        'scope': '50 states + DC. Saved data only; no network request was made. All SQLite databases opened read-only.',
        'inputs': {
            'directory_db': 'delivery/archive-directory/directory.sqlite3 (records, record_counties, counties, search/browse)',
            'capture_index': 'catalog/documents.sqlite3 (records.source_url, versions.final_url; used for saved-URL dedupe)',
            'open_us_law': 'sources/open_us_law_20260918/catalog.sqlite3 (files row totals; records_fts topical queries; court_rules payload chapter names)',
            'trellis': 'sources/trellis/catalog/catalog.sqlite3 (links category coverage_county = observed; pages status 200 = saved)',
            'source_directory': {'path': 'sources/public_law_directory_20260919/catalog.json', 'sha256': sha(ROOT + '/sources/public_law_directory_20260919/catalog.json'), 'entries': len(cat)},
            'source_archive_links': 'sources/source_archive_links_20260919/links.jsonl',
            'focused_summary': 'delivery/focused_legal_corpus/summary.json',
        },
        'definitions': {
            'focused_laws_tiers': {
                'body': 'kinds law_chapter_body, verified_law_document_derivative, legal_text_fragment, captured_law_representation, law_text_fragment, observed_comprehensive_constitution',
                'unreviewed_page': 'kinds needs_content_review, law_document_title_evidence_needs_review (saved text exists, not confirmed to be a law body; many are hub/index pages)',
                'navigation': 'kind legal_inventory_navigation',
            },
            'count_caveat': 'Counts are saved records/rows, never unique laws. Open US Law rows are third-party structured reproductions (snapshot v2026.08, publisher date 2026-08-14), not official captures; its source_url values were not retrieved. A focused record carrying two category tokens is counted under each.',
            'court_rule_label_caveat': 'civil/evidence/appellate rows are keyword matches on the publisher chapter name. Code states keep these in statutes (e.g. CA Evidence Code and CCP, NY CPLR, KS ch. 60, WI chs. 801-911, LA Code of Civil Procedure and Code of Evidence, OK title 12, GA title 9 and 24, SD titles 15 and 19), so a zero label is a prompt to check, not proof of absence.',
            'topic_caveat': 'Topical hits are FTS phrase matches; zero hits means the phrase set was not found (terminology differs by state, e.g. Louisiana prescription/peremption).',
            'jurisdiction_rule': 'State taken only from the explicit state field; county only from record_counties FIPS links. Venue host matches are reported separately and are not county assignments.',
        },
        'totals': dict(totals),
        'flag_index': dict(flag_index),
        'data_quality_observations': {
            'records_without_single_recognised_state': stage['records_without_recognised_state'],
            'trellis_nonstandard_observed_urls': stage['trellis_nonstandard_observed_urls'],
        },
        'topic_gaps_open_us_law': stage['topic_gaps'],
        'topic_hits_local_directory_index': directory_topics,
        'high_volume_venues': venues,
        'trellis_unsaved_profile_urls_by_state': stage['trellis_unsaved_profile_urls_by_state'],
        'gap_fill_candidates_summary': {
            'file': 'packets/gap_fill_candidates.jsonl', 'count': len(cand),
            'by_gap_type': dict(collections.Counter(r['gap_type'] for r in cand)),
            'by_priority': dict(collections.Counter(str(r['priority']) for r in cand)),
            'by_state': dict(collections.Counter(r['state'] for r in cand)),
            'distinct_hosts': len({r['host'] for r in cand}),
            'reviewed_but_already_saved': [s for s in sel['skipped'] if s.get('reason', '').startswith('already_saved')],
        },
        'states': M,
    }
    json.dump(final, open(OUT + '/coverage_matrix.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    # ---- generated markdown tables ----
    L = []
    L.append('| State | OUL statutes | OUL const. | OUL regs | OUL court rules (civ/evid/app label rows) | Official statutes body/unrev/nav | Official court rules body/unrev | Official regs | Imported forms | Imported rules/orders | Counties | Trellis saved/observed | County local rules (counties) | County forms | Clerk pages | Src-dir refs (linked) |')
    L.append('|---|---:|---:|---:|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---|')
    for a, r in M.items():
        O = r['open_us_law']
        S = r['open_us_law_court_rule_sets']
        F = r['directory']['focused_laws']
        g = lambda k, tr: F.get(k, {}).get(tr, 0)
        sg = r['directory']['seeger']
        cr = r['directory']['county_records']
        cg = r['directory']['county_distinct_geoids']
        T = r['trellis_county_profiles']
        sd = r['source_directory']
        lr = cr.get('local_rules', 0) + cr.get('pending_local_rules', 0)
        lrc = max(cg.get('local_rules', 0), 0) + cg.get('pending_local_rules', 0)
        L.append('| %s | %s | %s | %s | %s (%d/%d/%d) | %d/%d/%d | %d/%d | %d | %d | %d | %d | %d/%d | %d (%d) | %d | %d | %d (%d) |' % (
            a, '{:,}'.format(O.get('statutes', 0)), O.get('constitutions', 0), '{:,}'.format(O.get('regulations', 0)),
            '{:,}'.format(O.get('court_rules', 0)), S['civil_label_rows'], S['evidence_label_rows'], S['appellate_label_rows'],
            g('statutes', 'body'), g('statutes', 'unreviewed_page'), g('statutes', 'navigation'),
            g('court_rules', 'body'), g('court_rules', 'unreviewed_page'), sum(F.get('regulations', {}).values()),
            sg.get('court_form_or_other_document', 0), sg.get('court_rule_or_order', 0),
            r['county_registry'].get('counties_total', 0), T['saved'], T['observed'], lr, lrc,
            cr.get('local_forms_fees', 0) + cr.get('pending_local_forms_fees', 0), cr.get('clerk_pages', 0),
            sd['references'], sd['linked_to_saved']))
    V = []
    V.append('| Venue (FIPS) | Trellis profile | County-linked records | Local rules / forms / clerk linked | Saved docs on court host (not county-linked) | Src-dir refs on court host |')
    V.append('|---|---|---:|---|---:|---:|')
    for v in venues:
        V.append('| %s (%s)%s | %s | %d | %s / %s / %s | %d | %d |' % (
            v['venue'], v['fips'], '' if v['tier'] == 'primary' else ' *', v['trellis_profile_status'], v['county_linked_total'],
            'yes' if v['county_linked_local_rules'] else 'no', 'yes' if v['county_linked_forms'] else 'no',
            'yes' if v['county_linked_clerk_page'] else 'no', v['directory_records_on_court_hosts_not_county_linked'],
            v['source_directory_reference_count']))
    Tm = []
    Tm.append('| Topic | Total hits | States with zero statute hits | States with zero court-rule hits |')
    Tm.append('|---|---:|---|---|')
    for k, tv in stage['topic_gaps'].items():
        zs = tv['states_with_zero_statute_hits']
        zc = tv['states_with_zero_court_rule_hits']
        show_cr = k in ('class_action', 'expert_evidence', 'complex_coordination')
        Tm.append('| %s | %s | %s | %s |' % (k, '{:,}'.format(tv['total_hits_all_jurisdictions']),
                                          ('%d: ' % len(zs)) + ', '.join(zs), (('%d: ' % len(zc)) + ', '.join(zc)) if show_cr else 'n/a (statutory topic)'))
    U = []
    U.append('| State | Statute pages >=20k / 2k-20k / <2k chars | Court-rule pages >=20k / 2k-20k / <2k chars |')
    U.append('|---|---|---|')
    for a, r in M.items():
        us = r['directory']['unreviewed_text_size']
        s_ = us.get('statutes', {})
        r_ = us.get('court_rules', {})
        if s_.get('ge_20k', 0) + r_.get('ge_20k', 0) + s_.get('2k_to_20k', 0) + r_.get('2k_to_20k', 0) >= 40:
            U.append('| %s | %d / %d / %d | %d / %d / %d |' % (
                a, s_.get('ge_20k', 0), s_.get('2k_to_20k', 0), s_.get('lt_2k', 0),
                r_.get('ge_20k', 0), r_.get('2k_to_20k', 0), r_.get('lt_2k', 0)))
    final['unreviewed_official_pages_text_size_totals'] = dict(size_tot)
    json.dump(final, open(OUT + '/coverage_matrix.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    md_path = OUT + '/state_county_gaps.md'
    md = open(md_path, encoding='utf-8').read()
    try:
        old = json.load(open(OUT + '/_work/generated_tables.json', encoding='utf-8'))
    except OSError:
        old = {}
    for key, name, tbl in (('{{STATE_TABLE}}', 'state_table', L), ('{{VENUE_TABLE}}', 'venue_table', V),
                           ('{{TOPIC_TABLE}}', 'topic_table', Tm), ('{{UNREV_TABLE}}', 'unreviewed_table', U)):
        new_text = '\n'.join(tbl)
        old_text = '\n'.join(old.get(name) or [])
        if key in md:
            md = md.replace(key, new_text)
        elif old_text and old_text in md:
            md = md.replace(old_text, new_text)
    open(md_path, 'w', encoding='utf-8', newline='\n').write(md)
    print('size totals', dict(size_tot))
    json.dump({'state_table': L, 'venue_table': V, 'topic_table': Tm, 'unreviewed_table': U, 'totals': dict(totals),
               'flag_index': dict(flag_index), 'directory_topics': directory_topics},
              open(OUT + '/_work/generated_tables.json', 'w', encoding='utf-8'), indent=1)
    print(json.dumps(dict(totals), indent=0))
    print('\n'.join(V))
    for k, v in directory_topics.items():
        print(k, v['total'], v['law_or_federal_hits'][:5])


if __name__ == '__main__':
    main()
