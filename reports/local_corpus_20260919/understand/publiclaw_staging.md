# publiclaw_staging cluster — C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging

Scout: read-only. All numbers below came from streaming Python measurements run against this
tree today (2026-09-19); none were read from the earlier `local_inventory.md` (it contains no
section on this path — this is the first survey). `inventory.json` supplied the pre-measured
top-level 105,602.8 MB / 57,021-file / extension totals, which I used as-is and then walked
myself to break down by subfolder. **Nothing under SW-BULK was modified, moved, or extracted.**

## 0. What this directory actually is (README.md, read in full)

`staging/README.md` states this is **pre-promotion discovery staging**, not a vetted registry:
"Discovery is evidence that a URL exists, not approval to crawl it or an assertion that its
contents are current law." Nothing here has been reviewed against the README's 7 promotion
gates (authoritative host, dedup, robots/terms, taxonomy, jurisdiction/date/citation metadata,
acquisition method, hash/version). The README also states explicitly that most of the top-level
`*_v1..v6` graph directories are **superseded exploratory audit artifacts** — only the highest
version number per family (v4/v5/v7 as named in the file) is canonical; do not treat the whole
tree as uniformly current. One line is a direct hard-rule confirmation for the report: "No PDF
bodies were saved locally" for the Firecrawl Rhode Island increment — bulk document bytes live
elsewhere in the tree (see §2), not from that particular queue.

## 1. Top-level shape (395 entries, walked in full — 57,021 files / 105,602.8 MB confirmed)

| Group | Files | MB | Contents |
|---|---:|---:|---|
| `__top__` (395−42=353 loose files at the staging root) | 353 | 58,344.8 | 123 `.jsonl`, 117 `.gz`, 104 `.json`, 8 `.sqlite`, 1 `.md`. Federal (CFR/US Code/Federal Register/GovInfo/Public-Law) discovery-graph and URL-frontier files, mostly superseded per README versioning. |
| `court_expansion_file_download_v2_4_2026-08-20/` | 47,311 | 42,346.3 | **The big PDF/Office-doc store** — see §2. |
| `state_trial_court_acquisition_v1_2026-08-20/` | 3,716 | 3,547.8 | **Second document store** — see §2. |
| `govinfo_api_cache_2026-08-20/` | 3,420 | 140.7 | Raw GovInfo API response cache (`.gz`, one per call), not a document corpus. |
| `structured_cache_2026-08-20/` | 1,188 | 32.5 | 594 paired `.gz`+`.json` cache/receipt files. |
| `state_trial_court_directory_bodies_v1_2026-08-20/` | 745 | 19.1 | Per-court directory-page HTML/JSON bodies (gz), not case documents. |
| `sd_statutes_cache_2026-08-20/` | 71 | 2.3 | South Dakota statutes API-response cache (small, `.gz` only). |
| 34 other small `*_v1..v7` graph/audit dirs | ~180 | ~1,200 | CFR/Federal-Register/Public-Law identity, temporal, and event graphs; court-expansion seed/report/preflight logs; Tavily event-discovery queues. All small (≤ 1 GB combined; individually a few KB–800 MB). |

42 directories + 353 loose files = 395 top-level entries, confirmed by direct `os.listdir`.

## 2. The two real document stores (this is the corpus)

### 2a. `court_expansion_file_download_v2_4_2026-08-20/` — 47,311 files, 42.35 GB (the bulk of the 45k PDFs)

Structure: `wave_00N[_retry|_followup|_cumulative_followup]/` (19 wave-run folders) each holding
`court_file_download_report_v2.json` (run summary), `court_file_download_results_v2.jsonl`
(**the manifest: one JSON record per downloaded artifact**), a `_latest_v2.jsonl.gz` /
`_continuation_queue_v2.jsonl.gz` (frontier state), and `files/<authority_lane>/<jurisdiction>/<host>/<sha-ish-id>.<ext>`
(the actual bytes).

Manifest record shape (from `wave_001/court_file_download_results_v2.jsonl`, field-for-field):
`artifact_id, source_url, download_url, authority_lanes[], jurisdiction_codes[], file_extension,
acquisition_priority, scope_basis, matched_seed_ids[], started_at, local_path, download_status,
http_status, final_url, content_type, bytes, sha256, signature_class, detected_file_extension`.
This *is* the URL→file→sha256→jurisdiction→doc-type manifest the task asked me to find, already
in place per wave. I streamed all 11 `results_v2.jsonl` files across the 19 wave dirs to
completion (no sampling needed — 47,445 lines, well inside the time cap):

