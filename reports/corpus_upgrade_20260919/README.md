# Corpus and MVP upgrade round (September 19, 2026)

Goal: more accurate sourcing, categories, placement and dates; deeper mass-tort coverage (MDLs,
regulations, agency safety data, coverage gaps); a cleaner interface; and groundwork for a later
export to the external litigation platform. Live at http://127.0.0.1:8769/ (server PID recorded in
`delivery/archive-directory/server.json`; restart only with `restart.ps1` or `start_server.ps1` here).

## What is live

| Area | Data layer | Counts (as published by the layer) |
|---|---|---|
| Documents, Laws & rules, Explore | `sources/record_facets_20260919` (derived-facet sidecar over all 58,310 directory records) | "Other saved resources" 30,432 → 21 records; statutes 7,426 → 15,812; rules 1,163 → 2,653; constitutions 1 → 1,946; regulations 233 → 649; judge material separated (22,597). Review states, file types, jurisdiction level, typed dates, 4,618 repaired display titles, 150 invalid captures (parked/shell/empty) hidden by default, 4,919 wrong county joins listed |
| MDLs & mass torts | `sources/jpml_mdl_20260919` (JPML pending-MDL reports as of 2026-09-01) | 166 pending MDLs, 206,182 actions pending, 716,121 total, 50 transferee districts; 164 of 176 rows joined to a saved judge profile by exact name + court; 18 CourtListener master dockets cross-checked; every count labelled with its report date |
| Regulations | `sources/federal_regulations_20260919` | 12,622 CFR sections indexed (5,562 in the mass-tort slice of Titles 16/21/40/49); full GPO Title 21 text (8,415 sections) beside the Open US Law publisher text; 6,702 eCFR version rows; 2,259 Federal Register documents; 316 agencies. Amendment, publication, effective and snapshot dates are separate fields |
| Agencies & safety data | `sources/agency_safety_20260919` | 12 datasets, 243,682 records: FDA drug/device/food enforcement, Drugs@FDA, PMA, device classification, CRLs, shortages, Orange Book, FDA warning-letter and recall exports, local CPSC file (provenance unknown); 13 original bulk files served as verified bytes |
| Coverage & gaps | `sources/law_tier_20260919` | 56 jurisdictions; 10,013 unreviewed official law records classified (statute body 4,899, hub/index 1,085, navigation 508, notice 957, court rule body 449, constitution body 625, form 204, other 1,286); 36,086 Open US Law court-rule rows typed; 17,942 topic candidates across 13 mass-tort topics; 28 venues; 1,073 unsaved Trellis county profiles |
| State legal resources | `sources/doj_state_resource_map_20260919` | 56 DOJ state/territory pages from saved captures, 3,201 links in their published sections, 13 circuits; joined to the source directory by exact or normalized URL |
| Source directory | `source_directory.py` + `sources/source_archive_links_20260919` | 5 new reference-type filters (research task, file type, layer, publisher type, access requirement); 554 references linked to already-saved records; link to the DOJ state directory |
| Records | `app.js` | Stable deep link `#record/<id>` with Copy link / Copy citation; saved dates now shown for the 16,454 focused records |
| Sidebar | `index.html` + `areas.js` | 9 visible entries; unpublished areas (Settlements, Courts, Statistics, Counsel) stay hidden until their data layer passes validation; secondary pages live under "Library & coverage" |

`/api/supplements` reports every data layer's validation envelope and re-verifies uniform envelopes'
file hashes live; area pages show a status card instead of inventing content when a layer is not ready.

## Round 3 (September 19, later): four hubs, state grid, remaining layers

- **Navigation:** the sidebar is four hubs (Map & places, Law & regulation, Courts & litigation, Library). A tab bar under the
  top bar lists the hub's pages; a page whose data layer is not validated is not listed. `HUBS` in `app.js` is the single map.
