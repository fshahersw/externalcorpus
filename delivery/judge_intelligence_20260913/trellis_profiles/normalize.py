"""Normalize saved public Trellis judge-profile HTML; never fetch or execute it."""
import argparse
from collections import Counter, defaultdict
import csv
import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
VERSION = 'trellis-profile-normalizer-1.0.3'
HEADINGS = re.compile(r'<h([1-6])\b[^>]*>.*?</h\1>', re.I | re.S)
TABLES = re.compile(r'<table\b.*?</table>', re.I | re.S)
ROWS = re.compile(r'<tr\b.*?</tr>', re.I | re.S)
CELLS = re.compile(r'<(td|th)\b[^>]*>(.*?)</\1>', re.I | re.S)
ANCHORS = re.compile(r'<a\b[^>]*>.*?</a>', re.I | re.S)
EDUCATION_CREDENTIAL = re.compile(
    r'\b(?:Juris Doctor(?:ate)?|Doctor of Jurisprudence|Bachelor of|Master of)\b'
    r'|\b(?:law|bachelor[\u2019\']?s?|master[\u2019\']?s?|doctoral|undergraduate|graduate|associate[\u2019\']?s?)\s+degree\b'
    r'|\bdegree\s+(?:in|from)\b'
    r'|(?<!\w)(?:J\.?D\.?|B\.?A\.?|B\.?S\.?|B\.?B\.?A\.?|LL\.?B\.?|LL\.?M\.?|M\.?A\.?|M\.?S\.?|M\.?B\.?A\.?|Ph\.?D\.?)(?!\w)',
    re.I,
)


def is_education_passage(value):
    """Require a credential or named graduation, not a career transition."""
    if EDUCATION_CREDENTIAL.search(value):
        return True
    for match in re.finditer(r'\bgraduat(?:ed|ing)\s+from\s+([^,;.\n]+)', value, re.I):
        institution = re.sub(r'\s+in\s+\d{4}\s*$', '', match[1], flags=re.I).strip()
        if re.fullmatch(r'(?:the\s+)?(?:(?:law|high)\s+)?(?:school|college|university)', institution, re.I):
            continue
        if re.search(r'\b(?:university|college|school|academy|institute)\b', institution, re.I):
            return True
    return False


def is_professional_service_passage(value):
    """A negated presiding transition does not assert professional service."""
    candidate = re.sub(
        r'\bwhen\s+not\s+presiding\s+(?:over\s+legal\s+(?:proceedings|matters)|on\s+the\s+bench)\b',
        '', value, flags=re.I,
    )
    if candidate != value:
        # Only inside these mixed personal passages, remove a sentence with an
        # explicit relative as its subject. A relative's employer or committee
        # must not become the judge's service. Other sentences remain eligible.
        candidate = re.sub(
            r'(?:^|(?<=[.!?])\s+)(?:her|his|their)\s+'
            r'(?:husband|wife|spouse|father|mother)\b[^.!?]*(?:[.!?]|$)',
            '', candidate, flags=re.I,
        )
        # The observed mixed passages also assert actual military, mock-trial,
        # or legal-organization board roles. Keep those independent assertions.
        if re.search(
            r'\bveteran\s+of\s+(?:the\s+)?(?:United\s+States\s+)?(?:Army|Navy|Air Force|Marine Corps|Coast Guard)\b'
            r'|\bcoach(?:ed|es|ing)?\b[^.!?]{0,100}\bmock[- ]trial\b'
            r'|\bsat\s+on\s+the\s+Executive Board\s+for\s+the\s+Elder Justice Center\b',
            candidate, re.I,
        ):
            return True
    return bool(re.search(r'\bassignments?\b|\bpresiding\b|\bcommittee\b|\bassociation\b|\bserved\b', candidate, re.I))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rel(p):
    return p.resolve().relative_to(ROOT).as_posix()