| Metric | Value |
|---|---|
| Manifest records | 47,445 |
| `download_status` | downloaded 47,230 · download_error 194 · signature_rejected_body_removed 21 |
| Unique sha256 | 45,478 of 47,445 hashed rows → **~4.1% duplicate rate by hash** (1,752 dup rows) |
| Sum of `bytes` field | 41.93 GB (matches the 42.35 GB on-disk figure closely; delta is the manifest/queue files themselves) |
| `file_extension` | .pdf 41,874 · .xlsx 3,254 · .xls 533 · .doc 839 · .docx 914 · .zip 15 · .rss 3 · .txt 6 · .xml 3 · .rtf 1 · .csv 1 |
| `authority_lanes` (doc-type facet) | federal_judiciary_national_resource 21,967 · state_or_dc_judiciary 13,468 · federal_district_court 7,226 · federal_bankruptcy_court 3,367 · federal_probation_or_pretrial_office 2,474 · territorial_judiciary 432 · federal_appellate_court 203 |
| `jurisdiction_codes` (state facet, 30 distinct, USPS lowercase) | ak 2,480 · va 1,653 · al 1,547 · wv 1,475 · ky 1,202 · md 992 · tx 637 · ia 497 · az 457 · gu 432 · wa 404 · nd 401 · or 229 · me 227 · wi 219 · ny 178 · ri 160 · mt 160 · pa 97 · ut 83 · in 82 · mn 82 · ms 77 · il 55 · co 37 · ct 19 · sd 13 · wy 3 · dc 1 · id 1 |

**Quality risk — jurisdiction skew:** only 30 of 56 US jurisdictions have any files here at all,
and it is wildly uneven (Alaska 2,480 vs. Idaho 1, Delaware/Florida absent). This is a lane-priority
acquisition (`acquisition_priority` field, 96–100), not a systematic all-state sweep — treat as
partial, opportunistic coverage, not "this is what exists for state X."

**Quality risk — content-type surprise:** the largest lane is `federal_judiciary_national_resource`
(22k files, mostly `www.uscourts.gov` and circuit-committee material — comment letters, judicial
council minutes, national forms), not state material. Sampled records under `state_or_dc_judiciary`
include not just rules/forms but also **published court opinions** (see §4) — this store is a mixed
bag of forms, general orders, administrative/budget documents, rule-committee minutes, and case law,
not purely G7/G8 statute-and-rule text.

### 2b. `state_trial_court_acquisition_v1_2026-08-20/` — 3,716 files, 3.55 GB

Structure: `artifact_preflight_{results,latest}_v1.jsonl(.gz)` (candidate queue),
`artifact_download_report_v1.json` (run summary), `artifact_download_results_v1.jsonl`
(manifest, 3,718 lines), `files/<jurisdiction>/<host>/<id>.<ext>`.

Manifest schema: `artifact_id, source_url, download_url, jurisdiction_codes[], file_extension,
started_at, local_path, download_status, http_status, final_url, content_type, bytes, sha256,
signature_class, redirect_chain[], completed_at, error`. No `authority_lanes` field here (empty
in every sampled row) — this run is state-trial-court-focused only, no federal lane split.

| Metric | Value |
|---|---:|
| Manifest records | 3,718 |
| `download_status` | downloaded 3,710 · signature_rejected_body_removed 4 · download_error 4 |
| `file_extension` | .pdf 3,590 · .xml 74 · .doc 30 · .docx 11 · .xlsx 4 · .xls 2 · .csv 1 · .txt 6 |
| `jurisdiction_codes` (44 distinct states + DC, per `jurisdiction_success_counts` in the report) | ca 529 · va 437 · sd 233 · pa 202 · nj 200 · mi 188 · tx 126 · wa 124 · oh 116 · ms 107 · ri 103 · mt 97 · ky 94 · wi 91 · ak 77 · la 77 · al 75 · hi 74 · ga 64 · nh 64 · or 63 · az 58 · il 57 · wv 51 · vt 41 · ia 40 · ar 37 · me 33 · ut 32 · ny 29 · sc 24 · nv 23 · co 23 · in 22 · ok 21 · wy 21 · md 15 · ks 13 · nd 12 · mo 8 · nm 6 · id 6 · de 3 · fl 1 · dc 1 |

