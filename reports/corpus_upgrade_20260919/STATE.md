# STATE CHECKPOINT (2026-09-19, after round 3) — read this first after any context reset

Project: `C:/Users/firas/Downloads/SCRAPE`. App: `delivery/archive-directory` (stdlib `server.py --serve`, port 8769, vanilla
`app.js` + `areas.js` + `styles.css`, no build). Agent rules: `reports/corpus_upgrade_20260919/BRIEF.md`.

## Operate
- Python: `C:/Users/firas/AppData/Local/Programs/Python/Python311/python.exe`. Bash guard blocks `$VAR`, `$(...)`, backticks,
  `python -c`; use quoted heredocs, absolute paths, `python -m unittest discover -s <abs dir> -p <pattern>`. PowerShell tool is fine.
  Guard needs `jq` on PATH (copied into the Python311 folder).
- Server dies with its launcher session. Start if down: `reports/corpus_upgrade_20260919/start_server.ps1`. Deploy Python changes:
  `reports/corpus_upgrade_20260919/restart.ps1`. Static files (js/css/html) are read per request: no restart needed.
- Live checks: `reports/corpus_upgrade_20260919/verify_round2.py` (31 checks) and `verify_scaffold.py` (14 checks).
- Never rebuild `directory.sqlite3`, `catalog/documents.sqlite3`, the Open US Law index or the focused publication. New data =
  hash-gated supplement under `sources/<name>_<date>/` (uniform `validation.json`) + fail-closed adapter in the app folder.
- User is cost-sensitive: at most ~3 concurrent agents, tight scopes, resume from disk. A 14-agent fan-out once hit the session limit.

## UI structure (current)
- Sidebar = 3 hubs (`HUBS` in `app.js`): Map & places (US map `#overview`, Counties, Coverage & gaps, State resources);
  Law & regulation (Laws & rules, Regulations, Agencies & safety, Sources, All documents [+ scope switch to `#federal`]);
  Courts & litigation (Judges, MDLs, Courts, Counsel & firms, Court statistics, Settlements). Tab bar `#hub-tabs`; a tab with a
  supplement id shows only when `/api/supplements` reports it ready (cached 45 s, background refresh — needs the pending restart).
- Library hub removed: `#collections` redirects to `#mdls`; `#collection/<id>` pages remain, linked from MDL 3080, Settlements, Courts;
  `#datasets` and `#library` are footer links.
- Home (`#overview`) = heading + search + clickable state tile grid (`renderUsMap` in `areas.js`) -> `#state/<USPS>` pages with county chips.
- Pages render once on `DOMContentLoaded` (app.js last line); `areas.js` registers pages on `window.ARCHIVE_AREAS`.
- Generic listing/detail contract: adapters expose `listing(params)`, `detail(id)`, optional `original(file_id)`; routes
  `/api/area/<settlements|courts|counsel|statistics>`, `/api/area/<name>/item?id=`, `/supplement-files/<name>/<file_id>`; one renderer in `areas.js`.
- Judge profile: evidence chips + FJC appointments table from `judge_structured` overlay (`profile.structured`), MDL block (`profile.mdls`).
  Judge list filters: status, role, president (from overlay facets).

## Validated data layers (all under `sources/`)
record_facets (58,310 rows; derived categories, review state, file type, typed dates, validity) · jpml_mdl (166 pending MDLs as of
2026-09-01; 9 judges unresolved by name) · federal_regulations (12,622 CFR sections; GPO Title 21 text) · agency_safety (243,682
FDA/CPSC records) · law_tier (coverage matrix, 17,942 topic candidates) · doj_state_resource_map (56 pages, 3,201 links) ·
judge_structured (10,669 rows; 4,074 FJC; 3,701 bridged to CourtListener by native ids) · settlements (861 rows; aggregator feed;
35 saved pages; no agreements/orders) · court_spine (5,413 courts, 176 logos) · mdl_counsel (full records only for MDL 2666; five
MDLs name-only) · federal_court_statistics (92 tables; 6,329 CJRA per-judge rows, unlinked to profiles) · gap_fill_acquisition
(40 Firecrawl captures, 37 credits; balance ~3,678) · source_archive_links (554) · trellis_coverage (2,477 of 2,478 listed counties).

## In flight / queued (started 2026-09-19 ~06:30 local)
1. Workflow `judge-alias-resolution` (run `wf_e4099a7c-c42`): resolves M. Casey Rodgers (entity `judge-entity-24222174cb13b7162bfcfcbc`,
   FJC name Margaret Catharine Rodgers) and 8 other JPML names via CourtListener assigned-judge person id -> FJC jid bridge; adds
   `judge_aliases` layer + hook in `judges.py`; rebuilds the MDL registry. After it finishes: restart server, confirm search
   "Casey Rodgers" and MDLs 2885/3140 on her profile.
2. Workflow `gap-backfill`: (a) judge evidence (CJRA rows + SW-BULK assignments + CourtListener education/positions onto profiles),
   (b) counsel paging via CourtListener then (c) settlement orders/agreements from MDL master dockets, (d) retry of 31 failed Trellis
   county captures. Each: build -> independent verify -> repair. Wire any new adapter into `server.py`/`areas.js` afterwards.

