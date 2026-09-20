"""Capture real adapter responses and write sources/federal_regulations_20260919/integration_spec.json."""
import json
import sys
import time
from pathlib import Path

ROOT = Path('C:/Users/firas/Downloads/SCRAPE')
sys.path.insert(0, str(ROOT / 'delivery/archive-directory'))
import federal_regulations as regs  # noqa: E402

OUT = ROOT / 'sources/federal_regulations_20260919/integration_spec.json'
TEXT_LIMIT = 400
LIST_LIMIT = 3
FORBIDDEN = ('Users', 'sqlite3', str(ROOT), 'C:/', 'C:\\')


def trim(value, key=None):
    if isinstance(value, dict):
        return {k: trim(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [trim(v, key) for v in value[:LIST_LIMIT]]
    if isinstance(value, str) and len(value) > TEXT_LIMIT and key in ('text', 'dates_text_raw', 'detail', 'authority_note_as_printed'):
        return value[:TEXT_LIMIT] + ' ...[trimmed for the example; %d characters in the live response]' % len(value)
    return value


def walk(value):
    yield value
    if isinstance(value, dict):
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def timed(fn, *args, **kwargs):
    start = time.time()
    result = fn(*args, **kwargs)
    return result, round(time.time() - start, 3)


regs.reset_cache()
info, t_info = timed(regs.info)
assert info['ready'], info
calls = {}
calls['info'] = (info, t_info)
calls['titles'] = timed(regs.titles)
calls['parts'] = timed(regs.parts, '21')
calls['sections'] = timed(regs.sections, '21:314')
calls['sections_as_of'] = timed(regs.sections, 'cfr:21:314', as_of='2019-06-01')
calls['section'] = timed(regs.section, '21 C.F.R. § 314.80')
calls['section_publisher_only'] = timed(regs.section, '16 CFR 1115.4')
calls['search_text'] = timed(regs.search, q='medical device report', title='21', part='803', limit=3)
calls['search_publisher_text'] = timed(regs.search, q='substantial product hazard', title='16', limit=3)
calls['search_amended'] = timed(regs.search, date_type='amendment_date', dfrom='2025-01-01', dto='2025-12-31', record_type='section', limit=3)
calls['search_fr'] = timed(regs.search, q='postmarketing safety', record_type='fr_document', date_type='fr_publication_date', dfrom='2014', dto='2016', limit=3)
calls['agencies'] = timed(regs.agencies, slice_only=True)
doc_id = calls['section'][0]['related_fr_documents']['documents'][0]['document_number']
calls['fr_document'] = timed(regs.fr_document, doc_id)
calls['search_error'] = timed(regs.search, date_type='made_up')

print('timings:', {k: v[1] for k, v in calls.items()})
print('counts:', json.dumps(info['counts']))
print('publisher_index:', info['publisher_index'])
print('titles:', [(t['title'], t['parts_total'], t['parts_in_slice'], t['official_text_local']) for t in calls['titles'][0]['titles']])
print('parts 21 slice total:', calls['parts'][0]['total'], 'first part temporal:', calls['parts'][0]['parts'][0]['temporal']['source_as_of'])
print('sections 21:314 total:', calls['sections'][0]['total'])
print('as_of block:', {k: v for k, v in calls['sections_as_of'][0]['as_of'].items() if k != 'caveat'})
sec = calls['section'][0]
print('section texts:', [(t['source'], t['text_hash_verified'], t['text_length'], t['temporal']['source_as_of']) for t in sec['texts']])
print('section history:', [(h['ecfr_amendment_date'], h['ecfr_issue_date'], h['substantive']) for h in sec['history']])
print('section printed cites:', len(sec['printed_fr_citations']), 'resolved', sec['related_fr_documents']['printed_citations_resolved'],
      'part docs', sec['related_fr_documents']['part_documents_total'], 'listed', len(sec['related_fr_documents']['documents']))
print('section reconciliation:', sec['reconciliation']['category'])
p16 = calls['section_publisher_only'][0]
print('16/1115.4 texts:', [(t['source'], t['text_hash_verified'], t['unavailable_reason']) for t in p16['texts']])
for name in ('search_text', 'search_publisher_text', 'search_amended', 'search_fr'):
    r = calls[name][0]
    print(name, 'total', r['total'], 'first', [(x['id'], x.get('matched_in')) for x in r['results'][:3]], 'publisher', r['publisher_index'])
print('agencies slice:', [(a['slug'], len(a['slice_parts'])) for a in calls['agencies'][0]['agencies']])
print('search_error:', calls['search_error'][0].get('error'))

bad = set()
for name, (value, _) in calls.items():
    for block in walk(value):
        if isinstance(block, str):
            for needle in FORBIDDEN:
                if needle in block:
                    bad.add((name, needle, block[:80]))
print('forbidden strings found:', sorted(bad)[:10])
assert not bad

examples = {name: trim(value) for name, (value, _) in calls.items()}
note = 'Real responses captured from the adapter on 2026-09-19; lists trimmed to %d items and long texts to %d characters for readability.' % (LIST_LIMIT, TEXT_LIMIT)

signatures = {
    'module': 'delivery/archive-directory/federal_regulations.py',
    'test': 'delivery/archive-directory/test_federal_regulations.py',
    'gate': 'validation.json status == "passed" and ready == true; every data_files entry re-hashed (SHA-256) and re-verified when size/mtime changes; '
            'SQLite opened read-only per call; closed gate -> ready/available false, empty lists, None',
    'constants': {'DEFAULT_LIMIT': regs.DEFAULT_LIMIT, 'MAX_LIMIT': regs.MAX_LIMIT, 'LIST_DEFAULT_LIMIT': regs.LIST_DEFAULT_LIMIT,
                  'LIST_MAX_LIMIT': regs.LIST_MAX_LIMIT, 'RELATED_DOCS_LIMIT': regs.RELATED_DOCS_LIMIT,
                  'DATE_TYPES': regs.DATE_TYPES, 'TEXT_SOURCES': regs.TEXT_SOURCES, 'RECORD_TYPES': list(regs.RECORD_TYPES)},
    'functions': [
        {'name': 'info', 'signature': 'info() -> dict', 'returns': 'ready/available flags, reason, validation counts (+ live counts), checks, qualification, license_ref, publisher_index availability, DATE_TYPES, TEXT_SOURCES, limits'},
        {'name': 'titles', 'signature': 'titles() -> dict', 'returns': '{available, reason, total, titles:[title]} ordered by title number'},
        {'name': 'parts', 'signature': 'parts(title, include_all=False, page=1, limit=500) -> dict', 'returns': '{available, reason, title, include_all, total, page, limit, pages, parts:[part]}; slice parts only unless include_all'},
        {'name': 'sections', 'signature': 'sections(part, as_of=None, title=None, page=1, limit=500) -> dict',
         'returns': '{available, reason, found, part, as_of, total, page, limit, pages, sections:[section summary]}; part accepts cfr:21:314, 21:314, "21 CFR 314" or 314 with title=; as_of=YYYY-MM-DD lists identifiers present per eCFR version metadata (as_of.supported false with reason before the history start or for malformed dates)'},
        {'name': 'section', 'signature': 'section(citation) -> dict | None',
         'returns': 'summary + texts[] (one per source: gpo_ecfr_xml, open_us_law), history[] (eCFR versions), amendment_citations_as_printed, printed_fr_citations, related_fr_documents, reconciliation; citation accepts "21 C.F.R. § 314.80", "21 CFR 314.80", "cfr:21:314.80"'},
        {'name': 'fr_document', 'signature': 'fr_document(document_number) -> dict | None  (alias: document)',
         'returns': 'Federal Register metadata with publication_date, effective_on_publisher_extracted, dates_text_raw, docket_ids, regulation_id_numbers, agencies, cfr_parts_linked, cited_by_sections, urls'},
        {'name': 'agencies', 'signature': 'agencies(slice_only=False, q=None) -> dict', 'returns': '{available, reason, total, agencies:[agency]}; agencies with slice_parts first'},
        {'name': 'search', 'signature': 'search(q=None, title=None, part=None, agency=None, record_type=None, date_type=None, dfrom=None, dto=None, page=1, limit=25) -> dict',
         'returns': '{available, reason, total, page, limit, pages, results:[section summary | fr_document summary with matched_in], filters, date_filter, publisher_index, error?}'},
        {'name': 'reset_cache', 'signature': 'reset_cache() -> None', 'returns': 'drops the gate cache (tests / after a rebuild)'},
    ],
}

routes = [
    {'route': '/api/regulations/titles', 'method': 'GET', 'adapter': 'titles()', 'params': {}, 'example': examples['titles']},
    {'route': '/api/regulations/parts', 'method': 'GET', 'adapter': "parts(title, include_all, page, limit)",
     'params': {'title': 'CFR title number (16, 21, 40, 49); required', 'include_all': '1 to list every eCFR-structure part, default slice parts only',
                'page': 'default 1', 'limit': 'default 500, max 1000'}, 'example': examples['parts']},
    {'route': '/api/regulations/sections', 'method': 'GET', 'adapter': 'sections(part, as_of, title, page, limit)',
     'params': {'part': 'cfr:21:314 | 21:314 | "21 CFR 314" | 314 (with title); required', 'title': 'title number when part is bare',
                'as_of': 'YYYY-MM-DD; optional; metadata-only listing, see as_of.caveat', 'page': 'default 1', 'limit': 'default 500, max 1000'},
     'example': examples['sections'], 'example_as_of': examples['sections_as_of']},
    {'route': '/api/regulation', 'method': 'GET', 'adapter': 'section(citation)',
     'params': {'citation': '"21 C.F.R. § 314.80" | "21 CFR 314.80" | "cfr:21:314.80"; required; 404 when the adapter returns None'},
     'example': examples['section'], 'example_publisher_text_only': examples['section_publisher_only']},
    {'route': '/api/regulations/search', 'method': 'GET', 'adapter': 'search(q, title, part, agency, record_type, date_type, dfrom, dto, page, limit)',
     'params': {'q': 'words, each a prefix, all required; matched in section headings, local GPO text, Open US Law publisher text (on demand) and Federal Register titles/metadata',
                'title': 'title number', 'part': 'part reference as for /sections', 'agency': 'eCFR agency slug, e.g. food-and-drug-administration',
                'record_type': 'section | fr_document', 'date_type': 'one of DATE_TYPES; required when dfrom/dto are given',
                'dfrom': 'YYYY | YYYY-MM | YYYY-MM-DD inclusive', 'dto': 'same', 'page': 'default 1', 'limit': 'default 25, max 100'},
     'example': examples['search_text'], 'example_publisher_text_hit': examples['search_publisher_text'],
     'example_amendment_date_filter': examples['search_amended'], 'example_fr_documents': examples['search_fr'], 'example_error': examples['search_error']},
    {'route': '/api/regulations/agencies', 'method': 'GET', 'adapter': 'agencies(slice_only, q)',
     'params': {'slice_only': '1 to return only the agencies that map to slice parts', 'q': 'substring on name/short name/slug'}, 'example': examples['agencies']},
    {'route': '/api/regulations/document', 'method': 'GET', 'adapter': 'fr_document(id)',
     'params': {'id': 'Federal Register document number, with or without the fr_doc: prefix; required; 404 when None'}, 'example': examples['fr_document']},
]

ui = {
    'area': 'Regulations',
    'area_key': 'regulations',
    'placement': 'New top-level area rendered by areas.js through window.ARCHIVE_AREAS, between Agency safety and Judges; the Federal area of the directory stays as is.',
    'pages': [
        {'page': 'Browse', 'section': 'Title > Part > Section tree', 'source': '/api/regulations/titles, /parts?title=, /sections?part=',
         'labels': ['Official text local (Title 21 only)', 'Publisher text on demand', 'In research slice'],
         'filters': [{'name': 'Title', 'values': ['16', '21', '40', '49']}, {'name': 'Slice only / all parts', 'param': 'include_all'},
                     {'name': 'As of date (metadata only)', 'param': 'as_of'}]},
        {'page': 'Section', 'section': 'Texts side by side (GPO official copy, Open US Law publisher copy), History, Printed amendment citations, Related Federal Register documents, Reconciliation',
         'source': '/api/regulation?citation=',
         'labels': ['GPO volume amendment marker (AMDDATE)', 'eCFR amendment date', 'eCFR issue date', 'Publisher snapshot date', 'Hash verified / not served']},
        {'page': 'Search', 'section': 'Regulations search',
         'source': '/api/regulations/search',
         'filters': [{'name': 'Text', 'param': 'q'}, {'name': 'Title', 'param': 'title'}, {'name': 'Part', 'param': 'part'},
                     {'name': 'Agency', 'param': 'agency', 'source': '/api/regulations/agencies?slice_only=1'},
                     {'name': 'Record type', 'param': 'record_type', 'values': ['section', 'fr_document']},
                     {'name': 'Date type', 'param': 'date_type', 'values': list(regs.DATE_TYPES), 'labels': regs.DATE_TYPES},
                     {'name': 'From / to', 'params': ['dfrom', 'dto']}],
         'result_badges': ['matched_in: heading | gpo_text | open_us_law_text | fr_title | fr_metadata', 'record_type']},
        {'page': 'Federal Register document', 'section': 'Document metadata', 'source': '/api/regulations/document?id=',
         'labels': ['Publication date (publisher)', 'Effective date as extracted by the publisher (unverified)', 'Docket ids', 'RINs', 'CFR parts referenced', 'Cited by sections']},
    ],
    'caveats': [
        'Official regulation text is held locally only for Title 21 (GPO govinfo eCFR bulk XML); its currency is the printed volume amendment marker, not a per-section date. eCFR is authoritative but unofficial; the official edition is the annual CFR.',
        'Titles 16, 40 and 49 show publisher text from the Open US Law index (Vaquill AI, CC BY 4.0) read on demand; it carries a snapshot date, not an as-of or effective date, and is served only when its hash matches the build-time hash.',
        'Amendment and issue dates are eCFR version metadata since 2016/2017; the as-of listing is metadata only and omits sections without version rows (count shown); it is never point-in-time text.',
        'Federal Register dates are publisher fields; effective_on is publisher-extracted and unverified; effective_from/effective_to are never inferred and always null.',
        'Related Federal Register documents are linked either by a printed amendment note resolved by volume and page, or by the publisher\'s cfr_references to the whole part; neither is a per-section legal assertion.',
        'Title 40 parts have no Federal Register document links (packet budget, see gaps.json).',
    ],
}

spec = {'schema_version': '1', 'supplement': 'sources/federal_regulations_20260919', 'adapter': signatures, 'routes': routes, 'ui': ui,
        'example_note': note, 'edges': {'file': 'edges.jsonl', 'rows': info['counts'].get('edges'),
                                        'description': 'Relationship edges emitted by build.py (cfr section/part <-> fr_doc, agency -> cfr part, oul row -> cfr section); the adapter does not serve them directly; unresolved joins are in unresolved.jsonl with reasons.'},
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime())}
text = json.dumps(spec, indent=1, ensure_ascii=False)
for needle in FORBIDDEN:
    assert needle not in text, needle
OUT.write_text(text + '\n', encoding='utf-8')
print('wrote', OUT.name, len(text), 'chars')
