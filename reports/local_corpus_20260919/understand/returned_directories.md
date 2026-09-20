# Cluster: returned_directories — measured findings (2026-09-19)

Scope measured: `C:/Users/firas/Downloads/returnedfiles` (15,048 files, 2,202,260,882 bytes = 2.20 GB, walked in
full) and the 6 named zips in `C:/Users/firas/Downloads/`. All counts below came from streaming Python
(`os.walk`, `json.loads` per line, `csv.reader`, `zipfile`/`tarfile` in-memory listing, `hashlib.sha256`) run via
the PowerShell tool with the project's Python 3.11. No file under `SW-BULK`/`returnedfiles`/the zips was modified,
moved, or extracted to disk. The only file written is this report (plus scratch survey outputs under
`%TEMP%`, outside the project and outside the source folders).

## 0. TL;DR
- The 6 zips are **not new data**: 5 of them (`filejhs`, `filesjhg`, `filestoxxx`, `filejaaas`, `filesdee`) are
  byte-identical (SHA-256 verified) zip wrappers around loose files already sitting in `returnedfiles/`. Only
  `filesccsdfsdfs.zip` carries content with no loose counterpart: a nested `uscourts_crawl_1404.tar.gz`.
- `returnedfiles/_normalized/` (built 2026-08-22, `normalize_returned.py` in the loose files) already parsed
  2,418 of the 15,048 raw files into a typed, joinable layer: 60,456 records, 22,108 links, 0 unclassified,
  with `content_sha256`, `state`, `host`, `page_type`, `record_type`, and a back-pointer `source_file` to the
  original raw file. This is the single highest-value asset in the cluster — treat it as a near-finished
  candidate supplement, not raw material to re-parse.
- None of the datasets in this cluster (by filename) are referenced from `SCRAPE/sources` or
  `SCRAPE/delivery/archive-directory` today — a content grep for the domains only turned up incidental mentions
  inside captured page text, not filename/path references. Confirmed not yet wired in.
- The DOJ "sweep" is two different things with very different novelty: `doj_state_sources.jsonl` (2,746 URLs,
  1,469 domains) is 99.7% the same domains as the already-ingested `doj_state_resource_map_20260919` (1,591
  hosts, 3,201 link rows) — it adds almost nothing. `doj_sweep_urls.jsonl` (55,711 URLs, 64 domains, 13 states
  only: AK AR CT KS MI2 MO NC2 ND NV2 OK OR WV WY2) is a genuine one-hop-deeper document harvest (18,849
  PDF/DOC files + 36,862 HTML) that G7/G8 do not have yet, but it only covers 13 states, not all 50.

## 1. Inventory by named cluster

| Path / dataset | Format | Measured rows / size | Loose vs zip |
|---|---|---|---|
| `returnedfiles/doj_state_sources.{jsonl,csv,md}` + `filejhs.zip` | jsonl/csv/md | jsonl 2,965 rows (630,982 B); csv 2,965 rows | identical (sha256 match) |
| `returnedfiles/doj_sweep_urls.jsonl` + `doj_sweep_documents.csv` (+ `filejhs.zip`) | jsonl/csv | jsonl 55,711 rows (13,998,691 B); csv 18,849 rows | identical |
| `returnedfiles/state_admin_agency_*` + `filesjhg.zip` | jsonl/csv/md | jsonl 118,056 rows (25,302,492 B); csv 26,784 rows | identical |
| `returnedfiles/tier1_toxicology_directory.*` + `filestoxxx.zip` | jsonl/csv/md | jsonl 15,073 rows (3,186,445 B); csv 15,073 rows | identical |
| `returnedfiles/deep_crawl_*` + `filesdee.zip` | jsonl/csv/md | jsonl 178,961 rows (33,787,197 B); csv 63,684 rows | identical |
| `returnedfiles/ca_jccp_registry.*` + `filejaaas.zip` | jsonl/csv/md | jsonl 1,392 rows (2,368,473 B); csv 1,392 rows | identical |
| `filesccsdfsdfs.zip` → `uscourts_crawl_1404.tar.gz` (nested) | tar.gz of md+json | 17 members, 84,531,322 B uncompressed, listed via streaming (not extracted) | **no loose counterpart** |
| `returnedfiles/_normalized/` (records/links/coverage/unclassified) | jsonl+json | 60,456 records / 22,108 links / 0 unclassified (records.jsonl 38.3 MB, links.jsonl 7.3 MB) | loose only, no zip |
| `returnedfiles/bulk/` (CourtListener bulk CSVs, 2026-06-30 snapshot) | csv.bz2 ×25, .sql, .sh | 27 files, 201.6 MB compressed | loose only |
| `returnedfiles/settlementsverdicts/` (verdict lead index) | json/csv/md | 7 files, 7.2 MB (`verdict_lead_index.json` 4.1 MB, `vli_records.csv` 2.3 MB) | loose only |
| `returnedfiles/` loose "other" (14,850 files not in the named buckets above) | mixed | 1.84 GB; sub-clusters below | loose only, **sampled not exhaustively itemized** |

