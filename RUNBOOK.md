# September 19 four-hub interface and remaining layers — deployed

Read `reports/corpus_upgrade_20260919/README.md` ("Round 3"). The sidebar is four hubs with an in-page tab bar; the home
page has a clickable state grid leading to `#state/<USPS>` pages with county chips. New validated layers: judge structured
overlay, settlements, courts and logos, MDL counsel, and a 40-capture Firecrawl gap-fill (37 credits). Court statistics was
still building. Restart with `reports/corpus_upgrade_20260919/restart.ps1`; `verify_round2.py` passed 31 live checks.

---

# September 19 county litigation resources — current active work

Read `reports/county_litigation_20260919/NEXT_RUN.md` first. The current user asks for county-by-county extraction of official local rules, forms, orders, filing guidance, fees, court facts and contacts from saved sources and observed official links. They authorize using the remaining Firecrawl balance, superseding the earlier reserve. Inspect the new collector's lock/progress; never duplicate active work. Preserve original evidence and publish only validated, accurately scoped resources to the existing MVP.

# September 19 Trellis refocus — prior completed batch

Read `reports/trellis_refocus_20260919/NEXT_RUN.md` first for the latest user scope, active Firecrawl worker, county coverage sidecar, judge report-link/portrait work and deployment procedure. Preserve the external-agent upgrade described below. Do not launch a second collector or rebuild the main corpus for sidecar changes. Counts in older sections are historical; use fresh validated receipts.

# September 19 corpus and MVP upgrade — newest deployed checkpoint

Read `reports/corpus_upgrade_20260919/README.md` and `NEXT_RUN.md` first. Live now: a derived-facet
sidecar over all 58,310 directory records (accurate categories, review states, file types, typed
dates, repaired titles, hidden parked/shell captures; "Other" fell from 30,432 to 21 records), an
MDLs & mass torts area from the JPML report dated 2026-09-01 (166 pending MDLs, 164 rows joined to
saved judge profiles by exact name + court, MDL blocks on judge profiles), a Regulations area
(12,622 CFR sections, full GPO Title 21 text, 2,259 Federal Register documents), Agencies & safety
data (243,682 FDA/CPSC records), Coverage & gaps (56 jurisdictions, 17,942 topic candidates), the
DOJ state legal resource map (56 pages, 3,201 links), five reference-type filters on the source
directory, stable `#record/<id>` deep links with copy-citation, and a sidebar that shows only
areas whose data layer passed validation. `/api/supplements` re-verifies every layer's envelope.
Server restarts go through `reports/corpus_upgrade_20260919/restart.ps1` (or `start_server.ps1`
when the port is down); `verify_round2.py` passed 26 checks over 32 requests. Settlements, court
statistics, court spine, judge structured data, Trellis coverage and canonical ids remain partial
on disk with no data claims. Two stale `test_mvp.py` expectations are unchanged.

---

# September 19 archive links in the source directory — previous checkpoint

Read `reports/source_archive_links_20260919/NEXT_RUN.md` first. The 588 exact saved-URL
candidates from the litigation review are resolved without any download: 554 source
references now link to existing saved records (370 directory records with fresh
SHA-256 checks, 204 retained official_courts captures served as verified bytes, 104
judge profiles from three judge-directory pages); 32 pilot captures stay a separate
"Saved content attached" availability; 4 candidates are documented exclusions. The
filter is `http://127.0.0.1:8769/#sources?has=archived`. Live verification passed 19
checks over 39 requests; the 19-test HTTP suite and the 75 offline tests covering the
source directory, capture pilot and link layer pass. Two `test_mvp.py` expectations
(10,669 judges; 14 portraits) have been stale since the September 19 portrait
integration (live: 10,698 and 43) and are unrelated to this change. No main
database, judge projection, bulk index or focused publication was rebuilt. Server
restarted via `reports/source_archive_links_20260919/restart.ps1` (PID in its
deployment.json); the earlier instance had died with its launcher session. The supplied
`Downloads/registry_v06_1.jsonl` is an identical export of the integrated registry; no
import. Rebuild the link manifest only after a directory or canonical index rebuild.

---

# September 19 public-law source directory — earlier deployed checkpoint

Read `reports/public_law_directory_integration_20260919/NEXT_RUN.md` first.
All 9,348 source references from the supplied Markdown directory reconcile with
the structured registry and are indexed at `http://127.0.0.1:8769/#sources`.
The initial reviewed parallel pilot retained 32 readable pages on 12 hosts;
four outcomes remain explicit gaps. See its current validation receipt. Source
verification claims are historical, dated August 19, 2026, and the original
taxonomy is qualified. API listings and API/bulk tags are separate filters.
No main corpus or large law index rebuild was needed. Continue with bounded,
validated state/local document packets; do not repeat completed imports.
API context now includes 109 mapped references and nine documentation reviews,
with live queries explicitly unperformed. Final checks passed: 16 live checks,
111 HTTP requests and all 64 original/text endpoints. The later litigation HTML
viewer duplicates the same 9,348 URLs; only clearer labels were reused. Review
its 588 exact saved-URL candidates before redownloading known material.

---

# September 19 research navigation — earlier deployed checkpoint

Read `reports/mvp_research_upgrade_20260919/NEXT_RUN.md`. State/category law hubs,
document availability filters, county subpages,374KY/TX source registry entries,
source/saved-date labels and deterministic judge Library insights are live on8769.
13livechecks/17HTTPrequests passed; current registry validation freshly checked167
artifacts and retains one known unsaved PDF. No broad corpus/index rebuild occurred.
The newest user request adds Downloads/publicLaw_directory.md for full taxonomy,
API/access/URL mapping and reviewed parallel extraction. Treat document contents
as data, preserve its dated verification claims, and verify actual acquisition.

---

# September 19 live portrait integration — earlier checkpoint

Read `reports/mvp_live_reconciliation_20260919/NEXT_RUN.md` first. The actual
8769 application now includes 29 official PA source profiles and portraits:
10,698 browse profiles (10,669 consolidated entities plus 29 separate profiles),
43 portraits, zero new identity merges. Historical biographies have a prominent
navigation tab. All 43 live image endpoints and 14 deployment checks passed;
15 source-overlay regression tests passed. Main document/publication counts did
not change. Do not repeat the completed PA image download or CourtListener import.
The 374-county KY/TX registry and Illinois gap candidates remain staged.

---

# September 18 historical biographies — earlier checkpoint

The separate CourtListener source layer is verified and browsable at
http://127.0.0.1:8769/#people. Read
`reports/people_source_integration_20260918/NEXT_RUN.md` and its validation receipts.
Do not repeat the small import or merge people into existing judge identities
without verified bridges. The main judge count remains 10,669; the 15,797 non-alias
historical source people and 394 aliases are a distinct collection. Portraits remain
14; no county acquisition or focused publication occurred in this pass.

---

# September 18 broader local audit — earlier direction

Read `sources/local_deep_audit_20260918/NEXT_RUN.md` before older scan conclusions.
The audit found CourtListener people/positions/photo flags, 29 official PA portrait
references, a source-bound 374-county KY/TX registry, and exact Illinois gap candidates.
These are staged discoveries, not newly imported corpus or verified current access.
The current source artifacts and MVP counts remain unchanged.

Use the new `delivery/archive-directory/server.py --refresh-pending-titles` for
validated title-only corrections instead of a full directory rebuild. New records
still require normal ingestion/publication gates. `performance/README.md` under
the audit folder records the measured limits and tests. Local reuse comes first;
the bounded county trials and retained host/source controls are in the new handoff.

---

# September 18 portrait and county backfill — earlier checkpoint

