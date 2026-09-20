# cl_bulk — CourtListener bulk tables + `_normalized` scraped-page set

Scope: `C:/Users/firas/Downloads/returnedfiles/bulk` (CourtListener Postgres CSV bulk export) and
`C:/Users/firas/Downloads/returnedfiles/_normalized` (a Firecrawl-derived normalized-page dataset). Read-only
survey; nothing under `returnedfiles/` was modified. All row counts below were measured in this run by
streaming the `.csv.bz2` files with Python's `csv` module (`escapechar="\\"`, `doublequote=False`) unless
marked "sampled" or "prior survey, not re-verified here". This extends and corrects
`reports/corpus_upgrade_20260919/understand/local_inventory.md` §1 (CL bulk) and the `_normalized` note in its
§5; that report is the prior partial survey and is not repeated here except where corrected.

## 0. Snapshot identity and how to read this data

- `returnedfiles/bulk`: 27 files, 201.6 MB on disk (25 `.csv.bz2` + `schema-2026-06-30.sql` +
  `load-bulk-data-2026-06-30.sh`). Filenames carry snapshot label `2026-06-30`; one sampled `citations` row has
  `date_created 2025-10-25`, so the true CourtListener export date is not independently confirmed — treat
  `2026-06-30` as the filename label, not a verified export date.
- `load-bulk-data-2026-06-30.sh` and `schema-2026-06-30.sql` are the CourtListener bulk-data loader and its
  **full application schema** (people/positions/disclosures/search/recap/audio — 90+ `CREATE TABLE` statements),
  not a description of what's actually shipped here. Only 25 of those tables have a matching `.csv.bz2` file;
  the rest (see §3) are schema-only with **zero local rows**.
- CSV dialect is Postgres COPY-style: backslash-escaped, `doublequote=False`. Python's default `csv.reader`
  mis-splits multiline/embedded-comma fields on this data — every count below used the correct dialect.
- No README/manifest sits next to `bulk/` beyond the schema SQL and loader script; no licence file. CourtListener
  bulk data is published under CourtListener's own terms (not fetched here — flag for a licence check before any
  redistribution to the external platform).

## 1. `returnedfiles/bulk` — table-by-table (measured this run)