## Decisions waiting on the user
SEC EDGAR needs a declared User-Agent contact (nothing sent) · settlements feed licence conflict · party names withheld above 1,000
per docket (`PARTY_NAME_PUBLISH_LIMIT` in `sources/mdl_counsel_20260919/build.py`) · resuming the county-litigation Firecrawl collector
(2,437 URLs pending; owned by the user's other session) · two stale `test_mvp.py` expectations (10,669 judges / 14 portraits).

## Update (2026-09-19, later)
- DONE: judge alias layer `sources/judge_aliases_20260919` (5 aliases by CourtListener-person == FJC-jid bridge: Rodgers, Milazzo,
  Phillips, Garaufis, Cote; 4 unresolved with reasons: Wolson, Bailey, Shelby, Singhal). `judges.py` searches aliases; profiles show
  "Also printed as"; MDL registry rebuilt (162 MDLs with a resolved judge, 4 without). Reviewer accepted with 5 minor notes to fix later:
  (1) add a given-name contradiction guard to alias acceptance; (2) designation path should publish the entity's FJC court, not the
  transferee court; (3) fold the 10 new docket receipts into MDL `cl_links`; (4) alias + text tokens should combine per token, not
  per whole query; (5) receipts wording says "verbatim" but responses were re-typed from the connector output.
- Server restarted (supplement cache now refreshes in the background). `verify_round2.py`: 32 checks passed.
- Pre-wired (inactive until the layer validates): `profile.evidence` from `judge_evidence.evidence_for` and `judgeEvidenceSection` in `areas.js`.
- STILL RUNNING: workflow `gap-backfill` (run `wf_691830fc-e37`): judge evidence, counsel paging, settlement court documents, Trellis retries.
  When it finishes: restart the server (new Python adapters), check `/api/judge` carries `evidence`, check Counsel/Settlements counts, rerun verify.

## Update (2026-09-19, gap-backfill finished; server restarted; verify_round2.py 32/32)
- judge_evidence_20260919 LIVE on profiles (`profile.evidence`): 3,983 entities gain a block; CJRA counts attached to 1,010 judges
  (3,028 of 6,329 rows; 3,301 unresolved, never guessed; 3 two-district judges shown per court); SW-BULK assignments, CourtListener
  education/positions via cl_person_id only. Minor review notes open: acronym casing in detail text, duplicate fact label, U+FFFD in
  10 job titles, 'Unassigned' label double count.
- mdl_counsel: connector paging largely failed again (57 full attorney records, 4,432 rows, 2,213 firm rows after removing
  bar-admission notes and address lines from firm names; 53 rejected texts logged by reason). Still partial for five MDLs.
- settlements: 869 rows = 848 aggregator + 13 saved pages + 8 'settlement-phrase docket search' rows (92 docket entries; 55
  settlement-specific; MDL 2738 and 3060 explicitly 'no settlement-specific entry found'). Docket-entry evidence only; no document opened.
- Trellis retry: 29 credits spent, 0 gained (URLs were known 404s or already recovered by the other session). CLOSED; do not re-queue.
  Guard added. Firecrawl balance 3,649. Optional 2-row county-name crosswalk offered to the coverage layer owner.

## Update (2026-09-19 ~15:30Z) — Round 5: local bulk corpora (SW-BULK, returnedfiles)
- User pointed at local corpora; scouting + verified plan: `reports/local_corpus_20260919/` (inventory.json, understand/*.md,
  INTEGRATION_PLAN.md with two Verification sections, BUILD_CONTRACT.md). Model policy from the user: Sonnet for builders/readers,
  Opus for review/synthesis/wiring, Fable only orchestrates.
- RUNNING: workflow `local-corpus-build` (run `wf_b41790ff-14c`): slices crosswalk -> documents/activity/appearances/inventory;
  courtdocs (index over 51k staged court files, originals served in place), stateproc (NJ MCL + CA JCCP), disclosures
  (CourtListener financial disclosures, codes only), sdstatutes, seeds (county seed packets from the 19,245-URL state map; NOT
  ingested). Then one Opus wiring pass (server.py/areas.js/app.js; two new tabs: State mass torts, Court documents). AFTER IT
  FINISHES: restart.ps1, run verify_round2.py, browser-check MDL page / judge profile / state page, then review + ingest seeds.
- SW-BULK/README says private firm work product: every derived layer carries license_ref sw_bulk_private_firm_work_product and
  export_allowed:false; local loopback MVP only. FindLaw (ToS) and topverdict leads (reuse-prohibited) are NOT built: user decision.
- County collector (other session's `sources/county_litigation_firecrawl_20260919`): it was crashing at checkpoint time
  ("Checkpoint artifact mismatch": one saved HTML file missing). Patched `checkpoint()` to hold out a damaged resource
  (validation.held_artifact_failures) instead of aborting; 14 collector tests pass. Relaunched with launch.ps1 at ~15:20Z
  (PID 34640, 1-hour cap, ~2,230 pending). User authorised heavy Firecrawl use. Relaunch again with launch.ps1 when it exits
  while pending > 0; publication = `sources/county_litigation_20260919/build.py --checkpoint <dir>` + audit + live verify scripts.

## Update (2026-09-19 ~15:50Z) — user: "you are ignoring the URL data" -> second workflow
- RUNNING: workflow `url-directory-and-registry-build` (run `wf_6c7b74c8-1b0`), no wiring phase (returns wiring specs):
  (U) 7 Sonnet normalisers -> Opus merge into `sources/url_directory_20260919/url_directory.sqlite3` (~500k URLs: state/federal
  agency, deep crawl, DOJ sweep, toxicology + source catalogs, court maps + _pdf_directory, raw Firecrawl map/search outputs,
  returnedfiles state-code/court folders), adapter `url_directory.py`, `frontier_documents.jsonl` / `frontier_pages.jsonl`
  (not-yet-saved official documents/pages ranked for the next download run). Shared helper I wrote: `urlnorm.py`.
  (P) `sources/uscourts_pages_20260919` (1,404 saved uscourts.gov pages split per URL) + adapter `uscourts_pages.py`.
  (R) Opus scout of `SW-BULK/publiclaw_registry_v2/current` (v22 knowledge graphs, never examined) -> up to 6 `plr_*` layers.
- AFTER BOTH WORKFLOWS: wiring for these (URL directory = main page of Law & regulation > Sources with layer/state/agency/doc
  filters; blocks on state, agency, court and regulation pages) must run AFTER `local-corpus-build`'s wiring agent finishes
  (same files). Then restart + verify. Then acquisition: direct-download the ranked frontier_documents (robots + host pacing via
  the existing crawler; Firecrawl for HTML pages), county seeds ingest, returnedfiles state-code folders not yet in the MVP.

## Update (2026-09-19 ~16:40Z) — user: "too slow, do tasks yourself". Orchestrator now builds directly.
- STOPPED workflow `url-directory-and-registry-build` (wf_6c7b74c8-1b0); reused its two finished normalised lists.
- BUILT + LIVE (by me): `sources/url_directory_20260919` (build.py + urlnorm.py; 548,765 list rows -> 487,499 distinct URLs,
  478,975 without noise, 10,708 hosts, 142,534 documents, 7,474 already saved; frontier_documents.jsonl 128,680 and
  frontier_pages.jsonl 300,774 = ranked not-yet-saved official URLs) + adapter `url_directory.py` (tab Law & regulation >
  URL directory, route `#urls`, `/api/area/urls`, `/api/urls/block?state|agency|court`, state-page block).
  `sources/uscourts_pages_20260919` (1,404 saved uscourts.gov pages, 0 held) + `uscourts_pages.py` (tab Courts & litigation >
  U.S. Courts pages, `#uscourts`). FTS5 snippet() is unusably slow on multi-MB texts: excerpt uses instr/substr instead.
- WIRED (by me, script `reports/local_corpus_20260919/wire_round5b.py`): agent-built `court_documents` (50,940 files, originals
  served from SW-BULK staging after sha check; tab Court documents), `state_proceedings` (1,432: NJ MCL 40 + CA JCCP 1,392; tab
  State mass torts; MDL page block; state page block), `judge_disclosures` (21,832 filings; judge profile section
  `profile.disclosures`; route `#judge-disclosures`). `/api/blocks?state=|court=`. verify_round2.py still 32/32.
- STILL RUNNING: workflow `local-corpus-build` (wf_b41790ff-14c): MDL documents / activity / appearances / inventory + sd_statutes,
  then reviews. Its final Opus "wire" agent would duplicate the wiring above: when those four slices validate, STOP the workflow
  and wire them by hand (MDL page blocks via for_mdl; routes mdl-documents, mdl-activity, mdl-appearances, mdl-cases).
- County collector: 2,388 resources / 559 counties at 16:06Z (was 661 / 268), 251 pending. When it exits: publish with
  `sources/county_litigation_20260919/build.py --checkpoint <latest>` + audit + live verify; then ingest
  `sources/county_seed_packets_20260919/seeds_county.jsonl` (80 seeds, 52 new counties) and relaunch.
- NOT DONE: `SW-BULK/publiclaw_registry_v2/current` (v22 graphs) never examined; returnedfiles state-code folders (IN, AR, MO, NV,
  OK, PA, DC, IL, KY, MD) not checked against the MVP; download run over frontier_documents not started.

## Update (2026-09-19 ~17:40Z) — more direct builds; verify_round2.py now 43 checks, all passing
- BUILT + LIVE (by me): `sources/federal_register_history_20260919` from SW-BULK publiclaw staging document identities:
  1,006,725 Federal Register documents 1994-01-03..2026-08-20 (201,957 cite a CFR part; 9,322 distinct parts; 472 agencies;
  118,666 with RIN). Adapter `federal_register_history.py` (tab Law & regulation > Federal Register, `#federal-register`,
  filters type/agency/CFR title+part/year/text; `for_cfr` feeds `fr_history` on `/api/regulation` = rule history per CFR part).
  NOTE: `publiclaw_registry_v2/registry_v2.sqlite` (19 GB canonical graph) is NOT on disk; its inputs are in `staging/`.
  Still unused there: plaw_* graphs (Public Law <-> U.S. Code), cfr_identifier_normalization, state_trial_court_acquisition_graph
  (nodes/edges 25 MB gz), ecfr_hierarchy (267 MB), federal_register_docket_entities (609k dockets).
- WIRED (scripts wire_round5c.py / wire_round5d.py): MDL page blocks appearances / docket_documents / docket_activity / cases via
  lazy `for_mdl` (layers appear by themselves when their adapter lands; no restart needed for a new adapter module), routes
  mdl-cases (4,159 live), mdl-appearances (878 live), mdl-documents + mdl-activity (adapters still being built by the workflow),
  sd-statutes (71 titles / 45,296 sections; button on #state/SD). Do not display `fraction_of_jpml_actions_pending` (a rate).
- County collector run ended cleanly: 2,508 resources / 559 counties; Firecrawl credits 3,471 -> 1,633 (1,838 used); 117 pending.
  Publication: `sources/county_litigation_20260919/build.py --checkpoint .../20260919T161021224866Z` needs Python311 (bs4), and I
  patched it to hold 5 originals that have no extracted text. RUNNING in background at the time of writing; afterwards run
  scripts/audit_county_litigation_20260919.py + scripts/verify_county_litigation_live_20260919.py.
- Workflow `local-corpus-build` still running (documents + activity builders, reviews). STOP it before its final "wire" agent
  starts (wiring is already done by hand); keep its review findings.

## Update (2026-09-19 ~17:40Z)
- County publication DONE: `sources/county_litigation_20260919` now 3,378 resources / 706 counties (was 976 / 470); audit passed
  (0 errors, 155 text-gap warnings); live verify passed. 5 originals without extracted text are held (patch in build.py).
- Ingested `sources/county_seed_packets_20260919/seeds_county.jsonl` (501 seeds, 213 counties, 192 with no coverage before; the
  reviewer's inverted-priority blocker was repaired first) and relaunched the collector at ~17:25Z (launch.ps1, 1-hour cap,
  Firecrawl balance was 1,633). When it exits: publish its latest checkpoint the same way (Python311 interpreter).
  `seeds_statewide.jsonl` (9,503) is NOT ingested: statewide judiciary pages, decide separately.
- NEW download run (no Firecrawl): `corpus/agency_science_documents_20260919` (prepare.py -> config.json + seeds.jsonl, shared
  `pipeline/corpus_crawler.py`, robots + 2 s host pacing, links not followed, 20 GB free-disk guard): 13,160 unsaved documents
  from ATSDR, CPSC, NHTSA, NTP, EPA, JPML, CMS, CDC, FDA (OSHA paused: robots disallow; SEC excluded: needs declared contact).
  Hidden process, 4-hour cap, receipt `run_launch.json`. Status: `python pipeline/corpus_crawler.py --root
  corpus/agency_science_documents_20260919 status`. TODO when volume exists: supplement + adapter (Agencies hub) over its
  corpus.sqlite3 export, and re-run `sources/url_directory_20260919/build.py` so saved_status picks the new files up.
- Workflow `local-corpus-finish` (wf_79d1d8db-b35) running: repairs (disclosures, sd_statutes), docket-activity adapter, Opus
  reviews of the four MDL layers. No wiring step. The old workflow task w5vp9x56z is killed.

## Update (2026-09-19 ~18:00Z) — all ten local-corpus slices validated, reviewed, repaired and wired; verify_round2.py 43/43
- Workflow `local-corpus-finish` done. Opus reviews found privacy blockers (natural-person plaintiff names in MDL docket captions
  and docket text; a sample/publisher fraction shown as a fact) in documents / activity / inventory / appearances: all fixed by
  the builders (captions of individual member cases now read "docket number (court)"; `fraction_of_jpml_actions_pending` removed;
  appearances distinguish direct vs member-edge linkage). Disclosures (9 fixes) and SD statutes (8 fixes) repaired.
  Known residual: the activity layer's "X v. Y" redaction is a conservative regex, not guaranteed 100% recall.
- UI: `mdlLayerBlock` in areas.js (script wire_round5e.py) renders type chips -> filtered listing (`#mdl-documents?mdl=N&doc_type=…`,
  `#mdl-activity?mdl=N&entry_type=…`), firm rows, party counts (individuals counted, never named); server adds `mdl_number` to
  every MDL block. Disclosure holdings are objects now ({description, inferred, redacted}); renderer handles both.
- Agents restarted the server once outside restart.ps1 (file lock during a rebuild); state is healthy, restart.ps1 used since.
- Download run `corpus/agency_science_documents_20260919`: 252 files in the first 20 min; hosts paused by the crawler and NOT
  retried: www.osha.gov (robots), www.epa.gov, www.cpsc.gov, stacks.cdc.gov (HTTP 403). ATSDR / NHTSA / NTP / JPML / CMS continue.
- County collector run 2 (PID 38528, launched 17:22Z): 2,788 records / 617 counties at 17:40Z, then quiet (7 pending, 10 in
  flight; likely pacing/checkpoint hashing). Hard cap 18:23Z. NEXT: publish latest checkpoint with Python311
  (`sources/county_litigation_20260919/build.py --checkpoint <latest.json path>`), audit, live verify.
- STILL TODO: supplement + adapter over the downloaded agency/science documents; rebuild url_directory afterwards;
  `seeds_statewide.jsonl` decision; returnedfiles state-code folders vs MVP; plaw/US Code graphs and state trial court graph
  from publiclaw staging; court-document title extraction (5,730 of 41,874 PDFs done; resumable `extract_titles.py`).

## Update (2026-09-19 ~19:20Z) — after a machine reboot at 18:30Z (killed server, collector, downloader)
- Server restarted with start_server.ps1 (restart.ps1 refuses when the recorded PID belongs to another process after a reboot).
- Download run `corpus/agency_science_documents_20260919` resumed (hidden, 4 h cap; `run_launch.json`). NEW LIVE layer over it:
  `sources/agency_science_documents_20260919` (build.py re-runnable; 930 files at build: NHTSA 289+, NTP 158, JPML 147, ATSDR 137,
  CDC, EPA, CMS, FDA; full-text search; original served after sha check) + adapter `agency_science_documents.py`, tab
  Law & regulation > Agency documents (`#agency-documents`). Re-run build.py to pick up new downloads (no restart needed).
- NEW LIVE layer `sources/saved_web_pages_20260919` + `saved_pages.py` (tab Law & regulation > Saved pages, `#saved-pages`, state
  page block via /api/blocks): 15,557 pages from returnedfiles capture folders (justice.gov wide crawl 9,995; Illinois circuit
  courts 3,497; Montana Code 499; D.C. Courts 499; Nevada Legislature 470; Philadelphia + PA courts 592 incl. the Complex
  Litigation Center mass-tort program pages). Excluded by design: codes.findlaw.com captures (ARKcodelaw folder; terms), 195
  Oklahoma docket/case pages and search.txcourts.gov (litigant names). Rebuild in progress to add the second capture format
  (illinoiscourts_highvalue 2,462 docs, mdoutputs).
- County publication of checkpoint 20260919T173648625646Z crashed twice on a malformed href ("[site:url-brief]"): patched
  `sources/county_litigation_20260919/build.py` (safe_target) and `delivery/archive-directory/readable.py` (skip malformed links).
  Third run in progress. Collector itself is stopped (7 pending, 10 stale in-flight); `seeds_statewide.jsonl` still not ingested.
- verify_round2.py: 49 checks passing before the saved-pages layer; ('saved-pages', 15000) added to the generic-area checks.
- STILL TODO: 2026 Indiana Code (returnedfiles/2026-Indiana-Code: 37 HTML titles 181 MB + constitution/acts PDFs) as a statutes
  layer; kentucky_county_snapshots (120 county JSONs with clerks/judges/hours; likely already in county_registry_integration);
  plaw/US Code graphs + state trial court graph from publiclaw staging; court-document title extraction; url_directory rebuild.

## Update (2026-09-19 ~20:00Z) — verify_round2.py 51/51
- Saved pages rebuilt: 19,066 pages / 35 hosts (adds Illinois Courts high-value 2,407 incl. annual/statistical reports, and 1,106
  Kentucky/other court pages; titles cleaned). Searches in saved_pages.py and indiana_code.py ignore common stop words.
- NEW LIVE layer `sources/indiana_code_2026_20260919` + `indiana_code.py` (`#indiana-code`, button on #state/IN): 83,148 sections
  (76,333 with text, 6,438 repealed, 377 expired as printed), 37 titles / 1,086 articles / 8,975 chapters, split only on the
  edition's own markup; citation search ("34-20-2-1") and full text. Local PDFs (2026 Acts, Noncode Statutes, Constitution) are
  listed in validation.json as not indexed.
- County publication (third attempt, after the malformed-href fixes) still running as background task bpnvhjgcq; afterwards run
  scripts/audit_county_litigation_20260919.py and scripts/verify_county_litigation_live_20260919.py.
- Download run alive since 18:37Z (PID in corpus/agency_science_documents_20260919/run_launch.json); rebuild
  sources/agency_science_documents_20260919/build.py periodically to publish new files.

## Update (2026-09-19 ~20:40Z) — user priorities: county rules/filing coverage 80-90%, UI cleanup + fewer tabs, PLAW/USC, PDF titles, finish fast
- MEASURED county coverage before this round: 3,144 counties; 759 (24%) with any saved resource; only 80 (2%) with a county-assigned
  rules/forms/filing/orders/fees resource; 1,232 published resources have no county. County publication now 3,640 resources / 759 counties.
- Firecrawl balance 1,376 (checked with new `scripts/fc_capture.py credits`; tool also does bounded `scrape` with receipts and `search`;
  basic proxy only, robots respected, no retries). Hard budget: no purchases.
- RUNNING workflow `county-filing-sources-and-polish` (wf_235d0f9a-e82): 10 Sonnet state-cluster agents (all 50 states + DC) record OFFICIAL
  state-judiciary sources (local rules by circuit/district/county, statewide rules, forms, e-filing, fees, standing orders, directories) into
  `sources/county_filing_sources_20260919/states/<USPS>.jsonl` with captures under `captures/<USPS>/` (cap 110 captures per agent), each
  followed by an Opus verifier that deletes rows not found in their capture. Same workflow: Opus UI agent (owns app.js/areas.js/styles.css/
  index.html: tab merge via segmented switches -> Law hub 5 tabs, Litigation hub 7 tabs; disclaimers collapsed to "About this data";
  title cleaner; max 2 badges; county/state filing sections) and Sonnet Public Law / U.S. Code agent (`sources/public_law_uscode_20260919`,
  adapter `public_laws.py`, route `public-laws` already in GENERIC_AREAS).
- MINE (done, Python only): `sources/county_filing_sources_20260919/build.py` (merges state rows + county-assigned saved resources; rejects any
  official row whose URL is not in its capture, commercial hosts, non-exact county names) and adapter `county_filing.py`; server routes
  `/api/county-filing?fips=`, `/api/county-filing/state?state=`, `/api/county-filing/coverage` (wire_round6a.py). AFTER THE WORKFLOW: run
  build.py, check percent_with_local_rules / percent_with_any, restart, verify, browser-check county + state pages and the merged tabs.
- Background: court-document title extraction (3 h cap, resumable; then rerun court_document_library build.py), url_directory rebuild
  (now counts agency downloads as saved), agency/science download run (4 h cap; rerun its build.py to publish new files).

## Update (2026-09-19 ~20:20Z local-clock 15:20) — front-end round 7 (user: pills are amateur; wants real map, dashboards, better judge pages)
- First UI agent finished (tabs with segments, `dataNote`/`footnote` disclosures, `cleanTitle`, max-2 badges, county filing section).
  I then applied `reports/local_corpus_20260919/wire_round7_frontend.py` (backups `*.pre_round7.bak` beside the four files):
  * segment pills REMOVED; `applyWorkbench()` in app.js (MutationObserver on #main) re-parents each page into `.workbench` =
    left `.rail` (Collection list from `window.ACTIVE_SEGMENTS` with hints + the page's own `form.filters` stacked) + results.
  * Laws & rules collections: State & federal law (#laws) | Full-text state codes (#state-codes, new combined adapter
    `state_codes.py`: state filter IN/SD, ids "<USPS>:<id>") | Public Laws & U.S. Code (#public-laws). Indiana/SD tabs gone.
  * REAL MAP: `usmap.js` + `assets/us-counties-albers-10m.json` (us-atlas 3.0.1, ISC, jsDelivr; SOURCE.txt beside it; own TopoJSON
    decoder, plain SVG). Home: states clickable, county borders toggle, shading metrics incl. % of counties with a rules/filing
    source. State page: county map shaded by filing coverage (`/api/county-filing/state-counties`), click -> county page.
  * CSP is `style-src 'self'`: injected <style> blocks are BLOCKED. usmap styles live in styles.css. The two module agents were told
    to inject styles -> after they finish, MOVE their CSS text into styles.css (or the modules render unstyled).
- URL directory rebuilt with `content_type` facet (131k URLs typed: Rules 17k, Regulatory text 16k, Opinions 15k, Statistics 15k,
  Enforcement 9.9k, Forms 6.4k, ...) + adapter filters `content`, `level`.
- County filing interim merge (39 states): 66.3% of counties with any official rules/filing source, 30.4% with local rules.
  My merge script is `merge_county_sources.py` (an agent overwrote `build.py` in that folder with its own helper: ignore build.py).
- RUNNING: workflow wf_235d0f9a-e82 (state clusters + verifiers + PLAW; PLAW layer went ready: 2,155 public laws) and workflow
  wf_0ac214fd-df4 (Opus: `statsviz.js` court-statistics dashboard -> hook `registry.statistics.page = StatsViz.page`; `judgeui.js`
  -> hooks JudgeUI.profile/person/card in app.js). index.html already loads both files; server serves a stub until they exist.
- TODO after agents: hooks + CSS move, rerun merge, restart, verify_round2, browser pass, final report.

## Update (2026-09-19 ~20:50Z) — county coverage result, workbench rail live, verify_round2.py 58/58
- County filing sources FINAL first pass (51 jurisdictions, `merge_county_sources.py`, gate passed): 3,144 counties; 3,042 (96.8%) with
  at least one official rules/filing source; 2,639 (83.9%) with a rules source of any scope (local or statewide) PLUS a filing source;
  1,357 (43.2%) with a LOCAL rules source mapped by an official page. Zero-row states by legitimate barrier: MA, NH (robots disallow),
  MI (courts.michigan.gov robots Disallow: /). Levels: rules_and_filing / statewide_rules_and_filing / rules_only / filing_only / none.
- Firecrawl credits: 612 after the first pass. RUNNING second pass workflow `county-local-rules-second-pass` (wf_11a2a029-168): IL TN NC WI
  OK MO FL AL LA CO IA GA NY VA, 65 captures per agent max, appends to states/<USPS>.jsonl, Opus verifier per cluster. AFTER IT: rerun
  merge_county_sources.py (adapter reloads by file signature; no restart needed), report new percentages.
- Front end: `applyWorkbench()` now adopts late-arriving forms/results (script wire_round7c); rail polish + collections for
  Judges (profiles / historical biographies / disclosures) and All documents (whole library / federal & DOJ) (wire_round7d);
  state-codes page renders without a supplement gate; hooks installed for `window.StatsViz.page` (areas.js) and
  `window.JudgeUI.profile` (app.js) (wire_round7b). STILL TO DO when workflow wf_0ac214fd-df4 finishes: move the injected CSS of
  statsviz.js / judgeui.js into styles.css (CSP style-src 'self'), replace any setAttribute('style')/innerHTML style usage with
  CSSOM, hook JudgeUI.person + JudgeUI.card, browser pass on #statistics, a judge profile, #people/<id>.
- verify_round2.py: 58 checks (adds county filing coverage >= 80%, map geometry 51/3,142, usmap.js, state-codes, public-laws).

## Update (2026-09-19 ~21:20Z) — front-end modules live; verify_round2.py 58/58; no console errors on checked pages
- `statsviz.js` LIVE (hook in areas.js): Court statistics dashboard = 5 KPI tiles, Series/Topic/Period/search controls, Charts|Table toggle
  (hash param view=), 71 bar-chart cards + 3 mini tables + per-court CJRA cards, detail dialog with chart/table. Styles via constructed
  stylesheet (CSP-safe).
- `judgeui.js` LIVE (hooks in app.js via wire_round7e): JudgeUI.profile (identity header, status chip, stat tiles, anchor section nav,
  at-a-glance rail, timeline, disclosures), JudgeUI.person (historical biographies), JudgeUI.card (both lists). ensureStyle now uses a
  constructed stylesheet first (no blocked <style>, no console error).
- Rail: quick-view `.filter-chips` rows move into the rail as an option list ("Profile information"); collections list rebuilds when
  supplement readiness arrives (`renderRailCollections`); `#main > .people-section-nav/.scope-switch/.view-switch` hidden when the rail
  has collections. Judges collections: Judge profiles | Historical biographies | Financial disclosures. All documents: Whole library |
  Federal court & DOJ sources.
- County page first section "Rules, forms and filing sources" confirmed live (Harris County TX). County page takes ~10 s to open
  (`/api/counties?q=<fips>` is slow): candidate for a later fix.
- WAITING: workflow wf_11a2a029-168 (second local-rules pass) -> rerun merge_county_sources.py -> report percentages.

## Update (2026-09-20 ~08:45Z) — rounds 8 and 9; verify_round2.py 83/83
Round 8 (2026-09-19 evening, compact UI + backfill):
- Navigation is three hubs: States & counties (Map | State law | Counties | Coverage | State resources), Federal law & agencies
  (Law & regulations | Agencies | Sources | All documents), Courts & litigation (Judges | MDLs & mass torts | Courts | Counsel & firms).
  Collections sit in the left rail (grouped and dense when more than five). Wiring scripts: reports/local_corpus_20260919/wire_round8*.py.
- State law: `sources/state_code_outline_20260919` (196,529 headings over 2,978,617 provisions) + `law_outline.py` + `lawreader.js`:
  state -> code/title -> chapter -> section, reading layout, previous/next. CA, NY, LA, MD code names expanded.
- New layers from background agents: counsel_directory (2,170 firms / 2,378 attorneys), verdict_settlement_reports (3,312, captions
  redacted), cpsc_injury_data (NEISS 410,201 + SaferProducts 69,333), expert_rulings_scan (2,035), agency_hub + regsui.js
  (19 agency profiles), source_directory_documents (993), agency_science_documents rebuilt (5,659).
- County filing sources after the third (free) pass: 3,144 counties; 96.8% any source; 82.0% rules of any scope + filing;
  54.6% local rules. Blocked: MA, NH, MI, NC. Firecrawl balance ~170 credits; no purchases authorised.
- supplements.py keeps a persistent digest cache: readiness scan 67 s -> 0.2 s. Vendor names are removed from display prose only.
- MACHINE: on 2026-09-19 the Windows kernel non-paged pool reached ~14.7 GB of 15.2 GB (driver leak, no user process), everything
  paged out and looked hung; the machine was rebooted 2026-09-20 01:05 local. Both hidden downloaders are STOPPED
  (agency_science_documents: 6,312 pending; source_directory_documents: ~290 pending incl. 240 NAAG settlement PDFs). Relaunch only
  while watching `\Memory\Pool Nonpaged Bytes`.

Round 9 (2026-09-20, open-source enrichment, done without sub-agents):
- Pinned upstream copies + provenance: `sources/upstream_open_data_20260920` (fetch.py survey/get, fetch_pypi.py, README with licences).
- `citation_reference_flp_20260920` (reporters-db): 1,262 reporters, 373 law citation forms, 798 journals -> #citation-guide (Courts tab).
- `court_reference_flp_20260920` (courts-db + seal-rookery): 2,809 courts (2,504 in the registry by identical court id), 253 seals
  (231 hash-verified, 1 held) -> merged into court registry detail; `/api/court-resolve?q=`.
- `judge_portraits_flp_20260920` (judge-pics): 1,179 federal-government portraits by CourtListener person id; 1,174 biographies and
  1,155 judge profiles now show a portrait (was 43). 68 state/unlicensed portraits held. portraits.free.law answered 429 after 364
  files; the rest came from the repository at its pinned commit.
- `limitation_periods_20260920`: 459 cells (CC BY 4.0 table) + check of 147 PI / wrongful-death / malpractice cells against saved
  statutes: 121 same period, 18 same period in a general section, 4 DIFFER (LA PI, ME wrongful death, MT and NH malpractice),
  9 section not saved (GA/NC withdrawn, WA RCW 4.16.080 and ME 24 s.2902 missing from the snapshot), 1 no wording recognised.
- `law_snapshot_audit_20260920`: publisher's statute completeness per state (50 complete, PA partial, GA + NC withdrawn) in the law browser header.
- `citation_index_20260920` (eyecite): 24,289 saved documents scanned in 31 min (6 workers); 60,591 authorities (50,724 cases,
  9,354 statutes/regulations, 513 journals); 3,064 open saved law text, 555 a saved Federal Register entry, 49 a saved public law;
  9,074 case-shaped strings without a case name excluded. #citation-index, "Cited in N saved documents" in the law reader,
  "Authorities cited" inside saved documents. Re-run `build.py scan` after new text arrives (resumable), then `build.py`.
- Project skills: `.claude/skills/` = statutory-analysis, enhance-prompt, building-chronologies, proposition-checking,
  adversarial-qc (lq-skills, Apache-2.0, unmodified, PROVENANCE.md) + own `legal-archive-api` (how to query this library accurately).
- Reviewed, not used: mayhewsw/legal-linking (no licence; 3.3 GB of scraped opinions), legal-data templates, 68 non-federal portraits.
- Open: SW-BULK FAERS files (205 GB) need a dedicated streaming summary; court-document PDFs (45 GB) have no extracted text, so
  they are not in the citation index; state statute citations are not resolved to saved text yet (only U.S.C./C.F.R.);
  county page still slow to open; decisions pending with the user: FindLaw index, SEC EDGAR contact, 9,503 statewide seeds.

## Update (2026-09-20 ~09:20Z) — machine memory problem diagnosed and fixed (not a driver)
- Full write-up: reports/machine_memory_20260920/README.md; re-check tool: reports/machine_memory_20260920/pooltags.ps1.
- Cause: C:\Users\firas is an accidental git repository; the desktop app's once-a-minute `git ls-files --others --exclude-standard :/`
  walked the whole user profile (~155,000 file operations per second), and ntfs.sys (pool tag NtFC) + filter-manager contexts grew
  ~35 MB/min in non-paged memory until the machine thrashed.
- Fix applied: `/*` appended to C:\Users\firas\.git\info\exclude (backup exclude.bak-20260920). The app's command now takes 0.06 s;
  NtFC growth 0; paging ~100 pages/sec. 3.5 GB already held is only reclaimed by a reboot (then start_server.ps1).
- Owner actions still open: revoke the GitHub token that is embedded in that repository's remote address; decide whether the
  profile-level repository should exist; SCRAPE needs its own `git init` if it is to be versioned.
- The two hidden downloaders can be relaunched now (the memory problem was unrelated to them).

## Update (2026-09-20 ~11:40Z) — round 10: footer pages retired; project pushed to GitHub (code in git, data in releases)
- Footer tabs removed with their data (`wire_round10_footer_tabs.py`): "Data downloads" (#datasets, /api/datasets) and
  "Collection status" (#library, the `datasets` + `live` blocks of /api/summary, `live_jobs()`). Old links open Home. Three tests
  updated. Live verifier still 83/83. Main database not rebuilt.
- SCRAPE is now its own git repository (branch main) -> https://github.com/fshahersw/externalcorpus (PRIVATE; the owner chose
  "make it private, push all" after being told it was public). Repo-local identity = the owner's GitHub no-reply address. Repo-local
  `http.version=HTTP/1.1` because pushes over HTTP/2 failed with a TLS integrity error on this machine.
- Git = code only (~1,075 files, 5 MB): `.gitignore` prunes whole data folders (so `git status` takes 2 s and the desktop app's poll
  cannot start another directory walk), `.gitattributes` = `* -text` (byte-exact checkouts; small files are hash-checked at start-up).
- Data = release assets, written by `tools/push_data.py`, restored by `bootstrap.py` (both standard library; how-to in TRANSFER.md):
  93 units / 274,815 files / 130.1 GB raw = the whole project minus git-tracked files + the 43 GB of court-document originals the
  index names under SW-BULK (restored under `external/`, where `court_documents.py` now looks first). Deterministic tar(.gz) streams
  cut into 128 MB parts; each archive ends with a per-file listing (path, size, mtime_ns, SHA-256); `data_manifest.json` (asset,
  refreshed after every unit) lists units, parts, licence lines. Court documents use release `data-20260920-courtdocs` (1,000-asset limit).
- Verified end to end: fresh clone + `bootstrap.py pull` of two units = 1,269 files byte-identical to the originals, nanosecond
  times restored; `tools/test_transfer_roundtrip.py` (offline, 6 tests) also proves a damaged part is refused.
- Never packaged: .auth (DPAPI credential), devvvv (separate project/repo), .tools, node_modules, __pycache__, logs, locks, -shm.
  `tools/scan_secrets.py git` must print 0 before every code push (it did); the full-tree scan log is in reports/hosting_plan_20260920/.
- NETWORK FAULT on this machine: about 1 upload in 15 dies with `tls: bad record MAC` (and git's `SEC_E_MESSAGE_ALTERED`): bytes are
  being altered between this PC and the internet. TLS refuses them and retries succeed, so nothing damaged is stored, but the
  adapter/driver/router should be looked at by the owner (assistant does not change adapter settings).
- Upload runs hidden (`tools/start_push.ps1`, log `_transfer_scratch/push.log`, resumable). After it ends: rebuild
  `sources/source_directory_documents_20260919`, then `citation_index build.py scan` + `build.py`, run `push_data.py push` again
  (only changed units are re-packaged), commit `data_manifest.json`.
- Owner statement recorded: seeger / SW-BULK folders are the owner's own collections from public sources; the older "private firm
  work product" labels inside validation.json files are unchanged because start-up gates read them (relabel = separate task).
- Credential scan of all 196,990 non-compressed data files (`tools/scan_secrets.py tree`, then `tools/explain_secret_hits.py`): 27 files
  flagged, 84 strings, every one explained and none is the owner's: 29+ URL slugs that begin "sk-" (njcourts.gov opinion URLs,
  docket-vendor case URLs), 14 access-key IDs inside third parties' signed download links, one Amazon product-link SubscriptionId in
  a CPSC recall record, one S3 bucket path in a scraped agency URL. No Firecrawl keys, GitHub tokens, authorization headers or
  private keys anywhere. Logs: reports/hosting_plan_20260920/secret_scan_tree.log and secret_hits_explained.log.
- 12:15Z collector for source_directory_documents ended (time budget; 999 saved, 291 pending). Rebuilt its index and the citation
  index (946 new documents; 25,235 scanned, 60,616 authorities, 0 failures). Live verifier 83/83.

## Update (2026-09-20 ~20:40Z) — GitHub transfer complete and verified
- Release upload finished: 94 of 94 units, 0 held, 0 failed; 130.21 GB raw -> 85.88 GB packed in 746 parts across releases
  `data-20260920` and `data-20260920-courtdocs`. `tools/verify_release.py`: every part present, size equal, and GitHub's own SHA-256
  digest equals the manifest for all 746. One superseded asset is left on the release (`top_level_files-8727d8.tar.p001`, the older
  copy of the loose top-level files); the owner can delete it.
- The repository was switched back to PUBLIC by the owner during the upload. Pass 2 therefore held 15 units flagged restricted
  (docket-vendor material); the owner instructed "do not hold anything back", so pass 3 ran with `--include-restricted`. All of those
  units had already been uploaded while the repository was private; only two had changed. While the repository is public, every
  release asset (including the vendor-derived ones) can be downloaded by anyone.
- Owner added loose files to the project root on 2026-09-20 (CRS reports, reginfo PRA inventory XML 105 MB, CSV/XLS exports); they are
  in the `(top-level files)` unit. `.gitignore` now ignores loose top-level files except code and write-ups (GitHub's 100 MB limit
  rejected a push that had swept them in). Owner also uploaded `externalcorpus-workbench-upgrade.zip` through the GitHub website;
  it is in git history and was kept (rebased on top of it, no force push).
- Code head: see `git log`; data_manifest.json is committed. Refresh later: `python tools/push_data.py push [--include-restricted]`,
  then `python tools/verify_release.py`.
