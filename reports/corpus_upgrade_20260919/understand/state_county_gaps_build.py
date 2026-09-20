"""Read-only builder for the state/county coverage matrix (stage 1).

Opens every SQLite database with mode=ro, makes no network request and writes only
inside reports/corpus_upgrade_20260919/understand/. The Open US Law topical numbers are
read from _work/oul_analysis.json, produced by state_county_gaps_topics.py.
"""
import collections
import datetime
import json
import re
import sqlite3

ROOT = 'C:/Users/firas/Downloads/SCRAPE'
OUT = ROOT + '/reports/corpus_upgrade_20260919/understand'
WORK = OUT + '/_work'

STATES = [
    ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'), ('CA', 'California'),
    ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'), ('DC', 'District of Columbia'),
    ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'), ('IL', 'Illinois'),
    ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'),
    ('ME', 'Maine'), ('MD', 'Maryland'), ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'),
    ('MS', 'Mississippi'), ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
    ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
    ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'), ('OR', 'Oregon'),
    ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'), ('SD', 'South Dakota'),
    ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'), ('VA', 'Virginia'),
    ('WA', 'Washington'), ('WV', 'West Virginia'), ('WI', 'Wisconsin'), ('WY', 'Wyoming'),
]
NAME2AB = {n: a for a, n in STATES}
SLUG2AB = {n.lower().replace(' ', '-'): a for a, n in STATES}

BODY = {'law_chapter_body', 'verified_law_document_derivative', 'legal_text_fragment',
        'captured_law_representation', 'law_text_fragment', 'observed_comprehensive_constitution'}
REVIEW = {'needs_content_review', 'law_document_title_evidence_needs_review'}
NAV = {'legal_inventory_navigation'}
SITE = {'county_government_entry_unreviewed', 'county_government_website_to_verify',
        'county_government_entry', 'county_government'}
LOCAL_RULES = {'local_rules', 'juvenile_probate_local_rules_text',
               'court_administrative_orders_local_rules_index', 'court_local_rules_download_landing'}
LOCAL_FORMS = {'court_forms_filing_documents', 'court_filing_fee_schedule', 'judicial_records_request_form'}


def ro(path):
    return sqlite3.connect('file:' + path + '?mode=ro', uri=True)


def tier(kind):
    ks = {k.strip() for k in kind.split(';')}
    if ks & BODY:
        return 'body'
    if ks & NAV:
        return 'navigation'
    if ks & REVIEW:
        return 'unreviewed_page'
    return 'other'


def cat_tokens(cat):
    toks = {t.strip() for t in (cat or '').split(';')}
    out = set()
    if 'statutes' in toks:
        out.add('statutes')
    if 'constitution' in toks:
        out.add('constitution')
    if 'administrative_code' in toks:
        out.add('regulations')
    if 'court_rules' in toks:
        out.add('court_rules')
    if 'state_rule' in toks:
        out.add('trellis_state_rule')
    return out or {'other_law'}


def county_bucket(kind):
    k = kind.split(';')[0].strip()
    if k in SITE:
        return 'county_site_pages'
    if k == 'coverage_county':
        return 'trellis_county_profile'
    if k in LOCAL_RULES:
        return 'local_rules'
    if k in LOCAL_FORMS:
        return 'local_forms_fees'
    if k == 'court_clerk_office':
        return 'clerk_pages'
    if k == 'court_local_resources':
        return 'court_local_resources'
    if k == 'local_laws_codes' or 'ordinance' in k:
        return 'local_laws_codes'
    return 'other_county'


