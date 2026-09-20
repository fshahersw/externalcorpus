"""Offline judge evidence audit; no source mutation, entity inference, or network."""
from collections import Counter, defaultdict
import csv
import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PACKAGE = ROOT / 'delivery/focused_legal_corpus/judges'
VERSION = 'judge-evidence-audit-1.0.0'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rel(p):
    return p.resolve().relative_to(ROOT).as_posix()


def read_rows(p):
    return [json.loads(line) for line in p.read_bytes().splitlines() if line.strip()]


def write(name, data):
    with (OUT / name).open('w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def jsonl(name, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def csv_rows(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = {}
            for k in fields:
                v = row.get(k)
                if isinstance(v, (dict, list)):
                    v = json.dumps(v, ensure_ascii=False)
                if isinstance(v, str) and v.startswith(('=', '+', '-', '@')):
                    v = "'" + v
                out[k] = v
            writer.writerow(out)


class RowParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells, self.cell, self.anchor, self.hidden = [], None, None, 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('svg', 'script', 'style'):
            self.hidden += 1
        if tag in ('td', 'th'):
            self.cell = {'tag': tag, 'attrs': attrs, 'parts': [], 'anchors': [], 'semantic_markers': []}
        if self.cell is not None:
            if tag == 'a':
                self.anchor = {'attrs': attrs, 'parts': []}
            if tag in ('img', 'svg', 'span', 'i') and any(attrs.get(k) for k in ('title', 'aria-label', 'alt', 'data-toggle', 'data-target')):
                self.cell['semantic_markers'].append({'tag': tag, 'attrs': attrs})

    def handle_data(self, data):
        if self.cell is not None and not self.hidden:
            self.cell['parts'].append(data)
            if self.anchor is not None:
                self.anchor['parts'].append(data)

    def handle_endtag(self, tag):
        if tag in ('svg', 'script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        if tag == 'a' and self.anchor is not None and self.cell is not None:
            self.cell['anchors'].append({'attrs': self.anchor['attrs'], 'text': ' '.join(''.join(self.anchor['parts']).split())})
            self.anchor = None
        if tag in ('td', 'th') and self.cell is not None:
            self.cell['text'] = ' '.join(''.join(self.cell.pop('parts')).split())
            self.cells.append(self.cell)
            self.cell = None


def extract_rows(html, context):
    result = []
    for table_index, table in enumerate(re.findall(r'<table\b.*?</table>', html, re.S | re.I)):
        headers = []
        for row_index, markup in enumerate(re.findall(r'<tr\b.*?</tr>', table, re.S | re.I)):
            parser = RowParser()
            parser.feed(markup)
            if parser.cells and all(x['tag'] == 'th' for x in parser.cells):
                headers = [x['text'] for x in parser.cells]
                continue
            if 'Judge Name' not in headers:
                continue
            cells, column = [], 0
            for cell in parser.cells:
                span = int(cell['attrs'].get('colspan', 1))
                cell['logical_headers'] = headers[column:column + span]
                column += span
                cells.append(cell)
            name_cell = next((x for x in cells if x['logical_headers'] == ['Judge Name']), None)
            if not name_cell:
                continue
            link = next((a for a in name_cell['anchors'] if re.match(r'https://trellis\.law/judge/[^/?#]+$', a['attrs'].get('href', ''))), None)
            if not link:
                continue
            combined = next((x for x in cells if x['logical_headers'] == ['Court', 'County']), None)
            court = next((x for x in cells if x['logical_headers'] == ['Court']), None)
            county = next((x for x in cells if x['logical_headers'] == ['County']), None)
            status = next((x for x in cells if x['logical_headers'] == ['Status']), None)
            analytics = next((x for x in cells if x['logical_headers'] == ['Analytics']), None)
            numeric = bool(analytics and re.search(r'\d', analytics['text']) and re.search(r'percent|%|rate|median|average|granted|denied', analytics['text'], re.I))
            result.append({**context, 'row_id': sha((context['source_url'] + '#' + str(table_index) + ':' + str(row_index)).encode())[:20], 'profile_url': link['attrs']['href'], 'reported_name': link['text'] or name_cell['text'], 'reported_court': court['text'] or None if court else None, 'reported_county': county['text'] or None if county else None, 'reported_court_county_combined': combined['text'] or None if combined else None, 'reported_status': status['text'] or None if status else None, 'analytics_cell': analytics, 'numeric_analytics_observed': numeric, 'analytics_status': 'numeric_cell_requires_review' if numeric else ('affordance_only' if analytics else 'not_present_in_saved_row'), 'content_kind': 'directory_row_not_individual_profile', 'county_assignment_note': 'A colspan=2 court/county label is retained intact; county is not inferred from it.' if combined else None, 'evidence': {'json_pointer': '/html', 'table_index': table_index, 'row_index': row_index, 'row_html_sha256': sha(markup.encode()), 'cells': cells}, 'identity_note': 'A publisher profile URL and source name string; not a verified unique person or current appointment.'})
    return result


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    inputs, verified, issues = [], {}, []
    for name in ['sources.jsonl', 'summary.json', 'state_coverage.json', 'judge_assignments.jsonl', 'names.jsonl', 'gaps.jsonl', 'schema.json']:
        p = PACKAGE / name
        inputs.append({'path': rel(p), 'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size, 'role': 'existing judge package snapshot; not newly normalized'})
    official = read_rows(PACKAGE / 'sources.jsonl')
    official_summary = json.loads((PACKAGE / 'summary.json').read_bytes())
    official_coverage = json.loads((PACKAGE / 'state_coverage.json').read_bytes())
    assignments = read_rows(PACKAGE / 'judge_assignments.jsonl')
    names = read_rows(PACKAGE / 'names.jsonl')
    codes = {r['state']: r['state_code'] for r in official_coverage}
    states = {v.lower(): k for k, v in codes.items()}
    dbpath = ROOT / 'sources/trellis/worker/frontier.sqlite3'
    db = sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    db.execute('BEGIN')
    frontier = [dict(r) for r in db.execute("select * from frontier where category in ('judge_directory','judge_profile') order by url")]
    imported = [r['path'] for r in db.execute('select path from imported')]
    db.close()
    jsonl('judge_frontier_snapshot.jsonl', frontier)
    inputs.append({'path': rel(dbpath), 'snapshot': rel(OUT / 'judge_frontier_snapshot.jsonl'), 'snapshot_sha256': sha((OUT / 'judge_frontier_snapshot.jsonl').read_bytes()), 'captured_at_utc': stamp, 'access': 'read-only transaction; snapshot only'})
    saved = [r for r in frontier if r['status'] == 'downloaded' and r['response_path']]
    source_audit, directory_rows, profile_captures = [], [], []
    for row in saved:
        path = Path(row['response_path'])
        if not path.is_absolute():
            path = ROOT / path
        raw = path.read_bytes()
        data = json.loads(raw)
        data = data.get('data', data)
        metadata, html, markdown = data.get('metadata', {}), data.get('html', ''), data.get('markdown', '')
        title = metadata.get('title', '')
        title_state = next((s for s in codes if title.startswith(s + ' Judge Directory')), None)
        state = states.get(row['state']) or title_state
        context = {'source_url': row['url'], 'state': state, 'state_code': codes.get(state), 'source_path': rel(path), 'source_sha256': sha(raw), 'publisher': 'Trellis', 'evidence_class': 'publisher_reported_directory_fact'}
        totals = [{'range_start': int(m[1]), 'range_end': int(m[2]), 'reported_total': int(m[3].replace(',', '')), 'literal': m[0]} for m in re.finditer(r'(\d+)\s*[-–]\s*(\d+) of ([\d,]+) results', markdown)]
        barriers = [{'line': i + 1, 'text': line.strip()} for i, line in enumerate(markdown.splitlines()) if re.search(r'full print and download access|subscribe at|upgrade (?:now|plan|to)|/pricing', line, re.I)]
        record = {**context, 'category': row['category'], 'metadata': {k: metadata.get(k) for k in ['title', 'sourceURL', 'url', 'scrapeId', 'statusCode', 'cachedAt', 'contentType']}, 'embedded_html_sha256': sha(html.encode()), 'embedded_markdown_sha256': sha(markdown.encode()), 'embedded_digest_basis': 'UTF-8 bytes of decoded JSON string; original provider JSON untouched', 'html_characters': len(html), 'markdown_characters': len(markdown), 'reported_directory_totals': totals, 'subscription_signals': barriers, 'analytics_header_or_marketing_only': bool(re.search(r'analytics', markdown, re.I)), 'missing_html': not bool(html)}
        if row['category'] == 'judge_directory':
            extracted = extract_rows(html, context) if html else []
            directory_rows.extend(extracted)
            record['extracted_directory_rows'] = len(extracted)
            if not html:
                record['extraction_limit'] = 'No saved HTML; Markdown is retained but not positional-column parsed. The state-specific HTML directory may cover the same rows.'
        else:
            profile_captures.append(record)
            record['extraction_limit'] = 'Newly present profile capture: content-specific review needed; this baseline audit does not guess profile fields.'
        source_audit.append(record)
        verified[rel(path)] = sha(raw)
    # Existing imported source evidence is checked only for unexpected saved profiles,
    # without scanning unrelated law/county response payloads or acquiring anything.
    unaccounted_profile_paths = [p for p in imported if re.search(r'(?:[/\\]judge[/\\]|judge_profile)', p, re.I) and p not in {r['response_path'] for r in saved}]

    official_profile_evidence = []
    patterns = {'appointment_or_election': r'\bappointed\b|\breappointed\b|\bsworn in\b|\bselected by his colleagues\b', 'education': r'\bdegree\b|\bJ\.D\.|\bjuris doctor\b|\bLaw School\b|\bSchool of Law\b', 'professional_history': r'\bserved as\b|\bpracticed\b|\bprivate practice\b|\bAttorney General\b', 'professional_service': r'\badjunct\b|\bcommittee\b|\bcommissions?\b|\bJudges Association\b'}
    for source in official:
        if source['source_type'] != 'individual_judge_profile':
            continue
        for pkey, hkey in [('raw_path', 'raw_sha256'), ('text_path', 'text_sha256')]:
            p = ROOT / source[pkey]
            got = sha(p.read_bytes())
            if got != source[hkey]:
                issues.append({'path': rel(p), 'issue': 'official profile hash mismatch'})
            verified[rel(p)] = got
        text = (ROOT / source['text_path']).read_text(encoding='utf-8')
        lines = text.splitlines()
        fields = {}
        for name, pattern in patterns.items():
            hits = [{'line_number': i + 1, 'text': line, 'text_sha256': sha(line.encode())} for i, line in enumerate(lines) if len(line) > 70 and re.search(pattern, line, re.I)]
            fields[name] = {'status': 'source_passage_present' if hits else 'not_observed_in_saved_text', 'value': None, 'passages': hits[:5], 'note': 'Passage availability, not entity/date normalization; navigation and unrelated appointments require report-level review.'}
        official_profile_evidence.append({'source_url': source['source_url'], 'state': source['state'], 'reported_title': source['title'], 'raw_path': source['raw_path'], 'raw_sha256': source['raw_sha256'], 'text_path': source['text_path'], 'text_sha256': source['text_sha256'], 'capture_times': source['capture_times'], 'content_kind': 'official_profile_or_office_detail', 'fields': fields, 'performance_statistics': None, 'statistics_status': 'not_supported_by_profile_biography', 'currency': 'Statements as captured; not certified current appointment.'})

    reports = []
    groups = defaultdict(list)
    for r in directory_rows:
        groups[r['profile_url']].append(r)
    for url, rows in sorted(groups.items()):
        reports.append({'report_id': sha(url.encode())[:20], 'profile_url': url, 'report_type': 'saved_directory_fact_report', 'reported_names': sorted({r['reported_name'] for r in rows}), 'reported_states': sorted({r['state'] for r in rows if r['state']}), 'reported_court_or_combined_labels': sorted({r['reported_court'] or r['reported_court_county_combined'] for r in rows if r['reported_court'] or r['reported_court_county_combined']}), 'reported_counties': sorted({r['reported_county'] for r in rows if r['reported_county']}), 'reported_status_values': sorted({r['reported_status'] for r in rows if r['reported_status']}), 'biography': None, 'biography_status': 'individual_trellis_profile_not_captured_in_baseline', 'directly_reported_trellis_analytics': None, 'analytics_status': 'no_verified_numeric_judge_analytics_in_directory_evidence', 'independently_computed_case_outcomes': None, 'case_outcome_status': 'not_computable_from_directory_or_biography; no defined judge-linked decision cohort', 'source_rows': [{'row_id': r['row_id'], 'source_url': r['source_url'], 'source_path': r['source_path'], 'source_sha256': r['source_sha256'], 'table_index': r['evidence']['table_index'], 'row_index': r['evidence']['row_index']} for r in rows], 'limitations': ['Not a resolved unique-person identity.', 'Directory status may be blank, historical, or conflicting; no missing value is zero.', 'Court/county colspan text remains combined; no inferred county or official-person join.', 'No judge quality, win probability, or grant propensity conclusion.']})
    coverage = []
    for s in official_coverage:
        sr = [r for r in directory_rows if r['state'] == s['state']]
        caps = [x for x in source_audit if x['state'] == s['state']]
        pending = [x for x in frontier if x['category'] == 'judge_profile' and x['state'] == s['state_code'].lower()]
        coverage.append({'state': s['state'], 'state_code': s['state_code'], 'official_roster_sources': s['saved_roster_sources'], 'official_individual_profile_sources': s['saved_profile_sources'], 'official_structured_assignment_rows': s['existing_structured_assignments'], 'official_name_strings': s['distinct_existing_name_strings'], 'trellis_saved_directory_captures': sum(x['category'] == 'judge_directory' for x in caps), 'trellis_directory_rows': len(sr), 'trellis_distinct_observed_profile_urls_in_rows': len({r['profile_url'] for r in sr}), 'trellis_saved_profile_captures': sum(x['category'] == 'judge_profile' for x in caps), 'trellis_known_profile_frontier_urls': len(pending), 'reported_status_present_rows': sum(r['reported_status'] is not None for r in sr), 'reported_status_missing_rows': sum(r['reported_status'] is None for r in sr), 'separate_county_field_present_rows': sum(r['reported_county'] is not None for r in sr), 'verified_numeric_judge_analytics': None, 'independent_case_outcome_rates': None, 'judge_inventory_complete': False, 'metric_scope': 'saved-source availability, not a population estimate'})
    metrics = {'computed_at_utc': stamp, 'basis': 'saved directory rows and existing official package only', 'trellis_directory_rows': len(directory_rows), 'trellis_distinct_profile_url_keys': len(groups), 'trellis_status_label_counts': dict(Counter(r['reported_status'] or 'not_reported' for r in directory_rows)), 'trellis_combined_court_county_rows': sum(r['reported_court_county_combined'] is not None for r in directory_rows), 'trellis_distinct_profile_urls_by_status_label': {label: len({r['profile_url'] for r in directory_rows if (r['reported_status'] or 'not_reported') == label}) for label in sorted({r['reported_status'] or 'not_reported' for r in directory_rows})}, 'official_texas_assignment_rows': len(assignments), 'official_texas_distinct_name_strings': len(names), 'official_texas_assignment_counties': len({r['county_geoid'] for r in assignments}), 'official_assignment_rows_with_phone': sum(bool(r.get('source_fields', {}).get('Phone')) for r in assignments), 'official_assignment_rows_with_court_email': sum(bool(r.get('source_fields', {}).get('Court Email')) for r in assignments), 'independent_case_outcome_statistics': None, 'win_rate': None, 'grant_rate': None, 'time_to_ruling': None, 'null_reason': 'No analyzed judge-linked decision cohort with stable identity, timeframe, denominator, adjudicated outcome definitions and deduplication.'}
    schema = {'version': VERSION, 'field_groups': [
        {'group': 'directory_facts', 'fields': ['profile_url', 'reported_name', 'reported_state', 'reported_court_or_combined_label', 'reported_status'], 'availability': 'present_in_saved_Trellis_directory_rows', 'provenance': 'source file/hash plus HTML table/row/cell evidence', 'limits': 'Court and county span two header positions in a single source cell; not two independent values. State directories can include federal, tribal, retired and deceased judges.'},
        {'group': 'official_profile_facts', 'fields': ['reported_title', 'appointment_or_election_passages', 'education_passages', 'professional_history_passages', 'professional_service_passages'], 'availability': 'present_to_varying_degrees_in_eight_saved_official_profile_or_office_pages', 'provenance': 'original/text hashes and exact text lines', 'limits': 'Passage evidence only; official_courts agent owns normalization and resolving dates/roles.'},
        {'group': 'official_roster_assignments', 'fields': ['name', 'court', 'county_name', 'county_geoid', 'public_office_phone', 'court_email', 'office_address'], 'availability': 'existing_Texas_assignment_rows', 'limits': 'Public office contacts and assignments, not unique-person count or current nationwide roster.'},
        {'group': 'directly_reported_Trellis_analytics', 'fields': ['metric_name', 'value', 'unit', 'time_window', 'denominator', 'case_or_motion_filters', 'publisher_methodology', 'source_capture'], 'availability': 'no_verified_numeric_judge_metrics_in_saved_directory_baseline', 'value': None, 'limits': 'Analytics column headings, switches and marketing are not numerical analytics. Subscription notice explicitly concerns print/download; exact analytics entitlement or pricing is not established.'},
        {'group': 'independently_computed_case_outcomes', 'fields': ['decision_count', 'grant_rate', 'denial_rate', 'mixed_outcomes', 'trial_outcome_rate', 'time_to_ruling'], 'availability': 'not_computable_from_current_audited_sources', 'value': None, 'requirements': ['Exact judge identity and assignment at decision time', 'Defined source universe, date window, court and matter/motion type', 'Decision-level identifiers and full outcome evidence', 'Separate grants, denials, partial outcomes, withdrawals and unresolved events', 'Deduplicate amended/reconsidered decisions', 'Publish numerator, denominator, missingness and sample limits'], 'limits': 'No data is null. A provider rate must remain attributed and never be relabeled as independently calculated.'}], 'supported_computations': ['Counts of saved source pages, rows and distinct profile URL keys', 'Counts of explicitly reported status labels with missing kept separate', 'Coverage by source-state context', 'Counts of existing Texas assignments/name strings/county associations'], 'unsupported_computations': ['National judge population coverage percentage', 'Win/grant/denial rates', 'Predicted judge decisions', 'Judge quality, ideology or fairness scoring from biography/directory membership']}
    template = {'report_id': None, 'judge_identity': {'reported_name': None, 'official_identifier': None, 'publisher_profile_url': None, 'identity_resolution_status': 'unresolved'}, 'facts_as_reported': [], 'official_source_correspondence': [], 'publisher_analytics': {'status': 'not_observed', 'metrics': None}, 'independent_statistics': {'status': 'not_computable', 'cohort': None, 'numerator': None, 'denominator': None, 'values': None}, 'source_gaps': [], 'capture_times': [], 'edition_or_current_service_limits': [], 'evidence': [], 'rule': 'Every substantive field requires a source URL, raw/text path+hash and locator; absent values remain null. Distinguish publisher values from independent calculations.'}
    summary = {'audit_at_utc': stamp, 'version': VERSION, 'official_package_built_at': official_summary['built_at'], 'official_saved_sources': len(official), 'official_roster_sources': sum(x['source_type'] == 'judge_roster_or_directory' for x in official), 'official_profile_sources': len(official_profile_evidence), 'official_roster_jurisdictions': sum(x['saved_roster_sources'] > 0 for x in official_coverage), 'trellis_saved_directory_captures': sum(r['category'] == 'judge_directory' for r in saved), 'trellis_saved_profile_captures': len(profile_captures), 'trellis_directory_rows_extracted_from_html': len(directory_rows), 'trellis_distinct_profile_url_reports': len(reports), 'trellis_numeric_analytics_cells': sum(r['numeric_analytics_observed'] for r in directory_rows), 'trellis_known_profile_urls_by_status': dict(Counter(r['status'] for r in frontier if r['category'] == 'judge_profile')), 'reported_totals_are_publisher_counts_not_population_denominators': True, 'independent_case_outcome_statistics_computed': False, 'unexpected_imported_profile_paths': unaccounted_profile_paths, 'source_file_hashes_freshly_verified': len(verified), 'validation_issues': issues, 'network_requests': 0, 'source_mutations': 0, 'full_judge_corpus_complete': False}
    jsonl('trellis_directory_rows.jsonl', directory_rows)
    csv_rows('trellis_directory_rows.csv', directory_rows, ['state', 'profile_url', 'reported_name', 'reported_court', 'reported_county', 'reported_court_county_combined', 'reported_status', 'analytics_status', 'source_url', 'source_path', 'source_sha256', 'row_id'])
    jsonl('trellis_source_audit.jsonl', source_audit)
    jsonl('official_profile_field_evidence.jsonl', official_profile_evidence)
    jsonl('judge_reports.jsonl', reports)
    write('coverage.json', coverage)
    csv_rows('coverage.csv', coverage, list(coverage[0]))
    write('analysis_results.json', metrics)
    write('schema_audit.json', schema)
    write('judge_report_template.json', template)
    write('summary.json', summary)
    write('input_provenance.json', inputs)
    write('validation.json', {'validated_at_utc': stamp, 'issue_count': len(issues), 'issues': issues, 'source_hashes': verified, 'report_url_uniqueness': len(reports) == len({r['profile_url'] for r in reports}), 'null_performance_values_preserved': all(r['independently_computed_case_outcomes'] is None and r['directly_reported_trellis_analytics'] is None for r in reports), 'source_files_unchanged_on_final_check': all(sha((ROOT / p).read_bytes()) == h for p, h in verified.items())})
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
