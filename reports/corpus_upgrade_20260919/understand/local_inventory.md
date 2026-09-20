# Local inventory: valuable data not yet visible in the MVP

Agent: local-inventory. Read-only. Generated 2026-09-19. No network, no imports, no edits to existing files.
All databases opened `mode=ro`. Counts below were measured in this run unless marked (prior audit).
"MVP" = `delivery/archive-directory` (directory.sqlite3 `browse`: focused 16,454; seeger 18,360; judge_enrichment
11,926; judge_entities 10,669; federal 591; pending_publication 301; judge_vendor 2; trellis_browser_counties 6;
provider_laws 1; 29,311 distinct source URLs) plus the adapters (people, judges, local_library, county_registry,
source_directory, source_captures, source_archive_links, bulk_laws).

## 0. Headline findings

1. CourtListener people layer is already imported (6 tables) and the People UI already shows positions and
   education. What is NOT shown: political affiliations (8,486 rows), appointer, how_selected (11,265 positions),
   termination_reason (10,259), Senate votes (703), sector. Tables never imported: courthouses (near-empty, low
   value), court-appeals-to (8), races (6,542, sensitive), financial disclosures (32,336 + 1.9 M investments),
   opinion-panel memberships (835,148), citations (127 MB, header only), originating-court-information (20 MB).
   There is NO ABA-ratings CSV in the snapshot (the table exists only in `schema-2026-06-30.sql`).
2. The SW-BULK release is the best local judge-to-MDL evidence and is completely invisible in the MVP:
   867 judges / 4,776 assignments / 3,409 assigned matters (4,159 matters total), plus 181 attorneys, 12 firms,
   878 counsel appearances, 503 parties, 53 MDL membership edges, 900 opinions, 25 FJC outcomes.
3. Magistrate judges central to NJ/other MDLs (e.g. Leda Dunn Wettre 169 assignments, Mark Falk 51, Lois Goodman
   49, Joel Schneider 26) have no name-token presence in the 10,698-profile Judges UI (16 of the top 60 SW-BULK
   judges absent; all absentees checked look like magistrates). All 850 native IDs exist in the People layer.
4. 206 of 207 federal court logo/seal entries carry a court ID that equals a CourtListener court ID exactly
   (e.g. `FD:njd` -> `njd`). 295 verified images exist but only 4 images are served by the MVP (269 court
   entries are listed with `asset_id: null`). The same court-ID prefixes (`FD:`, `FB:`, `F:`, `ST:`, `LC:`) are
   on all 11,178 Seeger court documents (`metadata.source_collections`), so logo <-> court <-> documents <->
   judges positions <-> SW-BULK matters can be joined by ID with no name matching.
5. Seeger court documents are badly under-labelled in the MVP: 10,543 of them share the single kind
   `court_form_or_other_document`; `county` is empty for all 18,360 seeger rows although 177 documents carry an
   explicit `LC:<state>_<county>` registry collection; `source_date` is filled for only 16 of 11,178.
6. 2,329 saved official-court records in `catalog/documents.sqlite3` (collections `official_courts*`) have
   neither source_url nor final_url in the MVP `browse` table: county courthouse directories (IL, CO, WV),
   judge profiles (WV, IL), court rules (134), judicial directory downloads. 2,339 of the 2,380 URL-missing
   catalog records have searchable text.
7. The returned page inventory (13,644 distinct URLs) overlaps the 9,348-reference source directory by exact URL
   on only 19 URLs (39 after scheme/www/trailing-slash normalisation); only 63 returned URLs are in MVP `browse`.
   It is effectively an unused saved-text pool, but 9,852 of 14,047 files are justice.gov (OSG briefs 3,825,
   ATR case docs 2,906) - low priority for this product. High-value remainder: Philadelphia courts 602 (394 PDF
   URLs, 240 forms), DC courts 496 (473 form-search pages), PA courts 395, NV legislature 456, Montana code 500
   (folder misnamed `MO-codelaw`), Allegheny 199, OSCN 198, NJ courts 88, KY courts 33.
8. `returnedfiles/_pdf_directory/url_directory.jsonl` is a pre-classified frontier of 96,648 unique URLs
   (14,762 PDFs) with only 190 exact overlaps with the 9,348 directory. It already contains 1,053 uscourts.gov
   statistics/data-table URLs and 591 fda.gov URLs - the exact categories the user asked for.