Sub-clusters inside "other" (measured by prefix/extension, not opened individually except samples):

| Sub-cluster | Files | Bytes |
|---|---|---|
| `www.courts.phila.gov_*.json` (per-page captures incl. mass-tort docket-search results by drug name) | 602 | 6.9 MB |
| `illinoiscourts_highvalue_part00{1-7}.md` + `illinoiscourts_URL_INDEX.md` | 15 | 99.1 MB |
| `findlaw_opinions_part{1-4}of4.tar.gz` + `findlaw_opinion_index.csv` + `findlaw_all_pages.jsonl` + `findlaw_index.md` | 7 | 250.6 MB |
| `www.kycourts.gov_*` (KY courts pages) | 24 | 0.7 MB |
| `batch0{1-6}.json` | 6 (12 counted incl. dupes) | 0.36 MB |
| everything else (numbered `N.pdf`/`N.html` Firecrawl crawl parts, `registry.jsonl`, `texas.jsonl`, `url_directory.{jsonl,csv}`, NEISS/CPSC `Recalls.csv`/`IncidentReports.csv`, `neiss2025.xlsx`, `CMS-*_content.pdf`, `congressionalreport.pdf`, `2026KAcodes*.pdf`, `pacode_serial_2026.pdf`, `ky_counties_raw.json`, `parsed_tx_counties.json`, `parsed_la{ccl,dj}.json`, session/checkpoint files) | 14,184 (13,956 distinct names) | 1.48 GB |

The last row is **not itemized file-by-file** — 32 measurement calls would be needed to open each one; this is
flagged under "not verified" below. `_normalized/records.jsonl` already classifies most of it by `page_type`
(see §3), which is the fastest path to using it rather than re-surveying raw files one at a two.

## 2. Zip vs loose comparison (byte-identical check, full SHA-256)

| Zip | Members | Loose match | Verdict |
|---|---|---|---|
| `filejhs.zip` (0.57 MB) | 5 (doj_state_sources.{csv,jsonl,md}, doj_sweep_{urls.jsonl,documents.csv}) | all 5 sha256-identical to `returnedfiles/*` | pure zip wrapper, delete-safe duplicate |
| `filesjhg.zip` (1.84 MB) | 3 (state_admin_agency_*) | all identical | pure wrapper |
| `filestoxxx.zip` (0.36 MB) | 3 (tier1_toxicology_directory.*) | all identical | pure wrapper |
| `filejaaas.zip` (0.67 MB) | 3 (ca_jccp_registry.*) | all identical | pure wrapper |
| `filesdee.zip` (2.44 MB) | 3 (deep_crawl_*) | all identical | pure wrapper |
| `filesccsdfsdfs.zip` (12.47 MB) | 3: `uscourts_crawl_1404.tar.gz` (12,378,443 B), `uscourts_crawl_index.md` (292,846 B), `uscourts_external_links.csv` (75,195 B) | **no loose copy of any of the 3 members exists in `returnedfiles/`** | this zip is the sole carrier of the uscourts.gov crawl — do not delete |

Neither "newer/authoritative" question applies here beyond the above: the 5 wrapper zips and their loose
counterparts are the *same bytes*, so there is no staleness question — either copy can be deleted without loss,
loose is more convenient (no unzip step for an adapter).

## 3. `filesccsdfsdfs.zip` → `uscourts_crawl_1404.tar.gz` — the uscourts.gov Firecrawl crawl (G10)

Listed via `tarfile.open(fileobj=io.BytesIO(...), mode='r:gz')` without extracting to disk.
- `uscourts/_meta.json`: `{"success": true, "status": "completed", "completed": 1404, "total": 1404,
  "creditsUsed": 57642}` — a completed Firecrawl `crawl` job, 1,404 pages, 57,642 credits (large job).