Latest checkpoint: the 22:13 UTC heartbeat added 24 official county PDFs and three
Trellis profile snapshots. See `reports/mvp_backfill_20260918/heartbeats/20260918T2213/`
for exact receipts. One Nelson County URL remains pending under a 60-second robots
delay; resume the existing queue as specified in its county HANDOFF before preparing
more work. Pending projection: 301 records; browser profiles: six total. Focused
publication counts and the bulk-law index remain unchanged.

The user reauthorized continuing county/Trellis gap backfill while improving judge portraits, filtering and navigation. Follow the new top section of REQUEST.md and `reports/mvp_backfill_20260918/NEXT_RUN.md`; the blanket county pause below is historical. Broad cases/dockets/unrelated URL collection remains outside the resumed scope. Reuse the completed bulk-law index and existing source snapshots.

The previous official county queues have no pending URLs; do not restart them to manufacture activity. New substantive county links require an observed source, exact county association, reviewed packet and existing access/host controls. A fresh signed-in Trellis county-profile page loaded; this is browser-profile access evidence only. Respect remaining provider/direct and document-entitlement barriers. Publication remains separate from newly saved captures.

---

# September 18 personal MVP checkpoint — previous phase

The latest user priority is clean navigation, dedicated judge/state/county pages, useful categories/filters and reuse of existing local legal assets. Full acquisition is not required now. Keep new broad law/county/vendor collection paused; do not restart old queues from historical instructions below. The live UI is http://127.0.0.1:8769/. Current maintenance instructions and verification are in `reports/mvp_cleanup_20260918/NEXT_RUN.md` and `verification.json`.

Open US Law is published and searchable: `sources/open_us_law_20260918/ready.json` says ready:true, external-content FTS integrity passed and quick_check is ok. All 229 file counts reconcile with 2,978,617 rows, five original-row comparisons and three search checks passed. No importer remains to restart. This is publisher snapshot completion, not nationwide legal completeness or currency.

The new judge presentation has 10,669 conservative entities, of which 5,942 have detailed profile content. Five portraits have source-backed identity links; nine candidate matches remain held. Sources and original variants remain in the existing entity/evidence layer. Dedicated profile tabs separate overview, career, analysis and actual publisher-linked documents. `delivery/archive-directory/judges.py` builds this presentation only; no new identity merging happens in the UI.

Four curated local-library collections expose bounded previews, with 28 selected PDFs, 24 page-labeled text derivatives and four small court marks/icons. MDL-3080 has 1,612 cataloged PDFs but only 24 selectable document previews in this MVP. The settlement catalog has 848 records with four selected official PDF previews. County images are explicitly associated court branding, not county seals or courthouse photography. Exact artifact allowlists bind path, size and hash; external originals remain unchanged.

---

# September 18 enrichment checkpoint — historical preparation

The user requested Vaquill open-us-law enrichment, import of the Seeger staging directory and related library, cleaner reading views, gap recovery and conservative judge deduplication. The local directory remains http://127.0.0.1:8769/. See `reports/enrichment_upgrade_20260918/NEXT_RUN.md` and the adjacent final `verification.json` for operation and evidence. The historical checkpoints below remain dated records.

The entire pinned Open US Law v2026.08 snapshot is downloaded: 229 publisher-checksummed Parquets and 2,978,617 source rows. Its separate importer has committed all rows and is building its large full-text index. Do not interrupt or duplicate a healthy importer. The live authoritative completion gate is `sources/open_us_law_20260918/ready.json` with `ready:true` and integrity evidence. No bulk search completion or national completeness is implied by saved Parquets or a count of indexed rows. Publisher-withdrawn GA/NC statutes, 311,321 missing source URLs, legal versions and historical status remain explicit.

The Seeger import is validated: 18,360 records, comprising 11,194 originals and 7,166 structured provisions. All source originals remain unchanged. A separate validated recovery overlay added text to 384 existing document identities (382 DOC/RTF and two scanned PDFs), with no duplicate records. Its manifest SHA is `dc415c617ee8da7fe6b823abbb4c9272c6848b3ba0440196f4e895bf85ee2c4e`; preserve its parent and derivative hash gates in every rebuild. One large NJ RTF remains unresolved, while its 5,856 separately imported provisions are available. Partial-text PDF and OCR limitations remain.

The reader now has 34,545 nonempty derived reading bodies and 451 empty-body entries, before adding bulk rows. All 16,001 focused canonical text bindings and all 384 recovered record bindings passed checks; originals/raw extraction remain available. `scripts/validate_reading_views.py` uses directory-namespaced source IDs, verifies all recovered bindings and samples output hashes. The default UI is readable prose with collapsed technical metadata, and preserves source/capture/edition/OCR caveats.

Judge projection v1.0.1 has 10,669 conservative display entities from 11,928 source observations, with all 60,849 fact claims and 708 analyses preserved. There are 1,211 possible and 885 conflicting candidate pairs kept unmerged. Do not label this a certified count of currently serving judges. The main directory has 47,571 source observations and 45,588 display groups; its 58,240 database rows include generated entity projections and must not be added to source counts. Bulk source rows are not globally deduplicated unique provisions.

The 30-minute heartbeat is updated for this scope and preservation contract. Continue eligible official state/county legal content through the existing reviewed queues and controls after the bulk importer has finished. Use the normal focused-publication rebuild before directory refresh; preserve all supplements. New Trellis/paid-vendor judge acquisition remains paused. The local directory's API and reader checks pass; final bulk browser/search verification follows its ready gate.

---

**Directory verification:** all10 integration checks passed after HTTP delivery changes; desktop/mobile, full-text search, county drilldown, judge analysis and export UI checked. Evidence: delivery/archive-directory/verification.json. Source-only and pending records remain separately labeled.

# September 18 local directory and acceleration checkpoint

The working directory is http://127.0.0.1:8769/ (delivery/archive-directory/START.cmd). It indexes 29,211 browse records: 16,454 published captures; 11,926 judge observations; 2 vendor profiles; 591 federal entries (15 captures +576 observed links); one provider law directory;237 unpublished downloads. County inventory remains 3,144 rows. Directory rows overlap across source representations and are not unique documents or people.

The Firecrawl pilot used13credits and ended with5,087. Only the DHR directory is eligible, no statutory bodies. Eight unexpected redirects to NYSenate were quarantined and excluded. Preflight redirects and source eligibility before future provider submissions; never retry this closed pilot or import provider folders blindly. See sources/targeted_firecrawl_20260918/receipt.json and redirect_incident.json.

Use sources/directory_pending_20260918/build_pending.py then validate_pending.py to refresh the awaiting-publication projection; sources stay unchanged and exact published triples are excluded. Rebuild the local directory afterward. The three completed collectors have348(state followup),697(county local),129(WA)downloads. Arizona had592saved/139pending at17:47UTC and resumed for1800seconds under existing controls with launcher PID33148. Check fresh process/queue before further work.

Publication cache tests30pass. Exact byte verification of20.58GB/~106,845files was measured at~110seconds; baseline not yet established and no productioncache-hit timing claimed. Use --no-rebuild-cache during actively changing acquisition if the fingerprint overhead is unhelpful; once stable, a successful full build can establish the conservative baseline. Never equate a skipped unchanged checkpoint with new acquisition or broader validation.

# September 18: upgraded collection and local archive directory

The user authorized use of the existing upgraded Firecrawl account for scoped useful collection. Live CLI status reports 5,100 remaining credits and a five-job parallel limit. Start with a maximum 50-credit pilot; subsequent 30-minute continuations may use at most 100 credits per run with a 250-credit reserve, always checking fresh capacity and preserving provider receipts. These are conservative working limits, not a request to buy credits. Preserve existing robots, host pacing, source boundaries and paused access barriers. Do not use provider routing to bypass them. Tavily is a separate configured service, not unlocked by a Firecrawl key.

