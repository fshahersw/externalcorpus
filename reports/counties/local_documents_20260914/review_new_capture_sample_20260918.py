"""Add a bounded manually reviewed sample; originals and collector queues are untouched."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
COLLECTION = 'corpus/county_local_documents_20260914'
REVIEWS = [
    (441, 'court_filing_fee_schedule', 'information_page', True, None, ['Effective 7/1/2023', 'Civil Case – $87.00']),
    (481, 'county_legislative_committee_event', 'event_page', False, None, ['Cortland County Legislature', 'Judiciary & Public Safety Committee']),
    (493, 'draft_land_use_ordinance_notice', 'notice_page', False, 'Draft label observed; ordinance enactment not verified.', ['Draft - High Impact Land Use Ordinance', 'July 14, 2026 5:39 PM']),
    (503, 'county_code_disclaimer_acceptance_page', 'disclaimer_page', False, None, ['DISCLAIMER - Code of Ordinances', 'Please indicate your acceptance of the above disclaimer: *']),
    (505, 'county_permit_application_directory', 'link_directory', False, None, ['Construction Permit Applications', 'Printable Building & Trade Application Worksheets']),
    (506, 'proposed_ordinance_public_information_event', 'notice_page', False, 'Proposed ordinance and public-information sessions; no enactment evidence.', ['proposed Unified Development Ordinance (UDO)', 'The latest draft of the UDO will be available September 2']),
    (514, 'county_ordinance_text', 'legal_text_pdf', False, 'Ordinance-form text; enactment date and current legal currency not verified.', ['ORDINANCE DIRECTING REMOVAL OF BALES', 'NOW, THEREFORE, BE IT ORDAINED BY THE BOARD OF COUNTY']),
    (523, 'court_local_rules_download_landing', 'link_directory', True, 'Source reports updated January 20, 2026; current legal currency unverified.', ['ATHENS COUNTY COURT OF COMMOM PLEAS LOCAL RULES', 'Updated: January 20, 2026']),
    (532, 'mixed_county_meeting_and_court_docket_directory', 'link_directory', True, None, ['Meeting agendas, minutes, dockets, and schedules across Fairfield County boards, courts, and agencies.', 'Judge Dockets']),
    (534, 'juvenile_probate_local_rules_text', 'legal_text_html', True, 'Rule text saved; current legal currency unverified.', ['Rule IX', 'Local Rule of Court Pertaining to Bank Deposits']),
    (553, 'municipal_code_of_ordinances_pdf', 'legal_text_pdf', False, 'City of Atoka code identifies 2020 publication; supplements and current legal currency not certified.', ['CITY OF ATOKA', 'CODE OF ORDINANCES', 'August 1, 2020, and still in effect on that date']),
    (577, 'unsigned_county_ordinance_text', 'legal_text_pdf', False, 'Enactment line is blank; enactment and effective date are not established by this saved copy.', ['ORDINANCE NO. 2 OF 2026', 'ORDAINED AND ENACTED this _____ day of __________________, 2026']),
    (593, 'court_efiling_system_migration_notice', 'notice_pdf', True, 'Dated e-filing migration notice; not an actual case filing or current operational guarantee.', ['Public Notice to Filers and the Public', 'CourtPro Opens on Monday, August 31, 2026']),
    (601, 'municipal_court_ticket_payment_information', 'information_page', True, None, ['Pay Parking Fines Pay Red Light and Speed Related Fines', 'Online payments are provided by Providence Pay-By-Web']),
    (603, 'county_council_committee_event', 'event_page', False, None, ['County Council Worksession Room', 'Judicial & Public Safety Committee']),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    sample = OUT / 'content_kind_sample.jsonl'
    old_bytes = sample.read_bytes()
    existing = [json.loads(line) for line in old_bytes.decode('utf-8').splitlines()]
    by_key = {row['resource_key']: row for row in existing}
    sources = {row['resource_id']: row for row in map(json.loads, (OUT / 'resources.jsonl').read_text(encoding='utf-8').splitlines()) if row['collection'] == COLLECTION}
    additions = []
    for ident, kind, shape, judicial, status, literals in REVIEWS:
        source = sources[ident]
        assert source['status'] == 'downloaded' and source['public_page_or_document_captured']
        for field in ['raw_evidence', 'text_evidence', 'metadata_evidence']:
            evidence = source[field]
            path = (ROOT / evidence['path']).resolve(); path.relative_to(ROOT)
            assert digest(path.read_bytes()) == evidence['sha256']
        assert source['metadata_evidence']['resource_binding_valid'] and source['text_evidence']['strict_utf8_valid']
        assert source['text_evidence']['hash_matches'] and source['text_evidence']['expected_sha256_valid']
        text = (ROOT / source['text_evidence']['path']).read_text(encoding='utf-8')
        spans = []
        for literal in literals:
            start = text.index(literal)
            spans.append({'literal': literal, 'start_char': start, 'end_char': start + len(literal), 'text_path': source['text_evidence']['path'], 'text_sha256': source['text_evidence']['sha256']})
        review = {'resource_id': ident, 'resource_key': source['resource_key'], 'collection': COLLECTION, 'url': source['url'], 'title': source['title'], 'actual_resource_kind': kind, 'document_shape': shape, 'contains_actual_case_filing': False, 'judicial_administration_resource': judicial, 'legal_effective_status': status, 'effective_date': None, 'enacted_status_verified': False, 'classification_basis': 'Manual review of saved source text; targeted sample does not certify the unsampled corpus or current legal status.', 'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'reported_source_categories': sorted({c['category'] for c in source['contexts']}), 'county_associations': [{'geoid': c['jurisdiction'].get('geoid'), 'source_association_strength': c['source_association_strength']} for c in source['contexts']], 'raw_evidence': source['raw_evidence'], 'text_evidence': source['text_evidence'], 'metadata_evidence': source['metadata_evidence'], 'supporting_spans': spans}
        if review['resource_key'] in by_key:
            assert by_key[review['resource_key']]['raw_evidence']['sha256'] == review['raw_evidence']['sha256']
            continue
        additions.append(review)
    rows = existing + additions
    assert len({r['resource_key'] for r in rows}) == len(rows)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = OUT / ('content_kind_sample.before_' + stamp + '.jsonl')
    backup.write_bytes(old_bytes)
    ready = OUT / ('content_kind_sample.ready_' + stamp + '.jsonl')
    ready.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows), encoding='utf-8')
    ready.replace(sample)
    summary = {'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'reviewed_resources': len(rows), 'newly_reviewed_resources': len(additions), 'sampling': 'Targeted review of selected legal texts, notices, directories and suspected false positives; not a random population sample.', 'resource_kinds': dict(Counter(r['actual_resource_kind'] for r in rows)), 'judicial_administration_resources': sum(r['judicial_administration_resource'] for r in rows), 'actual_case_filings_in_sample': sum(r['contains_actual_case_filing'] for r in rows), 'all_new_source_hashes_and_literal_spans_verified': True, 'prior_sample_preserved': backup.relative_to(ROOT).as_posix(), 'prior_sample_sha256': digest(old_bytes), 'sample_sha256': digest(sample.read_bytes()), 'full_collection_semantic_accuracy_certified': False, 'discovery_categories_must_not_be_used_as_actual_filing_or_rule_counts': True, 'network_requests': 0, 'queue_or_frozen_packet_changes': 0, 'unclassified_pdf_text_gaps_in_targeted_selection': [477, 487]}
    (OUT / 'content_kind_sample_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