- `uscourts/_index.json`: list of 1,404 `{n, url, title, status, md_chars, domain}` records — all
  `domain: "www.uscourts.gov"`, `status: 200` in the sampled rows. This is the per-page **metadata index**
  (title, char count) but not a separable per-page body.
- Page bodies live concatenated across `uscourts/uscourts_court_links_part001.md` … `part013.md` (13 files,
  84.5 MB uncompressed total across the tarball) — extracting one page's text requires locating it inside the
  concatenated markdown, which the crawl output does not index by URL. Treat "1,404 pages of raw markdown, not
  yet split per-URL" as a build-time task, not a done deal.
- `uscourts/_external_links.json`: 677 outbound links from those pages (federal defenders, Supreme Court, etc.)
  — a small, usable seed list for `sources/public_law_directory_20260919`-style link tracking (G14).
- `uscourts_external_links.csv` (sibling to the tar.gz, not inside it) is a second, separate 75,195-byte export
  of the same/similar external-link set — not diffed against `_external_links.json` (not verified below).
- Nothing in this bundle overlaps `federal_court_statistics_20260919` (CJRA tables) — this is uscourts.gov
  *pages* (court structure, admin, links), not statistical tables. G10 gap is about statistics tables
  specifically; this dataset instead strengthens the **court/website-link directory** side of G6/G14.

## 4. CA JCCP registry (G5) — `ca_jccp_registry.*` (loose, identical inside `filejaaas.zip`)

- 1,392 rows (jsonl 2,368,473 B; csv 291,694 B; md 142,982 B). Schema (csv header):
  `jccp_no, date_received, category, title, counties, judges, case_numbers, log, page`.
  jsonl adds a `text` field (raw extracted narrative) not in the csv.
- **Quality risk, verified by inspection of the first 2 jsonl rows**: `judges` and `text` are extraction
  artifacts, not clean fields. Example: `judges: ["Assigning Hon. Susan I.", "Marie", "Marie S.", "Marie S.
  Wiener", "Marie Weiner", "Susan Irene Mateo Request"]` for one JCCP entry — this is a jumbled token split of
  a PDF-table extraction ("Hon. Marie S. Weiner", "Hon. Susan Irene Etezadi") rather than a validated judge
  name list. **Do not join this `judges` field to `judge_structured`/`judge_aliases` by string match** without
  a manual cleaning pass — it will produce false merges (the prohibition on merging by name alone in BRIEF.md
  is directly at risk here). `counties` (semicolon-joined names, e.g. `"Marin;Santa Clara"`) and `case_numbers`
  are cleaner and safe to use for county/docket join keys.
- `category` facet present (`other`, `wage_hour`, `masstort_candidate`, …) — usable filter for a listing view.
- Native ids: JCCP number (`jccp_no`) is the CA-native coordination-proceeding id; no CourtListener/FJC id
  present (this is a state registry, not federal). Join key to MVP: none direct today — would need a new
  `state:CA` + `jccp:<no>` id grammar entry (not in the existing native-id grammar list in BRIEF.md); propose
  `jccp:CA:<jccp_no>`.
- Date field `date_received` (e.g. "12/26/17", "7/30/26") — ambiguous basis (received-by-registry vs.
  filed-with-court); treat as `captured_at`-adjacent, not `effective_from`, until the source page's own label
  is checked (not verified here — would require opening the CA courts source page, out of scope for this
  read-only, no-network task).
- Fills: **G5** (CA JCCP judges/coordination registry) directly — no full alternative exists in the current MVP
  per BRIEF.md/STATE.md (CA JCCP explicitly named as unresolved in G5). Effort to build a supplement: **S**
  for the raw listing (data is already flat and small); **M** if the judges field is re-cleaned before joining.

## 5. DOJ state sweep, state admin agency directory, tier-1 toxicology, deep-crawl (G7/G8/G9/G14)

All four share the same row schema family: `{url, kind, domain, label, refs, sources}` (or `{state, section,
subsection, label, url, domain}` for `doj_state_sources`, or `{url, title, group, content_kind, discovered_via,
domain}` for tier1_toxicology). None carry native ids (no CourtListener/FJC/FIPS/MDL fields) — join key to the
MVP is **domain/URL string match only**, or (for `doj_state_sources`) `state` (full lowercase name, not USPS
code — needs a name→FIPS/USPS crosswalk before joining to `state:<USPS>`).