Build and maintain the read-only local directory in delivery/archive-directory. Keep published captures, live queue counts, supplementary captures and link-only federal resources clearly separated. Reuse existing judge data; judge/vendor and broad Trellis acquisition remain paused. Selected official federal/DOJ resources are an explicitly separate supplement, with no inferred county jurisdiction.

# Active priority — state laws and county local documents (2026-09-14)

**September 18, 16:51 UTC — latest checkpoint; earlier counts below are history.** The validated aggregate contains **16,454 capture records and 15,837 distinct searchable texts**, adding 277 saved source records and 20 OCR representations. Receipt: `reports/county_law_focus_20260914/rebuilds/20260918T164217Z/receipt.json`; independent release verification: `reports/county_law_focus_20260914/heartbeats/20260918T1622/release_verification.json`. The prior attempt restored the old package after detecting an OCR-directory validator mismatch; the corrected finalizer and index now share the exact `OCR_MANIFESTS` allowlist. Eight regression checks and an independent replay of all 356 derivatives passed. Use the normal locked seven-step rebuild, not a one-off refresh helper.

The published state-follow-up component has 295 downloads: 289 NC PDFs plus six Nebraska exports; 28 historical notices are explicitly classified. Its finite 355-URL family ledger is `reports/county_law_focus_20260914/heartbeats/20260918T1622/state_family_completion_20260918T1628/summary.json`. At resume there were 53 NC URLs and 153 Arizona URLs pending; seven Georgia robots exclusions remain unchanged. These are reviewed-family counts, not whole-state or national completion.

The substantive county packet `sources/counties/local_documents_20260914/batches/20260918T163032097064Z` is independently reviewed and **already ingested**: 186 exact observed document URLs, across 83 candidate county associations. There are now 786 general county seed URLs plus 129 WA rule URLs, across six county packets (eight total including the two state packets). Do not ingest the preserved shallow draft `20260918T162632681563Z` or the earlier unfiltered `20260914T074809815784Z`. Future selectors should prioritize actual rule/code/order/form documents, including deeper links from saved county-local landing pages; new counties are secondary. Do not pad a smaller qualifying batch with administration pages. The reviewer accepts `--expected-count` for a bounded packet below 200.

State-follow-up, Arizona and county-local collectors resumed at 16:51 UTC with 1,800-second budgets; fresh status is in `execution_checkpoint.json`. Preserve Arizona's 120-second pacing. Let live finite runs finish, validate newly captured content, then rebuild under all eight source locks. `update_execution_checkpoint.py` now verifies eight ingested packets. No Washington source download queue remains pending.

Washington OCR now covers **30 unique PDFs / 358 pages / 31 source representations** across two immutable passes. The new 20-PDF pass is `corpus/county_local_rules_washington_20260914/ocr_passes/20260918T162345Z`; its source/hash/manual-quality receipt is `reports/counties/local_rules_washington_20260914/ocr/passes/20260918T162345Z/release_receipt.json`. **Six PDFs / 300 pages remain**, listed in the adjacent `deferred_remaining_unique_pdfs.json`. The older 26-PDF gap count is superseded. Use a separate future pass and add only its exact reviewed manifest to `scripts/build_document_index.py:OCR_MANIFESTS`; the finalizer imports that same list. Keep blank-page/signature-noise flags, provenance, and unverified legal currency explicit.

**08:02 UTC checkpoint supersedes the older operational counts below.** The published aggregate now contains 16,157 capture records and 15,544 distinct searchable texts, including 476 county-local captures and 11 OCR source representations from 10 unique PDFs. The state follow-up snapshot includes 200 NC PDFs plus six Nebraska full-rule exports; 16 short historical notices are explicitly classified. All 129 Washington court labels are preserved, with 76 county-unassigned records retained as such. Full and field-refresh receipts are `reports/county_law_focus_20260914/rebuilds/20260914T074951Z/receipt.json` and `reports/county_law_focus_20260914/rebuilds/20260914T080106Z_county_labels/receipt.json`.

The filtered third general county packet `sources/counties/local_documents_20260914/batches/20260914T075036205099Z` is reviewed and ingested. There are now 600 general county seed URLs plus 129 WA rule URLs across five county packets. The earlier unfiltered draft `20260914T074809815784Z` is evidence only; never ingest it. All seven state/county packets are checked by `update_execution_checkpoint.py`. State-law, Arizona and county-local jobs resumed after publication with 1,800-second budgets; see fresh processes and `execution_checkpoint.json` instead of historical PIDs. Keep those finite runs checkpointed when they stop and rebuild before resuming again.

The normal seven-step rebuild now preserves court labels automatically. Do not rerun the one-time `refresh_county_labels_20260914.py`: it was bound to the preceding exact package. The remaining WA OCR gap inventory is `reports/counties/local_rules_washington_20260914/ocr/remaining_gaps_20260914T0747.json`, with 26 unique PDFs still needing OCR. Preserve the first frozen OCR pass when preparing another.

The latest executable checkpoint is `reports/county_law_focus_20260914/execution_checkpoint.json`; earlier timestamps below are history. Read `reports/county_law_focus_20260914/DATA_QUALITY.md` before resuming. The first two general county batches contain 400 reviewed URLs; Washington's two rule batches contain all 129 exact PDF links from three saved court indexes. State follow-up contains 355 reviewed URLs (342 NC chapters, six Nebraska chapter exports and seven Georgia rules with recorded robots exclusions). These are finite source-family inventories, not national completeness.

Use `scripts/start_collector.ps1 -Job <job> -RunSeconds <budget> -PythonPath 'C:/Users/firas/AppData/Local/Programs/Python/Python311/python.exe'`. Jobs are `official-law-resume3`, `official-law-state-rules`, `county-local-documents`, and `county-wa-rules`; roots and observed process IDs are in the checkpoint. Check real processes and OS locks first. Do not restart an exhausted batch or reingest a completed packet. Keep Arizona's 120-second delay and all shared host controls unchanged.

Both state packets and all four county packets are ingested. Resume eligible pending state URLs from the existing queue after a stable checkpoint; do not re-ingest the 255-URL continuation. Further county preparation uses `scripts/prepare_county_local_documents_20260914.py --timestamped`, prioritizing new county associations and exact legal/court/clerk/document links. Review raw source anchors, county mapping and merged config before any ingestion. Preserve uncertain authority and case-filing availability as explicit gaps.

The prior aggregate was validated at 06:48 UTC; newer raw captures are not in that snapshot yet. Let the finite state and Arizona workers stop naturally, then run `reports/county_law_focus_20260914/rebuild_focused_package.py` with installed Python. It locks the eight reviewed roots, freezes scope, backs up the previous package, runs seven build steps including `county_local_resources`, and restores the prior package after a failed build. Do not invoke the standalone finalizer to skip this workflow. The county supplement can acquire its own two locks when run alone, but publishing it before the coordinated aggregate rebuild would leave the old package file manifest stale.

Washington's frozen first OCR pass is `corpus/county_local_rules_washington_20260914/ocr/pdf_ocr_manifest.jsonl`: 10 documents/63 pages, source and derivative hashes validated under `reports/counties/local_rules_washington_20260914/ocr/validation.json`. It is integrated into the next index adapter, with OCR confidence and visual-reading-order limitations preserved. Do not overwrite this frozen pass when preparing additional OCR; remaining scan gaps need a separately evidenced pass. Five reviewed NC historical notices are hash-bound in `sources/official_laws/state_rules_followup_20260914/content_annotations.json` and must not become active-law claims.