9. Trellis: everything downloaded is already in the MVP (1,433 county profiles, all 1,367 state-rule pages by
   exact URL, 1,300 profiles, 4,458 directory rows). The unused part is the discovered frontier: 17,123 state-rule
   URLs, 1,077 county coverage URLs, 11,099 judge-profile URLs (1,300 later fetched by judge_focus), 938 filing
   URLs, 95,884 case URLs.
10. `devvvv/` is a snapshot of the external Seeger Weiss platform app (TanStack Start + Lovable, AWS). It holds
    no reusable legal data, but it holds the integration target: `docs/ingest-contract-v1.md` (matter bundle
    contract) and `db/kb/0003_reference_courts.sql` (`reference.courts`, `reference.judges`,
    `reference.court_documents`) whose `court_id` is the same CourtListener/DocketBird ID convention.

---

## 1. CourtListener bulk tables (`C:/Users/firas/Downloads/returnedfiles/bulk`, snapshot label 2026-06-30)

27 files, 201.6 MB. PostgreSQL CSV dialect: `escapechar=backslash, doublequote=False, strict=True` (default CSV
parsing mis-splits multiline fields). Snapshot label comes from filenames; a citations row has
`date_created 2025-10-25`, consistent with a later export, not independently verified.

| Table | Rows | In MVP? | Key fields | Value / note |
|---|---|---|---|---|
| people | 16,191 (394 aliases, 3,711 fjc_id, 4,449 with death date, 1,230 has_photo) | Yes (`sources/courtlistener_people_20260918/catalog.sqlite3`, People UI 15,797 + 394 aliases) | id, names, dob/dod + granularity, fjc_id, is_alias_of_id, has_photo | Already shown |
| positions | 51,291 (15,613 people; 21,225 blank position_type; 17,326 `jud`; 969 `mag`) | Yes; UI shows role, court, org, location, start/end, nomination/election/confirmation/retirement | 38 columns | NOT shown: how_selected 11,265; termination_reason 10,259; appointer_id 8,664 (references positions.id, not people); votes_yes 703; sector 6,766; supervisor 160; predecessor 148 |
| educations | 12,777 (7,398 people) | Yes; shown (school, degree, year) | school_id, degree_level/detail/year | Already shown |
| schools | 6,011 | Yes (join only) | name, ein | - |
| political_affiliations | 8,486 (7,226 people): d 4,535, r 3,817, j 68, f 24, w 22, i 15; source a 5,433 / o 1,809 / b 47 / blank 1,197 | Imported, NOT shown anywhere | political_party, source (a=appointer, b=ballot, o=other), date_start/end + granularity | Smallest safe add: show as "source-recorded affiliation (basis: appointer/ballot/other)" with dates; never as an inferred leaning |
| courts | 3,361 (ST 2,618; F 127; FD 125; SA 111; FB 95; SS 86; S 55; FS 42...). in_use t=471; url 1,056; parent_court_id 2,819; fjc_court_id 200; pacer_court_id 204; start_date 437; end_date 403 | Imported; used only as the People court filter | id, citation_string, short/full name, jurisdiction code, parent_court_id, url, start/end dates | High value as the canonical court registry / ID spine (see section 6) |
| courthouses | 3,361 rows but only 4 with address1, 9 with city, 1 with county, 3 with building name, 6 court_seat=t | No | court_id, address, county, state | Effectively a state-per-court stub. Do NOT present as a courthouse directory |
| court-appeals-to | 8 | No | from_court_id, to_court_id | Tiny; appeal routing edges |
| races | 6,542 (6,521 people) + 8-row lookup | No | person_id, race_id | Sensitive demographic attribute; recommend not surfacing |
| retention-events | 0 | - | - | Empty |
| ABA ratings | No CSV present | - | - | Only in schema SQL. Cannot be backfilled locally |
| financial-disclosures | 32,336 (3,392 people) + investments 1,901,720, positions 37,050, reimbursements 33,472, spousal income 20,174, debts 18,775, non-investment income 15,302, agreements 10,007, gifts 2,025 | No | year, report_type, is_amended, page_count, sha1, filepath (CourtListener S3 PDF path), person_id | Recusal/conflict research value for MDL defendants (investments by issuer). Large; treat as a separate optional layer. Thumbnails are document thumbnails, not portraits |
| search_opinioncluster_panel | 835,148 (3,285 people) | No | opinioncluster_id, person_id | Panel membership only; needs opinion-cluster metadata (not local) to be meaningful. Could support a "published-opinion panel count (CourtListener snapshot)" with denominator stated |
| search_opinion_joined_by | 1,028 (285 people) | No | - | Minor |
| citations | 127 MB bz2, rows not counted (header only) | No | volume, reporter, page, type, cluster_id | Citation -> cluster resolver. Useful later for the platform's citation verification; out of MVP scope |
| originating-court-information | 20 MB bz2, not counted | No | docket_number, assigned_to_str/id, ordering_judge, date_filed/disposed/judgment | Appellate-origin judge linkage; out of MVP scope |

