"""Generates accuracy_audit.md and accuracy_defects.json from one findings list (read-only audit, 2026-09-18)."""
import json, pathlib
OUT = pathlib.Path(__file__).resolve().parent
B = 'http://127.0.0.1:8769'
AD = 'delivery/archive-directory/'
D = []
def add(id, severity, area, title, repro, observed, expected, affected, root, fix):
    D.append({'id': id, 'rank': len(D) + 1, 'severity': severity, 'area': area, 'title': title,
              'reproduction': [B + r if r.startswith('/') else r for r in repro], 'observed': observed, 'expected': expected,
              'affected_count': affected, 'root_cause': root, 'fix': fix})

add('D01', 'critical', 'classification',
    'Review-state values are used as the document type, so about 11,000 saved statutes, constitutions and court rules sit in "Other saved resources"',
    ['/api/explore?group=laws', '/api/documents?group=laws&kind=needs_content_review&limit=5',
     '/api/documents?group=laws&state=New%20Jersey&q=constitution&kind=needs_content_review'],
    'Laws hub shows local Constitutions=1, Regulations=0, Rules=76, Other=10,674. "New Jersey Constitution | NJ Legislature" and "Rules of Court | NJ Courts" are category "other". In focused, kind=needs_content_review (7,187) and law_document_title_evidence_needs_review (2,826) are content-review states, not types (quality text_artifact_available_content_review_required on 10,004 of them).',
    'Each record keeps its retained source category. Payload category/categories_json on the 12,276 focused "other" records maps to statutes 7,636, rules 1,585, constitutions 1,259, regulations 151, multi-valued 423, genuinely other 1,193, none 4.',
    {'recoverable_with_source_category': 11079, 'focused_other_records': 12276, 'review_state_kind_records': 10013},
    AD + 'server.py:_build, focused loop: add(... kind = county_reviewed_resource_kind or content_kind or category) puts content_kind (a review state) ahead of category; ' + AD + 'categories.py:classify has no mapping for review states so they fall to "other".',
    'Do not rewrite kind. Add a derived-facet sidecar (hash-gated supplement) with derived_category, category_basis="retained source category field" and review_state=needs_content_review. classify(kind) stays the fallback; explore._local_rows, query_documents(category) and public_item read derived_category when present and show review_state as a separate badge/filter. Multi-valued categories_json become multi-membership like record_groups. Original kind/category stay in payload as retained source claims. See D11 for the one collection whose source category is itself unreliable.')

add('D02', 'critical', 'dates',
    'Saved/source/effective dates are missing from lists, filters and sort; focused and Open US Law records always show "Unknown"',
    ['/api/record?id=<focused display id> (checked on a law_chapter_body record: saved_at null while metadata.retrieved_at=2026-09-13T10:48:25+00:00)',
     '/api/documents?group=laws&dataset=open_us_law&state=New%20Jersey&limit=2 then /api/record?id=oul:...',
     '/api/explore?group=all (datasets[].source_as_of null and no saved_at key for all 10 collections)'],
    'document_dates reads only captured_at. Focused payloads carry retrieved_at, indexed_at, raw_hash_verified_at, so saved_at=null for all 16,454 focused records; judge_entities (10,669) have no date key at all. Open US Law records return source_as_of/saved_at/effective_date = null although the dataset has snapshot_date 2026-08-14 and publisher_record has year, last_amended_year and act_status. Seeger metadata.source_date is filled on 24 of 18,360. /api/documents items contain no date field; ordering is title only; no date range or sort parameter exists. Law hub cards call evidenceDates(dataset.source_as_of, dataset.saved_at), never supplied, so every collection shows Unknown/Unknown.',
    'Four separate explicit date fields per record (saved_at, source_as_of, publication_date, effective_date), each with its evidence field name and precision; list items expose saved_at and source_as_of; sort=saved_desc|source_desc|title; saved_from/saved_to and source_year filters; unknown stays unknown and sorts last.',
    {'open_us_law_records_without_any_date': 2978617, 'focused_saved_at_missing': 16454, 'judge_entities_without_date': 10669, 'seeger_with_source_date': 24},
    AD + 'evidence_dates.py:document_dates (captured_at only; retrieved_at ignored; no publisher snapshot fallback); ' + AD + 'server.py:build_browse (browse has no date columns) and query_documents (ORDER BY title only); ' + AD + 'bulk_laws.py:item (no citation/status/snapshot date); ' + AD + 'explore.py:summary (no saved_at key).',
    'document_dates: accept retrieved_at as a saved_at source (report saved_at_field=retrieved_at and retrieval_time_basis); for oul: records set source_as_of from the import snapshot_date with basis "publisher snapshot date" and expose last_amended_year as publisher-reported, never as effective_date. Put saved_at/source_as_of/source_year in the sidecar with an index so query_documents can filter and sort without touching directory.sqlite3. HTTP Last-Modified stays excluded.')