Update live county evidence with `scripts/update_county_local_documents_progress_20260914.py`; update state evidence with `sources/official_laws/state_rules_followup_20260914/check_downloads.py` using both seed files. `update_execution_checkpoint.py` verifies the six ingested packets; it is specific to these packets, not a generic future batch registrar. Preserve prepared, ingested, downloaded, usable-text and substantive-content counts separately. Only a passing coordinated rebuild publishes a new aggregate snapshot.

Current scope is `reports/county_law_focus_20260914/scope.json`. Audit fresh SQLite queues, real processes and OS locks; the 04:29 process report is historical. Resume eligible remaining official laws with unchanged source policies. Reconcile and rebuild the focused package at stable checkpoints. Then prepare isolated exact observed county court/clerk/local-rule/form/filing/document batches under `sources/counties/local_documents_20260914`; acquire using the existing public crawler and shared hosts. Retain FIPS/state, source association strength, original hashes, edition/date and download/extraction outcomes. Do not expand unrelated public URLs or claim full source completeness from a drained batch.

Further judge/vendor collection and old Trellis selectors stay paused. Seal already acquired vendor data without expanding the probe. Access failures remain gaps until their conditions change; no purchase or upgrade is authorized. Historical workflow notes below are superseded when conflicting.

---

# Historical priority — standardized judge enrichment

The latest user request authorizes acquiring reputable alternative judge analysis and professional data, adding it to the existing corpus and standardizing judge records accurately. Current scope is `reports/judges/focus_20260913/scope.json`. New public sources and outputs are isolated under `sources/judges/enrichment_20260914/` and `delivery/judge_enrichment_20260914/`.

Collect a finite official judicial-performance evaluation cycle with its methodology and a public authoritative federal professional-biography dataset where accessible. Keep state, federal and administrative judge systems explicit. Official retention/survey evaluations are different measurements from motion outcomes; do not combine their percentages or invent missing denominators. Preserve source labels, dates, original artifacts, SHA-256 hashes and evidence for each fact. Retain individual source observations even after a confirmed identity link. Name-only and ambiguous matches remain unresolved; current service is not inferred from a historical profile.

The existing finite Trellis profile selector continues unchanged. Inspect fresh worker status, process/OS locks and remote job markers before any action; recover the same job instead of duplicating submission. Do not restart cases, filings, law/county collectors or broad URL discovery. The existing sealed package remains immutable. Commercial vendor documentation is useful for planning imports; no additional account purchase or product upgrade is authorized. Preserve the historical sample-report partition. The notes below are dated history when they conflict with this priority.

---

# Active priority — fast judge profiles and reports

The latest user instruction authorizes the privately configured Firecrawl account for judge data. Current scope is `reports/judges/focus_20260913/scope.json`. Judge collection uses the isolated `sources/trellis/judge_focus_20260913/` frontier and holds both worker locks. Source selections are frozen and replayed against literal saved links; do not crawl cases, dockets, filings or general URLs.

Recover an unresolved remote batch using its identical selection and job ID before any new submission. Authentication, credit and access failures are terminal until their actual condition changes. Inspect fresh process/OS-lock evidence and the job manifest; a historical run row alone does not prove active collection. Use basic proxy, verified TLS, concurrency two, a finite budget and a 100-credit reserve. Never print the key or send browser cookies to Firecrawl.

The first 300 profiles and the next 1,000 are staged under `sources/judges/focus_20260913/`. Validate and deduplicate the next selector again before launch. Normalize newly saved originals and existing official rosters into `delivery/judge_intelligence_20260913/`; retain raw hashes, literal field evidence, historical uncertainty and source-specific identities. Numeric analytics require actual source values, labels and period/denominator context. The browser is now signed in: the current plan requires an additional80USD/month subscription for full Judge Analytics. No upgrade is authorized. Public preview evidence and the separate12page marketing sample PDF are under `sources/judges/focus_20260913/report_sample/`; no sample values are promoted to actual judge metrics.

Existing finite official law collectors may finish naturally. The prior law/county direction below is dated history and is superseded during judge focus; do not restart those collectors or use their earlier progress percentages for judges. The prior legal package remains its dated snapshot.

---

# Active acquisition — renewed focused continuation

## Official-only continuation checkpoint workflow

The active thread continuation is `continue-official-legal-corpus` (30-minute checks). Current reviewed roots and latest status live in `reports/remaining_resume_20260913/scope.json`. Use the actual `.crawler.lock` ownership plus process evidence to distinguish a live collector from a historical unfinished run row. Preserve orphaned run history; do not invent a clean end.

The 04:29 UTC observation records two healthy finite collectors: Arizona PID 39168 and quick-law PID 36852. Quick2 finished cleanly at 04:00:17 UTC: all 600 added originals passed fresh raw/hash/metadata checks. Its 489 Idaho PDFs have nonempty collector text, and all 111 new Louisiana DOCX originals now have frozen, independently checked offline text under `offline_docx_pass2/`. Root verified 2,411 XML package parts, all derivative bytes and parent identities, and all 130 first-pass files remained unchanged. Only this validated derivative family was added to the index and law reconciliation; 22 production index tests passed. Evidence is in `reports/remaining_resume_20260913/heartbeat_20260914T041629Z.json`.

All 955 remaining observed Idaho chapter-PDF candidates were separately reviewed, deduplicated and ingested from `sources/official_laws/resume_20260914_quick3/`. The 04:27 UTC quick-law launch has a 3,600-second budget, preserves the prior 750 captures, and changes only the exact path allowlist. No candidates remain deferred in this reviewed Idaho chapter family; this does not resolve other national gaps. The reviewed continuation denominator is now 3,735 URLs. A fresh county redirect review found 15 changed records but zero new eligible endpoints: 12 targets were already saved, one was already forbidden, and two leave for external CMS hosts. Keep the Leon forbidden-host gap and held Washington ancestry unchanged.

**A group package refresh is pending.** Let both healthy finite collectors stop naturally. When Arizona stops around 04:43 UTC, leave it checkpointed while the quick-law batch drains; do not immediately restart it and prevent the pending stable rebuild. At the next check with both stopped, acquire all five collection locks and run the six rebuild steps below, then resume accessible Arizona work with its unchanged 120-second delay. Never force-kill a healthy collector or modify its active config to publish sooner. Post-03:40 captures and the 111 new DOCX derivatives are verified raw-corpus additions but are not yet in the published package.

The hidden WMI launcher now supports finite continuation jobs: `./scripts/start_collector.ps1 -Job official-law-resume3` (3,600 seconds), `-Job county-entries-continuation` (900 seconds), and `-Job county-registry-continuation` (1,200 seconds). It checks both direct crawler processes and wrapper processes before launching these jobs. Check current locks, pending rows, shared access barriers and the scope first; do not start completed or wholly blocked queues. The direct law process launched at 02:21 UTC ended cleanly at 03:21 UTC with its finite time budget. New launches use an independent hidden WMI process with persistent logs and checkpoint metadata. The latest process manifest records actual ownership and completed runs separately from preserved historical unfinished run rows.

The 2026-09-14 saved-link review added `official-law-quick` for `corpus/official_law_resume_quick_20260914` (900 seconds by default). `-RunSeconds 600` selects a shorter finite budget for any of these four continuation jobs. Its first 150 exact official originals across Maine, Louisiana, Oregon and Idaho all downloaded, with a clean exhausted frontier at 03:30:17 UTC. Louisiana uses `administrative_code`, and Oregon retains its 2026 update/supplement designation. Louisiana DOCX originals require separate verified offline text derivatives under `offline_docx/`; collector text remains unchanged. The county alias integration contains 101 exact new URLs and 101 direct registered-domain contexts, and its collector finished with 340 saved responses at 03:21:08 UTC. One additional cross-domain ancestral context is held separately in `reports/remaining_resume_20260913/county_alias_review_20260914/integration/deferred_chain_associations.jsonl`; its endpoint has another valid direct context, so the endpoint is still collected without inferring that ancestral association. Frozen prep receipts and root ingestion receipts preserve before/after evidence. Do not regenerate or reingest either completed batch. Another 1,555 eligible law URLs remain in the frozen deferred-candidate file and need the next finite deduplicated review.