Date semantics: all person/position dates have companion `date_granularity_*` (`%Y`, `%Y-%m`, `%Y-%m-%d`);
Jan 1 may mean year-only. Event dates (nominated/elected/confirmation/retirement) have no granularity column.
`date_created/modified` are CourtListener row timestamps, never legal dates.
Quality risks: people includes non-judges, aliases, deceased; a court-linked position is not proof of current
service (5,771 positions / 5,645 people have no termination date and a court - this is NOT a current-judge count);
`fjc_id` (legacy) != FJC `nid`.

Smallest safe integrations:
- A. Extend `people.py` position/profile view with the already-imported columns (how_selected, termination_reason,
  appointer display name via `position_profiles`, vote counts, political affiliation with basis + dates). No new
  import; schema already validated. Effort small.
- B. Build a `court_registry` supplement from `courts` (3,361) keyed by CL court id, with parent hierarchy,
  jurisdiction code, citation string, url, in_use, start/end. Becomes the ID spine for logos, Seeger documents,
  SW-BULK matters, devvvv `reference.courts`.

## 2. Judge assignment evidence (SW-BULK release)

Path: `C:/Users/firas/Downloads/SW-BULK/AWS-BATCH1-DOCKETS/releases/b2b-cdbb8d040b95c7b65cfc/` (built
2026-08-24T04:59Z, `manifest.json` has per-file rows + sha256; 21 gz JSONL datasets).

| Dataset | Rows | Fields |
|---|---|---|
| judges | 867 (850 with `native_judge_id` = CourtListener person id; 17 name-only) | judge_id (uuid), name, native_judge_id, record_status, source_record_ids |
| judicial_assignments | 4,776 (assigned_judge 3,422; referred_judge 1,354); 865 distinct judges; 3,409 distinct matters; 100% join to judges and matters | assignment_id, judge_id, matter_id, role, source_record_ids |
| matters | 4,159 (terminated 2,950; active 1,193; supporting_master 16); node_role public_docket 4,086 / target_matter 57 / support_master 16 | case_name, case_status, court_id (CL id), date_filed (1987-01-08..2026-08-04, none missing), date_terminated, docket_number, matter_key `court|docket` |
| matter_relationships | 53 (`member_of_mdl`) | from/to matter |
| matter_aliases | 4,202 | - |
| courts | 140 | court_id (CL), name |
| attorneys / firms / counsel_appearances / parties | 181 / 12 / 878 / 503 | firm_id e.g. `seeger_weiss`, `simmons_hanly_conroy`; appearance role (un-normalised: `LEAD ATTORNEY` vs `lead_attorney`, stray `"10"`) |
| opinions | 900 | CL cluster/opinion ids, date_filed, type |
| outcomes | 25 | `fjc_case_disposition` raw codes, evidence_level `official_dataset_reported` |
| docket_entries / documents | 41,946 / 13,971 | metadata, not filings |
| source_records / provenance / review_records | large | CourtListener docket URLs, catalog hashes |
| coverage | 8 | scope statements (seeger_weiss, competitor, mdl_member, fjc_linked, active, terminated; bankruptcy/appeal not available) |

Top courts: njd 523, ilnd 315, nysd 285, scd 255, moed 239, cand 213, paed 180, azd 103, ohnd 94, flmd 83,
jpml 77. 194 matters have an `-md-/-ml-/-mc-` docket number; 333 case names start "In re".
Top assigned judges (assigned_judge role only): Gergel 203, Cecchi 172, Rowland 157, Kennelly 100, Campbell 96,
Scheindlin 91, Martinotti 59, Marston 49, Hudspeth 44, Gonzalez Rogers 43, Polster 42, Norton 38.

Date semantics: `date_filed`/`date_terminated` are docket dates from CourtListener; release built 2026-08-24;
assignments carry no assignment date. Risks: selection is Seeger-Weiss/competitor/MDL-anchored, not a national
sample, so counts are "assignments observed in this dataset" with denominator 4,159 matters; `record_status:
active` is a registry flag, not judicial service; 17 judges have no native id (must stay unlinked); appearance
roles need normalisation; no outcomes beyond 25 FJC codes - no rates of any kind.