| Dataset | Rows | Domains | Fills | Novelty vs MVP |
|---|---|---|---|---|
| `doj_state_sources.jsonl` | 2,965 (2,746 unique URLs) | 1,469 | G7/G14 (state resource directory) | **Low** — 1,465/1,469 domains (99.7%) already present as `host` in `doj_state_resource_map_20260919/resources.jsonl` (3,201 rows, 1,591 hosts, measured directly). Only 4 new domains: `public.govdelivery.com`, `theworknumber.com`, `vote.gov`, `www.nyls.edu`. This is effectively the same DOJ 56-page link harvest re-exported, not new pages. |
| `doj_sweep_urls.jsonl` / `doj_sweep_documents.csv` | 55,711 rows / 18,849 docs | 64 domains, 34 beyond the existing DOJ hosts | G7/G8 (state statute/reg documents, one hop past the DOJ index page) | **Real but narrow** — covers only 13 states (tag `sources`: AK AR CT KS MI2 MO NC2 ND NV2 OK OR WV WY2), not all 50/56. `kind` breakdown: 10,676 pdf, 8,172 doc, 36,862 html, 1 zip. Genuinely new documents (state rules registers, admin code drafting manuals, etc. — e.g. Arkansas Register PDFs, ND legislative drafting manual) not present elsewhere in the MVP. |
| `state_admin_agency_urls.jsonl` / `*_documents.csv` | 118,056 rows / 26,784 docs | not fully deduped (near-dupe URL pairs seen, e.g. `a257.g.akamaitech.net` vs `a257.gakamaitech.net` — same GPO PDF via two legacy CDN hostnames) | G9 (state administrative agencies + federal regulatory) | Row 1 sample tagged `sources: "CMS"`, `layer: "federal_agency"` — despite the "state_admin_agency" filename, the sampled rows are **federal** (CMS/FTC/GPO), not state-agency; the `layer` field distinguishes this internally. A build must not assume filename = state-agency-only; check `layer` per row. |
| `tier1_toxicology_directory.jsonl/.csv` | 15,073 rows | includes noise (e.g. a `twitter.com/share?url=...` share-link counted as a toxicology URL) | G9 (federal/toxicology science sources) | `group` facet (`ATSDR`, presumably others) usable as a filter; `discovered_via` gives crawl provenance (e.g. `"atsdr_docs:link"`). Needs a share-link/tracking-URL filter before use — not deduplicated for that in the raw file. |
| `deep_crawl_urls.jsonl` / `deep_crawl_documents.csv` | 178,961 rows / 63,684 docs | wide domain spread incl. CDN/file-hosting hosts (`*.filesusr.com`, `*.azureedge.net`) | G9/G14 (regulatory documents, e.g. `sources: "ca_oal"` = CA Office of Administrative Law approvals) | Broadest and least curated of the four; `sources` tag values seen include `fjc` and `ca_oal` — mixed-provenance grab-bag, needs per-`sources`-tag triage before it is safe to treat as one dataset. |

None of these five datasets have a `captured_at`/date field in the sampled rows at all — they are URL
directories (frontier lists), not captured documents; the actual bytes behind each URL have **not** been
fetched as part of this cluster (no local PDF/HTML bodies live next to these jsonl/csv files). Effort to turn
any one into a real MVP layer: **listing/frontier only = S** (just load the URL table as a browsable directory
per G14); **fetching+parsing into real records = L** (needs the bounded-packet network process in BRIEF.md,
one host at a time, for each of tens of thousands of URLs).

## 6. `_normalized/` — pre-built classification layer (highest-value item in this cluster)

`returnedfiles/_normalized/{records.jsonl, links.jsonl, coverage_report.json, unclassified.jsonl}`, built by
`returnedfiles/normalize_returned.py` (present as a loose file, 59,248 B, not opened for logic review — flagged
under "not verified"). From `coverage_report.json` (read directly, not sampled):

- Read 2,418 of the 15,048 raw files (the per-page/UUID/search-result/map-url files, county rosters, judge
  rosters — **not** the DOJ/state-admin/toxicology/deep-crawl jsonl/csv, the CA JCCP registry, the zips, or
  `bulk/`, based on the record-type mix). Emitted 60,456 typed records, 42,670 unique URLs, 22,108 links,
  **0 unclassified** records, 8,321 Firecrawl credits accounted for.