add('D03', 'high', 'jurisdiction',
    'Federal material has no usable jurisdiction or court facet: 8,013 Seeger federal records have blank state while bulk federal law uses state "Federal"',
    ['/api/explore?group=federal', '/api/explore?group=laws&state=Federal', '/api/documents?group=federal&state=New%20Jersey&limit=5'],
    'group=federal has 8,508 display groups but the state dropdown (51 states) reaches only the 496 court-website records; federal + New Jersey returns 5. Laws > Federal shows 0 local documents although 1,077 U.S.C. provisions and 233 FDA / 21 CFR provisions are saved locally (group=federal, state=""). 6,703 Seeger records carry metadata.source_jurisdictions=["Federal"] and source_courts (253 distinct published court labels, e.g. "Arizona district court", "Tax Court") that are not indexed.',
    'A jurisdiction_level facet (federal / state / county / territory / multi) and a court facet built from the published court label; "Federal" selectable in every group; local U.S.C./CFR provisions reachable from Laws > Federal and Regulations.',
    {'seeger_federal_blank_state': 8013, 'with_explicit_federal_claim': 6703, 'distinct_source_courts': 253, 'local_usc_cfr_provisions': 1310},
    AD + 'server.py:_build supplements loop (state = p.state_if_explicit or p.state; metadata.source_jurisdictions and source_courts never read); ' + AD + 'bulk_laws.py:state_names maps FEDERAL to "Federal" for bulk only.',
    'Sidecar fields jurisdiction_level and court_label_as_published copied verbatim from metadata.source_jurisdictions/source_courts (explicit evidence; no inference of state from a court name). Offer "Federal" for local records whose source_jurisdictions contains Federal; add court param to /api/documents. Base-table state stays "".')

add('D04', 'high', 'filters',
    'Five Source-directory filters in the UI are dead: the API ignores them and returns no facets for them',
    ['/api/sources?content_kind=pdf&limit=1', '/api/sources?layer=federal&limit=1', '/api/sources?task_family=x&limit=1', '/api/sources?category=Uncategorized&limit=1'],
    'content_kind, layer, task_family, source_type and access_requirements each return total 9,348 (unfiltered). Facet keys returned: jurisdictions, categories, access_methods, statuses, availability only, so the File type / Research task / Source layer / Publisher type / Access requirement selects render empty. Category matching is case sensitive (Uncategorized -> 0) while jurisdiction is case-insensitive.',
    'content_kind=pdf -> 1,676; xlsx 136; zip 104; docx 61; api 16; json 2; csv 1; page 7,352. Facets task_families, content_kinds, layers, source_types, access_requirements returned with counts.',
    {'source_references': 9348, 'dead_filters': 5},
    AD + 'source_directory.py:listing (filters dict limited to jurisdiction, category, access_method, verification_status; facets copied from catalog.json which holds only 4 lists) versus the field list in ' + AD + 'app.js (renderSources, line 457).',
    'Extend listing() filter keys to the five fields already present on every entry (PUBLIC already exposes them); compute their facets in _decode; casefold category like jurisdiction. No data change.')

add('D05', 'high', 'classification',
    '3,648 "Uncategorized" source references: 2,846 have an evidence-backed label in their own layer/subsection/task_family fields',
    ['/api/sources?category=uncategorized&limit=30'],
    'uncategorized is the largest category (39% of 9,348). Own-field evidence: subsection "State Agencies & Offices" 505; State and Local Courts / Bankruptcy Courts 487; layer court_practice 314; tribunal_topical 209; Local Government 163; Commercial & Third-Party 158; layer enforcement 140; Executive & Regulatory 134; Legislature and Laws 100; sci_evidence 73; safety_data 69; case_law 52; task_family only 359. Residual without signal: 802 (711 state_resource harvest rows such as year-number titles on sos.mo.gov).',
    'A derived display category with a basis label; the existing 27 categories untouched; new display buckets for state agencies, courts directory, local government, executive/regulatory, court practice, tribunals, science evidence, commercial/third-party.',
    {'derivable': 2846, 'uncategorized': 3648, 'residual': 802},
    'sources/public_law_directory_20260919 builder keeps a blank original_category as "uncategorized" (taxonomy_qualification: no semantic recategorization); ' + AD + 'source_directory.py has no derived layer.',
    'Add derived_category + derived_category_basis (e.g. "subsection: State and Local Courts --- Supreme Court") at _decode time or in a sidecar, using the explicit rule table below. Keep category=uncategorized and original_category=null as retained source claims; the detail view shows "Source map: uncategorized".')