Smallest safe integration: a hash-gated supplement `judge_assignments_<date>` with (cl_person_id, judge name as
released, role, matter_key, case_name, court_id, date_filed, date_terminated, case_status, mdl parent via
matter_relationships). Surface on the People profile by exact `native_judge_id == people.id` (850 judges) as
"Matters in the saved Seeger docket dataset (N of 4,159; built 2026-08-24)". This also fixes the magistrate gap
(section 0.3) without any name merge. The 181 attorneys / 12 firms / 878 appearances are the only local seed for
the requested firm/attorney layer - small, but ID-clean.

## 3. Judge deliverables (13-14 Sept)

- `delivery/judge_intelligence_20260913` (snapshot `20260914T060412605837Z`): 7,736 observation reports
  (official 1,978; trellis_profile 1,300; trellis_directory 4,458), 15,171 official + 26,847 Trellis fact
  records, 1,520 dashboard/report link records, 0 verified numeric analytics, `judge_search.sqlite3` (24.5 MB).
  It is the base of `judge_enrichment_20260914`, which IS in the MVP (dataset `judge_enrichment` = 11,926 rows =
  1,978 + 1,300 + 4,458 + 116 state evaluations + 4,074 federal biographies). Net-new visible value is low;
  unused pieces: `state_coverage.csv` (coverage/gap table by state) and `dashboard_report_links.jsonl` (1,520
  Trellis report links - links to paid analytics, label as "publisher report link, not acquired").
- `delivery/judge_enrichment_20260914` (snapshot `20260914T060427974584Z`): 10,877 identity groups, 60,833 fact
  claims, 258 analysis records (116 commission performance evaluations, 114 commission votes, 28 survey ratings),
  1,654 verified originals, `judge_corpus.sqlite3` 343 MB. Judges UI reports only 118 profiles with
  `analysis_count > 0` and 1,605 with biography out of 10,698; 5,971 have details. NOT verified: whether all
  60,833 fact claims are rendered or only a subset.
- `delivery/judge_vendor_enrichment_20260914`: 2 observations (Sabraw Lexis Context preview: 449 measurements;
  Gilstrap Lex Machina: 1 publisher-reported count 2,276 patent cases 2023-2025). In MVP as `judge_vendor` (2).
  Nothing further to extract; both are patent/S.D. Cal. and not mass-tort relevant.

Conclusion: judge analysis is "poor" because the local evidence that is analysis-like (assignments, MDL
membership, panel counts, disclosures) is not joined to profiles, not because the 13-14 Sept packages are unused.

## 4. Trellis (`sources/trellis/catalog/catalog.sqlite3`, 122 MB, updated 2026-09-13T21:29Z)

Tables: `pages` 2,896 (all status 200; provider `Firecrawl basic/public`; fields url, category, jurisdiction,
title, content_sha256, markdown_path, observed_at, source_mtime), `links` 302,248 (source_url, url, category,
label), `counties` 1,433 (state, county_slug, fields_json, official_website, case_links, judge_links,
website_validation_status).

| Category | Discovered (distinct) | Downloaded | Not downloaded | In MVP |
|---|---|---|---|---|
| coverage_county | 2,510 | 1,433 (45 states + federal) | 1,077 (TX 135, VA 88, GA 84, MO 60, KS 55, IA 51, NC 51, IN 48, MN 46, OH 44...) | 1,433 as focused `coverage_county` |
| state_rule | 18,490 | 1,367 (19 states: PA, NV 114; WA, TX, RI 112; MA 79; NY, NJ, MD 78; CT 68; AZ 65; OR, MN, IL 64; DE 48; OH, GA, FL, CA 29) | 17,123 (RI 2,808; NJ 2,482; WA 2,054; NV 1,124; DE 1,109; TX 936; IL 904; NY 834; OH 809; MD 768; PA 748; GA 702) | all 1,367 by exact URL (951 navigation, 443 text fragments, 24 captured representations) |
| judge_profile | 11,099 | 0 in this catalog; 1,300 later via `judge_focus_20260913` | ~9,800 | 1,300 profiles + 4,590 directory-derived entities |
| judge_directory | 1,766 | 46 | 1,720 | 46 |
| filing | 938 | 0 | 938 | 0 |
| motion_dictionary | 34 | 1 | 33 | 0 |
| case | 95,884 | 0 | - | 0 (county pages show a non-exhaustive sample) |