| Table (file) | Rows measured | Cols | Already in MVP? | Key fields | Notes |
|---|---|---|---|---|---|
| `people-db-people` | 16,191 | 26 | Yes — `sources/courtlistener_people_20260918/catalog.sqlite3`, People UI (15,797 + 394 aliases) | id, name_first/middle/last/suffix, fjc_id, dob/dod+granularity, has_photo, is_alias_of_id | 3,711 rows have `fjc_id` non-blank |
| `people-db-positions` | 51,291 | 38 | Yes (role/court/org/dates shown) | 38 cols incl. how_selected, termination_reason, appointer_id, votes_yes, sector | Same as prior survey; not re-diffed here |
| `people-db-educations` | 12,777 (7,398 distinct person_id) | 8 | Yes | school_id, degree_level/detail/year | matches prior survey exactly |
| `people-db-schools` | 6,011 | 6 | Yes (join only, not surfaced alone) | name, ein | |
| `people-db-political-affiliations` | 8,486 (7,226 distinct person_id) | 10 | **Yes — correction to prior survey.** `sources/judge_structured_20260919/build.py:199-214` joins `political_affiliations` into the judge overlay and `delivery/archive-directory/areas.js:538` renders it on judge profiles with the caption "As recorded by CourtListener with its stated source and dates; not a finding about the judge." It also feeds a `cl_political_affiliation` scoring weight (+5) in `judge_structured`'s evidence score. | political_party, source (a=appointer/b=ballot/o=other), date_start/end+granularity | Prior survey (local_inventory.md line 68) said "Imported, NOT shown anywhere" — that was true before `judge_structured_20260919` was built; it is now live. Worth re-verifying the caption text is not stale. |
| `people-db-races` | 6,542 (6,521 distinct person_id) + `people_db_race` 8-row lookup | 3 / 2 | No | person_id, race_id | Sensitive demographic attribute — do not surface (per prior survey and BRIEF's contact-detail caution extends naturally to demographic fields) |
| `people-db-retention-events` | 0 (header only, 12 cols) | 12 | N/A | — | Confirmed empty |
| `courts` | 3,361 (3,361 distinct `id`) | 20 | Yes — 100% of these ids already loaded into `sources/court_spine_20260919/courts.jsonl` as `id_kind="courtlistener"` (verified by exact set match this run: 3,361 bulk ids == 3,361 spine `cl_court_id` values, 0 missing either direction) | id, pacer_court_id, fjc_court_id, citation_string, short/full name, url, start/end date, jurisdiction, parent_court_id | Jurisdiction breakdown (measured): ST 2,618, F 127, FD 125, SA 111, SS 86, FB 95, FS 42, S 55, SAG 16, TRA 18, MA 11, TRT 14, TRS 6, TT 6, I 3, TRX 4, T 2, TA 2, C 5, TS 5, St 1, blank 1 |
| `courthouses` | 3,361 (3,286 with non-blank `court_id`, all of which resolve into `court_spine`'s 3,361 `courtlistener`-kind rows) | 11 | No | id, court_seat, building_name, address1, address2, city, county, state, zip_code, country_code, court_id | **G6 measured: address completeness is near-zero.** Of 3,361 rows: `address1` non-blank 4, `city` non-blank 9, `county` non-blank 1, `building_name` non-blank 3, `court_seat=true` 6, `address2` non-blank 0. Only the 4 rows with `address1` actually join a court_spine court to a street address. This table is a per-court state/id stub, **not** a courthouse directory — matches and reconfirms the prior survey's characterization. G6 (courthouse street addresses across 5,413 courts) is **not fillable from this file**; another source is needed. |
| `court-appeals-to` | 8 | 3 | No | from_court_id, to_court_id | Tiny appeal-routing edge list |
| `search_opinioncluster_panel` | 835,148 (3,285 distinct person_id) | 3 | No | opinioncluster_id, person_id | Needs opinion-cluster metadata (not shipped locally) to be meaningful |
| `search_opinion_joined_by` | 1,028 (285 distinct person_id) | 3 | No | — | Minor |
| `search_opinioncluster_non_participating_judges` | 0 (header only, 3 cols) | 3 | N/A | — | Confirmed empty |
| `financial-disclosures` | 32,336 (3,392 distinct person_id) | 16 | No | year, report_type, is_amended, page_count, sha1, filepath (CourtListener S3 PDF path), person_id | Parent record only; filepath points at CourtListener's own S3, not a local file — no original PDF is present locally |
| `financial-disclosure-investments` | 1,901,720 (sampled at 500k-row checkpoints, ran to completion in 17.5s — full count, not a sample) | 18 | No | description, income/gross-value codes, transaction_date, transaction_partner, financial_disclosure_id | By far the largest sub-table; issuer/transaction-partner text is useful for MDL-defendant recusal/conflict research per prior survey |
| `financial-disclosures-agreements` | 10,007 | 7 | No | | |
| `financial-disclosures-debts` | 18,775 | 8 | No | | |
| `financial-disclosures-gifts` | 2,025 | 8 | No | | |
| `financial-disclosures-non-investment-income` | 15,302 | 8 | No | | |
| `financial-disclosures-positions` | 37,050 | 7 | No | | (outside-position disclosures, distinct from `people-db-positions`) |
| `financial-disclosures-reimbursements` | 33,472 | 10 | No | | |
| `financial-disclosures-spousal-income` | 20,174 | 7 | No | | |
| `originating-court-information` | 973,419 (full count, ran to completion in 9.9s) | 16 | No | docket_number, assigned_to_str/id, ordering_judge_str/id, date_filed/disposed/judgment, date_received_coa | Appellate-origin-court linkage; sample row had almost all fields blank — sparse table, blank-rate not further profiled |
| `citations` | **sampled**: streamed 12,000,000 rows in 50.7s and hit the 55s time cap without reaching EOF; true row count is materially higher and was not measured. Header/sample only. | 8 | No | volume, reporter, page, type, cluster_id, date_created/modified | `date_created` on the sampled row is `2025-10-25`, the only concrete evidence in this dataset that the export postdates the `2026-06-30` filename label |

Grep of `sources/` and `delivery/` for these table/file names (this run) confirms only `people`, `positions`,
`educations`, `schools`, `courts` (via `court_spine_20260919`), and — newly — `political_affiliations` are
wired into the live app. `courthouses`, `court-appeals-to`, `races`, `retention-events`, all `financial-*`
sub-tables, `originating-court-information`, `search_opinioncluster_panel`, `search_opinion_joined_by`, and
`citations` have **zero** references outside their own `bulk/` directory: confirmed unused.

## 2. Tables named in the schema SQL but with NO local data (schema-only, 0 rows available)

Checked every `CREATE TABLE public.*` in `schema-2026-06-30.sql` (90+ tables: `audio_*`, `disclosures_*`,
`people_db_*`, `recap_*`, `search_*`) against the 25 `.csv.bz2` files actually present. Tables the task/BRIEF
gaps call out that have **no matching CSV**, i.e. cannot be backfilled from this directory at all:
- `people_db_abarating` / `people_db_abaratingevent` — **ABA ratings: no CSV, confirmed** (matches prior survey).
- `people_db_source` / `people_db_sourceevent` — the CourtListener "sources" table (evidentiary source per
  person record) — no CSV.
- `people_db_attorney`, `people_db_attorneyorganization`, `people_db_attorneyorganizationassociation`,
  `people_db_party`, `people_db_partytype` — attorney/firm/party tables relevant to G1/G2 — **schema exists,
  zero rows shipped**. This bulk export cannot fill G1 (counsel/firms) or G2 (parties); that has to come from
  the CourtListener connector (as `mdl_counsel_20260919` already attempts) or SW-BULK, not this directory.
- `recap_fjcintegrateddatabase` — the FJC Integrated Database table (G10, federal court statistics) — **schema
  exists, zero rows shipped.** The MVP's `federal_court_statistics` layer (92 tables, 6,329 CJRA rows per
  STATE.md) must come from a different source; it is not derivable from this bulk snapshot.
- `search_parenthetical` / `search_parentheticalgroup` — no CSV (parentheticals/citation summaries not shipped).
- `search_docket*`, `search_opinion*` (full docket/opinion text tables), `recap_pacer*`, `recap_rss*`,
  `audio_*` — none shipped; only the two tiny join tables (`search_opinioncluster_panel`,
  `search_opinion_joined_by`) and `citations` (a citation index, not full-text opinions) are present. **This
  directory is not a source for G11 case-law/opinions** — it never claims to be; no FindLaw content is
  anywhere in `bulk/`.

## 3. G6 courthouse join to `court_spine_20260919` (measured this run)

- `court_spine_20260919/courts.jsonl`: 5,413 rows total — `id_kind` breakdown: `courtlistener` 3,361,
  `county_registry` 1,996, `local_registry` 56.
- All 3,361 `courtlistener`-kind spine rows have a `cl_court_id` that exactly matches a `courts-2026-06-30.csv`
  `id` (bidirectional set equality: 0 unmatched either way).
- `courthouses-2026-06-30.csv` has 3,286 rows with a non-blank `court_id`; all 3,286 join to spine
  `cl_court_id` (100% of the non-blank ones). But **only 4 of those 3,286 carry a street address**
  (`address1` non-blank) — so the join key is clean but the payload is empty. `courthouses` cannot fill G6 for
  the 5,413 courts; it can theoretically fill it for at most 4.
- The 1,996 `county_registry` spine rows are the only ones with non-empty `locations` (measured: exactly 1,996
  non-empty `locations` fields, matching row-for-row) — that data comes from a different pipeline
  (county registry, not CL bulk) and was already counted by the court_spine builder, not re-verified here.

## 4. Four unresolved MDL judges — checked against `people-db-people` (measured this run)

Per STATE.md, `judge_aliases_20260919` left Wolson, Bailey, Shelby, Singhal unresolved. Checked `name_last`
substring match (case-insensitive) against all 16,191 `people-db-people` rows:

| Name | Matches in people-db-people | fjc_id present? | Assessment |
|---|---|---|---|
| Wolson | 1 exact: id 8652, "Joshua David Wolson", dob 1974-01-01 | **Yes — `fjc_id 6385006`** | Only one candidate, so name collision risk is low, but `6385006` is a 7-digit value while every other sampled `fjc_id` in this file is a small legacy integer (e.g. 76, 2170, 3141, 3444) — inconsistent format. **Do not treat this as a verified FJC bridge without checking the FJC nid convention first**; it looks more like it could be a CourtListener person id miscoded into the `fjc_id` column than a genuine legacy FJC id. Flag as a data-quality risk to verify before using it as alias-resolution evidence. |
| Bailey | 17 distinct people named "...Bailey" | 2 of 17 have `fjc_id` (John Preston Bailey id 148 fjc_id 3141; Thomas Jennings Bailey id 149 fjc_id 76, d. 1963 — a historical judge, clearly not an MDL match) | **Cannot resolve by name alone** — 17 candidates, no first name given in the gap description to disambiguate; several are 19th/20th-century deceased judges. This table alone does not resolve the Bailey gap; would need the JPML docket's judge first name to narrow it. |
| Shelby | 2 distinct: David Davie Shelby (fjc_id 2170, 1847-1914, clearly historical, 5th Cir. era) and Robert James Shelby (fjc_id 3444, dob 1970-01-01) | Both have `fjc_id` | Robert James Shelby (b. 1970) is the plausible living-judge candidate (matches the public record of a sitting U.S. District Judge named Robert J. Shelby) but this was not cross-checked against any MDL docket assignment in this run — flag as a lead, not a resolved bridge. |
| Singhal | 1: "Anuraang H. Singhal", no `fjc_id` | No | Spelling risk: the commonly known S.D. Fla. district judge is usually spelled "Anuraag Singhal" (one fewer "a"). Per BRIEF's "never merge people by name alone" rule, this is a **candidate with a spelling mismatch and no fjc_id to bridge on** — do not auto-merge; would need independent confirmation (e.g. CourtListener API lookup by docket-assigned judge string) before treating this as the same person. |

None of these four should be auto-merged from this evidence alone; all four need either a first-name-qualified
JPML docket cross-check or a CourtListener/FJC id lookup that this local file does not provide with certainty.

## 5. `returnedfiles/_normalized` (measured this run + read `coverage_report.json` in full)

4 files, 45.6 MB: `records.jsonl` (38.3 MB), `links.jsonl` (7.3 MB), `coverage_report.json` (4.4 KB, a build
manifest — read in full), `unclassified.jsonl` (0 bytes, empty).

`coverage_report.json` (generated_at 2026-08-22T08:50:15Z; `input_dir` = the whole `returnedfiles` tree; 2,418
files read; 8,321 Firecrawl credits used) states, authoritatively:
- `records_emitted` 60,456; `unique_urls` 42,670; `links_emitted` 22,108; `unclassified` 0.
- `by_record_type`: `map_url` 40,897 + `crawl_log_url` 14,383 (these two = 55,280 are crawl-map/log rows with no
  page content — matches prior survey's "mostly map/crawl-log URLs"), `search_result` 2,106, `page` 2,021 (the
  only rows with real extracted content), `county_record` 614, `judge_roster_row` 363, `binary_blob` 34,
  `links_summary` 14, `answer` 9, `extract` 7, `batch` 6, `job` 2.
- `by_state` top: US 19,356 (federal/multi-state), NJ 12,342, IL 3,883, TX 3,866, KY 3,377, PA 2,389, NE 1,990,
  CA 1,958, IA 1,708, DC 1,484, SD 1,230.
- `by_page_type` (exact match to prior survey's numbers, now with full list from the manifest itself rather than
  re-derived): `other_page` 20,060, `document` 8,293, `forms` 4,633, `news_press` 4,434, `court_statistics`
  2,736, `opinion_document` 2,291, `legislation` 2,152, `opinions_index` 1,575, `judge_directory` 1,256,
  `administrative_order` 1,223, `county_court_site` 1,059, `county_page` 872, `court_calendar` 775,
  `judicial_conduct` 764, `judge_profile` 739, `rules` 653, `attorney_discipline` 644, `third_party_asset` 613,
  `court_improvement` 602, `jury_info` 490, `legal_education` 469, `statute` 406, `probation_services` 385,
  `self_help` 370, `judge_roster` 363, `api_endpoint` 304, `medical_source` 257, `efiling` 251,
  `interpreter_services` 230, `court_records_access` 203 (list truncated in the manifest itself; other smaller
  categories exist but were not enumerated by the source file).
- `by_host` top: `www.njcourts.gov` 6,739, `www.uscourts.gov` 5,381, `www.congress.gov` 4,338,
  `www.illinoiscourts.gov` 3,867, `library.njcourts.gov` 2,747, `www.kycourts.gov` 2,632,
  `www.federalregister.gov` 2,509, `www.flsd.uscourts.gov` 2,406, `www.txcourts.gov` 2,292.

Record schema (`records.jsonl`, sampled first record and header keys — full file streamed for row count only,
not fully parsed per-record for this report): `url, host, state, page_type, page_detail, title, access_model,
record_type, source_file, content_sha256, parsed_ok, data, provenance`. `provenance` carries Firecrawl-specific
fields: `mode`, `scrape_id`, `status_code`, `content_type`, `credits_used`, `proxy_used`, `throttled`, `warning`,
`fresh_fetch`, `ingested_at` (capture timestamp, 2026-08-22 — **this is a capture/build date, not a legal
effective date**, per BRIEF rules). The sampled `page` record's `data` block for an opinion document extracted
structured fields (court, case name, docket numbers, judges/panel, filed/issued dates) via LLM-style extraction
— useful shape for `opinion_document`/`judge_roster_row` types but **`parsed_ok` and extraction confidence were
not audited across the full 60,456 rows in this run**; only the shown sample was inspected.

Confirms prior survey: only ~2,021 `page` rows carry real content; the rest are crawl telemetry. This file is
**not currently referenced anywhere in `sources/` or `delivery/`** (grep of both trees for `_normalized`,
`records.jsonl` found no hits outside `returnedfiles` itself) — fully unused today.

## Gap mapping

| Gap | Filled by this cluster? | Which data | Join key | Effort |
|---|---|---|---|---|
| G1 counsel/firms | **No** | `people_db_attorney*`/`people_db_party*` are schema-only, 0 rows | — | — |
| G2 parties | **No** | `people_db_party`/`people_db_partytype` schema-only, 0 rows | — | — |
| G3 settlements/verdicts w/ provenance | **No** | not present in this cluster | — | — |
| G4 four unresolved judges | **Partial lead only** | `people-db-people` name search (§4) | `name_last` substring, `fjc_id` where present | S (to formalize as a documented candidate list, not a resolution) |
| G5 state coordinated-proceeding judges | **No** | not present | — | — |
| G6 courthouse addresses/contact | **No — measured and ruled out.** `courthouses` table joins cleanly (3,286/3,361 by court_id) but only 4 rows have a street address | `court_id` == `courts.id` == `court_spine.cl_court_id` | — |
| G7 county-level courts/clerks/forms | **No** | not present in this cluster | — | — |
| G8 state statute/reg gaps | **No** | not present | — | — |
| G9 state/federal agencies | **No** | not present | — | — |
| G10 federal court statistics | **No** | `recap_fjcintegrateddatabase` schema-only, 0 rows | — | — |
| G11 case law/opinions | **No, and not attempted** | only `citations` (index, sampled, no full text) and two opinion-cluster join tables | `cluster_id` | — |
| G12 SEC | **No** | not present | — | — |
| G13 canonical id graph | **Yes, already done** | `courts` == `court_spine.cl_court_id` (100% join, confirmed this run); `people.id`/`fjc_id` already the spine for judge identity | `cl_court_id`, `cl_person_id`, `fjc_id` (with the Wolson caveat in §4) | — (already integrated) |
| G14 source/URL frontier | **Partially, already known** | `_normalized/records.jsonl` `map_url`/`crawl_log_url` rows (55,280) are themselves a URL frontier, distinct from `_pdf_directory/url_directory.jsonl` covered by the prior survey | url | S — filtering/dedup against the 9,348-entry directory not done here |

Two additional build-effort notes not in the gap list but supported by this cluster:
- **Financial disclosures as a recusal/conflict-of-interest layer** (32,336 disclosure headers + 1,901,720
  investment-transaction rows, joined by `person_id` == `cl_person_id`): Effort **M** — needs per-judge
  aggregation (issuer/transaction-partner text is free-form, not a clean ticker/company table) and a UI surface
  that does not exist today; no PII beyond what CourtListener already published (these are federally mandated
  public disclosures, not private individuals' contact data).
- **`political_affiliations` is already live** (§1) — no further build needed; only a documentation fix (the
  prior survey's "not shown anywhere" note is now stale).

## What was NOT measured / verified

- `citations-2026-06-30.csv.bz2` full row count (sampled to 12,000,000 rows / 50.7s, did not reach EOF within
  the time cap — the true count is higher and unknown).
- Per-row null/blank-rate profiling of `originating-court-information` beyond one sampled row (it looked very
  sparse but this is not a measured percentage).
- Whether `financial-disclosures.filepath` (CourtListener S3 paths) resolves to anything fetchable, or whether
  any of those PDFs exist elsewhere in this project's other folders (SW-BULK, Seeger-Corpus-Enrichment) — not
  checked, out of this cluster's paths.
- Full-file audit of `_normalized/records.jsonl` `parsed_ok`/extraction-quality across all 60,456 rows (only
  the manifest counts and one sample record were inspected).
- Robert James Shelby / Anuraang Singhal / any Bailey candidate against an actual MDL docket judge-assignment
  record — this report only searched `people-db-people` by surname, it did not cross-reference JPML dockets,
  which live outside this cluster's assigned paths.
- Whether the `bulk/` snapshot is a copy of, or diverges from, any other CourtListener bulk export elsewhere in
  the project (e.g. inside SW-BULK or Seeger-Corpus-Enrichment) — no second copy of this exact file set was
  found or diffed; nothing in this cluster's two paths looked like a duplicate of the other.