add('D06', 'high', 'jurisdiction',
    'One 114-byte parked-domain redirect page is published as 90 county websites and joined to 80 counties in 26 states',
    ['/api/documents?county=01021&limit=10', '/api/documents?group=counties&q=swishercounty.gov&limit=3', '/api/documents?group=laws&state=South%20Dakota&q=sdlegislature.gov/Constitution'],
    'Chilton County AL lists "https://swishercounty.gov/" with state = 26 states and 90 source records. The raw file (sha 6dc9c7fc93bb...) is a script redirect to /lander. record_counties holds 4,885 rows from these 89 multi-state records; the record own evidence says registry_state_codes=["TX"], county_name_association=UNREVIEWED. Also 31 sdlegislature.gov/Constitution/* captures are one identical 5,982-byte SPA shell ("Loading... Your browser is not supported", 162 chars) counted as Saved text; 4 zero-byte captures; 219 focused captures under 1 KB; titles "An Error Has Occurred", "Redirecting...".',
    'Shell, parked, challenge and empty captures are excluded from publication and county joins; county joins never come from a shared raw-file hash.',
    {'wrong_county_joins': 4885, 'parked_shell_urls': 90, 'counties_polluted': 80, 'spa_shell_records': 31, 'zero_byte': 4, 'under_1kb': 219},
    AD + 'server.py:_build (raw_geo built from trellis_raw_paths/reported_site_raw_paths/candidate_site_raw_paths, then geos |= raw_geo[d.raw_path]): raw paths are content-addressed, so identical shell bytes union every county that ever received that shell. Upstream county-site collector accepted HTTP 200 shells.',
    'Sidecar capture_validity (shell_redirect, spa_shell, empty, ok) from an exact hash list plus size/text thresholds; non-ok records leave eligible results, county joins and saved_sites counts. At the next rebuild, skip raw_geo joins when one raw hash maps to more than one registrable domain. Raw bytes and receipts are kept.')

add('D07', 'high', 'labels',
    'Titles that are URLs, extraction placeholders or site boilerplate',
    ['/api/documents?group=counties&kind=local_rules&limit=10', '/api/documents?group=federal&q=Model%20Civil%20Protective%20Order&limit=5', '/api/documents?group=laws&dataset=open_us_law&state=New%20Jersey&category=statutes&page=300&limit=1'],
    'Focused display groups: 2,934 URL titles (2,697 URL-titled records are needs_content_review PDFs), 312 placeholder titles ("[DOCX text]" 199, "[Word 2003 XML text]" 75, "[OCR]" 37) which public_item renders as "<url> [DOCX text]", 641 site-name titles shared by 5+ pages ("Nebraska Legislature" 240, "Kansas Statutes" 122, "Code of Virginia" 74), 82 generic ("Home", "PDF", "Title", "1", "@"). pending_publication: 113 URL titles. public_item also mangles legitimate titles that start with "[": "[Model] Civil Protective Order" becomes "https://www.moed.uscourts.gov/... [Model] Civil Protective Order" (5 seeger, 4 judge records). Open US Law list titles are bare section headings ("Effective date") without the citation held in the citation column.',
    'Display title = best explicit evidence (document heading, citation, de-slugged filename) with title_basis; original title retained. Bulk items show "N.J. Stat. 12A:10-106 - Effective date".',
    {'focused_url_titles': 2934, 'boilerplate_titles': 641, 'placeholder_titles': 312, 'pending_url_titles': 113, 'generic_titles': 82, 'bracket_mangled': 9},
    AD + 'server.py:_build add() (title or url); ' + AD + 'server.py:public_item (startswith("[") rule too broad); ' + AD + 'bulk_laws.py:item (title only); pending_titles.py repairs only pending_publication.',
    'Sidecar display_title + title_basis using the existing pending_titles method extended to focused (first heading / citation line of saved text, else de-slugged filename, else host + path). Narrow the public_item rule to the exact extraction placeholders. bulk_laws.item: prefix citation when the title lacks it.')