The 03:40:53 UTC package snapshot passed validation with 13,741 capture records and 13,298 distinct searchable texts. It includes 1,314 official-continuation responses, 1,249 nonempty collector text files and 40 verified offline DOCX derivatives. Quick2 was then reviewed and ingested from `sources/official_laws/resume_20260914_quick2/`: 111 Louisiana administrative-code DOCX parts/books and 489 Idaho full-chapter PDFs, adding 600 exact paths to the existing quick-law root. Every other live config value was preserved. The hidden quick-law collector now has a finite 1,800-second budget; Arizona resumed separately with a 3,600-second budget. Check actual process ownership in `reports/remaining_resume_20260913/current_processes.json`. The live queue denominator increased from 2,180 to 2,780 URLs; earlier percentages remain dated snapshots. Another 955 Idaho candidates are explicit in the quick2 deferred file.

Keep both frozen DOCX passes unchanged. The first pass contains 40 derivatives and the completed second pass contains 111. Parent/fetch/raw/metadata/text and package-part hashes, the declared literal-digest basis, and unsupported formatting/part inventories remain separate. The explicit second family has passed root validation and is accepted for the next stable index build; the finalizer already counts parent-linked searchable document derivatives separately from collector text. New responses collected after publication are not yet part of the published snapshot. Earlier candidate counts and quick2 process notes immediately above are dated history; quick3 and the current process manifest govern the next action.

After collectors reach a stable checkpoint, rebuild in this order:

1. `python scripts/build_document_index.py build`
2. `python scripts/build_focused_laws.py` (performs the fresh law reconciliation and count-lineage pass)
3. `python scripts/build_focused_counties.py`
4. `python scripts/build_focused_package.py`
5. `python scripts/finalize_official_resume_20260913.py`
6. `python delivery/ui-sketch/build_data.py`

Only the reviewed collection allowlists have been extended. The county builder separates registered-domain candidates, reported websites, observed HTTP redirects and inferred origins from robots redirects. It also separates empty responses from nonempty saved text. The finalizer requires every reviewed collection's exclusive OS lock and every saved original URL/hash in both the component manifests and focused index. It records historical unfinished run IDs without altering them. Do not run older finalizers that restore obsolete paid-expansion/cutoff status.

Current source scope remains official laws and official county/government entries; no Trellis, paid API, cases, dockets or judge expansion. Full titles/documents are preferable when already observed, but preserve edition and extraction limits. Arizona's genuine 120-second crawl delay must remain in effect.

Latest user direction: **Continue official sources only**. Collect official state-law sources and observed official county entry pages. Trellis browser/Firecrawl acquisition is deferred; no replenishment is awaited. Current scope is `reports/remaining_resume_20260913/scope.json`.

User authorized renewed acquisition on 2026-09-13T22:51:10.094047+00:00. Continue only remaining state-law sources and county profiles/official entry pages. Reuse the existing archive. Do not expand cases, dockets, judges or general site URLs. Live Firecrawl balance is 1 credit; wait for replenishment before paid batches. Official-source agents are preparing new finite deduplicated batches with existing robots and host controls. The delivered package remains a prior snapshot until new captures are verified and integrated. Current scope: `reports/remaining_resume_20260913/scope.json`. This active instruction supersedes historical cutoff notes below.

---

# Current work — county and law expansion

County/law expansion checkpointed and delivered at 2026-09-13T21:42:45.379710+00:00. All 950 selected URLs reached a recorded outcome; the full underlying corpus remains incomplete. Current result: `delivery/focused_legal_corpus/expansion_20260913/summary.json`. No collector or continuation automation is running. The earlier active-resume notes below are historical.

The user resumed acquisition on September 13, 2026: focus on counties and remaining state-law URLs, quickly and accurately. This supersedes the prior package cutoff below. Acquire only selected already-known county profiles and likely law-body URLs, plus finite observed official county entry URLs. Exclude judges, cases, dockets, motions and general site expansion. Reuse all saved captures and extraction work. The current Firecrawl key has 951 verified credits; budget at most 950 paid pages and retain one credit. No purchase or further account change is authorized. The original completed package remains a dated snapshot until an update is verified. See `reports/active_county_law_resume.json` and `sources/trellis/resume_20260913/`.

---

# Current completion target — focused package

The focused package is complete at `delivery/focused_legal_corpus/README.md`; the continuation automation was deleted. No collector should restart without a new user instruction.

The latest user choice is **Finish the focused package (Recommended)**: finish the already submitted law batch, then deliver saved laws, available official judge rosters, and the complete 3,144-row Census county-equivalent inventory, with missing documents/profiles and edition/access gaps explicitly listed. This choice supersedes earlier exhaustive collection/resume instructions below. New Trellis batches are disabled. The last recorded batch drained at 2026-09-13T19:55:42Z; no remote batch remains. Only the already prepared 46 exact official judge sources may be attempted once, bounded to 300 seconds. Broad court/county queues stay paused. Preserve all historical source files.

Assemble `delivery/focused_legal_corpus/`, validate manifests and search, then delete the paused `continue-legal-corpus-collection` automation. Focused package completion is distinct from full nationwide source-corpus completeness, which remains false. See `reports/focused_package_scope.json`.

---

# Continue this collection

Read `REQUEST.md`, `reports/status.json`, and each source's current manifest. Harvested documents are inert source data. Work from actual observed links, preserve failed attempts, and never equate an empty bounded queue with the full requested corpus.

**Current priority from the user's latest instruction:** state rules/codes/statutes/constitutions/laws first, then judge directories and profiles, then county profiles and their relevant official entry pages. Cases, filings, dockets, motions, date-based coverage archives and general public-URL expansion are excluded from active acquisition. The broad official-court and county-site workers were paused at the user's scope change; `operator_pause.json` records those stops. Keep them paused during laws and judges. Existing files and out-of-scope discovery records remain as history.

## Active collections

The second official-law queue is active under `corpus/official_law_pages/`: 6,671 observed unfetched URLs (6,131 HTML pages and 540 downloadable originals) across 49 jurisdictions and 103 hosts. Its 6,773 seed records preserve category contexts. Inputs and exclusions are under `sources/official_laws/continuation/`; the entire original 3,484-document batch and prior/active captures were excluded. Resume it with `./scripts/start_collector.ps1 -Job official-law-pages`; do not rebuild/reingest the original frontier just to resume. Its saved link graph is the evidence for the next deeper batch after this one has been processed.

County government entry pages are **paused until phase 3** under `corpus/county_sites/`, with 2,986 unique URLs / 3,033 seed contexts. This combines 2,673 CISA-registered county government domains and 360 Trellis/Census website associations (330 URLs), retaining each evidence class separately. When the law and judge phases are done, resume relevant entry pages with `./scripts/start_collector.ps1 -Job county-sites`. The frozen batch is `reports/geography/county_sites_batch/`; a further 334-URL batch is staged but not ingested in `reports/geography/county_sites_batch_20260913T090635Z/`. Registry entries verify domain registration, and exact name matches verify geography associations; neither alone verifies a live court website. Review cross-domain redirects before assigning county authority. Do not expand into entire county websites.