class InertText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden, self.first_attrs = [], 0, None

    def handle_starttag(self, tag, attrs):
        if self.first_attrs is None:
            self.first_attrs = dict(attrs)
        if tag in ('script', 'style', 'svg', 'noscript', 'template'):
            self.hidden += 1
        if tag in ('br', 'p', 'div', 'li', 'tr') and not self.hidden:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'svg', 'noscript', 'template'):
            self.hidden = max(0, self.hidden - 1)
        if tag in ('p', 'div', 'li', 'tr') and not self.hidden:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(fragment):
    p = InertText()
    p.feed(fragment)
    return '\n'.join(' '.join(line.split()) for line in ''.join(p.parts).splitlines() if line.strip())


def attrs(fragment):
    p = InertText()
    p.feed(fragment)
    return p.first_attrs or {}


def sections(html):
    headings = list(HEADINGS.finditer(html))
    result = []
    for i, h in enumerate(headings):
        stop = next((x.start() for x in headings[i + 1:] if int(x[1]) <= int(h[1])), len(html))
        result.append({'heading': plain(h[0]), 'level': int(h[1]), 'start': h.start(), 'body_start': h.end(), 'end': stop, 'html': html[h.end():stop]})
    return result


def write_json(name, data):
    with (OUT / name).open('w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def write_rows(name, rows):
    with (OUT / name).open('w', encoding='utf-8', newline='\n') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n')


def write_csv(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            row = {}
            for k in fields:
                v = r.get(k)
                if isinstance(v, (dict, list)):
                    v = json.dumps(v, ensure_ascii=False)
                if isinstance(v, str) and v.startswith(('=', '+', '-', '@')):
                    v = "'" + v
                row[k] = v
            w.writerow(row)


def normalize_capture(data, source_path, raw_bytes):
    data = data.get('data', data)
    metadata = data.get('metadata') or {}
    source_url = metadata.get('sourceURL') or metadata.get('url')
    final_url = metadata.get('url') or source_url
    html, markdown = data.get('html') or '', data.get('markdown') or ''
    raw_hash = sha(raw_bytes)
    capture_id = sha(((source_url or '') + ':' + raw_hash).encode())[:24]
    ctx = {'capture_id': capture_id, 'source_url': source_url, 'source_path': source_path, 'source_sha256': raw_hash, 'publisher': 'Trellis', 'evidence_class': 'publisher_assertion_not_official_verification'}
    gaps, facts, links, metrics, candidates, table_evidence = [], [], [], [], [], []
    profile = {**ctx, 'final_url': final_url, 'parser_version': VERSION, 'source_metadata': metadata, 'metadata_sha256': sha(json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode()), 'metadata_digest_basis': 'Sorted decoded JSON metadata; UTF-8 ensure_ascii=False', 'embedded_html_sha256': sha(html.encode()), 'embedded_markdown_sha256': sha(markdown.encode()), 'embedded_digest_basis': 'UTF-8 decoded JSON string; original bytes retained separately', 'reported_name': None, 'reported_state': None, 'reported_court': None, 'reported_county': None, 'reported_county_basis': None, 'biography': None, 'education': [], 'current_appointment_label': None, 'appointment_passages': [], 'professional_service_passages': [], 'career_history': [], 'directly_reported_analytics': None, 'independently_computed_statistics': None, 'identity_status': 'publisher_profile_url_not_resolved_unique_current_person', 'current_service_verified': False}

    def gap(kind, note, evidence=None):
        gaps.append({**ctx, 'gap_type': kind, 'note': note, 'evidence': evidence})

    def evidence(start, end, label):
        fragment = html[start:end]
        return {'json_pointer': '/html', 'section_or_label': label, 'html_character_start': start, 'html_character_end': end, 'html_fragment_sha256': sha(fragment.encode()), 'literal_text': plain(fragment), 'literal_text_sha256': sha(plain(fragment).encode()), 'offset_basis': 'Python Unicode code-point offsets in decoded provider HTML string', 'source_url': source_url, 'source_path': source_path, 'source_sha256': raw_hash}

    def fact(field, value, ev, note=None):
        row = {**ctx, 'fact_id': sha((capture_id + ':' + field + ':' + str(ev['html_character_start']) + ':' + json.dumps(value, sort_keys=True, ensure_ascii=False)).encode())[:24], 'field': field, 'value': value, 'evidence': ev, 'interpretation_limit': note or 'Direct publisher assertion; capture time is not proof of current truth.'}
        facts.append(row)
        return row

    if not source_url or not re.match(r'^https://(?:www\.)?trellis\.law/judge/[^/?#]+/?$', source_url):
        gap('not_individual_judge_profile_url', 'Source is not an exact public judge profile URL.')
        profile['status'] = 'excluded_non_profile'
        return profile, facts, links, gaps, metrics, candidates, table_evidence
    if metadata.get('statusCode') not in (None, 200) or '/login' in (final_url or '') or '/signup' in (final_url or ''):
        gap('saved_access_or_http_barrier', 'Saved response is an access or non-200 page; no biography inferred.')
        profile['status'] = 'access_or_http_gap'
        return profile, facts, links, gaps, metrics, candidates, table_evidence
    if not html:
        gap('saved_html_missing', 'Markdown retained in original JSON, but this parser requires actual HTML heading/table evidence.')
        profile['status'] = 'missing_html'
        return profile, facts, links, gaps, metrics, candidates, table_evidence
    sec = sections(html)
    h1 = next((s for s in sec if s['level'] == 1), None)
    if h1:
        label = re.sub(r'^Judge\s+', '', h1['heading']).split(': Professional Background')[0].strip()
        if label and not re.search(r'login|sign in|access denied|just a moment', label, re.I):
            profile['reported_name'] = label
            fact('reported_name', label, evidence(h1['start'], h1['body_start'], 'h1'), 'Removed literal heading prefix Judge and fixed promotional suffix only; not identity resolution.')
    # State is read from the profile breadcrumb, not inferred from unrelated cases.
    for ol in re.finditer(r'<ol\b[^>]*class=["\'][^"\']*breadcrumb[^"\']*["\'][^>]*>.*?</ol>', html, re.S | re.I):
        for a in ANCHORS.finditer(ol[0]):
            aattrs = attrs(a[0])
            if aattrs.get('data-category') == 'state':
                profile['reported_state'] = plain(a[0])
                fact('reported_state', profile['reported_state'], evidence(ol.start() + a.start(), ol.start() + a.end(), 'profile breadcrumb state'))

    for s in sec:
        heading = s['heading'].strip().casefold()
        if heading == 'biography':
            paras = []
            for p in re.finditer(r'<p\b[^>]*>.*?</p>', s['html'], re.S | re.I):
                value = plain(p[0])
                if not value:
                    continue
                if re.search(r'^(?:subscribe|sign in|log in|upgrade|unlock)\b.{0,100}(?:view|biography|profile|access)', value, re.I):
                    gap('biography_access_placeholder', 'Biography paragraph is an access prompt, not a factual body.', evidence(s['body_start'] + p.start(), s['body_start'] + p.end(), 'Biography access placeholder'))
                    continue
                ev = evidence(s['body_start'] + p.start(), s['body_start'] + p.end(), 'Biography paragraph')
                paras.append(value)
                fact('biography_passage', value, ev)
                if re.search(r'\bappoint|\belect|\bsworn|\belevated|\bnamed in', value, re.I):
                    profile['appointment_passages'].append(value)
                    fact('appointment_or_selection_passage', value, ev, 'Preserves whole passage; may include prior legal roles, not only appointment to the bench.')
                if is_education_passage(value):
                    fact('education_passage', value, ev)
                if is_professional_service_passage(value):
                    profile['professional_service_passages'].append(value)
                    fact('service_or_role_passage', value, ev)
            profile['biography'] = '\n\n'.join(paras) or None
        if heading in ('about', 'court info', 'career history'):
            for table_index, t in enumerate(TABLES.finditer(s['html'])):
                headers = []
                for row_index, r in enumerate(ROWS.finditer(t[0])):
                    cells = list(CELLS.finditer(r[0]))
                    values = [plain(c[2]) for c in cells]
                    if not cells:
                        continue
                    if all(c[1].lower() == 'th' for c in cells):
                        headers = values
                        continue
                    start = s['body_start'] + t.start() + r.start()
                    ev = evidence(start, start + len(r[0]), s['heading'] + ' table row')
                    ev.update(table_index=table_index, row_index=row_index)
                    table_evidence.append({**ctx, 'section': s['heading'], 'headers': headers, 'literal_cell_values': values, 'evidence': ev})
                    if heading == 'about' and len(values) >= 2:
                        key_span = next((m for m in re.finditer(r'<span\b[^>]*>.*?</span>', cells[0][2], re.S | re.I) if 'judge-about-key' in attrs(m[0]).get('class', '').split()), None)
                        key = plain(key_span[0]) if key_span else values[0]
                        value = values[1]
                        if key.lower() == 'education':
                            profile['education'] = value.splitlines()
                            fact('education_table', profile['education'], ev, 'Uses explicit key span and second value cell; ignores duplicated mobile value in label cell.')
                        elif key.lower() == 'current appointment':
                            profile['current_appointment_label'] = value
                            fact('current_appointment_label', value, ev, 'Publisher label Current Appointment is preserved; current service is not independently verified.')
                        else:
                            fact('about_' + re.sub(r'\W+', '_', key.lower()).strip('_'), value, ev)
                    elif heading == 'court info' and len(values) >= 2:
                        key, value = values[0].rstrip(': ').casefold(), values[1]
                        if key == 'current court':
                            profile['reported_court'] = value
                            fact('reported_court', value, ev, 'Literal Current Court publisher value; state prefix retained.')
                        elif key == 'county':
                            profile['reported_county'], profile['reported_county_basis'] = value, 'explicit Court Info county cell'
                            fact('reported_county', value, ev)
                        elif key in ('clerk phone', 'court phone'):
                            fact('public_office_contact', {key: value}, ev, 'Publisher-listed clerk/court contact, not a private judge contact.')
                    elif heading == 'career history' and headers and len(headers) == len(values):
                        history = dict(zip(headers, values))
                        profile['career_history'].append(history)
                        fact('career_history_row', history, ev)
        # Require a same-row metric label, value, period and denominator. Do not
        # turn preview cards, images, recent-case counts or years into analytics.
        if re.search(r'analytics|statistics|motion analysis|case outcome', heading) and not re.search(r'recent cases|documents', heading):
            for t in TABLES.finditer(s['html']):
                headers = []
                for r in ROWS.finditer(t[0]):
                    cells = list(CELLS.finditer(r[0]))
                    values = [plain(c[2]) for c in cells]
                    if cells and all(c[1].lower() == 'th' for c in cells):
                        headers = [v.casefold().rstrip(':') for v in values]
                        continue
                    if not values or not any(re.search(r'\d', x) for x in values):
                        continue
                    mapped = dict(zip(headers, values)) if len(headers) == len(values) else {}
                    find = lambda labels: next((mapped[x] for x in labels if mapped.get(x)), None)
                    metric, value = find(['metric', 'measure', 'statistic']), find(['value', 'rate', 'result'])
                    period, denominator = find(['period', 'time period', 'date range', 'window']), find(['denominator', 'sample size', 'n', 'population'])
                    start = s['body_start'] + t.start() + r.start()
                    ev = evidence(start, start + len(r[0]), s['heading'] + ' analytics table')
                    if metric and value and period and denominator and re.search(r'\d', value) and re.search(r'\d', denominator):
                        metrics.append({**ctx, 'metric_label': metric, 'value_as_reported': value, 'period_as_reported': period, 'denominator_as_reported': denominator, 'filters_as_reported': mapped.get('filters'), 'origin': 'directly_reported_by_Trellis_not_independent_calculation', 'evidence': ev})
                    else:
                        candidates.append({**ctx, 'literal_cell_values': values, 'reason': 'metric_label_value_period_and_denominator_not_all_present_in_same_table_row', 'evidence': ev})
    # A location explicitly printed in a judicial career row is retained as a
    # publisher county assertion, with no claim that the role is current.
    if profile['reported_county'] is None:
        locs = []
        for f in facts:
            if f['field'] == 'career_history_row' and re.search(r'judge|justice', f['value'].get('Role', ''), re.I):
                where = f['value'].get('Where', '')
                location = where.split(',')[0].strip()
                if re.search(r'\b(?:County|Parish|Borough)\b', location):
                    locs.append((location, f['evidence']))
        if len({v for v, e in locs}) == 1:
            profile['reported_county'] = locs[0][0]
            profile['reported_county_basis'] = 'literal judicial Career History location; current assignment unverified'
            fact('reported_county_from_judicial_career_location', locs[0][0], locs[0][1], profile['reported_county_basis'])
    excluded_cases, excluded_docs, subscribed = 0, 0, []
    seen_links = set()
    for a in ANCHORS.finditer(html):
        at = attrs(a[0])
        href, label = at.get('href', ''), plain(a[0])
        absolute = urljoin(source_url, href)
        if re.match(r'^https://(?:www\.)?trellis\.law/(?:judge-dashboard/|judge-report/)', absolute) and absolute not in seen_links:
            seen_links.add(absolute)
            links.append({**ctx, 'url': absolute, 'raw_href': href, 'label': label or at.get('title'), 'kind': 'dashboard_preview' if '/preview' in absolute else 'dashboard_or_report_link', 'access_status': 'observed_link_only_not_fetched_by_normalizer', 'numeric_analytics_saved': False, 'evidence': evidence(a.start(), a.end(), 'observed dashboard/report anchor')})
        if re.search(r'trellis\.law/case/', absolute):
            excluded_cases += 1
        if re.search(r'trellis\.law/(?:doc|document)/', absolute):
            excluded_docs += 1
        if re.search(r'subscribe to view|upgrade to view|sign in to view', label, re.I):
            subscribed.append({'label': label, 'section_status': 'restricted_field_placeholder_in_saved_page', 'html_character_start': a.start(), 'html_character_end': a.end()})
    if subscribed:
        gap('subscription_placeholders', 'Saved page contains restricted fields. Their values remain unavailable; no placeholder becomes zero.', {'count': len(subscribed), 'examples': subscribed[:5]})
    if not profile['biography']:
        gap('biography_body_not_observed', 'No actual Biography paragraph body parsed; other facts may still be available.')
    if not metrics:
        gap('numeric_analytics_unavailable', 'Dashboard links or promo images are not numeric analytics. No complete metric/value/period/denominator row was observed.')
    if candidates:
        gap('numeric_analytics_context_incomplete', 'Potential analytics rows are retained separately without promoting incomplete context to metrics.', {'candidate_rows': len(candidates)})
    for field in ('reported_name', 'reported_state', 'reported_court', 'reported_county'):
        if not profile[field]:
            gap(field + '_not_observed', 'No unambiguous direct publisher block supplied this field.')
    profile.update(status='parsed_profile' if profile['biography'] else 'partial_profile', education_status='explicit_table_values' if profile['education'] else ('biography_passage_only' if any(f['field'] == 'education_passage' for f in facts) else 'not_observed'), appointment_status='source_passages_present' if profile['appointment_passages'] else 'not_observed', directly_reported_analytics=metrics or None, dashboard_report_links=[x['url'] for x in links], saved_related_case_links_not_acquired=excluded_cases, saved_related_document_links_not_acquired=excluded_docs, fact_count=len(facts), gaps=[x['gap_type'] for x in gaps], statistics_status='No independent outcome statistics computed; biography, directory and recent-case snippets do not establish a decision cohort.')
    return profile, facts, links, gaps, metrics, candidates, table_evidence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-dir', type=Path, default=ROOT / 'sources/trellis/judge_focus_20260913/judges')
    ap.add_argument('--probe', type=Path, default=ROOT / '.firecrawl/judge-terry-l-bannon.json')
    args = ap.parse_args()
    paths = sorted(args.input_dir.glob('*.json')) if args.input_dir.exists() else []
    if args.probe.exists():
        paths = [args.probe] + paths
    profiles, facts, links, gaps, metrics, candidates, tables, inputs, failures = [], [], [], [], [], [], [], [], []
    seen = {}
    for p in paths:
        raw = p.read_bytes()
        digest = sha(raw)
        inputs.append({'path': rel(p), 'sha256': digest, 'bytes': len(raw)})
        if digest in seen:
            inputs[-1]['duplicate_original_of'] = seen[digest]
            continue
        seen[digest] = rel(p)
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('Provider response is not an object')
            result = normalize_capture(data, rel(p), raw)
            profile, ff, ll, gg, mm, cc, tt = result
            assert sha(p.read_bytes()) == digest, 'Source changed during parse; rerun against a stable saved capture.'
            profiles.append(profile)
            facts.extend(ff); links.extend(ll); gaps.extend(gg); metrics.extend(mm); candidates.extend(cc); tables.extend(tt)
        except Exception as e:
            failures.append({'source_path': rel(p), 'source_sha256': digest, 'error': type(e).__name__ + ': ' + str(e)})
    # Evidence validation is independent of text normalization: each recorded
    # substring is reselected from the original decoded HTML and rehashed.
    by_path = {x['path']: x for x in inputs}
    html_cache = {}
    for row in facts + links + metrics + candidates + tables:
        ev = row['evidence']; path = ev['source_path']
        if path not in html_cache:
            data = json.loads((ROOT / path).read_bytes()); data = data.get('data', data)
            html_cache[path] = data.get('html') or ''
        fragment = html_cache[path][ev['html_character_start']:ev['html_character_end']]
        assert sha(fragment.encode()) == ev['html_fragment_sha256']
        assert plain(fragment) == ev['literal_text'] and sha(plain(fragment).encode()) == ev['literal_text_sha256']
        assert row['source_sha256'] == by_path[path]['sha256']
    reports = [{**p, 'report_type': 'publisher_profile_evidence_report', 'fact_ids': [f['fact_id'] for f in facts if f['capture_id'] == p['capture_id']], 'report_limits': ['Publisher statements are not verified official/current assignments.', 'Raw originals and each fact passage remain independently traceable.', 'No case/doc URLs are acquired; saved related snippets are not an outcome cohort.', 'Missing analytics remain null; no invented rates, denominators or person counts.']} for p in profiles]
    write_rows('profiles.jsonl', profiles)
    write_csv('profiles.csv', profiles, ['capture_id', 'reported_name', 'reported_state', 'reported_court', 'reported_county', 'reported_county_basis', 'current_appointment_label', 'education', 'biography', 'career_history', 'status', 'gaps', 'source_url', 'source_path', 'source_sha256'])
    write_rows('facts.jsonl', facts)
    write_csv('facts.csv', facts, ['capture_id', 'field', 'value', 'fact_id', 'source_url', 'source_path', 'source_sha256', 'interpretation_limit', 'evidence'])
    for name, rows in [('report_rows.jsonl', reports), ('dashboard_report_links.jsonl', links), ('gaps.jsonl', gaps), ('reported_analytics.jsonl', metrics), ('unpromoted_analytics_candidates.jsonl', candidates), ('source_table_rows.jsonl', tables), ('input_manifest.jsonl', inputs), ('failures.jsonl', failures)]:
        write_rows(name, rows)
    summary = {'built_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'parser_version': VERSION, 'input_files': len(inputs), 'unique_original_payloads': len(seen), 'profile_capture_records': len(profiles), 'distinct_publisher_profile_urls': len({p['source_url'] for p in profiles if p['status'] in ('parsed_profile', 'partial_profile')}), 'statuses': dict(Counter(p['status'] for p in profiles)), 'fact_records': len(facts), 'biography_bodies': sum(bool(p['biography']) for p in profiles), 'directly_reported_numeric_analytics': len(metrics), 'dashboard_report_link_records': len(links), 'independent_statistics_computed': False, 'failure_count': len(failures), 'network_requests': 0, 'source_mutations': 0, 'unique_current_judge_count': None, 'full_judge_corpus_complete': False}
    write_json('summary.json', summary)
    write_json('validation.json', {'validated_at_utc': summary['built_at_utc'], 'source_files_verified': len(inputs), 'evidence_substrings_rehashed': len(facts + links + metrics + candidates + tables), 'failure_count': len(failures), 'failures': failures, 'originals_unchanged': all(sha((ROOT / x['path']).read_bytes()) == x['sha256'] for x in inputs), 'all_independent_statistics_null': all(p['independently_computed_statistics'] is None for p in profiles), 'missing_analytics_null': all(p['directly_reported_analytics'] is None or isinstance(p['directly_reported_analytics'], list) for p in profiles)})
    manifest = {rel(p): {'sha256': sha(p.read_bytes()), 'bytes': p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'files.sha256.json'}
    write_json('files.sha256.json', manifest)
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