add('D08', 'high', 'filters',
    'No file-type or data-type filter on documents although the type is derivable for every saved file',
    ['/api/documents?group=all&limit=1 (no file_type field or facet in the response)'],
    'Items expose has_original/has_text only. Derived from the saved original file suffix over 58,310 records: pdf 16,129; jsonl 13,574; json 7,749; html 6,765; txt 5,857; csv 4,074; docx 1,319; xml 1,315; doc 379; zip 8; xlsx 4; rtf 4; gz 3; no file 576; ".bin" 554 (type unknown although a content_type header exists for many). Seeger carries metadata.format; focused carries content_type.',
    'file_type facet (pdf, html, docx/doc, xlsx/csv, xml, json, zip, link only) and record_type facet (original document, structured provision, source observation, profile, registry row, publisher bulk record).',
    {'records_with_derivable_file_type': 57180, 'unknown_bin': 554, 'no_file': 576},
    AD + 'server.py:build_browse (no format column) and public_item (no file_type); ' + AD + 'explore.py:AVAILABILITY offers only text/original/link_only.',
    'Sidecar file_type (saved file suffix, else payload format/content_type, basis recorded) and record_type (metadata.record_type or dataset rule). Add file_type and record_type params to query_documents and facets to explore.summary.')

add('D09', 'medium', 'classification',
    'Seeger catch-all kind court_form_or_other_document (10,543) is labelled "Forms & documents" though about a third look like orders, rules or instructions',
    ['/api/documents?group=laws&category=other&state=Texas&limit=12', '/api/documents?group=federal&category=forms&q=Case%20Management%20Order&limit=5'],
    'Title/URL keyword hints: form-like 5,076; order 1,903 (e.g. "Case Management Order - Class Certification Case" under azd judge-orders); rule 797 ("Judicial Branch Certification Commission Rules"); instruction/guide/procedure 725; fee 56; no hint 1,986. Payload kind_basis: "source catalog/title organizing hint, not an independent content review".',
    'Subtype facet (form, order / standing order, rule, judge procedure, instructions / guide, fee schedule, other) with basis "title/URL hint"; bucket label "Court documents & forms" until reviewed.',
    {'likely_not_forms_estimate': 3425, 'records': 10543},
    'sources/seeger_import_20260918 resource_kind catch-all; ' + AD + 'categories.py:classify maps it to forms.',
    'Sidecar doc_subtype + subtype_basis from an explicit keyword table; no automatic move between top categories except where source_collections / URL path says judge-orders, general-orders or local-rules. resource_kind retained.')

add('D10', 'medium', 'classification',
    'Judge observations pollute document categories in the All view',
    ['/api/explore?group=all', '/api/explore?group=judges'],
    'trellis_directory (4,458 judge observations) matches the substring "directory" and is counted under "Courts & directories" (4,646 in group=judges); the remaining 18,139 judge records (10,671 display groups) are counted under "Other saved resources"; one focused record kind=document in the judges group yields Forms=1.',
    'Judge datasets get their own bucket ("Judge profiles & observations") or are excluded from legal-document category facets.',
    {'judge_records_in_other': 18139, 'judge_records_in_directories': 4458},
    AD + 'categories.py:classify (substring rule over "directory", "website", "portal", "roster"; no judges bucket); ' + AD + 'explore.py:_local_rows classifies every dataset by kind only.',
    'Add LABELS["judges"]; classify(kind, dataset=None) returns it for judge_* datasets; the default argument keeps current callers and tests unchanged.')

add('D11', 'medium', 'classification',
    'Trellis state-rules captures carry collection category court_rules although the URL path names constitution, code, statutes or administrative code',
    ['/api/documents?group=laws&category=other&state=Texas&limit=12'],
    '1,417 focused records from trellis.law/state-rules/<st>/<type>/: constitution 584, code 249, statutes 137, administrative-code 90, general-laws 66, court-rules 43, rules-of-civil-procedure 37, rules 29, others. All carry category court_rules; kinds legal_inventory_navigation 950, legal_text_fragment 443, captured_law_representation 24. "Sec. 1. FREEDOM AND SOVEREIGNTY OF STATE - Texas Code | Trellis Law" is constitution text.',
    'Derived category from the publisher path segment (the publisher own taxonomy, not hostname inference) with a basis label; source category retained.',
    {'non_rule_path_records_at_least': 1224, 'records': 1417},
    'Collection-level category assignment in the focused publication; becomes user-visible as soon as D01 starts using the payload category.',
    'In the D01 sidecar apply the path-segment rule before the payload category for this collection only; basis "publisher URL path segment".')