County profile fields (fields_json): population 1,429; county seat 1,419; website 1,386; administration address
1,366; "meaning" 1,361; phone 1,276; form of government 207; board of supervisors 159. 1,421 counties have
case_links, 1,072 judge_links; 1,384 official website hrefs observed.
Date semantics: `observed_at` = Firecrawl capture time (2026-09-13); population has no as-of year; law text has
no effective date. Risks: provider-rendered representation (hash of provider JSON, not HTTP bytes); Trellis is a
third-party re-publisher, so state-rule bodies are secondary to the official codes already indexed in Open US Law;
the account covers CA and IL only. Missing-county counts may include URL variants (not verified).
Smallest safe integration: none needed for downloaded data. For further scraping, the 1,077 county URLs are the
bounded, highest-value Trellis packet (11 packets of <= 100); the 17,123 rule URLs are low priority because
official sources exist; judge profiles only for named MDL judges via the Trellis MCP connector.

## 5. Returned page inventory vs the 9,348-reference source directory

Inputs: `sources/local_deep_audit_20260918/returned_page_inventory.json` (14,047 files, 13,644 distinct
source_url; fields path, source_url, title, source_sha256, text_sha256, markdown_chars, status_code, host) and
`sources/public_law_directory_20260919/catalog.json` (9,348 entries).

- Exact URL overlap: 19. Normalised (lowercase host, strip www, trailing slash): 39.
  By directory category: uncategorized 6, court_rules 5, regulations_register 3, court_forms 2, statutes_codes 2,
  agency_guidance 1. Hosts: leg.state.nv.us 5, pacourts.us 4, courts.phila.gov 3, njcourts.gov 3, mca.legmt.gov 2,
  justice.gov 1, kycourts.gov 1. 17 of 19 have HTTP 200 and >= 1,500 markdown chars.
- Returned URLs already in MVP `browse` by exact URL: 63.
- Status: 200 x 14,023; 404 x 12; 403 x 11. 12,845 files are 200 with >= 1,500 chars (soft-404 review not done).
- Hosts: justice.gov 9,852 (osg/brief 3,825; atr/case-document 1,706; atr/case 1,200; archives/jm 589;
  archives/usam 454; archives/oip 452; only 2 `/jmd/ls` pages, both Illinois); codes.findlaw.com 1,006 (MN, MI,
  WI code chapters - third-party re-publisher); courts.phila.gov 602; mca.legmt.gov 500; dccourts.gov 496;
  leg.state.nv.us 456; pacourts.us 395; alleghenycourts.us 199; montgomerycountypa.gov 198 (mostly non-court
  departments); oscn.net 198 (148 case-information pages - case data, keep out of the law library); njcourts 88.

Other unused returnedfiles assets measured in this run:
- `_pdf_directory/url_directory.jsonl`: 96,648 unique URLs (pdf 14,762; html 79,110; txt 2,215; xml 121; docx 70;
  wpd 38; xls 37); fields url, kind, domain, label, refs, found_on_count. Exact overlap with the 9,348 directory:
  190. Contains 1,053 uscourts.gov statistics/data-table URLs and 591 fda.gov URLs. Top domains: justice.gov
  52,920; congress.gov 4,301; uscourts.gov 2,735; federalregister.gov 2,524; dccourts 2,237; kycourts 2,232;
  pacourts 1,942; nebraskajudicial 1,827; njcourts 1,333; courts.phila 1,269; flsd.uscourts 1,210.
- `_normalized/records.jsonl`: 60,456 classified records (42,670 unique URLs; built 2026-08-22) with `page_type`
  (forms 4,633; court_statistics 2,736; opinion_document 2,291; legislation 2,152; judge_directory 1,256;
  administrative_order 1,223; county_court_site 1,059; county_page 872; court_calendar 775; judge_profile 739;
  rules 653; efiling 251), `state` (NJ 12,342; IL 3,883; TX 3,866; KY 3,377; PA 2,389...), `access_model`.
  Mostly map/crawl-log URLs (55,280), only 2,021 `page` records with content.
- `2026-Indiana-Code`: 77 files, 681 MB (40 PDF + 37 HTML title files, official 2026 Indiana Code). NOT verified
  whether Open US Law already covers IN statutes at the same edition.