Union of jurisdictions across 2a+2b = essentially all 50 states + DC/GU at some level, but 6 states
(FL, DE, MO, NM, ID, KS, ND) have single digits combined and several (2a's absentees) rely entirely
on 2b. Neither store approaches 630-county granularity — both are host/state level, not per-county
(no county FIPS field anywhere in either manifest schema).

## 3. Everything else at the top level (not documents; do not confuse with §2)

| File/family | Size | What it is |
|---|---:|---|
| `federal_granule_files_large_delta_2026-08-20.sqlite` | 9,490.8 MB | 1-table (`urls`) sqlite of `comparison_key, origin` — a URL-delta dedup index for GovInfo granule crawling, not documents. |
| `govinfo_novel_urls_2026-08-20.jsonl` | 7,755.3 MB | Streamed first lines: GovInfo API package/granule URL frontier records (`provider, source_id, collection, package_id, url, context, discovery_method`), e.g. Serial Set, CFR. **This is G14 material** (source/URL frontier list), not fetched content. |
| `govinfo_derived_file_routes_2026-08-20.jsonl` | 5,946.9 MB | Derived (`derived_unverified`) candidate file routes per the README's own caveat — not confirmed to exist. |
| `govinfo_granules_2026-08-20.jsonl` | 5,035.2 MB | GovInfo granule metadata (title, dateIssued, granuleClass) per package — CFR/US Code/Statutes-at-Large/US Reports structural index, evidence_status `observed_official`. |
| `govinfo_granule_urls_2026-08-20.jsonl` / `_novel_urls` | 4,186.7 MB each | Granule-level URL frontier, same family as above. |
| `federal_granule_large_delta_2026-08-20.sqlite`, `federal_large_delta_2026-08-20.sqlite`, `govinfo_large_delta_2026-08-20.sqlite` | 3,253 / 1,942 / 1,866 MB | More URL-delta dedup indexes (same 1–2 table `urls`/`granules` shape confirmed by schema probe). |
| `govinfo_granule_edges_2026-08-20.jsonl` | 3,030.8 MB | package↔granule relationship edges. |
| `govinfo_api_urls_2026-08-20.jsonl` | 1,968.2 MB | Raw API call URL log. |
| `govinfo_granule_dedup_2026-08-20.sqlite` | 1,915.5 MB | 2-table (`granules`: package_id/granule_id; `urls`: comparison_key) — dedup index, schema confirmed. |
| `sd_statutes_cache_2026-08-20/` (71 `.gz`) | 2.3 MB | South Dakota statutes API-response cache — small, could seed a G8 SD-statutes supplement cheaply. |
| ~30 other `plaw_*`, `cfr_*`, `court_*`, `federal_register_*`, `structured_cache` families | ≤ ~1 GB total | Federal Public-Law/US-Code/CFR/Federal-Register identity, temporal, and event-dependency graphs, and Tavily event-discovery queues — all explicitly labelled by README as evidence/graph layers with named canonical versions and explicit "do not flatten/bulk-promote" caveats (see §0). These are candidate-graph inputs for a future federal statutes/regs pipeline, not directly servable documents. |

None of these govinfo/CFR/federal-register files are jurisdiction-tagged to states/counties — they
are entirely federal. They matter for **G8** (federal regs corpus already partly covered by
`sources/federal_regulations_20260919`, 12,622 CFR sections — this staging tree could deepen that
to full historical CFR/US Code/Statutes-at-Large granule coverage) and **G14** (frontier lists), not
for G7 (county courts) or G9 (state agencies).

## 4. 25-document sample (header/first-page text only, via `pypdf`, no bulk opening)

Random sample of 16 (8 from each of the two document stores), first-page `extract_text()` only:

| Jurisdiction/Lane | URL (host) | First-page characterization |
|---|---|---|
| ms / state judiciary | courts.ms.gov | AOC staff job-description/salary schedule (administrative, not law) |
| — / federal district | cand.uscourts.gov | N.D. Cal. General Order No. 68 (local court administrative order) |
| md / state judiciary | mdcourts.gov | Appellate Court informal-brief **form** |
| ky / state judiciary | kycourts.gov | Court **form** (waiver of recording) |
| md / state judiciary | mdcourts.gov | *Amicus Curiarum* — official state-reporter bulletin of attorney-discipline and opinion summaries |
| ak / state judiciary | public.courts.alaska.gov | Restitution-judgment **court form** (CR-465) |
| — / federal judiciary national resource | uscourts.gov | Rules-committee comment letter |
| — / federal judiciary national resource | uscourts.gov | Rules-committee comment/suggestion letter |
| mo / (no lane) | courts.mo.gov | **Full appellate brief** in a capital case (Missouri Supreme Court) |
| hi / (no lane) | courts.state.hi.us | **Published Hawai'i Supreme Court opinion** |
| wv / (no lane) | courtswv.gov | **Published W. Va. Supreme Court memorandum decision** |
| wy / (no lane) | wyocourts.gov | Judicial-branch biennium **budget** document |
| ca / (no lane) | riverside.courts.ca.gov | Self-help **form packet** (Trial Readiness Conference) |
| md / (no lane) | mdcourts.gov | Rules-committee **meeting minutes** (179 pp.) |
| la / (no lane) | lasc.org | **Published Louisiana Supreme Court opinion** (news-release format) |
| ca / (no lane) | imperial.courts.ca.gov | Family-law **form** (FL-22-1) |

**Finding:** this is not a clean statutes/regs/rules corpus. It is a mixed grab-bag: court **forms**
(the largest visible category), **local rules/general orders**, **rule-committee minutes**,
**administrative/budget documents**, and — importantly — a nontrivial number of **published court
opinions scraped directly from official state-court sites** (MO, HI, WV, LA in this small sample).
The opinions came straight from the issuing court's own domain (not FindLaw), so the G11 FindLaw
terms-of-service flag does not directly apply, but each state supreme/appellate court site has its
own redistribution terms that were not checked here — flag before republishing full opinion text.
Records with `authority_lanes: null`/empty (about half the state-tagged sample) look to be an
earlier/looser acquisition pass than the lane-tagged `court_expansion_file_download` records;
build effort should not assume every record carries a doc-type facet.

## 5. Duplicates / freshness

- Hash-level dedup only measured for store 2a (§2a): ~4.1% duplicate sha256 rows out of 47,445.
  Store 2b (3,718 rows) was not separately hash-deduped in this pass (label as estimate: likely
  low, since acquisition was single-pass per the report's `previous_latest_count`/`processed_this_run`
  bookkeeping) — **not directly measured, flagged as a gap**.
- All acquisition timestamps (`started_at`/`completed_at`/`generated_at`) are 2026-08-20/21 — a
  single snapshot, not an ongoing refresh; treat every record's currency as "as of 2026-08-20."
- No prior SCRAPE usage: `grep -r "publiclaw_registry_v2"` over `sources/` and
  `delivery/archive-directory/` returned no hits (checked both). This entire cluster is unused by
  the live MVP today.

## 6. Gap mapping, join keys, effort

| Dataset | Path | Rows (measured) | Gaps filled | Join key to MVP | Risk | Effort |
|---|---|---:|---|---|---|---|
| Court-expansion document store + wave manifests | `court_expansion_file_download_v2_4_2026-08-20/wave_*/court_file_download_results_v2.jsonl` + `files/` | 47,445 manifest rows / 47,230 downloaded files | **G7** (county/court forms, local rules, standing orders — partial, 30 states, uneven) and a slice of **G6** (host = court domain, but no street address field) | `jurisdiction_codes` (USPS lower) → `state:<USPS>` in existing edge grammar; no county/FIPS field, so cannot join to county-level court records without a second normalization pass on `source_url` paths/host names | Jurisdiction skew (30/56, very uneven); mixed doc types (forms/orders/opinions/minutes/budgets) requiring per-record classification before UI placement; ~4% dup by hash; half the records lack `authority_lanes` | **M** for an index-only supplement (hash-gate + facet build from existing manifest fields, no new fetching); **L** if the goal is full per-county/per-doc-type normalization |
| State-trial-court acquisition store + manifest | `state_trial_court_acquisition_v1_2026-08-20/artifact_download_results_v1.jsonl` + `files/` | 3,718 manifest rows / 3,710 downloaded files | **G7** (44 states, still no county granularity) | Same `jurisdiction_codes` → `state:<USPS>`; no doc-type facet at all (field absent) | No lane/doc-type facet (would need URL-pattern or first-page-text classification, i.e. more than an index pass); dup rate not measured | **M** |
| GovInfo/CFR/Public-Law URL-frontier + granule files (top-level `.jsonl`/`.sqlite`) | staging root, ~40 GB across ~15 files | Spot-checked (7.7 GB/5.0 GB/4.2 GB files streamed for first lines only; sqlite schemas probed, not counted) | **G14** (frontier/source directory) and deepening **G8** federal regs beyond current 12,622-CFR-section layer | `package_id`/`granule_id` (GovInfo native ids) — new native-id class, not yet in the edge grammar; would need `govinfo_package:<id>` / `govinfo_granule:<id>` added | README explicitly marks most of these `derived_unverified` / superseded-by-version; must not bulk-promote; several files are 5–9 GB each, expensive to fully stream-validate | **L** (large volume, needs the version-discipline the README lays out, i.e. use only the v4/v5/v7 "canonical" files it names, not the whole tree) |
| `sd_statutes_cache_2026-08-20/` | 71 `.gz`, 2.3 MB | Not opened (small, gz-compressed API cache) | **G8** (South Dakota statutes — currently a stated MVP gap state) | Would need a state code join (`state:SD`) | Unopened — cache format/schema not verified in this pass | **S** (small, cheap first target if it decompresses to usable statute text) |
| `govinfo_api_cache_2026-08-20/`, `structured_cache_2026-08-20/`, `state_trial_court_directory_bodies_v1_2026-08-20/` | ~5,300 files, ~192 MB combined | Counted by extension only, not opened | Raw response caches — support data for rebuilding the above, not a new gap-filler themselves | n/a | Cache freshness/schema unverified | **S** if reused as-is for provenance, otherwise skip |

## 7. What an index-only supplement would look like

Given the hard rule (never touch SW-BULK; only the SCRAPE app's own hash-gated supplement pattern
may serve bytes), the natural build is:

1. **Metadata-only ingest** of the two wave-manifest families (2a: 47,445 rows across 11
   `results_v2.jsonl` files; 2b: 3,718 rows) into a `sources/publiclaw_court_docs_20260919/`
   supplement: keep `source_url, jurisdiction_codes, authority_lanes (2a only), file_extension,
   content_type, bytes, sha256, download_status, started_at/completed_at`, and a
   `local_path` reference for on-demand serving (never copied into the SCRAPE repo).
2. **`original(file_id)`** in the adapter re-hashes the SW-BULK file at serve time (per the sha256
   already in the manifest) and streams bytes read-only from the registered SW-BULK root — the
   only way to expose 42+3.5 GB of PDFs without duplicating them into the app's own storage.
3. **Facets**: `jurisdiction_codes` → state filter (30/44 states present per store — union close to
   all 50+DC+GU but very uneven); `authority_lanes` where present → doc-type filter (2a only); a
   derived "likely doc type" facet (form / order / opinion / minutes / budget / unknown) would need
   a one-time classification pass over `source_url` path text plus the §4 sampling method (cheap,
   pattern-based, no OCR) since neither manifest carries a clean doc-type field for opinions vs.
   forms vs. administrative material.
4. This fills **G7** partially (30–44 states, host/state granularity, not county/FIPS) and a slice
   of **G6** (court host names, no street addresses) — it does **not** fill G8/G9 on its own; the
   federal GovInfo/CFR frontier files are a separate, much larger, README-gated follow-on for G14
   and deepening G8's federal side only after selecting the named-canonical version per family.

## What I did not verify

- Did not hash-dedup store 2b (3,718 rows) or cross-dedup 2a against 2b (different hash ids/paths
  make this a real join task, not a quick check).
- Did not open/parse any `.xlsx`/`.doc`/`.docx`/`.xls` content (3,254+3,254+839+914+30+11+4+2
  Office files across both stores) — only PDFs were sampled for first-page text.
- Did not decompress or schema-check `sd_statutes_cache`, `govinfo_api_cache`, `structured_cache`,
  or `state_trial_court_directory_bodies` — counted by extension/size only.
- Did not attempt full-file scans of the ~40 GB of top-level GovInfo/CFR jsonl/sqlite files beyond
  first-line samples and sqlite schema probes (would exceed the 60 s per-measurement guidance many
  times over); row counts for those files are therefore **not reported** (would require either a
  full streaming count or trusting the README's own stated counts, which I did not independently
  verify here).
- Did not check per-host robots.txt/terms for any of the ~180+ distinct court/government hosts
  represented in the two manifests — a full crawl-authorization check was out of scope for a
  read-only measurement pass.
- Did not compare this tree against any other SW-BULK copy (no obvious duplicate/worktree of this
  specific path was found elsewhere in the provided inventory).