add('D12', 'medium', 'jurisdiction',
    'U.S. territory sources are filed under District of Columbia in the source directory',
    ['/api/sources?jurisdiction=dc&q=pr.gov&limit=10', '/api/sources?jurisdiction=dc&limit=100'],
    'Section "U.S. TERRITORIES --- COURTS, BARS, LEGISLATURES & AGENCIES" has 71 entries: 64 jurisdiction=dc, 3 vi, 2 pr, 1 us, 1 nm. Subsections name the territory (U.S. Virgin Islands 22, Puerto Rico 18, Guam 10, Northern Mariana Islands 8, American Samoa 1). Only 44 of 119 dc entries have a DC host. Facet shows Puerto Rico=2, U.S. Virgin Islands=3, and no Guam/CNMI/American Samoa. A further 33 state-TLD hosts are filed under us (harvest rows).',
    'Territory entries selectable under their territory; DC shows only DC.',
    {'territory_entries_under_dc': 64, 'with_explicit_territory_subsection': 59, 'state_hosts_under_us': 33},
    'Upstream registry_v06_1 jurisdiction claim retained verbatim by the sources/public_law_directory_20260919 builder; ' + AD + 'source_directory.py:listing filters on it.',
    'Derived jurisdiction_display from the entry own subsection when its section is the territories section; jurisdiction=dc retained as the source claim; add gu, mp, as facet values. The 33 us rows go to a review list and are not moved automatically (no hostname inference).')

add('D13', 'medium', 'labels',
    'Source-directory titles and section labels are frequently hostnames, filenames or harvest batch names',
    ['/api/sources?q=download.aspx&limit=10', '/api/sources?category=court_forms&q=forms&limit=30'],
    '555 titles equal the host; 20 are URLs; 2,463 entries sit in non-unique title sets of 5+ ("Forms" 135, "Official court" 94, "Download full text as PDF" 58, "download.aspx" 45, "list.aspx" 29, years "1980".."1984"). section is a batch label for 4,557 entries (HARVEST2-2026-08-19 3,246; HARVEST-2026-08-19 1,311); subsection is a URL or host for 5,032. app.js sourceDisplayTitle disambiguates only 9 exact words. All 9,348 entries share source_as_of 2026-08-19; only 1,175 have a description.',
    'Display title = title + court/agency context whenever the title is not unique; harvest batch shown as provenance, not as a topical section.',
    {'batch_label_sections': 4557, 'generic_duplicate_titles': 2463, 'host_titles': 555, 'url_or_host_subsections': 5032},
    'Registry harvest rows; ' + AD + 'app.js:sourceDisplayTitle (fixed word list); ' + AD + 'source_directory.py passes PUBLIC fields through unchanged.',
    'Compute display_title and display_section in source_directory._decode: append jurisdiction_label/host when the title count > 1 or title == host; present HARVEST* sections as "Harvested links (Aug 19, 2026)" grouped by host. Original fields retained.')

add('D14', 'medium', 'dates',
    'Legal status (repealed, reserved, renumbered, in force) is not shown in results or filterable',
    ['/api/documents?group=federal&q=Repealed&category=statutes&limit=5'],
    'Seeger provisions: source_status repealed 35, abrogated 6, reserved 5, renumbered 4, omitted 1, transferred 1, text_present 1,029, published_text 229, none 17,050. Open US Law has a status column and act_status in each publisher record, but /api/documents items omit it; repealed 28 U.S.C. 142 lists like an in-force section apart from its title.',
    'publisher_status on list items with an "as of snapshot" qualifier, a status filter, nothing hidden by default.',
    {'open_us_law_records_with_status_column': 2978617, 'seeger_non_current_provisions': 52},
    AD + 'bulk_laws.py:item/query (status and citation not selected); ' + AD + 'server.py:public_item (no status).',
    'Expose status as publisher-reported with its snapshot label; add a status param in bulk_laws.clauses scoped to state+kind queries (the 2.9M-row index has no status index and must not be rebuilt).')