- `mdoutputs` 125 files 92 MB markdown; `illinoiscourts_highvalue` 7 parts 49 MB; `illinois_county_circuits` 13
  circuit markdown dumps 27 MB (1st, 2nd, 4th, 5th, 6th, 9th, 10th, 13th, 15th, 16th, 17th, 19th Lake, Cook) -
  concatenated crawl dumps: county/circuit local rules and forms for Illinois, need splitting by page URL before
  use. `kentucky_county_snapshots` 120 JSON (already behind the county registry). `ARKcodelaw` 1,006 JSON is
  actually findlaw MN/MI/WI (folder names do not establish jurisdiction). `OKcodelaw` 200 = OSCN.
- `settlementsverdicts/` (built 2026-08-22): `verdict_lead_index.json` 3,312 results from 289 published lists, 670
  mass-tort tagged; CSVs: records, mass_tort_leads, firm_leaderboard, jurisdiction_rollup, coverage_gap_states.
  RESTRICTED: its own report states amounts are attorney self-reported, top-N truncated, and the publisher
  prohibits reuse/redistribution. Internal lead list only; do not publish in the MVP or platform; never use as
  base rates. If used at all: a private "leads to verify against dockets" queue.

## 6. Court logos / assets (295 images)

Paths: `sources/local_asset_discovery_20260918/` (`image_files.jsonl` 295 files, 21.5 MB: png 211, ico 29, svg
23, webp 19, gif 8, jpeg 4, bmp 1; `court_links.jsonl` 269 court entries; `asset_associations.jsonl` 493).
Kinds: court_seal 118, judiciary_logo 106, court_logo 29, favicon 226, judge_photo 14 (association counts).
Court entries: FD 94, FB 94, ST 56, F 13, FS 6, LC 6. With primary image: 238 (court_mark 228, favicon_only 10,
text_fallback 31). Identity scope: federal_court_site_mark 139, shared_federal_judiciary_mark 48,
statewide_judiciary_mark 37, site_icon 10, local_court_site_mark 2. Retrieved 2026-09-12. permission_status
`not_established` for all images.

Mapping measured in this run (entry id suffix vs CourtListener `courts.id`): F 13/13, FD 94/94, FB 93/94
(`azb` absent), FS 6/6 -> 206/207 exact. ST (`nj_state`...) and LC (`pa_philadelphia`...) have no CL id and need
a small explicit crosswalk (56 + 6 rows; LC rows map to county FIPS: Alameda, Los Angeles, San Francisco, St.
Louis, New York, Philadelphia).

MVP state: `local_library_presentation_20260918` lists 269 court-asset records but `assets.json` allowlists only
4 images (2 png, 1 gif, 1 svg) + 28 PDFs + 24 texts; the listed court-asset records have `asset_id: null`.
Smallest safe integration: content-addressed copy of the 238 primary raster marks into a supplement with an
allowlisted asset id per CL court id; show only on that exact court (never propagate a statewide mark to county
courts; 48 entries use the shared federal judiciary mark - label as shared); SVG (23) stays excluded or
sanitised; keep `permission_status: not_established` visible. Same table feeds devvvv `reference.courts.logo_key`
/ `logo_kind` / `logo_background` / `fallback_text` (fields already match 1:1).

## 7. Illinois regulation candidates

Evidence: `sources/local_deep_audit_20260918/counties/illinois_overlap.json`; data in
`C:/Users/firas/Downloads/Illinois/administrative-code/...` (53,660 clean texts fetched 2026-08-15 06:40-09:25;
3,472 act texts). 52,041 match the Open US Law index by official JCAR section-code basename; 1,619 do not.
Measured split of the 1,619: appendix 602, illustration 518, table 274, exhibit 144, plain section 81. By title:
077 Public Health 398, 035 Environmental Protection 260, 050 Insurance 182, 092 Transportation 155, 002 95, 023
67, 014 59, 001 56, 032 Energy 53, 089 Social Services 48, 080 47. First 200 clean paths all exist; median 919
bytes; none under 300 bytes.
Fields: title_id, section_code, section_number, section_title (HTML entities un-decoded, e.g. `&#x27;`), url
(ilga.gov JCAR), fetched_at, clean_path. Date semantics: fetched_at only; no effective date; hashes are
LF-normalised (CRLF on disk differs). Risks: raw HTML missing, 199 manifest paths absent, candidates are not
proven gaps. Smallest safe integration: supplement of the 1,619 as "qualified derivative, capture 2026-08-15,
official URL, no original bytes", prioritising Titles 77 and 35 (exposure tables/appendices matter in toxic-tort
work); decode entities; link each to its parent Part in the bulk index by the first 8 characters of section_code.
Also unused: eFileIL standards v6.0 (463 filing codes) and the 170-row June 2026 monthly court activity workbook
(5 counties) - the only local court-statistics data (prior audit).

