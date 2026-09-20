"""Small, readonly integrity and presentation audit of this exact pilot."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PILOT = ROOT / 'sources/public_law_acquisition_20260919'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt = json.loads((PILOT/'validation.json').read_text())
    assert receipt['status'] == 'passed' and receipt['passed'] is True
    assert receipt['resources_sha256'] == digest(PILOT/'resources.jsonl')
    assert receipt['summary_sha256'] == digest(PILOT/'summary.json')
    assert receipt['gaps_sha256'] == digest(PILOT/'gaps.json')
    rows = list(map(json.loads, (PILOT/'resources.jsonl').read_text(encoding='utf-8').splitlines()))
    gaps = json.loads((PILOT/'gaps.json').read_text())['items']
    assert len(rows) == 32 and len(gaps) == 4
    assert len({r['id'] for r in rows}) == len(rows)
    assert len({r['source_url'] for r in rows}) == len(rows)
    reviewed = []
    for row in rows:
        for path_key, hash_key in [('raw_path','raw_sha256'), ('text_path','text_sha256'), ('extracted_path','extracted_sha256'), ('reading_metadata_path','reading_metadata_sha256'), ('access_receipt_path','access_receipt_sha256')]:
            p = (ROOT/row[path_key]).resolve()
            assert p.is_relative_to(PILOT), p
            assert digest(p) == row[hash_key], p
        text = (ROOT/row['text_path']).read_text(encoding='utf-8')
        notes = json.loads((ROOT/row['reading_metadata_path']).read_text(encoding='utf-8'))
        http = json.loads((ROOT/row['access_receipt_path']).read_text(encoding='utf-8'))
        assert text.strip() and len(text) == row['text_characters']
        assert http['http_status'] == 200 and http['raw_complete'] is True
        assert http['requested_url'] == row['source_url'] == row['final_url']
        assert not re.match(r'(?i)^404\b|^page not found', row['title'])
        controls = re.findall(r'(?im)^\s*(?:#+\s*)?(?:Search form|Search this site|Text Size:|Decrease font size|Increase font size|Reset font size|You are here)\s*$',text)
        assert not controls, (row['source_url'], controls)
        assert row['source_as_of'] is None
        assert notes['reading_notes']['original_preserved'] is True
        reviewed.append({'source_url': row['source_url'], 'title': row['title'], 'text_characters': len(text), 'main_selector': notes['reading_notes']['selector'], 'links_preserved': len(notes['links']), 'navigation_controls_found': len(controls), 'source_as_of': None, 'scope': 'Page or directory only; linked documents not implied saved'})
    expected = {'https://www.ca10.uscourts.gov/clerk/rules': ['December 1, 2025', 'January 1, 2026'], 'https://www.ca11.uscourts.gov/rules-procedures': ['August 1, 2026'], 'https://www.ca9.uscourts.gov/rules/': ['September 17, 2026']}
    for url, snippets in expected.items():
        row = next(x for x in rows if x['source_url']==url)
        text = (ROOT/row['text_path']).read_text(encoding='utf-8')
        assert all(s in text for s in snippets)
    assert next(g for g in gaps if '?page=judges' in g['source_url'])['status'] == 'soft_404'
    with sqlite3.connect((PILOT/'corpus/corpus.sqlite3').as_uri()+'?mode=ro', uri=True) as db:
        assert db.execute("SELECT count(*) FROM resources WHERE url LIKE '%?page=judges' AND raw_path IS NOT NULL").fetchone()[0] == 1
        assert db.execute('SELECT count(*) FROM runs WHERE ended_at IS NULL').fetchone()[0] == 0
    mapping = list(map(json.loads,(HERE/'api_sources.jsonl').read_text(encoding='utf-8').splitlines()))
    assert len(mapping) == 109
    assert all(x['source_citation']['markdown_lines'] for x in mapping)
    assert not any(x['live_api_query_performed'] for x in mapping)
    assert len({r['url'] for r in mapping}) == len(mapping)
    out = {'status': 'passed', 'verified_at': datetime.now(timezone.utc).isoformat(), 'usable_page_captures': len(rows), 'explicit_gaps': len(gaps), 'artifact_hash_checks': len(rows)*5+3, 'cleaned_pages_reviewed': len(reviewed), 'source_date_assertions': 3, 'api_references_mapped': len(mapping), 'resources_sha256': receipt['resources_sha256'], 'all_collection_runs_stopped': True, 'reading_review': reviewed, 'limits': ['This is a bounded page capture pilot, not a full site, linked document or judge-profile corpus.', 'Reading text preserves source wording and links; it is a derivative, not a legal currency verification.', 'API documentation checks are separate from endpoint/data acquisition; no authenticated API queries were made.']}
    (HERE/'verification.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k != 'reading_review'}))


if __name__ == '__main__': main()