add('D15', 'medium', 'settlements',
    'Settlement library has no status/deadline/jurisdiction filters, stale "open" statuses and almost no attached documents; MDL-3080 lists 24 of 1,612 PDFs',
    ['/api/collection?id=settlements&status=Closed', '/api/collection?id=settlements&sort=deadline', '/api/collection?id=mdl-3080'],
    'collection() accepts q, family, kind, page, page_size only; status, state and sort are ignored (848 returned). Status: Claim window closed 448, Open for claims 365, Published record 21; status_as_of is June 16-19, 2026; 11 records say open while their ISO claim_deadline is before 2026-09-18. state=null for 848/848, court_label on 9, source_date on 0, documents attached on 3, reviewed records 9, saved PDFs 4. mdl-3080: record_count 1,612, total 24.',
    'Filters for status, deadline window, court/state as published, has documents; a computed "deadline passed since status date" flag; standard document types per settlement (agreement, notice, claim form, preliminary/final approval order, fee motion, plan of allocation).',
    {'settlements': 848, 'without_documents': 845, 'open_with_passed_deadline': 11, 'mdl3080_listed': 24, 'mdl3080_cataloged': 1612},
    AD + 'local_library.py:collection (fixed filter set; items from preview jsonl); sources/local_library_presentation_20260918 exports a 24-row preview for MDL-3080.',
    'Add status/deadline_before/deadline_after/has_documents params and sort to collection(); compute deadline_passed at request time from claim_deadline with the label "computed from published deadline". Document acquisition is a separate bounded packet task.')

add('D16', 'medium', 'filters',
    'Grouped results show the preferred record category, not the category that matched the filter; raw compound kinds in the Type select',
    ['/api/documents?group=laws&category=other&state=Texas&limit=12'],
    'category=other returns rows labelled "Forms & documents" because any member of a display group can match while the preferred member is displayed. 103 non-judge display groups have members in more than one category. Compound kinds ("local_rules; ocr_text" 31, "court_directory; ocr_text" 1, county entry compounds 8) are separate options; the Type select lists 116 raw kinds including review states.',
    'Result rows state the matched category or all member categories; ocr_text is a flag, not part of kind.',
    {'mixed_category_groups': 103, 'compound_kind_records': 40, 'raw_kind_options': 116},
    AD + 'server.py:query_documents (matched = any member; public_item(preferred)); _build keeps "; "-joined kinds.',
    'Return matched_categories per item; split compound kinds on "; " into kind + flags in the sidecar; Type select shows human labels grouped by category; review states move to a Review status filter.')

add('D17', 'medium', 'judges',
    'Judge filters cannot reach profiles with unknown system, state or court; three different judge totals are shown',
    ['/api/judges?limit=1', '/api/judges?system=federal&limit=1', '/api/judges?system=state&limit=1'],
    'total 10,698; federal 4,454 + state 4,413 = 8,867, leaving 1,831 profiles with no system and no "Unknown" option; 899 profiles have no state row, 1,490 no court row. 310 repeated names cover 635 profiles (expected under the no-merge-by-name rule, but the list gives no cue). Home card shows 10,669 (entities), Judges page 10,698 (+29 PA official profiles), explore group=judges 10,860 display groups. No filter for MDL assignment, service status, appointing authority or commission year; sort is name or score only.',
    'Explicit "Not recorded" facet values with counts; one documented definition per total; date/status filters from FJC fields where present.',
    {'no_system': 1831, 'no_court': 1490, 'no_state': 899, 'repeated_name_profiles': 635},
    AD + 'judges.py:_populate_projection (systems exclude "unknown"; states/courts rows only when present) and listing (no unknown option).',
    'Add has-no-system/state/court filter values in listing() (NOT IN subquery; no projection rebuild needed); label totals with their definitions. No identity merging.')

add('D18', 'low', 'labels',
    'Inconsistent or misleading labels and hard-coded statistics',
    ['/api/documents?group=counties&state=Alabama&kind=county_government_entry_unreviewed&limit=5', '/api/explore?group=laws&category=rules', '/api/summary'],
    'County homepages split across categories: county_government_website_to_verify (660) -> "Courts & directories" via substring "website"; county_government_entry_unreviewed (1,027) -> "Other". Presidential executive_order (738) -> "Rules & orders" (described as court rules); ruling 7,248, proclamation 1,832, presidential_document 655, enforcement_action 140, treaty 119 -> "Other". app.js datasetName has no entry for focused/federal so cards read "Focused". server.py hard-codes profiles 1300, federal_biographies 4074, evaluations 116, analyses 258, vendor_measures 450, files 229, county count 3144.',
    'One bucket for county government websites; executive/agency material under an explicit label; dataset labels from server definitions; statistics computed from source summaries.',
    {'bulk_other_records': 9994, 'county_homepages_split': 1687, 'executive_orders_in_rules': 738},
    AD + 'categories.py:classify; ' + AD + 'app.js:datasetName; ' + AD + 'server.py:_build baseline dict and enriched_summary.',
    'Extend classify with exact values (no new substrings); add an "executive" label or fold into guidance; datasetName falls back to the summary.datasets title; replace literals with counts read from source summary files.')