## 8. Catalog records not reachable in the MVP

`catalog/documents.sqlite3`: 18,844 records / 19,008 versions / 18,052 unique texts (1.40 G chars); retrieved_at
2026-09-13..14; `retrieval_time_basis` = source_reported 16,059, provider_capture_file_mtime 2,894,
browser_dom_captured_at 51. `content_type` is blank on 11,380 versions (file-type facet gap).
2,380 records have a source_url absent from MVP `browse`: corpus/official_courts 1,792; official_courts 489;
trellis_public 48; OCR 48; trellis_browser 3. Categories: docket_or_case_access 514; court_or_county_directory
503; judge_profile_or_directory 394; document 247; court_rules 134; court_directory 128;
court_directory_or_case_access 114; doj_state_court_index 56; case_access 55; state_judiciary_portal 54;
judge_directory 42; judicial_directory_download 13. For `official_courts*` (2,471 total) 2,329 are absent by
both source_url and final_url: WV 385, IL 189, CO 164, IN 103, OH 101, UT 74, IA 69, AK 68, AZ 60, NE 59, DE 59,
HI 57, WA 49, ID 46, MT 44, WI 43. Samples: illinoiscourts.gov county courthouse pages, coloradojudicial.gov
county trial-court pages, courtswv.gov circuit-judge profiles, txcourts.gov district/county clerks PDF.
NOT verified: whether the focused publication excluded these deliberately (case-search pages should stay out;
514 + 55 + 114 are case-access pages). Smallest safe integration: review the ~1,200 directory/judge/rules
records, publish through the existing pending-publication path with explicit state and, where the page itself
names the county, county FIPS. The 56 `doj_state_court_index` records relate to the user's justice.gov/jmd/ls
request.

## 9. Seeger staging (`C:/Users/firas/Downloads/Seeger-Corpus-Enrichment-2026-09-13/staging`)

Already imported: 11,181 court originals (pdf 9,480; docx 1,319; doc 379; rtf 3; 3.48 GB), 13 reference
originals, 7,166 provisions (NJ statutory 5,856; FDA regulatory 233; primary law 1,077), 848 settlement feed
records, 295 assets. MVP kinds: court_form_or_other_document 10,543; statutory_provision 6,695;
court_rule_or_order 635; rule_provision 238; regulatory_provision 233; reference_original 13; administrative 3.
Unused metadata on every court document (measured over 11,178 payloads): `source_courts` 100%;
`source_collections` prefixes ST 4,097, FD 3,295, FB 2,896, F 356, FS 356, STATE-IL 248, BANKRUPTCY-CA-Central
205, STATE-PA 188, LC 177 (pa_philadelphia 121, ca_los_angeles 31, ca_alameda 10, ca_san_francisco 7, la_orleans
5, ny_new_york 2, mo_st_louis 1), NAT 78; `source_date` only 16; `county_territorial_assignment_verified`,
`retrieval_eligible`, `review_status`, `kind_basis` present. MVP `state` filled on 10,342 of 18,360; `county`
on 0.
Smallest safe integration (no network): a relabel supplement that (a) maps each document to a CL court id via
`source_collections` (FD/FB/F/FS exact; ST -> state judiciary; LC -> county FIPS), (b) splits the 10,543-row kind
into form / standing order / local rule / instruction / order / fee schedule / other using title + existing
`kind_basis` (the devvvv `reference.court_documents.kind` enum is exactly
standing_order|local_rule|form|instruction|order|other), (c) records `source_date_kind: unknown` explicitly.
Not data: `10-Agent-Skills-Library` (150 skills), `11-Platform-Corpus` (agent specs, 84 synthetic scenarios) -
keep out of the legal corpus; `11-Platform-Corpus/integration/GAPS.md` G03 is a ready-made requirement list for
the reference evidence contract (source id, version hash, publisher, URL, jurisdiction/court, offsets,
publication/revision/effective dates, fetched time, rights status, language, currentness flags).

## 10. `devvvv/` (external platform snapshot)