def main():
    M = {a: {'state': n, 'abbr': a} for a, n in STATES}
    for a in M:
        M[a]['directory'] = {
            'focused_laws': collections.defaultdict(collections.Counter),
            'seeger': collections.Counter(),
            'pending_publication': collections.Counter(),
            'county_records': collections.Counter(),
            'county_distinct_geoids': collections.defaultdict(set),
        }

    c = ro(ROOT + '/delivery/archive-directory/directory.sqlite3')
    geo_by_rec = collections.defaultdict(set)
    for rid, g in c.execute('select record_id,geoid from record_counties'):
        geo_by_rec[rid].add(g)
    unk_state = collections.Counter()
    sql = ("select id,dataset,group_name,kind,state,payload from records where dataset in "
           "('focused','seeger','pending_publication','trellis_browser_counties') "
           "and group_name in ('laws','counties')")
    for rid, ds, grp, kind, state, payload in c.execute(sql):
        a = NAME2AB.get(state or '')
        if not a:
            unk_state[ds + '/' + grp + '/' + str(state)] += 1
            continue
        D = M[a]['directory']
        if grp == 'laws':
            if ds == 'focused':
                try:
                    cat = json.loads(payload).get('category')
                except Exception:
                    cat = ''
                for t in cat_tokens(cat):
                    D['focused_laws'][t][tier(kind)] += 1
            elif ds == 'seeger':
                D['seeger'][kind] += 1
            elif ds == 'pending_publication':
                D['pending_publication'][kind] += 1
        else:
            k2 = county_bucket(kind)
            if ds == 'pending_publication':
                k2 = 'pending_' + k2
            D['county_records'][k2] += 1
            for g in geo_by_rec.get(rid, ()):
                D['county_distinct_geoids'][k2].add(g)

    for st, pl in c.execute('select state,payload from counties'):
        a = NAME2AB.get(st)
        if not a:
            continue
        d = json.loads(pl)
        R = M[a].setdefault('county_registry', collections.Counter())
        R['counties_total'] += 1
        if d.get('saved_profiles'):
            R['with_saved_trellis_profile'] += 1
        if d.get('saved_sites'):
            R['with_saved_site_page'] += 1
        if d.get('local_resources'):
            R['with_local_resource'] += 1
        if d.get('published_local_resources'):
            R['with_published_local_resource'] += 1
        if d.get('website_evidence_status') == 'no_associated_website_evidence':
            R['no_website_evidence'] += 1

    o = ro(ROOT + '/sources/open_us_law_20260918/catalog.sqlite3')
    for st, k, rows in o.execute('select state,kind,sum(rows) from files group by 1,2'):
        if st in M:
            M[st].setdefault('open_us_law', {})[k] = rows
    oul = json.load(open(WORK + '/oul_analysis.json', encoding='utf-8'))
    for a in M:
        sets = oul['court_rule_sets'].get(a, [])

        def has(pat, sets=sets):
            rx = re.compile(pat, re.I)
            return sum(x['rows'] for x in sets if rx.search(x['chapter_name'] + ' ' + x['title_name']))

        M[a].setdefault('open_us_law', {})
        M[a]['open_us_law_court_rule_sets'] = {
            'rows_total': sum(x['rows'] for x in sets),
            'civil_label_rows': has(r'civil'),
            'evidence_label_rows': has(r'eviden'),
            'appellate_label_rows': has(r'appell|appeal'),
            'top_sets': [{'name': (x['chapter_name'] or x['title_name']), 'rows': x['rows']} for x in sets[:8]],
            'basis': 'keyword match on publisher chapter_name/title_name; heuristic only',
        }
        M[a]['topics_open_us_law'] = {
            t: {k: v for k, v in oul['topics'][t]['by_state'].get(a, {}).items()
                if k in ('statutes', 'court_rules', 'regulations')}
            for t in oul['topics']
        }

    t = ro(ROOT + '/sources/trellis/catalog/catalog.sqlite3')
    obs = set(u for (u,) in t.execute("select distinct url from links where category='coverage_county'"))
    saved = set(u for (u,) in t.execute("select url from pages where category='coverage_county' and status=200"))
    rx = re.compile(r'https://trellis\.law/coverage/([^/]+)/([^/?#]+)')
    tre = collections.defaultdict(lambda: {'observed': 0, 'saved': 0})
    odd = []
    unsaved_by_state = collections.defaultdict(list)
    for u in sorted(obs | saved):
        m = rx.match(u)
        if not m:
            continue
        s, slug = m.groups()
        if re.search(r'\.(gov|org|us|com)$', slug):
            odd.append(u)
            continue
        a = SLUG2AB.get(s)
        if not a:
            continue
        tre[a]['observed'] += 1
        if u in saved:
            tre[a]['saved'] += 1
        else:
            unsaved_by_state[a].append(u)
    for a in M:
        M[a]['trellis_county_profiles'] = dict(tre.get(a, {'observed': 0, 'saved': 0}))

    cat = json.load(open(ROOT + '/sources/public_law_directory_20260919/catalog.json', encoding='utf-8'))['entries']
    linked = set()
    for line in open(ROOT + '/sources/source_archive_links_20260919/links.jsonl', encoding='utf-8'):
        linked.add(json.loads(line)['source_id'])
    for a in M:
        M[a]['source_directory'] = {'references': 0, 'linked_to_saved': 0, 'by_category': collections.Counter()}
    for e in cat:
        a = (e.get('jurisdiction') or '').upper()
        if a in M:
            S = M[a]['source_directory']
            S['references'] += 1
            S['by_category'][e['category']] += 1
            if e['id'] in linked:
                S['linked_to_saved'] += 1

    for a, row in M.items():
        O = row.get('open_us_law', {})
        D = row['directory']
        fl = D['focused_laws']
        flags = []
        if not O.get('statutes'):
            flags.append('open_us_law_statutes_absent' + ('_publisher_withdrawn' if a in ('GA', 'NC') else ''))
        if not O.get('court_rules'):
            flags.append('open_us_law_court_rules_absent')
        if not O.get('regulations'):
            flags.append('open_us_law_regulations_absent')
        if not O.get('constitutions') and a != 'DC':
            flags.append('open_us_law_constitution_absent')
        crs = row['open_us_law_court_rule_sets']
        if O.get('court_rules'):
            if not crs['civil_label_rows']:
                flags.append('no_civil_labelled_rule_set')
            if not crs['evidence_label_rows']:
                flags.append('no_evidence_labelled_rule_set')
            if not crs['appellate_label_rows']:
                flags.append('no_appellate_labelled_rule_set')
        st_body = fl['statutes']['body']
        st_any = sum(fl['statutes'].values())
        if st_any and not st_body:
            flags.append('official_statute_captures_nav_or_unreviewed_only')
        if not st_any and not D['seeger'].get('statutory_provision'):
            flags.append('no_official_statute_capture')
        cr_off = sum(fl['court_rules'].values()) + D['seeger'].get('court_rule_or_order', 0)
        if not cr_off and not O.get('court_rules'):
            flags.append('ZERO_COURT_RULES_ANY_SOURCE')
        elif not cr_off:
            flags.append('no_official_court_rule_capture')
        if not sum(fl['regulations'].values()) and not O.get('regulations'):
            flags.append('ZERO_REGULATIONS_ANY_SOURCE')
        if not D['seeger'].get('court_form_or_other_document'):
            flags.append('no_statewide_forms')
        cr = D['county_records']
        if not cr.get('local_rules') and not cr.get('pending_local_rules'):
            flags.append('no_county_local_rules')
        if not cr.get('local_forms_fees') and not cr.get('pending_local_forms_fees'):
            flags.append('no_county_forms')
        if not cr.get('clerk_pages'):
            flags.append('no_clerk_pages')
        tp = row['trellis_county_profiles']
        if tp['observed'] == 0:
            flags.append('trellis_no_county_profiles_observed')
        elif tp['saved'] < tp['observed']:
            flags.append('trellis_profiles_partial')
        row['flags'] = flags
        D['focused_laws'] = {k: dict(v) for k, v in fl.items()}
        D['seeger'] = dict(D['seeger'])
        D['pending_publication'] = dict(D['pending_publication'])
        D['county_records'] = dict(cr)
        D['county_distinct_geoids'] = {k: len(v) for k, v in D['county_distinct_geoids'].items()}
        row['county_registry'] = dict(row.get('county_registry', {}))
        row['source_directory']['by_category'] = dict(row['source_directory']['by_category'])

    topic_gaps = {}
    for tname, tv in oul['topics'].items():
        topic_gaps[tname] = {
            'query': tv['query'],
            'total_hits_all_jurisdictions': tv['total'],
            'states_with_zero_statute_hits': [a for a in M if not tv['by_state'].get(a, {}).get('statutes')],
            'states_with_zero_court_rule_hits': [a for a in M if not tv['by_state'].get(a, {}).get('court_rules')],
        }
    result = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'records_without_recognised_state': dict(unk_state),
        'trellis_nonstandard_observed_urls': odd,
        'trellis_unsaved_profile_urls_by_state': dict(unsaved_by_state),
        'topic_gaps': topic_gaps,
        'states': M,
    }
    json.dump(result, open(WORK + '/coverage_matrix_stage1.json', 'w', encoding='utf-8'), indent=1, default=str)
    print('unrecognised', dict(unk_state))
    print('odd', odd)
    fc = collections.Counter(f for r in M.values() for f in r['flags'])
    for f, n in fc.most_common():
        print(n, f, [a for a in M if f in M[a]['flags']] if n <= 26 else '')


if __name__ == '__main__':
    main()