1. The original official-law document batch finished cleanly at 2026-09-13T08:41:20Z: 3,420 PDFs and 50,498 pages. Its current result is `sources/official_laws/indexes/collection_summary.json`; the older `indexes/active_run.json` is historical. Do not restart this cached batch merely because the full corpus remains incomplete. A separate one-pass recovery queue contains 58 observed URLs selected from 63 original retrieval errors. Its inputs, exclusions, preserved error snapshots, and Nebraska offline parser repair are under `sources/official_laws/recovery_pass_1/`; its live archive is `corpus/official_law_recovery_pass_1`. Resume an unfinished imported recovery queue with `./scripts/start_collector.ps1 -Job official-law-recovery`. It uses zero automatic retries and a documented 512 MiB response cap; do not explicitly retry the completed pass without new evidence. The historical TLS audit completed 63 verified checks; prior and new versions are preserved. Do not restart paused hosts without new evidence the barrier changed.
2. Trellis public source collection: `pipeline/firecrawl_batch_worker.py` uses the scoped SQLite frontier in `sources/trellis/worker/`. Start it with `./scripts/start_collector.ps1 -Job firecrawl-batch`. Each batch contains at most 20 observed URLs from one priority phase, with two concurrent browsers, basic proxy, verified TLS and a credit reserve. It imports existing files and resumes saved remote jobs. The user-supplied fresh key is DPAPI-encrypted outside this archive under `%LOCALAPPDATA%/LegalCorpusArchive/firecrawl-key.dpapi` and loaded only into the worker process. Never echo it, send Trellis cookies to Firecrawl, or fall back to the exhausted old environment key. `batch_status.json` and `batch_jobs/*/manifest.json` record progress and job accounting. An active or uncertain job is represented by `batch_active.json`; never delete that marker to force a new submission or start the single-page worker. Resolve its recorded remote job first. Both workers share process locks. A `sources/trellis/worker/STOP` file requests checkpointing and cancellation of an active remote job. Remove only that exact STOP file to resume an intentionally stopped worker when appropriate.
3. Authenticated Trellis: use the user's Chrome session only for relevant law/judge/county content when needed. Read `browser/access_observations.json` first; observed paid coverage is CA/IL and content views are finite. Paid case/docket/filing acquisition is now outside active scope. The three earlier downloaded PDFs and their original manifests remain available, but no manual case-download test is needed for the narrowed task. Do not guess protected endpoints or infer nationwide/API entitlement.
4. The broad official court continuation under `corpus/official_courts` is paused by the narrowed user request. Do not restart its whole 5,713-seed queue. For the judge phase, select only actual judge-directory/profile sources from saved evidence into a scoped batch. The original source authorities and access gaps remain under `sources/official_courts/continuation`. Do not interpret unreviewed CISA domain-name matches as verified court assignments. Earlier downloads and completed OCR remain available for search.

## Refresh indexes and reports

Historical paid-browser attempt: Alameda case `22CV005284` showed Chrome `ERR_BLOCKED_BY_CLIENT`; no PDF was saved or counted. The newer scope excludes case acquisition, so the previous request for a manual case-download check is superseded and is not a current blocker. Do not work around Chrome security or inspect browser download-history databases. The last observed Account Overview count was 17/75 before that case attempt.