add('D19', 'low', 'performance',
    'Free-text search in Laws takes 8-13 s and facet counts ignore the search text',
    ['/api/documents?group=laws&q=statute%20of%20limitations&limit=1', '/api/explore?group=laws'],
    'q="statute of limitations" 8.0 s; with availability=text 13.0 s; unfiltered group=all 6.0 s. explore.summary documents that it does not apply q, so category counts beside a search do not describe the search result.',
    'Typical response under 2 s; facets for the active search, or an explicit "counts ignore search text" note.',
    {'slowest_measured_seconds': 13},
    AD + 'server.py:query_documents (two FTS subqueries OR-ed inside IN over browse, then a display-group IN subquery, executed for count, source count and page; bulk count(*) over FTS).',
    'Materialise matching ids once per request into a temp table and reuse for count and page; lru_cache bulk FTS counts keyed by (q, filters, DB signature).')

RULES = [
    ("subsection contains State and Local Courts / Bankruptcy Courts / District Court / Courts of Appeal", 'courts_directory', 487),
    ("subsection contains Legislature and Laws", 'statutes_codes (legislative materials)', 100),
    ("subsection contains Executive and Regulatory / Governor", 'executive_regulatory', 134),
    ("subsection contains State Agencies", 'state_agencies', 505),
    ("subsection contains Local Government", 'local_government', 163),
    ("subsection contains Commercial & Third-Party", 'commercial_thirdparty', 158),
    ("layer = case_law", 'opinions_decisions', 52),
    ("layer in enforcement, agency_enforcement", 'enforcement_actions', 140),
    ("layer = safety_data", 'recall_safety_data', 69),
    ("layer = sci_evidence", 'science_evidence', 73),
    ("layer = court_practice", 'court_practice', 314),
    ("layer = tribunal_topical", 'tribunal_topical', 209),
    ("layer in discovery, mdl_practice", 'mdl_discovery_practice', 27),
    ("layer in insurance, bankruptcy, corporate, professional_license", 'layer name', 56),
    ("task_family present (fallback)", 'task family label', 359),
    ("no signal", 'uncategorized (unchanged)', 802),
]
CHECKS_OK = [
    'explore totals equal /api/documents totals for 22 tested filter combinations (group, category, state, availability, dataset); no facet/total mismatch when q is absent.',
    '/api/counties facet counts equal filtered totals for 10 tested combinations; 0 counties claim local_resources without linked records.',
    'No U+FFFD replacement characters in any browse title.',
    'Invalid group/category/state values return 0 rows and an invalid page returns HTTP 400.',
    'Territories are absent from the counties table by design (51 state values, 3,144 rows); New Jersey has 21 counties, 3 with local resources, 0 with a court registry.',
]
NOT_VERIFIED = [
    'Browser rendering of app.js was not exercised; UI findings come from reading app.js plus API responses.',
    'Content-level correctness of source categories was not reviewed; D01 counts rely on the retained source category field (see D11 for a known unreliable collection).',
    'D09 subtype counts are title/URL keyword estimates, not content review.',
    'Open US Law status distribution (2,978,617 rows) was not aggregated, to avoid a full scan of the bulk index.',
    '/api/people, /api/county-registry, /api/source detail and /source-assets were not audited.',
    'Judge identity accuracy and MDL judge coverage were not audited (filter reachability only).',
    'Settlement deadline check used ISO claim_deadline only; 234 records without a deadline were not assessed.',
    'The 33 state-TLD hosts filed under jurisdiction us were flagged by host pattern only and need manual review.',
]
SIDE = {'name': 'sources/record_facets_20260919', 'adapter': AD + 'record_facets.py', 'key': 'directory records.id; oul: ids handled by rule, not per row',
        'fields': ['derived_category', 'category_basis', 'review_state', 'doc_subtype', 'subtype_basis', 'file_type', 'file_type_basis', 'record_type', 'jurisdiction_level', 'court_label_as_published', 'saved_at', 'saved_at_field', 'source_as_of', 'source_as_of_field', 'publisher_status', 'capture_validity', 'display_title', 'title_basis'],
        'rule': 'Never overwrites kind, category, title, state or payload; every derived value carries its basis; fail-closed hash gate like county_registry.py.'}
