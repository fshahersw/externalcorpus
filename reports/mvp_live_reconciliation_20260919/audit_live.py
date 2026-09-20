"""Bounded live deployment reconciliation. Localhost only; no source changes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8769'
checks = []
requests = []


def check(name, passed, evidence):
    checks.append({'name': name, 'passed': bool(passed), 'evidence': evidence})


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def get(path, json_body=True):
    assert path.startswith('/') and not path.startswith('//')
    started = time.perf_counter()
    with urlopen(BASE + path, timeout=30) as response:
        data = response.read()
        metadata = {'path': path, 'status': response.status, 'mime': response.headers.get('Content-Type'),
                    'bytes': len(data), 'sha256': sha(data), 'seconds': round(time.perf_counter() - started, 6)}
    requests.append(metadata)
    return (json.loads(data) if json_body else data), metadata


def main():
    started = datetime.now(timezone.utc).isoformat()
    summary, _ = get('/api/summary')
    datasets, _ = get('/api/datasets')
    dataset_map = {row['id']: row for row in datasets['items']}
    for filename in ('app.js', 'styles.css', 'index.html'):
        raw, metadata = get('/' + filename, False)
        disk = (ROOT / 'delivery/archive-directory' / filename).read_bytes()
        check('Live static asset matches current disk: ' + filename, raw == disk,
              metadata | {'disk_sha256': sha(disk)})
    people, _ = get('/api/people?limit=1')
    aliases, _ = get('/api/people?limit=1&include_aliases=1')
    person, _ = get('/api/person?id=6781')
    born, _ = get('/api/person?id=1429')
    people_ready = read('sources/courtlistener_people_20260918/ready.json')
    people_summary = read('sources/courtlistener_people_20260918/summary.json')
    check('Biographies live with source alias scope',
          people['ready'] is True and people['total'] == 15797 and aliases['total'] == 16191,
          {'default': people['total'], 'with_aliases': aliases['total'], 'ready': people['ready']})
    check('Live biography preserves alias and date precision',
          person['id'] == '6781' and person['alias_of']['id'] == '1810' and born['birth']['text'] == '1933',
          {'alias': person['alias_of'], 'native_id': person['id'], 'birth': born['birth']})
    check('Live biography count matches published source receipt',
          people_summary['counts']['people'] == aliases['total'] == people_ready['summary']['counts']['people'],
          {'counts': people_summary['counts'], 'source_ready': people_ready['ready']})

    photos, _ = get('/api/judges?has=photo&limit=60')
    judges, _ = get('/api/judges?has=all&limit=1')
    detailed, _ = get('/api/judges?has=details&limit=1')
    judge_summary = read('sources/judge_presentation_20260918/summary.json')
    portraits = [json.loads(line) for line in (ROOT / 'sources/judge_presentation_20260918/portraits.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
    by_url = {'/judge-images/' + row['id']: row for row in portraits}
    image_proof = []
    for item in photos['items']:
        image, metadata = get(item['photo_url'], False)
        expected = by_url[item['photo_url']]
        local = (ROOT / expected['path']).read_bytes()
        valid = sha(image) == expected['sha256'] == sha(local)
        image_proof.append({'name': item['name'], 'url': item['photo_url'], 'bytes': len(image),
                            'sha256': sha(image), 'matches_manifest_and_disk': valid})
    check('All installed portraits are served as exact original bytes',
          photos['total'] == len(portraits) == judge_summary['profiles_with_photos'] and all(r['matches_manifest_and_disk'] for r in image_proof),
          {'installed': len(portraits), 'live': photos['total'], 'delivered_bytes': sum(r['bytes'] for r in image_proof), 'items': image_proof})
    check('Judge projection counts match live filters',
          judges['total'] == judge_summary['profiles'] and detailed['total'] == judge_summary['detailed_profiles'],
          {'all': judges['total'], 'detailed': detailed['total'], 'analyses': judge_summary['analysis_records']})

    counties, _ = get('/api/counties?limit=1')
    local_counties, _ = get('/api/counties?availability=local_resources&limit=1')
    adams, _ = get('/api/counties?q=19003&limit=1')
    pending, _ = get('/api/documents?dataset=pending_publication&view=sources&limit=1')
    pending_summary = read('sources/directory_pending_20260918/summary.json')
    check('Pending downloads are already visible as a separate dataset',
          pending['total'] == pending_summary['resources'] == dataset_map['pending_publication']['count'],
          {'live': pending['total'], 'local_manifest': pending_summary['resources'], 'by_group': pending_summary['by_group']})
    adams_row = adams['items'][0]
    check('County resource totals distinguish published and pending',
          adams_row['local_resources'] == adams_row['published_local_resources'] + adams_row['pending_local_resources'], adams_row)
    trellis, _ = get('/api/documents?dataset=trellis_browser_counties&view=sources&limit=10')
    batch_proofs = []
    for batch in dataset_map['trellis_browser_counties']['batches']:
        manifest = (ROOT / batch['folder'] / 'resources.jsonl').read_bytes()
        batch_proofs.append({'folder': batch['folder'], 'rows': len(manifest.splitlines()),
                             'hash_matches_live_receipt': sha(manifest) == batch['resources_sha256']})
    check('Both browser capture batches are indexed and exported',
          trellis['total'] == sum(b['rows'] for b in batch_proofs) == 6 and all(b['hash_matches_live_receipt'] for b in batch_proofs)
          and len(dataset_map['trellis_browser_counties']['files']) == 8,
          {'live': trellis['total'], 'batches': batch_proofs, 'export_links': 8})

    bulk_query = '/api/documents?' + urlencode({'dataset': 'open_us_law', 'state': 'New York', 'category': 'statutes', 'limit': 1})
    bulk, _ = get(bulk_query)
    bulk_record, _ = get('/api/record?' + urlencode({'id': bulk['items'][0]['id']}))
    bulk_ready = read('sources/open_us_law_20260918/ready.json')
    check('Bulk snapshot is live and returns readable legal text',
          bulk_ready['ready'] is True and summary['enrichment']['open_us_law']['records'] == bulk_ready['indexed_rows']
          and bulk['total'] == 40140 and len(bulk_record.get('text') or '') > 50,
          {'all_records': bulk_ready['indexed_rows'], 'ny_statute_rows': bulk['total'], 'sample_id': bulk['items'][0]['id'],
           'sample_text_characters': len(bulk_record.get('text') or ''), 'snapshot': bulk_ready['snapshot']})

    collections, _ = get('/api/collections')
    library_summary = read('sources/local_library_presentation_20260918/summary.json')
    library_assets = read('sources/local_library_presentation_20260918/assets.json')
    library_by_id = {row['id']: row for row in library_assets}
    collection_proof = []
    for item in collections['items']:
        detail, _ = get('/api/collection?' + urlencode({'id': item['id'], 'page_size': 1}))
        collection_proof.append({'id': item['id'], 'record_count': item['record_count'], 'preview_count': item['preview_count'], 'live_preview_total': detail['total']})
        if item['id'] == 'mdl-3080':
            document = detail['items'][0]
            raw, metadata = get('/library-assets/' + document['asset_id'], False)
            expected = library_by_id[document['asset_id']]
            check('Curated collection PDF bytes are actually downloadable', sha(raw) == expected['sha256'] and raw.startswith(b'%PDF'),
                  metadata | {'asset_id': document['asset_id'], 'title': document['title']})
    check('Curated collection previews match their bounded manifests',
          all(row['preview_count'] == row['live_preview_total'] for row in collection_proof), collection_proof)

    reading = read('sources/reading_views_20260918/summary.json')
    recovery = read('sources/seeger_text_recovery_20260918/directory_receipt.json')
    check('Reader/recovery live summary matches saved integration receipts',
          summary['enrichment']['reading']['readable_records'] == reading['readable_records']
          and summary['enrichment']['seeger']['text_recovery']['recovered'] == recovery['updated_records'],
          {'readable': reading['readable_records'], 'empty': reading['empty_records'], 'recovery_overlays': recovery['updated_records']})

    portrait_review = read('sources/local_deep_audit_20260918/portraits/portrait_reference_review.json')
    matrix = [
      {'feature': 'Current MVP interface', 'status': 'live', 'route': '#overview', 'scope': 'All three static assets match disk byte-for-byte at check time.'},
      {'feature': 'Focused validated publication', 'status': 'live_published', 'count': summary['published']['capture_records'], 'route': '#documents?dataset=focused', 'scope': 'Published snapshot; does not include the later pending additions.'},
      {'feature': 'Later county/law downloads', 'status': 'live_pending_publication', 'count': pending['total'], 'route': '#documents?dataset=pending_publication', 'scope': '220 county and81 law resources; searchable/browsable now, excluded from focused published totals.'},
      {'feature': 'Trellis county browser snapshots', 'status': 'live_source_layer', 'count': trellis['total'], 'route': '#documents?dataset=trellis_browser_counties', 'scope': 'Six DOM/text profiles, not case-file downloads; two immutable batches.'},
      {'feature': 'County directory', 'status': 'live_inventory', 'count': counties['total'], 'route': '#counties', 'scope': f"{local_counties['total']} counties have published or pending local-resource associations; {summary['coverage']['local_counties']} have published local resources. Inventory does not establish complete county records."},
      {'feature': 'Consolidated judges', 'status': 'live', 'count': judges['total'], 'route': '#judges', 'scope': f"{detailed['total']} detailed profiles; 708 source-bound analyses; {photos['total']} installed portraits. Not a current-judge census."},
      {'feature': 'CourtListener historical biographies', 'status': 'live_separate_source_layer', 'count': aliases['total'], 'route': '#people', 'scope': '15,797 non-alias records plus394 optional aliases; no additions to consolidated judge totals and no new portraits.'},
      {'feature': 'Open US Law snapshot', 'status': 'live', 'count': bulk_ready['indexed_rows'], 'route': '#laws?dataset=open_us_law', 'scope': '229 files, snapshot v2026.08; historical/repealed/guidance records included, some original source URLs missing.'},
      {'feature': 'Seeger records and cleaned reading overlays', 'status': 'live', 'count': dataset_map['seeger']['count'], 'route': '#documents?dataset=seeger', 'scope': '384 recovered texts integrated without new source records;451 reading-cache records still empty.'},
      {'feature': 'Curated local collections', 'status': 'live_bounded_previews', 'count': len(collections['items']), 'route': '#collections', 'scope': 'Four cards; MDL1612saved-PDF inventory has24browsable previews. Other collections retain their explicit reference/preview scope.'},
      {'feature': 'PA portrait reference queue', 'status': 'audit_only_at_check_time', 'count': portrait_review['accepted_image_references'], 'scope': '29 identity-context references from saved official profiles; not installed image bytes. Root may work on them after this snapshot.'},
      {'feature': 'CourtListener photo flags', 'status': 'audit_only_availability_hints', 'count': people['summary']['photo_flags'], 'scope': '1,230 source flags, not local image URLs or installed portraits.'},
      {'feature': 'KY/TX registry and Illinois section candidates', 'status': 'audit_only_at_check_time', 'scope': '374 registry rows and1,619 section-code candidates per prior bounded audit; no corresponding live dataset/adapter in the inspected registry.'},
      {'feature': 'Remaining acquisition/completeness', 'status': 'incomplete', 'scope': 'Live source queues report125Arizona URLs and1county URL pending; terminal errors remain. Full national laws/county filings/judge-analysis coverage is not claimed.'},
    ]
    findings = [
      {'priority': 'clarity', 'finding': 'Main directory timestamp is older than the newest biographies adapter; it is not a deployment-wide timestamp.', 'evidence': {'main_directory': summary['directory_built_at'], 'people_published': people_ready['completed_at']}},
      {'priority': 'clarity', 'finding': 'Historical biographies are live via a Judges-page link and #people, but do not appear in /api/datasets or the main sidebar.', 'evidence': {'dataset_ids': list(dataset_map), 'route': '#people'}},
      {'priority': 'stale_label', 'finding': 'Trellis quality text still says awaiting directory integration despite live indexing.', 'evidence': trellis['items'][0].get('quality')},
    ]
    output = {'started_at': started, 'finished_at': datetime.now(timezone.utc).isoformat(), 'base_url': BASE,
              'success': all(row['passed'] for row in checks), 'checks': checks, 'requests': requests,
              'matrix': matrix, 'findings': findings, 'directory_built_at': summary['directory_built_at'],
              'limitations': ['No full corpus rescan or large database rehash.', 'No server restart, source import, UI edit or external network acquisition.',
                              'Static asset equality is a point-in-time check; another agent may edit afterward.', 'Browser rendering and discoverability review is assigned to the parent separately.']}
    (OUT / 'live_verification.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'success': output['success'], 'checks': len(checks), 'requests': len(requests),
                      'photo_count': photos['total'], 'photo_bytes': sum(r['bytes'] for r in image_proof),
                      'local_resource_counties': local_counties['total'], 'failed': [r for r in checks if not r['passed']]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