TanStack Start + TypeScript app connected to Lovable (`AGENTS.md` warns against rewriting pushed history), AWS
(Aurora pgvector KB, S3, Dynamo, Bedrock, Lambda). No legal corpus data inside (only `samples/ingest/golden`
fixture and UI mockups). Do not modify. Reusable integration contracts:
- `docs/ingest-contract-v1.md` + `schemas/ingest-manifest-v1.json` + `schemas/ingest-docket-v1.csv-spec.md`:
  matter bundle (manifest.json, docket.csv, parties.csv, PDFs); identity `(matter_id, docket_source,
  entry_number, attachment_number)`; availability enum free_pdf/locally_supplied/pacer_link/text_only/sealed;
  sha256 + page_count verified at commit; `scripts/pipeline/validate_bundle.py` local pre-flight. This fits
  MDL-3080 (1,612 PDFs) and SW-BULK docket data, not reference law.
- `db/kb/0003_reference_courts.sql`: `reference.courts` (court_key, court_id = DocketBird/CourtListener id, name,
  level, jurisdiction, website, forms_pages[], logo_key, logo_kind, logo_background, compact_key, fallback_text,
  reuse_note, document_count), `reference.judges` (judge_key, court_key, name, surname, portrait_key,
  source_page, reuse_note), `reference.court_documents` (court_key, court_keys[], jurisdiction, title, kind,
  format pdf|docx|doc|rtf, bytes, page_count, source_url, source_date, source_date_kind, review_status, fillable,
  judge_name); also adds `assigned_judge`/`referred_judge` to `corpus.dockets`.
- `src/lib/courts.ts`: court ids follow the CourtListener convention (`njd`, `cand`, `paed`, `jpml`).
- There is no contract yet for statutes/regulations/settlements/judge analysis/source directory; GAPS.md G03
  describes what it must contain.
`.env.example` and credential-like files were not opened.

## 11. Other

- `delivery/ui-sketch/data.js` (8.3 MB): wireframe data built from `delivery/focused_legal_corpus` (inputs
  official_resources.jsonl, trellis_law_captures.jsonl, counties.jsonl, judges/sources.jsonl). Superseded by the
  archive-directory `focused` dataset; nothing new.
- SCRAPE root: 8 Open-US-Law parquet downloads (AK court rules x2, CA guidance, CA statutes, FL constitutions,
  FL court rules, FL statutes x2; two are duplicate "(1)" copies) dated 2026-09-18 19:22-22:34. NOT verified
  against the 2,978,617-row index; `us_ca_guidance.parquet` suggests a "guidance" kind worth checking.
- Prior-audit items not re-measured: LAWONTOLOGY graph (120,464 nodes / 169,399 edges / 21,357 page texts,
  MDL-3080), MATTER-ETL CSVs (436,005 docket metadata rows), MD-DONE Talc MDL 2738 (25 PDFs), source registries
  v2.2 (4,846) and v03 (6,262), 1,230 photo flags + 29 PA portrait references.

## 12. Recommended ID spine (for relationship mapping)

`cl_court_id` (courts 3,361) <- court logos (206 exact) <- Seeger documents (FD/FB/F/FS collections) <- People
positions.court_id <- SW-BULK matters.court_id <- devvvv reference.courts.court_id.
`cl_person_id` (people 16,191) <- SW-BULK judges.native_judge_id (850) <- financial disclosures (3,392) <- opinion
panels (3,285) <- political affiliations (7,226). Judges UI entities (FJC nid / Trellis / official) have NO
CourtListener id today (0 explicit candidates in the prior audit); a reviewed bridge table is required before
these layers appear on the same profile - until then show them on the People profile only.
County FIPS <- county registry (374) <- Trellis county profiles (1,433 by state+slug, already matched 1,421) <-
LC collections (7) <- catalog official_courts county pages (needs page-level evidence).

## 13. Not verified

- Row counts of citations and originating-court-information (header only).
- Whether every judge_enrichment fact claim is rendered in the Judges UI.
- Whether the 2,329 official_courts records were excluded from the publication on purpose; no content review.
- Soft-404/shell quality of returned pages beyond status + length.
- Trellis discovered-URL variants (duplicates by trailing slash/case) inside the 1,077 / 17,123 counts.
- Indiana Code 2026 and root parquet files vs the Open US Law index.
- Name-token presence check for MDL judges is not an identity match; absentees were not individually confirmed
  as magistrates.
- ST/LC logo crosswalks; image reuse permissions (all `not_established`).
- `C:/Users/firas/Downloads/litigation_source_browser.html` was not opened by this agent.