The supported Firecrawl batch endpoint uses the account's two batch/crawl starts per minute and two concurrent browsers. The worker spaces batch starts by at least 31 seconds and honors later server Retry-After/reset deadlines. This is separate from the single-page endpoint's ten requests per minute. A saved five-law-page probe completed in 9.661 seconds for five credits. See the official [batch documentation](https://docs.firecrawl.dev/features/batch-scrape) and [rate limits](https://docs.firecrawl.dev/rate-limits). Credit exhaustion and account/target barriers checkpoint instead of purchasing access. The launcher resolves the encrypted key's actual Windows packaged-app storage path before starting its independent process. Never run single-page and batch workers together.

Firecrawl scope version `2026-09-13-laws-judges-counties` enforces the new phase order. Only `/state-rules/`, judge directories/profiles (including ordinary directory pagination), and root state/county coverage pages can enter its active frontier. Prior case, document, motion, dated-coverage and filtered URLs are marked `in_scope=0`; pending ones become `deferred_scope`, preserving attempts and source evidence. New out-of-scope links remain in original captured HTML but are not added to acquisition or edge queues. Both pending and in-flight law pages finish before the judge phase can begin. Do not remove these scope restrictions just to empty an old all-URL queue.

Focused recovery follow-up: the first 58-URL pass finished with two downloads, 53 redirects and three transport errors. The 53 observed Wisconsin canonical PDF locations, such as `/constitution/wi.pdf` and `/statutes/statutes/132.pdf`, were reviewed, deduplicated against prior captures/queues, and ingested into the same recovery archive. All 53 downloaded successfully; recovery checkpoint `2026-09-13T09:49:58Z` records 55 downloads total and no pending URLs. Their source-redirect hashes and exact path scopes are saved under `sources/official_laws/recovery_pass_1/redirect_targets/`. Do not restart, reingest, or retry the completed pass without new evidence. The West Virginia original constitution is preserved at 114,704,102 bytes. Recovery OCR is prepared with `python pipeline/prepare_court_ocr.py --root corpus/official_law_recovery_pass_1` and runs with `./scripts/start_collector.ps1 -Job ocr-law-recovery`. The unified index accepts its verified derivatives linked to parent hashes. Generic law-page PDFs need the same selective screening after meaningful batches.

Run from this workspace:

```powershell
python scripts/build_catalog.py
python reports/geography/reconcile_counties.py
python scripts/build_document_index.py build
python scripts/build_law_queue_status.py
python scripts/build_status.py
```

The catalog incrementally parses completed public Trellis responses, extracts county fields and official websites, and writes distinct discovered case/judge/rule URL indexes. The current initial county queue is not the final national county inventory: reconcile its URLs with the 3,144-record Census 2026 county/equivalent baseline and official court organization.

The unified search index is `catalog/documents.sqlite3`, with CSV/JSONL manifests and source/capture-version validation. Its initial verified snapshot contained 6,180 records and 6,034 distinct searchable texts, including 47 OCR derivatives covering 495 pages. Run the incremental builder after source/index changes; do not index arbitrary workspace files, authentication settings or error logs. See `catalog/README.md`. Source and artifact hash checks had zero issues at the recorded snapshot.

Run `python reports/geography/reconcile_counties.py` after refreshing the Trellis catalog to update geography reports. The initial reconciled snapshot found two title/URL conflicts (Jackson/Washington and Sarasota/Manatee in Florida) and ten special jurisdictions that were not forced into Census counties. Website extraction version `2-website-href` uses exact observed HTML hrefs while retaining truncated display values and source provenance. CISA and Trellis entry queues are frozen batches; do not regenerate them solely to restart an active collector.

When the continuation OCR worker is idle, run `python pipeline/prepare_court_ocr.py` to screen newly downloaded court PDFs and reuse verified earlier screenings. Then run `./scripts/start_collector.ps1 -Job ocr-courts`. Its output is `corpus/official_courts/ocr/`, with per-page coverage and a `status.json` that counts only selected OCR pages. The initial continuation snapshot screened 254 PDFs / 9,716 pages and queued 355 scan pages across 40 PDFs. Sparse vector-only pages are flagged for review, and blank pages are skipped. Preparing while OCR is running is not supported.

The next court screening at 2026-09-13T09:04:03Z covered 282 PDFs / 10,729 pages and queued 502 scan pages, reusing the earlier 355 completed pages. The official-law originals now have the same page screening through `pipeline/prepare_law_ocr.py`. The `./scripts/start_collector.ps1 -Job ocr-laws` job first prepares a snapshot of successful saved PDF metadata, verifies the original hashes, then runs selected-page OCR under `sources/official_laws/ocr/`. It makes no network requests and does not alter the source metadata, documents or collector text. An unchanged source hash reuses its prior screening and verified OCR results. Do not run preparation against an OCR directory while its worker is active. Source-snapshot errors, sparse vector pages and screening failures remain explicit review items.

The first law screening finished at 2026-09-13T09:20:23Z: 3,418 unique PDF payloads / 50,494 pages (the original per-URL count is 3,420 PDFs / 50,498 pages). It found 245 scan pages across 30 PDFs; all 245 completed OCR with zero failed pages. It also flagged 1,132 sparse vector/text pages for possible review and skipped 55 blank pages. These flags are not proof of missing text, and OCR completion is not a guarantee of transcription accuracy. Refresh the unified index to include the completed derivatives.

The first independent generic court process (PID recorded in its active-run file) was launched before a harmless wrapper exit-code reporting fix. If that legacy process ends with `SystemExit: 0`, inspect its crawler checkpoint: exit code zero is successful, not a download failure. New launches handle zero correctly.

## Public HTTP crawler

See `pipeline/README.md` for its exact scoped config and seed schema. Ingest only observed, reviewed source paths. Use a separate `corpus/<collection>` directory and avoid overlapping workers. The current launcher uses hidden Windows WMI-created Python processes so editor/agent child-job cleanup does not terminate long downloads. It saves PID/command/log paths and prevents duplicates. Verify actual PID/command and fresh log progress; an old `active_run.json` alone is not evidence of a running process. Never report background work as complete.

Generic crawler v1.0.2 now coordinates exact hosts across processes through `corpus/_shared_hosts/hosts.sqlite3` and OS locks. After stopping the earlier generic workers, their saved pacing, robots policies, cooldowns and blocks were imported from all three archives. The focused law-page and recovery workers restarted at approximately 2026-09-13T09:22:50Z. Court/county workers remain paused by user scope. The shared coordinator preserves Arizona's 120-second delay and longer host policies while eligible hosts can proceed. Scheduling deferrals consume no attempt or retry budget. See `pipeline/README.md` for migration details; future generic collections must use the same coordinator.

A 30-minute Codex heartbeat named `Continue legal corpus collection` is active in this task. Its automation ID is `continue-legal-corpus-collection`. It resumes unfinished accessible work and should notify only on meaningful changes or required user action, then pause when only unresolved access blockers remain.

## Completion and stopping

Continue accessible work in the user's three-phase scope. Record meaningful errors and required user actions, and keep batches focused rather than crawling every discovered public URL. The original all-case corpus is no longer the active completion target. Completion of the narrowed scope requires reconciled law, judge and county inventories with preserved records and explicit access/OCR/edition gaps. A drained bounded queue alone is insufficient.

The law recovery OCR finished at 2026-09-13T09:57:23Z: all 218 selected scan pages from the West Virginia original constitution completed with zero failed pages. The 55 recovered PDFs contain 1,434 total pages; the other 1,216 pages retained embedded text. Reuse these completed screenings. The 2026-09-13T10:41:29Z search-index build now includes this verified derivative. That snapshot contains 12,550 source records and 12,087 distinct searchable texts, with zero file/hash reference issues.

The Trellis batch worker checkpointed at 2026-09-13T10:09:53Z with one Firecrawl credit remaining and no active remote batch. It saved all 401 batch results. Current scoped captures include 567 law pages, 46 judge directories, 841 county profiles and 46 coverage pages. `sources/trellis/worker/credit_pause.json` records the verified balance and resume condition. Do not repeatedly relaunch the worker or repeat the same user notification while credits are unchanged. Direct official-law collection remains active.

The saved law-page PDF snapshot has completed selective OCR through `./scripts/start_collector.ps1 -Job ocr-law-pages`. The launcher prepares a read-only snapshot under `corpus/official_law_pages/ocr/`, preserves embedded text and originals, then runs selected-page OCR using the verified local model. It has a separate worker lock and its own status files. Do not repeat preparation with unchanged inputs or run a second preparation while that job is active. Its 16 completed derivatives are included by the unified index.

The 90 observed Nebraska full statutory chapters were ingested once into `corpus/official_law_nebraska_chapters/` and completed through `./scripts/start_collector.ps1 -Job official-law-nebraska`. Inputs and verified source-redirect hashes are under `sources/official_laws/continuation/redirect_followup_20260913/`. Do not use the preparer README's older proposed import directory or reingest the batch. The downloaded chapter text contains the actual statute sections and preserves section symbols without replacement characters. Its bounded queue is complete; it used the same shared host coordinator.

The offline Word-format pass extracted all 48 DOCX lawbooks into `corpus/official_law_pages/document_derivatives/`, with separate original/metadata hashes, text hashes and parsing provenance in `manifest.jsonl`. It produced 119,633,549 bytes of text with zero errors. Content inspection subsequently identified the 75 apparent DOC files as direct Word 2003 XML, not legacy binary DOC. Their separately validated text is under `xml_document_derivatives/` (Pennsylvania constitution plus 74 statutory titles; 29,262,301 UTF-8 bytes). The index now has an explicit parent-verified document-text adapter for DOCX, Word XML and the verified Iowa EPUB. Preserve original declared MIME and the detected-format evidence; do not rerun the obsolete legacy-converter investigation.

The 90 Nebraska full-chapter batch completed at 2026-09-13T10:52:56Z with 90 downloads and no failures. The additional law-page OCR pass also completed: 672 PDFs / 84,425 pages screened, 52 selected scan pages across 16 PDFs processed, zero preparation or OCR errors. Neither finished job should be restarted with unchanged inputs.

The remaining original law queue has specific constraints documented in `reports/law_source_constraints.json`: Arizona continues under its 120-second delay; distinct slash redirects are normal and not a URL loop. South Carolina's cached robots denies all paths, even though a pacing-before-classification issue leaves 566 rows technically pending. Illinois blob storage has a robots-401 pause and Hawaii has a target-403 pause. Keep the underlying state/evidence intact; these pending counts are not a claim that those hosts are being fetched.

All 144 legal members of the three saved Colorado ZIP packages were streamed, hashed, and matched exactly to already captured standalone DOCX/HTML/PDF files. `document_derivatives/archive_member_reconciliation.jsonl` records the verified associations. The archives need no duplicate document extraction or new downloads. The one non-document image member remains inside its original ZIP.

The saved Iowa EPUB extraction completed offline at 2026-09-13T11:39:32Z: all 2,308 reading-order XHTML parts produced 51,529,513 UTF-8 text bytes. The source title is **2022 Code of Iowa**, not an assertion of current law. `corpus/official_law_pages/epub_document_derivatives/manifest.jsonl` preserves original/metadata hashes, all 2,319 member hashes, edition metadata, part order, parser limitations and the recorded mimetype packaging deviation. Six safety/order fixtures and independent original/text hash and spine-order checks passed. The separate saved MOBI remains unparsed; do not imply it was extracted or equivalent.

The production index build at 2026-09-13T11:46:14Z (builder 1.3.0) contains 12,787 source records, 12,324 distinct searchable texts and 1,026,014,179 indexed characters. It added the 90 Nebraska chapters, 16 law-page OCR derivatives, 48 DOCX derivatives, 75 Word XML derivatives, one Iowa EPUB derivative and seven newly saved Arizona pages. File/hash validation found zero issues. The index retains historical out-of-scope captures without restarting their queues. The original law-page collector remains active; Trellis remains checkpointed at the previously reported one-credit reserve.

`python scripts/build_law_queue_status.py` makes an offline snapshot in `reports/law_queue_status.json`. It separates ordinary paced network work from pending rows already constrained by saved host pauses or hash-verified robots evidence, without changing any crawler row, source file, pacing or access policy. The 2026-09-13T13:04Z snapshot had one Arizona title page still requiring network work and 613 rows with saved barriers (566 South Carolina, 39 Illinois, eight Hawaii). Rebuild the snapshot before a phase decision. The checker also considers the separate browser allowance: review a finite substantive law batch using a fresh live account observation before treating Trellis acquisition as exhausted. Once prepared accessible law work is exhausted and no remote Trellis batch is active, checkpoint the law collector and advance to reviewed judge sources with explicit law gaps. Do not wait indefinitely for the South Carolina pacing deadline, clear the pause, or declare statewide law completeness. Additional accessible law work identified by the jurisdiction audit still needs review first.

Arizona `/arsDetail/?title=N` captures are statute title/chapter/section navigation, not full statute bodies. The original constitution capture is also an article directory; its retained update notice is stale, so it does not establish the constitution's current edition. No full Arizona constitution body has yet been established by the saved collection. Law-source PDF capture totals also contain some ancillary legislative materials. Preserve these sources and distinguish them from substantive legal text in the jurisdiction coverage audit.

## Browser law collection and latest verified checkpoint

The signed-in Chrome method is documented in `corpus/trellis_browser_laws/README.md`. Its separate manifest contains 38 Arizona Constitution Article 2 section captures and their observed directory, with all observed child links reconciled and no missing section in that bounded listing. Raw selected DOM, exact legal text, timestamps and hashes are preserved; no cookies, account identity or credentials are exported. These are browser-rendered captures, not original HTTP responses or Firecrawl results. The local writer `scripts/trellis_browser_archive.py` makes no Trellis requests and runs only during an active browser batch; both prior helper processes were stopped after collection. Use the documented expected-source-URL wait when saving through its local form.

Account Overview at approximately 2026-09-13T12:50Z showed 59/75 content views used, leaving 16. This supersedes the older 17/75 observation. Check it live before selecting another finite substantive batch, budget directory visits and retain at least one view. Do not attribute the full change in account usage to this collector or purchase more views. Firecrawl remains separately paused at its previously observed one-credit reserve. If provider collection becomes available again, reconcile these browser URLs before scheduling duplicates; do not mark provider queue rows downloaded using browser artifacts.

The production index build at 2026-09-13T12:51:41Z, builder 1.4.0, contains 12,859 source records and 12,396 distinct searchable texts, including all 39 browser captures. File/hash validation found zero issues. The combined known scoped Trellis inventory is 1,539 saved of 25,668 URLs (6.0%); it is a growing discovered inventory, not proof of the full corpus denominator. Original/recovery/Nebraska document batches and the DOCX, Word XML, Iowa EPUB and selected OCR passes are completed; reuse unchanged results.

The offline jurisdiction audit is in `reports/laws/`, covering 51 jurisdictions and 154 category rows. Its snapshot retains 7,976 downloaded official-law URLs and 7,926 distinct raw payloads, with explicit gaps, editions and navigation/ancillary classifications. Fourteen category rows have no downloads and 24 have no verified nonempty text. No entire state or legal category is asserted complete. The bounded Arizona bulk-source review is `reports/arizona_bulk_source_review.json`; its reviewed candidates did not establish a current full constitution download.

Judge phase preparation is ready in `sources/official_judges/phase2_preparation/`. It identifies 91 already saved roster URLs in 27 jurisdictions, eight saved individual profiles, and 46 exact observed unfetched sources across eight states. No judge worker has started for this batch. Review its README and exact-path config when the law phase checkpoint permits advancing; keep the broad court queue paused. Preserve the staged sources' access, edition and jurisdiction gaps and do not equate roster rows with unique judges.

At 2026-09-13T13:06Z the prepared direct-law queue reached 4,290 downloads and zero accessible pending network URLs. The remaining 613 pending rows have the saved barriers described above. PID 14972 was verified and stopped while no resource was fetching; its `operator_pause.json` and active-run status record the checkpoint without changing source rows or host controls. Do not restart this idle queue without reviewed new accessible inputs or evidence a barrier changed. The finite Trellis browser law review remains before advancing to judges; the overall law corpus is still incomplete.

## Renewed Firecrawl law batches

The user supplied a replacement account key and asked to speed up. At 2026-09-13T19:35:41Z the official credit endpoint verified 1,400 credits; the key was replaced in the existing Windows user DPAPI file outside the archive and its decrypt/encrypt round trip was verified. The queue endpoint at 19:38:11Z verified `maxConcurrency: 2` and no existing jobs. `sources/trellis/worker/credential_changes/` records these key-free responses. CLI status setup stalled and its exact helper was stopped; successful direct official API checks established the balance and concurrency instead.

The hidden `firecrawl-batch` worker restarted at 19:41:33Z (PID 43988 at launch; always verify it live). Its launcher now selects 50-page batches, bounded by the current credit balance minus a one-credit reserve. The provider still uses two concurrent browsers and the 31-second submission interval. `--cache-max-age-ms 86400000` allows provider-cached versions up to 24 hours old; `--page-timeout-ms 180000` accommodates the larger queue. Formats remain Markdown, HTML and links, with basic proxy and verified TLS. Each prepared job retains its request options across restart, and cache metadata remains in its original provider result. These settings improve batching/cache throughput without asserting a measured speed multiplier. The 16 focused provider tests passed, including larger-batch credit limits and restart option preservation. See the official [batch contract](https://docs.firecrawl.dev/api-reference/endpoint/batch-scrape), [rate limits](https://docs.firecrawl.dev/rate-limits), and [cache behavior](https://docs.firecrawl.dev/features/fast-scraping).

The browser batch added all nine observed Article 12 county provisions and all three Article 16 provisions, using their already saved provider directories as enumeration evidence. There are now 51 browser captures (50 leaf texts and one directory). Account Overview immediately afterward showed 74/75 views used, approximately 19:33Z; its earlier counts are history. The local receiver PID 45064 was verified and stopped and its form/account tabs were closed. No background browser collection is running.

Before the provider restart, `scripts/reconcile_browser_law_queue.py` validated all 51 browser captures and reconciled their exact URLs as `captured_elsewhere`: 13 matching pending rows updated and 38 absent capture placeholders inserted. The report and before/after mapping are in `corpus/trellis_browser_laws/provider_queue_reconciliation/`. It preserved provider response paths, attempt counts, 98,296 unrelated frontier rows and all 1,026 prior attempt rows; nine offline checks passed. Repeat that scoped reconciliation under the worker lock only if additional browser captures are later added. Do not mark these records as provider downloads or overwrite their original browser provenance.

The focused review in `reports/laws/gap_review_20260913/` found no new comprehensive official document URL among the previously empty categories. Wyoming's constitution is already saved as `title97.pdf` under a statutes provenance context (81 pages; original and text hashes verified), so no duplicate download is needed. The other 23 category gaps remain explicit. The renewed Trellis credits keep laws as the active phase; judge acquisition has not begun.

The first renewed 50-page batch completed successfully. `reports/firecrawl_restart_first50_validation.json` records 50 HTTP-200 provider results, including 27 pages with law-text containers and 23 law directories, with zero validation issues. Their reported cache state was `miss`; no cache-derived speed multiplier is claimed. By the 19:47Z worker snapshot, 180 new provider captures had saved and collection remained running. The production index build at 19:46:47Z included the first 98 newly cataloged provider captures, 12 new browser sections and eight final Arizona navigation pages: 12,977 source records, 12,514 distinct searchable texts and zero file/hash reference issues. Later downloads await the next meaningful index refresh; do not repeat a build just to keep up with every page.