BASE = {'records': 58310, 'display_groups': 45658, 'local_documents_all': 45655, 'bulk_records': 2978617, 'other_category_all': 22470,
        'other_category_laws_local': 10674, 'source_references': 9348, 'uncategorized_sources': 3648, 'judge_profiles': 10698, 'counties': 3144}
doc = {'generated': '2026-09-18', 'server': B,
       'method': 'Read-only: code review of categories.py, explore.py, evidence_dates.py, source_directory.py, county_registry.py, server.py, bulk_laws.py, local_library.py, judges.py, app.js; GET-only API probes; SQLite mode=ro aggregates on directory.sqlite3, profiles.sqlite3, the Open US Law files table and catalog.json.',
       'baseline': BASE, 'defects': D,
       'uncategorized_rule_table': [{'when': w, 'derived': d, 'count': n} for w, d, n in RULES],
       'recommended_sidecar': SIDE, 'checks_passed': CHECKS_OK, 'not_verified': NOT_VERIFIED}
(OUT / 'accuracy_defects.json').write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def num(v): return format(v, ',') if isinstance(v, int) else str(v)
L = ['# Accuracy audit of the live MVP: classification, filters, placement, dates, labels', '',
     'Date: 2026-09-18. Read-only. Server ' + B + ' (GET only); SQLite opened with mode=ro; no existing project file was modified.',
     'Machine-readable copy: `accuracy_defects.json`. Both files are generated by `accuracy_audit_build.py` in this folder.', '',
     '## Baseline measured', '', '| Measure | Value |', '|---|---|']
L += ['| ' + k.replace('_', ' ') + ' | ' + num(v) + ' |' for k, v in BASE.items()]
L += ['', 'Half of all local display groups (22,470 of 45,655) are in "Other saved resources". In Laws, local Constitutions = 1 and Regulations = 0, although the record payloads say otherwise (D01, D03).', '',
      '## Defects ranked by user impact', '', '| # | Severity | Area | Defect | Main count |', '|---|---|---|---|---|']
for d in D:
    k, v = next(iter(d['affected_count'].items()))
    L.append('| ' + d['id'] + ' | ' + d['severity'] + ' | ' + d['area'] + ' | ' + d['title'] + ' | ' + k.replace('_', ' ') + ': ' + num(v) + ' |')
L.append('')
for d in D:
    L += ['### ' + d['id'] + ' - ' + d['title'], '', '- Severity: ' + d['severity'] + '. Area: ' + d['area'] + '.', '- Reproduce:']
    L += ['  - `' + r + '`' for r in d['reproduction']]
    L += ['- Observed: ' + d['observed'], '- Expected: ' + d['expected'],
          '- Affected: ' + '; '.join(k.replace('_', ' ') + ' = ' + num(v) for k, v in d['affected_count'].items()),
          '- Root cause: ' + d['root_cause'], '- Low-risk fix: ' + d['fix'], '']
L += ['## Rule table for the 3,648 uncategorized source references (D05)', '', '| Rule on the entry own fields (first match wins) | Derived display category | Count |', '|---|---|---|']
L += ['| ' + w + ' | ' + d + ' | ' + num(n) + ' |' for w, d, n in RULES]
L += ['', '`category=uncategorized` and `original_category=null` stay as retained source claims.', '',
      '## One shared fix: a derived-facet sidecar', '',
      'D01, D02, D03, D06, D07, D08, D09, D11, D14 and D16 can be delivered without rebuilding `directory.sqlite3` through one hash-gated supplement (`' + SIDE['name'] + '`, adapter `' + SIDE['adapter'] + '`) keyed by record id.',
      'Fields: ' + ', '.join(SIDE['fields']) + '.', SIDE['rule'], '',
      'The integrator then changes four read paths: `explore._local_rows` (category, file type, jurisdiction level), `server.query_documents` (new params file_type, record_type, court, jurisdiction_level, status, review_state, saved_from, saved_to, sort), `server.public_item` (display_title, dates, status, matched categories) and `source_directory.listing` (five extra filters, derived category, derived jurisdiction).', '',
      '## Checks that passed', ''] + ['- ' + x for x in CHECKS_OK] + ['', '## Not verified', ''] + ['- ' + x for x in NOT_VERIFIED] + ['']
(OUT / 'accuracy_audit.md').write_text('\n'.join(L), encoding='utf-8')
print('defects', len(D), '| json bytes', (OUT / 'accuracy_defects.json').stat().st_size, '| md bytes', (OUT / 'accuracy_audit.md').stat().st_size)