- **Map & places:** clickable US state grid on the home page (four metrics from the coverage layer), `#state/<USPS>` pages
  (law by family and source tier, gap flags, topic candidates, every county as a chip shaded by saved local resources,
  mass-tort venues, quick links to that state's laws, judges, sources and DOJ resources).
- **Density and filters:** compact spacing, auto-fit aligned filter grids, sub-category filter and saved-date presets on
  documents, FJC status / role / appointing-president filters on judges.
- **Judges:** `sources/judge_structured_20260919` (10,669 overlay rows; 4,074 with FJC appointments and a status dated
  2026-09-14; 3,701 bridged to CourtListener by native ids only). Profiles show evidence chips and an FJC appointments table.
- **Generic areas** (`/api/area/<name>`, one renderer in `areas.js`): Settlements 861 rows (deadline state computed against
  2026-09-19; 15 keyword-flagged mass-tort rows; 35 saved pages), Courts 5,413 rows (3,361 CourtListener courts, 1,996 KY/TX
  county courts, 176 logos, pending MDL counts), Counsel & firms 2,434 firms / 4,433 attorney rows / 295 parties from six MDL
  master dockets (full records for MDL 2666 only; party names withheld above 1,000 per docket).
- **Firecrawl gap-fill:** `sources/gap_fill_acquisition_20260919`: 40 captures in 18 states for 37 credits (balance 3,678);
  54 URLs skipped at robots/403 barriers and 5 rejected as shells, all in `gaps.json`. Sources with saved content: 32 -> 72.
- **Pending:** court statistics (93 fetched AO/CJRA files) was still building at hand-off; its tab appears when it validates.
- `verify_round2.py`: 31 live checks over 40 requests passed. Supplement readiness is cached for 45 s and warmed at start.

Not done / needs a decision: SEC EDGAR (declared contact required; Firecrawl was not used to route around it), courthouse
street addresses (no local source records them), real mass-tort settlement documents (administrator sites answer 403),
attorney paging for the five name-only MDLs (connector rejected typed arguments this session).

## Round 4 (September 19, last): three hubs, aliases, judge evidence, gap backfill

Supersedes the Round 3 notes above where they differ.

- **Navigation:** three hubs (Map & places, Law & regulation, Courts & litigation). The Library hub is retired: `#collections`
  redirects to `#mdls`; curated collections are linked from MDL 3080, Settlements and Courts; `#datasets` and `#library` are footer
  links. The US map tab is only heading + search + state grid.
- **Judge aliases** (`sources/judge_aliases_20260919`): 5 printed-name aliases accepted only where a CourtListener assigned-judge
  person id equals the FJC jid bridge (Rodgers, Milazzo, Phillips, Garaufis, Cote). 4 left unresolved with reasons (Wolson, Bailey,
  Shelby, Singhal). MDL registry: 162 of 166 MDLs with a resolved judge.
- **Judge evidence** (`sources/judge_evidence_20260919`, `profile.evidence`): 3,983 entities gain a block; CJRA counts on 1,010
  judges (3,028 of 6,329 rows attached by exact name + court; 3,301 unresolved, never guessed); saved-dataset assignments;
  CourtListener education and positions by native person id only.
- **Counsel & firms:** 2,213 firm rows (701 names cleaned of bar-admission notes / address lines, 53 withheld), 4,432 attorney
  rows, 57 full attorney records. Still partial: five MDLs are name-only.
- **Settlements:** 869 rows = 848 aggregator + 13 saved pages + 8 MDL docket phrase-search rows (92 docket entries, 55
  settlement-specific; MDL 2738 and 3060 labelled "no settlement-specific entry found"). No agreement, order or claim form was opened.
- **Trellis county retry:** 29 Firecrawl credits, 0 accepted captures (known 404s or already recovered elsewhere). Closed; a guard
  now blocks retries of unchanged failures. Balance 3,649.
- **Court statistics:** published (92 tables; 6,329 CJRA rows).
- `verify_round2.py`: 32 live checks over 42 requests passed after the final restart.

Open minor review notes: alias given-name contradiction guard; designation path court; fold 10 docket receipts into MDL `cl_links`;
per-token alias + text matching; "verbatim" wording on receipts; judge-evidence acronym casing, duplicate CJRA fact label,
U+FFFD in 10 job titles, 'Unassigned' label double count.

## Verification

- `verify_round2.py` → `round2_verification.json`: 26 live checks over 32 requests (static files match disk,
  derived categories, file-type/review/date filters, validity gating, federal link-only count 591, explore/listing
  agreement, MDL list/detail/judge link/original bytes, regulations texts, bad inputs → 404, main corpus untouched).
- `verify_scaffold.py` → `scaffold_verification.json`: 14 checks (supplements route, source filters, saved dates).
- Offline suites (all green): facets adapter 14 + build 9, facet wiring 5, explore 10, navigation 5, MDL adapter 17 + build 14,
  regulations adapter 15 + build 10, agency adapter 13 + build 16, coverage adapter 15 + classify 13, DOJ adapter 16,
  supplements 6, dates 8, source directory 16, capture pilot 15, source captures 22, archive links 6.
- Browser QA: desktop and 390 px on Documents, Regulations, Agencies, Coverage, Resources, MDLs; no overflow, no console
  errors from the new pages.

## What was not done (partial on disk, no data claims made)

- `sources/settlements_20260919`: classifier (16 tests) and 234 captured administrator pages exist; no settlement records,
  document registry or adapter yet. The 848 existing settlement references are a consumer aggregator feed with no
  mass-tort records and a licence conflict; real mass-tort settlements need court-side sources.
- `sources/federal_court_statistics_20260919`: 93 official AO/CJRA files fetched with receipts; no tables parsed, no adapter.
- `sources/court_spine_20260919`, `judge_structured_20260919`, `trellis_coverage_20260919` (30 free coverage responses saved),
  `mdl_counsel_20260919`, `canonical_ids_20260919`: scaffolding only.
- Facets fold in law-tier labels; court ids / county geoids / Seeger document subtypes from the court spine are still null.

## Decisions for the user

- SEC EDGAR fair-access needs a declared organisation + contact in the User-Agent; nothing was sent.
- Trellis judge tools are blocked by the account's view limit until 2027-01-01; only free coverage calls were used.
- FindLaw's terms prohibit scraping; it stays reference-only.
- openFDA bulk files were fetched before `download.open.fda.gov` robots.txt (HTTP 403) was treated as a barrier;
  the deviation is recorded in `sources/agency_safety_20260919/gaps.json` for your decision.
- The settlements feed licence conflict and the verdict-index reuse prohibition need a human decision before any export.

## Cost note

The first 14-agent build fan-out hit the account session limit and was stopped; round 2 finished the DOJ, agency,
law-tier and regulations layers from partial work, and three tightly scoped agents built the facets, MDL and
regulations-adapter layers. Remaining layers should be built one at a time, each behind its own validation gate.