- `records.jsonl` row schema (from the first record, fully shown): `url, host, state, page_type, page_detail,
  title, access_model, record_type, source_file, content_sha256, parsed_ok, data{...structured extraction...},
  provenance{mode, scrape_id, index_id, status_code, content_type, cache_state, cached_at, credits_used,
  proxy_used, throttled, warning}`. `source_file` is the exact raw filename this record came from (traceable
  back to a specific `returnedfiles/*.json`) and `content_sha256` lets a consumer re-verify against the raw
  file — this is the join key back to the raw corpus.
- `links.jsonl` row schema: `source_url, url, host, text, external, state, access_model, commercial` — a
  ready-made edge list (22,108 edges); `commercial` flags e.g. westlaw/lexis outbound links
  (`commercial_link_hosts: ["1.next.westlaw.com", "advance.lexis.com"]` — 2 hosts, licence-sensitive, must stay
  flagged not scraped, consistent with G11's FindLaw terms caveat).
- `by_page_type` (30 categories, full list in the file) directly maps to gaps: `judge_directory` 1,256 +
  `judge_profile` 739 + `judge_roster` 363 → **G4/G5**; `county_court_site` 1,059 + `county_page` 872 +
  `county_records_by_state: {KY: 120, TX: 254}` → **G7** (KY explicitly complete: `ky_county_coverage:
  {expected: 120, fetched: 120, missing: 0}`); `opinion_document` 2,291 + `opinions_index` 1,575 → **G11**
  (case law, watch licence — FindLaw content is in this mix, terms-prohibited per BRIEF); `statute` 406 +
  `legislation` 2,152 → **G8**; `administrative_order` 1,223 + `court_statistics` 2,736 → **G10**;
  `medical_source` 257 → **G9**. `roster_seats: 28, roster_vacancies: 2` is a small structured judge-vacancy
  fact set worth a direct look for G4.
- `by_state` covers 25 tags (state USPS codes + `US`, `THIRD_PARTY`, `INTL`, `unknown` 200) — NJ (12,342), IL
  (3,883), TX (3,866), KY (3,377), PA (2,389) are the largest single-state clusters, i.e. this layer is heavily
  NJ/IL/TX/KY/PA-weighted, not a uniform 50-state sample.
- `provenance_flags`: `cache_hits_not_fresh: 786`, `throttled_scrapes: 445` — ~5% of records carry a
  freshness/throttle caveat already flagged by the normalizer; any adapter surfacing this data should propagate
  those flags into its own `qualification` text rather than presenting all 60,456 records as uniformly fresh.
- `binary_blobs`: 34 records are base64-embedded PDFs (23.7 MB decoded estimate, all `application/pdf`) living
  inside JSON rather than as separate files — an adapter would need to decode `data`/`content` fields to serve
  these as `original()` bytes; not verified whether `records.jsonl` stores the base64 inline or only its hash
  (not opened for a binary_blob row — flagged as not verified).
- Quality risk: `unclassified: 0` is a strong claim for a 2,418-file, 60,456-record parse — worth a spot-check
  against `unclassified.jsonl` (confirmed 0 bytes / present as an empty file per the original inventory) before
  trusting it fully; the classifier's rules (in `normalize_returned.py`) were not read.
- Effort to adapt this into an `sources/<name>_20260919/` supplement: **S** — the hard normalization work is
  already done; a build here is mostly hash-gating `records.jsonl`/`links.jsonl` as-is, writing the uniform
  `validation.json` envelope, and mapping `page_type`/`state` to listing filters.

## 7. `returnedfiles/bulk/` — CourtListener bulk data snapshot (2026-06-30)

27 files, 201.6 MB compressed (`.csv.bz2` ×25, `schema-2026-06-30.sql`, `load-bulk-data-2026-06-30.sh`), not
decompressed (bz2 CSVs; would need per-file streaming decompression to get row counts — **not measured**, flagged
below). Largest: `citations-2026-06-30.csv.bz2` (127.4 MB), `financial-disclosure-investments` (36.6 MB),
`originating-court-information` (20.6 MB). This is the same family as the CourtListener people/courts/financial
bulk exports already partially used for `court_spine_20260919`/`judge_structured_20260919` (per STATE.md's "3,701
bridged to CourtListener by native ids") — **not diffed against what those layers already ingested** (would need
to decompress and compare row-level native ids; out of scope for this pass, flagged below). `citations` and
`search_opinioncluster_panel`/`search_opinion_joined_by` tables suggest this snapshot could feed **G11** citation
graph data (case law relationships) without touching FindLaw's prohibited terms — CourtListener bulk data
carries its own (permissive) licence, distinct from FindLaw scraping.

## 8. `returnedfiles/settlementsverdicts/` — verdict lead index (G3)

7 files, 7.2 MB. `verdict_lead_index.json` (4.1 MB) + `verdict_lead_index_report.md` + 5 CSVs
(`vli_records.csv` 2.3 MB, `vli_mass_tort_leads.csv`, `vli_coverage_gap_states.csv`,
`vli_firm_leaderboard.csv`, `vli_jurisdiction_rollup.csv`). Not opened for schema in this pass (flagged below) —
name pattern strongly suggests this is a **verdict/settlement lead-generation** dataset (firm leaderboard,
jurisdiction rollup, coverage-gap-by-state) rather than settlement agreement documents; likely overlaps
conceptually with the existing `settlements_20260919` (861 rows) and the "settlement licence conflict" already
flagged as a decision pending the user in STATE.md — **do not build against this without re-reading that
decision first**, since it may be the same licensed feed.

## 9. Already-used check (grep against SCRAPE/sources and SCRAPE/delivery/archive-directory)

Grepped for the exact filenames/dataset names (`doj_sweep`, `doj_state_sources`, `state_admin_agency`,
`tier1_toxicology`, `deep_crawl_urls`, `ca_jccp`, `uscourts_crawl`, `findlaw_opinions`, `courts.phila.gov`) across
`sources/` and `delivery/archive-directory/`. Two incidental hits only (`judges.py`,
`test_official_judge_overlay.py` matched the generic substring "returnedfiles", which is BRIEF.md's own path
reference, not a load of these specific files) — **no adapter or build script in the current MVP references any
dataset in this cluster by name**. Confirmed not yet integrated.

## 10. Native ids present / absent (summary)

- **Present**: none of the URL-directory datasets (§5) carry CourtListener/FJC/PACER/FIPS/MDL ids. `_normalized/`
  records carry `content_sha256` + `source_file` (internal join keys back to raw files) and `scrape_id` (Firecrawl
  job id) — useful for dedup/provenance, not for cross-MVP entity joins. `ca_jccp_registry` carries CA-native
  `jccp_no` only. `uscourts_crawl` carries none (page-level `n`/`url`/`title` only).
- **Absent everywhere in this cluster**: CourtListener docket/person/court id, FJC nid/jid, PACER case id, MDL
  number. Any join to `judge_structured`/`court_spine`/`jpml_mdl` from this cluster must go through URL/domain/
  county-name/state matching, never a native id — higher false-merge risk, consistent with BRIEF.md's warning.

## 11. Not verified / out of scope for this pass (time-boxed, flagged rather than guessed)

- The 13,956 distinct "misc singleton" file names inside `returnedfiles/other` (1.48 GB) were **not** opened
  individually — only grouped by name/extension and the top 40 by size listed (§1). `_normalized/coverage_report`
  covers a 2,418-file subset of this; the remainder (mostly numbered `N.pdf`/`N.html` crawl parts, `registry.jsonl`,
  `texas.jsonl`, `url_directory.{jsonl,csv}`, NEISS/CPSC exports, state code PDFs) is inventoried by name/size
  only.
- `returnedfiles/bulk/*.csv.bz2` row counts, schemas, and overlap with existing `court_spine`/`judge_structured`
  CourtListener ingestion — not decompressed or diffed.
- `returnedfiles/settlementsverdicts/*` — file names and sizes measured; JSON/CSV schema not opened.
- `uscourts_external_links.csv` (sibling of the tar.gz in `filesccsdfsdfs.zip`) vs. the tar's own
  `_external_links.json` — not diffed for exact overlap.
- `normalize_returned.py` classification logic — not read; the "0 unclassified" and page_type assignments are
  trusted from `coverage_report.json` only, not independently re-derived.
- Exact effective/publication dates for CA JCCP `date_received` and DOJ/toxicology/agency URL "as of" dates —
  none of the sampled records carry an explicit capture timestamp field; cannot state a build date for these
  URL-directory files beyond the zip/file mtimes (not extracted here since BRIEF.md says HTTP/file-system dates
  are not legal dates and mtimes were not specifically pulled).
- Personal contact details: none printed above; judge names appear only as already-published case-caption/roster
  text (public court filings and public rosters), not private-individual contact info.
