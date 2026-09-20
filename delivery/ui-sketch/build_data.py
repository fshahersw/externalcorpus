"""Create a small wireframe dataset from the already saved delivery manifests."""
import json
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PKG = ROOT / 'delivery/focused_legal_corpus'

def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]

laws = []
for filename, publisher in [('official_resources.jsonl', 'Official source'), ('trellis_law_captures.jsonl', 'Trellis')]:
    for r in rows(PKG / 'laws' / filename):
        body = r.get('body_status', '')
        status = 'Legal body identified' if body.startswith('observed_') or body.startswith('verified_') else 'Directory' if body == 'directory_navigation' else 'Body missing' if body == 'missing_body/storage_placeholder' or body == 'no_verified_nonempty_text' else 'Saved text · review scope'
        laws.append({'title': r.get('title') or r['source_url'], 'state': r['jurisdiction'], 'kind': r.get('category', ''), 'publisher': publisher, 'status': status, 'url': r['source_url'], 'raw': r.get('raw_path'), 'text': r.get('text_path'), 'hash': r.get('raw_sha256'), 'bodyStatus': body, 'excerpt': ''})
        if publisher == 'Trellis' and body == 'observed_nonempty_legal_container' and len([x for x in laws if x['excerpt']]) < 30 and r.get('capture_kind') == 'provider_rendered_public_page':
            raw = json.loads((ROOT / r['raw_path']).read_text(encoding='utf-8'))
            html = raw.get('data', raw).get('html', '')
            node = BeautifulSoup(html, 'html.parser').select_one('div.rule-header')
            if node:
                for child in node.select('h1,script,style'):
                    child.decompose()
                laws[-1]['excerpt'] = node.get_text(' ', strip=True)[:4500]

counties = []
for r in rows(PKG / 'counties/counties.jsonl'):
    counties.append({'title': r['name'], 'state': r['state'], 'kind': 'County equivalent', 'publisher': 'Census + saved source evidence',
        'status': {'matched_saved_profile': 'Profile saved', 'ambiguous_candidate_only': 'Match needs review'}.get(r['trellis_profile_status'], 'Inventory only'),
        'geoid': r['geoid'], 'vintage': r['geography_vintage'], 'sites': r['reported_website_urls'], 'candidates': r['registry_candidate_urls'],
        'siteSaved': bool(r['reported_site_capture_ids']), 'url': (r['trellis_profile_urls'] or [''])[0], 'raw': (r['trellis_raw_paths'] or [''])[0],
        'text': (r['reported_site_text_paths'] or [''])[0], 'hash': '', 'excerpt': ''})

judges = []
for r in rows(PKG / 'judges/sources.jsonl'):
    judges.append({'title': r['title'], 'state': r['state'], 'kind': r['source_type'], 'publisher': 'Official source', 'status': 'Saved source',
        'url': r['source_url'], 'raw': r.get('raw_path'), 'text': r.get('text_path') or (r.get('text_paths') or [''])[0], 'hash': r.get('raw_sha256'),
        'edition': r.get('edition_note'), 'excerpt': ''})

law_summary = json.loads((PKG / 'laws/summary.json').read_text(encoding='utf-8-sig'))
package_summary = json.loads((PKG / 'summary.json').read_text(encoding='utf-8-sig'))
county_summary = json.loads((PKG / 'counties/summary.json').read_text(encoding='utf-8-sig'))
data = {'laws': laws, 'counties': counties, 'judges': judges,
    'stats': {'countyInventory': len(counties), 'countyMatched': county_summary['matched_counties'], 'trellisProfiles': county_summary['trellis_profile_rows'], 'lawSources': law_summary['official']['downloaded_resource_urls'], 'trellisLaws': law_summary['trellis']['saved_representations'], 'trellisBodies': 443, 'judgeSources': len(judges), 'judgeRosterStates': 28, 'searchableTexts': package_summary['distinct_searchable_texts'], 'pendingLawUrls': law_summary['trellis']['observed_uncollected_urls']},
    'snapshot': 'September 13, 2026'}
serialized = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
(HERE / 'data.js').write_text('window.ARCHIVE = ' + serialized + ';\n', encoding='utf-8')
print(json.dumps({'laws': len(laws), 'counties': len(counties), 'judge_sources': len(judges), 'sample_excerpts': sum(bool(r['excerpt']) for r in laws), 'network_requests': 0}))
