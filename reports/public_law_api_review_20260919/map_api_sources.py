"""Map explicit registry/API references without guessing endpoints or auth."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json
import re
import sqlite3

HERE = Path(__file__).resolve().parent
SOURCE = Path('C:/Users/firas/Downloads/registry_v06_1.sqlite')
MARKDOWN = Path('C:/Users/firas/Downloads/publicLaw_directory.md')
PATTERN = re.compile(r'(?i)(/api(?:[/?-]|$)|/apis/|api[.-]|api-doc|developer|bulk.?data|data.?dump|/feeds?(?:[/.?]|$)|atom\.xml)')
VERIFIED = {
    'https://docs.openstates.org/api-v3/': {'status': 'key_required', 'method': 'X-API-KEY header or apikey query parameter', 'source': 'https://docs.openstates.org/api-v3/', 'note': 'Legislative information; people here are legislators, governors and other political offices, not a judge database.'},
    'https://legislature.vermont.gov/docs/api/v1/index.html': {'status': 'key_required', 'method': 'Authorization: Bearer key example; HTTPS required', 'source': 'https://legislature.vermont.gov/docs/api/v1/index.html', 'note': 'Publisher says obtain a key from legislature IT; wording mentions Basic Auth but the actual example uses Bearer. Preserve this documentation inconsistency until tested.'},
    'https://api.data.gov/docs/developer-manual/': {'status': 'key_required', 'method': 'X-Api-Key, supported query parameter or Basic Auth', 'source': 'https://api.data.gov/docs/developer-manual/', 'note': 'Shared gateway defaults are 1000 requests/hour, but agency-specific limits override them. DEMO_KEY has lower limits and is for exploration.'},
    'https://github.com/usgpo/api': {'status': 'key_required', 'method': 'api.data.gov key', 'source': 'https://github.com/usgpo/api', 'note': 'Current publisher README states 36000/hour,1200/minute,40/second default ceilings. Actual key response headers remain authoritative; no acquisition at those rates attempted.'},
    'https://api.govinfo.gov/docs/': {'status': 'key_required', 'method': 'api.data.gov key', 'source': 'https://github.com/usgpo/api', 'note': 'Interactive documentation returned a client-side shell; authentication established from the publisher repository.'},
    'https://open.gsa.gov/api/regulationsgov/': {'status': 'key_required', 'method': 'X-Api-Key header', 'source': 'https://open.gsa.gov/api/regulationsgov/', 'note': 'Read endpoints cover regulatory documents, comments and dockets. Submission endpoints are outside this acquisition scope.'},
    'https://law.lis.virginia.gov/developers': {'status': 'not_stated_on_reviewed_page', 'method': None, 'source': 'https://law.lis.virginia.gov/developers/', 'note': 'Official page confirms JSON/XML services plus PDF/CSV law-library downloads. The page does not establish credential requirements for each endpoint.'},
    'https://www.ecfr.gov/developers/documentation/api/v1': {'status': 'unverified', 'method': None, 'source': 'https://www.ecfr.gov/developers/documentation/api/v1', 'note': 'Documentation shell was reachable, but rendered text did not expose a key policy; do not infer unrestricted bulk access.'},
    'https://www.federalregister.gov/developers/documentation/api/v1': {'status': 'unverified', 'method': None, 'source': 'https://www.federalregister.gov/developers/documentation/api/v1', 'note': 'Registry says registration; rendered documentation did not establish the key policy. Historical tag retained, not promoted into verified API requirements.'},
}


def classify(row):
    url = row['url']; low = url.lower()
    if row['domain'] == 'npiregistry.cms.hhs.gov' and urlsplit(url).path.rstrip('/') == '/api': return 'explicit_query_endpoint'
    if low.startswith('https://api.nhtsa.gov/recalls/'): return 'explicit_query_endpoint'
    if '/feeds/' in low or low.endswith('/feeds/opinions'): return 'explicit_feed_url'
    if low.endswith('/bulkdata/submissions.zip'): return 'explicit_archive_download'
    if '/bulkdata' in low or low == 'https://open.fda.gov/data/downloads/': return 'bulk_download_directory'
    if 'api-signup' in low or 'request-an-api-key' in low: return 'credential_registration_page'
    if low.startswith('https://api.edgarfiling.') or '/create-manage-filer-user-api-tokens' in low: return 'filing_workflow_documentation_not_read_api'
    if any(x in low for x in ['docs','developer','/apis/','api-doc','api-page','open.gsa.gov/api/','about/api','app-support-web-services','github.com/usgpo/api','edgar-application-programming-interfaces','crashapi']): return 'api_documentation_or_service_landing'
    if row['content_kind'] == 'api': return 'api_service_landing_unverified_call'
    return 'related_reference_not_callable_endpoint'


def main():
    db = sqlite3.connect(SOURCE.as_uri() + '?mode=ro', uri=True); db.row_factory = sqlite3.Row
    all_rows = [dict(r) for r in db.execute('SELECT * FROM registry')]; db.close()
    lines = MARKDOWN.read_text(encoding='utf-8').splitlines()
    line_by_url = {}
    for number, line in enumerate(lines, 1):
        m = re.match(r'- \[.*?\]\((https?://[^ ]+?)\)', line)
        if m: line_by_url.setdefault(m[1], []).append(number)
    selected = [r for r in all_rows if r['content_kind'] == 'api' or r['layer'] == 'api_bulk' or PATTERN.search(r['url']) or re.search(r'(?i)\b(API|RSS|data dump|bulk data)\b', r['name']) or '/edgar-application-programming-interfaces' in r['url'] or '/nhtsa-datasets-and-apis' in r['url'] or '/CrashAPI' in r['url']]
    result = []
    now = datetime.now(timezone.utc).isoformat()
    for row in selected:
        auth = VERIFIED.get(row['url'])
        result.append({'registry_id': row['id'], 'name': row['name'], 'url': row['url'], 'reference_class': classify(row), 'source_record': row, 'source_citation': {'markdown_path': str(MARKDOWN), 'markdown_lines': line_by_url.get(row['url'], []), 'registry_path': str(SOURCE), 'registry_table': 'registry', 'registry_id': row['id']}, 'access_requirements': auth or {'status': 'unverified', 'source': row['url'], 'note': 'Original access tag is a directory claim; it does not specify API authentication, pagination or current rate limits.'}, 'requirements_reviewed_at': now if auth else None, 'live_api_query_performed': False})
    (HERE / 'api_sources.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in result), encoding='utf-8')
    summary = {'generated_at': now, 'registry_rows': len(all_rows), 'source_header_date': '2026-08-19', 'source_header_claims': {'records': 9348, 'liveness_verified': 8349, 'categorized': 5700, 'task_tagged': 8510}, 'historical_claims_not_current_reverification': True, 'typed_api_rows': sum(r['content_kind']=='api' for r in all_rows), 'api_bulk_layer_rows': sum(r['layer']=='api_bulk' for r in all_rows), 'nonempty_api_hints': sum(bool(r['api_hint']) for r in all_rows), 'mapped_references': len(result), 'classification_counts': dict(Counter(r['reference_class'] for r in result)), 'live_documentation_reviews': len(VERIFIED), 'api_calls_performed': 0, 'source_registry_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'source_markdown_sha256': hashlib.sha256(MARKDOWN.read_bytes()).hexdigest(), 'mapping_sha256': hashlib.sha256((HERE/'api_sources.jsonl').read_bytes()).hexdigest(), 'limitations': ['Mapped URLs are observed exact references, not generated endpoint guesses.', 'A documentation URL, layer tag or historical HTTP200 does not prove a callable unrestricted API.', 'No PACER login, filings submission, case bulk download or broad unreviewed crawl was performed.']}
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (HERE / 'live_documentation_review.json').write_text(json.dumps({'reviewed_at': now, 'method': 'Read official publisher documentation with web tool; no authenticated API query', 'items': VERIFIED}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__': main()
