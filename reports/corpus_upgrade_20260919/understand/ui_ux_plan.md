# UI/UX and navigation plan for the litigation research MVP (ui-ux-audit)

Scope: read-only audit of `delivery/archive-directory` (index.html, app.js 861 lines / 130 KB, styles.css 62 KB,
server.py + adapters), `delivery/ui-sketch` (Sep 13 concept), the literal `const M` / `const DATA` tables of
`C:/Users/firas/Downloads/litigation_source_browser.html` (parsed as JSON, never executed), and live GET calls to
http://127.0.0.1:8769 on 2026-09-19 ~04:25Z. No project file was modified.

---------------------------------------------------------------------------------------------------

## 0. What exists today (measured)

### Routes (hash router `#view/id?params`, `views` table at app.js:5-22, dispatcher `render()` at app.js:834)
Sidebar: Home `#overview`, Laws & rules `#laws`, Judges `#judges`, Counties `#counties`, Source directory `#sources`,
Collections `#collections`, All documents `#documents`; collapsed "Library details": `#federal`, `#datasets`, `#library`.
Detail routes: `#county/<geoid>` (tabs overview / rules / access), `#judge/<id>`, `#people`, `#person/<id>`,
`#source/<id>`, `#collection/<id>`. Documents open only in a `<dialog>` (`openRecord`, app.js:824) - there is **no
deep-linkable record route**, no CSV export, no copy-citation (grep for `record/`, `clipboard`, `download=` = 0 hits).

### API (server.py:587-650)
`/api/summary`, `/api/datasets`, `/api/documents`, `/api/explore`, `/api/sources`, `/api/source`, `/api/county-registry`,
`/api/counties`, `/api/judges`, `/api/judge`, `/api/people`, `/api/person`, `/api/collections`, `/api/collection`,
`/api/record`, `/api/text`, plus hash-verified byte routes `/files/`, `/library-assets/`, `/source-assets/`, `/judge-images/`,
`/bulk-files/`.

### Filter reality per page
| Page | Filters the UI offers | What the data could support but UI/API does not |
|---|---|---|
| Documents / Laws (`/api/documents`) | q, state (flat, 56), category (8 coarse buckets derived by string heuristics in `categories.py`), kind (only if already in the URL), availability (text / original / link_only), dataset, county geoid | **No date field in list items at all**; `browse` table has no date column. No file-type filter although payload has it (seeger sample: pdf 252 / docx 36 / doc 12 of 300). 116+ raw `kind` values. Review state is hidden inside `kind` (`needs_content_review` 7,187; `law_document_title_evidence_needs_review` 2,826; `county_government_entry_unreviewed` 1,027; `county_government_website_to_verify` 660). 13,322 of 58,310 browse rows have empty `state`. |
| Source directory (`/api/sources`) | q, jurisdiction (55), category (27; **uncategorized 3,648 = 39%**), access method (api 16 / download 1,980 / web 7,352), verification (8,349 historical / 999 not verified), availability (saved 32 / archived 554 / links only 8,762), `api_bulk=1` | Items already carry `layer`, `task_family`, `content_kind`, `source_type`, `access_requirements` but the **live server ignores those params** (every one returns total 9,348) and returns only 5 facets. `source_directory.py` on disk was changed at 04:24:39Z (after the 03:12:07Z server start) to add `TYPE_FACETS`; the running process has not loaded it and `app.js` has no controls for it. |
| Judges (`/api/judges`) | q, state, system (federal 4,454 / state 4,413), court (flat select of several thousand free-text names, e.g. "102nd District Court" and "102nd District Court of Texas" as separate options), sort, has = details 5,971 / all 10,698 / biography 1,605 / analysis 118 / photo 43 | No circuit/district hierarchy, no status (active/senior/terminated), no appointing president, no MDL flag, no date filters. Only **2 federal judges have any analysis**. Martinotti, Chhabria, Rosenberg, Fallon, Brody, Polster, Caldwell all exist as `consolidated_entity` with `analysis_count` 0 and no MDL linkage. |
| Counties (`/api/counties`) | q (name/GEOID), state, availability (local_resources 568, saved_information 2,150, none 2,576, court_registry 374) | No court-type, no "has local rules / forms / clerk / judges" split. Registry only KY + TX. |
| Collections (`/api/collection`) | one free-text box | Adapter already accepts `family` and `kind`; UI never sends them. Settlements: 848 rows, status on 848 (448 "Claim window closed", 365 "Open for claims"), claim_deadline 614, status_as_of 848, official_url 848, **court_label 9, state 0, applicable_states 76, documents 3**. MDL-3080: 1,612 PDFs cataloged, only 24 previewed; titles encode docket number + filing date ("0001. (08-04-2023) ORDER ...") that is not parsed into fields. |

### Temporal reality
Sampled `records.payload` (every 37th row, up to 300 per dataset): seeger `captured_at` 270/300, `metadata.source_date`
1/300; focused `retrieved_at` 300/300 and no source/effective date; judge_enrichment FJC rows carry nomination /
commission / senior-status / termination dates. `evidence_dates.py` already models `source_as_of`, `saved_at`,
`effective_date` correctly, but only the reader dialog shows them (`evidenceDates`, app.js:63); list cards show no date.
Conclusion: a date filter today can honestly be offered only on **capture date**, plus docket/filing dates for MDL-3080,
deadlines/status dates for settlements, service dates for judges. Everything else must show "Unknown".

### 390 px and accessibility check (live, emulated 390x844, 7 routes)
No horizontal overflow on `#overview`, `#sources`, `#judges`, `#documents`, `#counties`, `#collection/settlements`, `#laws`
(scrollWidth = clientWidth = 390). Filter forms already consume 223-326 px before the first result; `#sources` page is
10,555 px tall. `#collection/settlements` has 23 of 87 interactive elements under 24 px tall. Good foundations already
present: skip link, `aria-live` announcer, `aria-current`, focus return on dialog close, `prefers-reduced-motion`,
`textContent`-only rendering. Gaps: only 5 `:focus-visible` rules, light scheme only, tabs in judge profile and county page
are links/buttons without `role=tablist` semantics, filter chips use `aria-pressed` (fine) but facet counts are embedded in
option text.

### Ideas worth carrying over
- `litigation_source_browser.html`: facets t (14 task families), c (27 categories), k (8 content kinds), l (31 layers),
  j (55 jurisdictions), v (verified flag); counts are computed "filtered except own dimension" (`filteredExcept(dim)`);
  removable pills; sort curated/name/state; CSV export of the filtered set with columns
  name,url,jurisdiction,category,task_family,format,layer,domain,verified. Distribution: courts-procedure 4,191,
  law-authority 1,717, untagged 838, regulatory-administrative 799, settlement-recovery 374, ... complex-litigation 68;
  layers state_resource 4,956, court_practice 1,750, ... mdl_practice 15; kinds page 7,352, pdf 1,676, xlsx 136, zip 104,
  docx 61, api 16, json 2, csv 1.
- `ui-sketch`: master/detail split (list left, selected record right), "Coverage & gaps" page, copy source reference,
  CSV export. None of these made it into the MVP.

---------------------------------------------------------------------------------------------------

## 1. Navigation map (proposed)

Keep the hash router and one `views` table. Sidebar becomes five labelled groups (`<p class="nav-label">` already exists).
New areas render an honest empty state ("No saved data yet - see Source directory references: N") until their
supplement passes its hash gate; nothing is shown as populated before data exists.

```
RESEARCH
  Home                      #overview
  MDLs & mass torts         #mdls            -> #mdl/<mdl_no>          NEW
  Settlements               #settlements     -> #settlement/<id>       NEW (promoted from #collection/settlements)
  Judges                    #judges          -> #judge/<id>            (+ #people, #person/<id> unchanged)
LAW
  Laws & rules              #laws            (sub-tabs: Statutes & codes | Regulations | Court rules | Local rules &
                                              standing orders | Forms | Jury instructions | Constitutions)
  Regulations & agencies    #agencies        -> #agency/<slug>         NEW
COURTS & PLACES
  Courts & courthouses      #courts          -> #court/<court_id>      NEW
  Counties                  #counties        -> #county/<geoid>        (+ new tabs)
  Court statistics          #stats           -> #stat/<table_id>       NEW
PEOPLE & ORGANIZATIONS
  Firms & attorneys         #firms           -> #firm/<id>, #attorney/<id>   NEW (hidden until a supplement is ready)
REFERENCE
  Source directory          #sources         -> #source/<id>
  All documents             #documents       -> #record/<id>           NEW deep link (dialog stays as quick view)
  Relationship view         #relations?focus=<type>:<id>               NEW
  Library details           #datasets, #federal, #library, #coverage   (#coverage NEW, from ui-sketch)
```

### Per-area contract
| Area | Lists | Filters (shared model, section 2) | Detail page shows | Links out to |
|---|---|---|---|---|
| **MDLs & mass torts** `#mdls` | One card per MDL: MDL no., caption, transferee district, presiding judge(s), status (pending / closed / terminated as published by JPML), pending-action count **with its report date**, product/defendant tags, counts of saved documents and settlements | jur (circuit/district), status, category (products liability / drug / device / data breach ... as published), judge, date_type = transferred / report_as_of / filed, has = documents / settlement / leadership order | `#mdl/3080`: header facts with source + as-of; tabs **Docket & documents** (MDL-3080: 1,612 PDFs, parse "NNNN. (MM-DD-YYYY) TITLE" into docket_no / filed_date / doc_type ORDER, CMO, PTO, MOTION, BRIEF, EXHIBIT, TRANSCRIPT), **Orders & CMOs**, **Leadership / PSC** (firms, attorneys from appointment orders), **Settlement**, **Regulatory context** (FDA / agency records tagged to the product), **Source references** (source-directory rows with layer `mdl_practice` or task family `complex-litigation`, 68 rows) | judge, court, settlement, firm, agency, record, source |
| **Settlements** `#settlements` | Table/cards: title, type (mass tort / class / AG / government), court, judge, MDL no., status + `status_as_of`, claim deadline, amount as published, administrator, document count | jur, status bucket (open / closed / pending approval / paying), type, date_type = claim_deadline / status_as_of / final_approval, has = documents / official site / court identified, authority (official site vs aggregator), review | `#settlement/<id>`: facts with per-field evidence label; **standardized document shelf** in fixed order: Settlement agreement - Preliminary approval order - Long-form notice - Short-form notice - Claim form - Plan of allocation - Fee motion - Final approval order/judgment - Administrator FAQ - Other; each slot = saved file (sha256, bytes, pages, captured_at) or "not saved - official link" | mdl, court, judge, firm, record, source |
| **Regulations & agencies** `#agencies` | Agency cards (FDA, CPSC, NHTSA, EPA, OSHA, CMS, SEC, FTC, DOJ, state AG / state agencies) with counts by record family | agency, family (CFR part, Federal Register notice, guidance, warning letter, recall, 510(k)/PMA/NDA, MAUDE/FAERS dataset, enforcement action, SEC filing), jur, product/defendant tag, date_type = published / effective / captured, ftype, dtype | `#agency/fda`: tabs Regulations (CFR titles/parts) - Guidance - Enforcement & recalls - Data & APIs (source-directory rows category `adverse_event_data` 40, `recall_safety_data` 45, `enforcement_actions` 241, `regulations_register` 527, `agency_guidance` 170) - Saved documents | mdl, record, source |
| **Courts & courthouses** `#courts` | Tree: Federal -> circuit -> district -> division/courthouse; State -> court level -> county. Seeds available now: 269 court registry entries (207 federal/special, 56 state, 6 local), 295 court marks, KY/TX county registry (374 counties) | jur, court level (appellate / district / bankruptcy / state trial / state appellate / special), has = local rules / standing orders / forms / ECF procedures / HSD order / judges / logo, review | `#court/njd`: seal/mark (with `permission_status`), website, clerk, courthouse addresses (county FIPS only when explicit), tabs **Rules & standing orders**, **Forms**, **Filing instructions** (CM/ECF, HSD procedures, pro hac vice, fees), **Judges**, **MDLs here**, **Statistics**, **Source references** | judge, mdl, county, stats, record, source |
| **Counties** `#county/<geoid>` | unchanged list + availability | add: court type present, has local rules / forms / clerk / judge seats, state-law link | add tabs **Courts & clerks** (exists as "access"), **Judges** (registry seats; link to profile only when identity-reviewed), **Local rules & forms**, **State law** (deep link `#laws?jur=st:KY`), **Filing activity** (publisher-reported Trellis/official counts, labelled) | court, judge, record, source |
| **Court statistics** `#stats` | Catalog of saved tables: publisher, series (e.g. uscourts.gov Caseload Tables C-1, C-3, C-5; Judicial Business; JPML pending MDL report; state court annual reports), reporting period, geography level, file type | publisher, series, period (reporting_period_end range), geography level, court, ftype, authority | `#stat/<id>`: metadata, period + "as published", download of original XLSX/PDF/CSV, first-N-rows preview of parsed table, "used by" links. No derived rates unless numerator/denominator/period are shown | court, mdl, source |
| **Firms & attorneys** `#firms` | Firms: name, offices, MDL leadership roles count, settlements count. Attorneys: name, firm, bar jurisdictions, native IDs (CourtListener attorney id, state bar no.) | jur, role (lead / co-lead / PSC / liaison / defense), mdl, has = leadership order evidence, authority | Firm page: roles table (MDL, role, order date, evidence document), attorneys, settlements; Attorney page: appearances with native IDs; **never merged by name alone** - unmerged look-alikes listed as "possible same person (not confirmed)" | mdl, settlement, record |
| **Relationship view** `#relations` | Focus entity header + grouped neighbor lists (see section 3) | entity type, relation, basis, date range | n/a | everything |
| **Coverage & gaps** `#coverage` | Matrix state x family (statutes / regs / court rules / local rules / forms / judges / county registry) with counts and "none saved" cells; per-MDL-judge completeness | jur, family | click-through into the filtered list | all lists |

Home (`#overview`) gains a "Start from a matter" row: MDL search box + top pending MDLs, and "Start from a place": state
picker -> state hub (laws, regs, courts, counties, judges, source references for that state in one page, which is what the
DOJ state-by-state law library pages model).

---------------------------------------------------------------------------------------------------

## 2. Unified filter model

One spec-driven component `filterBar(spec, onChange)` replaces the three hand-built forms (`renderFilters` app.js:239,
`renderSourceDirectory` :453, `renderJudges` :654). All list endpoints accept the same parameter names and return the
same `facets` envelope `{name:[{value,label,count}]}` (already the shape `/api/sources` uses). Facet counts are computed
"filtered by every dimension except its own" (the litigation browser's `filteredExcept`), so a user never selects into
zero results.

**Name collision to avoid:** `from` is already a route parameter holding the back-link hash (`routeLink(...,{from:location.hash})`,
`readFilters` preserves it). Date bounds therefore use `dfrom` / `dto`.

| Param | Meaning | Canonical values | Derivation today | UI control |
|---|---|---|---|---|
| `jur` | Jurisdiction path | `us` ; `us:ca3` (circuit) ; `us:njd` (district, CourtListener court id) ; `us:njd:newark` (division/courthouse) ; `st:NJ` ; `st:NJ:34013` (county, 5-char FIPS string) ; `multi` ; `terr:PR` | `state` column, `record_counties`, source `jurisdiction`, judge `courts`. Legacy `state=New Jersey` and `jurisdiction=nj` stay accepted and are mapped server-side. Prefix match = hierarchy (selecting `us:ca3` includes `us:njd`). County only from explicit evidence (`record_counties`), never hostname | Three dependent selects: System -> Circuit or State -> District or County. On 390 px they stack; level 2/3 stay disabled until the parent is set |
| `family` | Document family (legal function) | statute, regulation, constitution, court_rule, local_rule, standing_order, form, jury_instruction, opinion, order, docket_filing, settlement_doc, agency_guidance, agency_enforcement, safety_data, statistics_table, directory_page, judge_profile, dataset, other | Extend `categories.py` from 8 to ~20 buckets; keep raw `kind` as secondary "Source classification" select (shown only inside an "Advanced" disclosure) | select with counts |
| `ftype` | File type of the preserved original | pdf, html, docx, doc, xlsx, csv, json, xml, zip, txt, image, api, none | `metadata.format`, stored Content-Type, file extension of `files.path`; source directory `content_kind` | select |
| `dtype` | Data type / representation (BRIEF rule) | source_reference, saved_page, original_file, extracted_text, published_record, structured_row, bulk_record, connector_response | dataset + has_original/has_text + adapter of origin (`open_us_law` = bulk_record; MCP = connector_response) | checkbox group (multi) |
| `avail` | What can be opened locally | text, original, both, link_only, archived | existing `availability` / source `has` (keep both as aliases) | select |
| `date_type` + `dfrom` + `dto` + `undated` | Which date the range applies to | captured, source_as_of, published, effective, filed, decided, deadline, status_as_of, service_start, reporting_period | see section 4. `undated=1` (default on) keeps records whose chosen date is unknown and shows the count "N without this date" | select + two `<input type="date">` + checkbox; presets "last 30 d / 12 mo / since 2020" |
| `authority` | Who published it | official_court, official_legislature, official_agency, official_other, nonprofit_or_assoc, commercial_or_thirdparty, institutional, connector | source `source_type` (4 values today), dataset (trellis = commercial, settlesignal = commercial), host allowlist `.gov/.us/uscourts.gov` as *hint only* labelled "official host" | select |
| `review` | Review status | reviewed, needs_review, unreviewed, to_verify, historically_verified, not_verified, rejected | currently encoded in `kind` suffixes and `quality`; source `verification_status` | select; default "any" with a persistent legend |
| `entity` | Relationship scope | `mdl:3080`, `judge:<id>`, `court:njd`, `county:34013`, `settlement:<id>`, `agency:fda`, `firm:<id>` | edges table (section 3) | hidden param set by "View all documents for ..." links; shown as a removable pill |
| `q`, `sort`, `page`, `limit` | unchanged | sort: relevance, title, date_desc, date_asc (on the selected `date_type`) | | |

Presentation rules
- Desktop: one row of primary filters (q, jur, family, date) + "More filters (n)" disclosure for ftype, dtype, avail,
  authority, review, source classification.
- 390 px: a single "Filters (n active)" `<details>` above results, closed by default; active pills always visible; "Show
  N results" button closes it. Keeps the pre-results block under ~120 px instead of today's 223-326 px.
- Every active filter is a removable pill (existing `activeFilters`), plus "Copy link" (URL already encodes state) and
  "Export CSV" of the current result set (server-side `format=csv`, capped 5,000 rows, includes id, title, jur, family,
  ftype, dtype, all date columns, source_url, sha256).
- Source directory gets the five facets already computed on disk (layer, task family, content kind, source type, access
  requirement) and a "Task" quick-row of 13 family buttons coloured as in the standalone browser.

---------------------------------------------------------------------------------------------------

## 3. Cross-entity relationship surfacing

### Data contract (one supplement, fail-closed like the others)
`sources/entity_links_<date>/edges.jsonl`, hash-gated by `validation.json`, loaded by a new adapter `entity_links.py`:
```
{"from":"judge:<profile id>","to":"mdl:3080","rel":"presides_over","basis":"jpml_pending_report",
 "evidence":{"record_id":"...","url":"...","sha256":"..."},"valid_from":"2023-08-04","valid_to":null,
 "as_of":"2026-09-02","confidence":"explicit_id|exact_url|published_statement|reviewed_name_plus_court"}
```
Node id namespaces: `judge:` (MVP profile id; carry `fjc_nid`, legacy `fjc_id`, `cl_person_id` separately), `court:`
(CourtListener court id for federal; `st:<STATE>:<slug>` for state), `county:<FIPS>`, `mdl:<no>`, `settlement:<id>`,
`record:<directory id>`, `source:<pld id>`, `agency:<slug>`, `firm:<id>`, `attorney:<id>`, `stat:<table id>`.

Relations to populate first (all from evidence that already exists locally or is one bounded packet away)
| Edge | Basis | Exists now? |
|---|---|---|
| record -> source (captured_from) | exact URL | yes: 554 linked references (`source_archive_links`) |
| source -> judge (profile recorded from page) | exact URL | yes: 104 judge entities |
| judge -> court (sits_on, with dates) | FJC service rows / CourtListener positions | yes in judge_entities + people layer (51,291 positions); needs court-id normalisation |
| court -> circuit/state (within) | static table | trivial |
| county -> court, county -> clerk, county -> judge seat | KY/TX registry (374 counties, 2,539 seats) | yes; judge link only when identity reviewed |
| mdl -> court, mdl -> judge | JPML pending-MDL report (one PDF/XLSX packet) | not yet; MDL-3080 -> njd / Martinotti can be asserted from the saved transfer order |
| mdl -> record (has_document) | collection membership | yes for MDL-3080 (1,612) |
| mdl -> settlement, settlement -> court/judge | settlement documents' captions | only 9 of 848 settlements have a court today |
| mdl -> firm/attorney (leadership) | PSC appointment orders in saved dockets | needs extraction |
| mdl/product -> agency record | explicit product tag | needs data |
| record -> record (cites) | citation extraction | later |

### UI
1. **"Connected records" panel** on every detail page (judge, court, county, MDL, settlement, source, record): groups by
   entity type with counts, each row = label + relation phrase + basis badge + validity dates, e.g.
   "Presides over MDL 3080 - Insulin Pricing - per JPML report as of Sep 2, 2026". Max 5 per group, "View all N" goes to
   the target list pre-filtered with `entity=`.
2. **Relationship view** `#relations?focus=mdl:3080`: not a force-directed graph. A three-column neighbor browser -
   left "points to this", centre focus card, right "this points to" - each a plain list grouped by type; clicking a
   neighbor refocuses (hash changes, Back works). At <=850 px it collapses to focus card + accordions. A path
   breadcrumb ("County 34013 > D.N.J. > Martinotti > MDL 3080 > Settlement") records the walk. Fully keyboard/AT
   operable, no canvas/SVG dependency, implementable in ~150 lines.
3. **Inline chips** on list cards: document card shows `MDL 3080`, `D.N.J.`; judge card shows `2 MDLs`; settlement card
   shows court + MDL chips. Chips are links (`routeLink`) not buttons.
4. **Integrity rules in the UI**: every edge shows its basis; `reviewed_name_plus_court` edges render with a "name + court
   match, reviewed" note; unreviewed name matches are never drawn as edges - they appear under "Possible matches (not
   linked)". Hostname never yields a county edge.

---------------------------------------------------------------------------------------------------

## 4. Temporal-awareness labelling rules

Server returns a uniform `dates` object on every list item and detail (extend `evidence_dates.document_dates`):
```
"dates":{"captured":"2026-09-12","source_as_of":null,"published":null,"effective":null,"filed":null,
         "decided":null,"deadline":null,"status_as_of":null,"reporting_period":null,
         "precision":{"captured":"day"},"basis":{"captured":"captured_at"},"primary":"captured"}
```
Rules
1. **Every date is printed with its type word.** Never a bare date. Fixed vocabulary: "Saved" (captured), "Source as of",
   "Published", "Effective", "Filed", "Decided", "Deadline", "Status as of", "Reporting period", "In office".
2. **Primary date per family** (what the card shows and what `sort=date_*` uses by default): statute/regulation/rule ->
   effective, else source_as_of, else "Effective date unknown - saved <date>"; opinion/order/docket filing -> filed/decided;
   settlement -> deadline + status_as_of; statistics -> reporting_period; judge analysis -> period + denominator; source
   reference -> source_as_of (2026-08-19 map date); everything else -> captured.
3. **Unknown stays "Unknown"** (muted style), never blank and never back-filled from HTTP `Last-Modified`, filenames, or
   URL path segments such as `/20210517/`. `Last-Modified` may appear only in the provenance block, labelled
   "Server file timestamp (not a legal date)".
4. **Precision preserved**: year-only and year-month values render as "2016" / "Jan 2016" (the `date()` helper at app.js:54
   already does this); ranges render "Jan 2016 - Dec 2025 (as published)".
5. **Staleness chip** computed client-side from `captured`: <=90 d none; 91-365 d "Saved N months ago"; >365 d "Saved over a
   year ago - check the source". For settlements: deadline in the past relative to today -> "Deadline passed" regardless
   of the stored status string; stored status always carries "as of <status_as_of>".
6. **Currency disclaimer by family**: law text cards show "Not verified as current law" unless an `effective` or
   `source_as_of` date exists; judge cards show "Current service not verified" when `current_service_verified` is false
   (field already in `/api/judges`).
7. **Snapshot-level dates** (Open US Law v2026.08, source map 2026-08-19, SettleSignal Sept 2026 snapshot) are shown once
   in the list header ("Bulk law snapshot: Aug 2026") and inherited by rows as `source_as_of` with
   `basis:"dataset_snapshot"`.
8. **Filter honesty**: choosing `date_type=effective` shows "N of M records have an effective date; K undated records
   are included/excluded" next to the results count.
9. **Timeline components** (judge career, MDL docket, settlement milestones) use an ordered list `<ol class="timeline">`
   with `<time datetime>`; undated items go in a trailing "Undated" group.
10. Publisher-reported analytics always print period, denominator, publisher and capture date in the card body (already
    done in `renderAnalysis`; keep as the pattern for court statistics).

---------------------------------------------------------------------------------------------------

## 5. API additions (all GET, read-only, loopback, JSON; each backed by a hash-gated adapter)

Shared list envelope: `{ready, total, page, limit, items, facets, dates_coverage:{<date_type>:{known,unknown}}, summary}`.
Shared params: section 2. `format=csv` on every list endpoint.

| Endpoint | Needed by | Notes |
|---|---|---|
| `GET /api/facets?scope=documents|sources|judges|counties|settlements|mdls|courts|agencies|stats` | filterBar | Cheap cached facet dictionary incl. the jurisdiction tree (`/api/jurisdictions` alias): nodes `{id,label,level,parent,counts:{documents,judges,sources,courts}}` |
| `GET /api/documents` (extend) | Documents, Laws | add `jur, family, ftype, dtype, date_type, dfrom, dto, undated, authority, review, entity, sort`; add `dates`, `ftype`, `dtype`, `family`, `review`, `bytes`, `pages`, `sha256`, `chips:[{type,id,label}]` to each item. Requires a sidecar index table (do **not** rebuild `directory.sqlite3`): `sources/document_facets_<date>/facets.sqlite3` keyed by record id, ATTACHed read-only like `archive` already is (server.py:413) |
| `GET /api/record?id=` (extend) | `#record/<id>` | add `dates`, `related` (first 5 per type), `citation` (pre-built plain-text reference string), `representations:[{dtype,url,sha256,bytes}]` |
| `GET /api/sources` (extend) | Source directory | restart picks up on-disk `layer, task_family, content_kind, source_type, access_requirements`; add `host`, `jur` prefix semantics, `format=csv` |
| `GET /api/mdls`, `GET /api/mdl?id=` | MDLs | list + detail; detail returns `documents` facet summary (doc_type counts, filed-date histogram by month), `judges`, `court`, `settlements`, `leadership`, `agencies`, `sources` |
| `GET /api/mdl-documents?id=&doc_type=&dfrom=&dto=&q=` | MDL docket tab | full 1,612-row catalog instead of the 24-item preview; fields docket_no, filed (parsed from title, basis `filename`), doc_type, pages, asset ids |
| `GET /api/settlements`, `GET /api/settlement?id=` | Settlements | list with status bucket facet computed server-side from `claim_deadline` vs today + stored status; detail returns `document_slots:[{slot,label,state:"saved|linked|missing",asset_id,url,sha256,captured}]` |
| `GET /api/agencies`, `GET /api/agency?id=`, `GET /api/agency-records?agency=&family=...` | Regulations & agencies | families listed in section 1 |
| `GET /api/courts`, `GET /api/court?id=` | Courts & courthouses | tree + detail; detail aggregates registry links, visual asset (with `permission_status`), rules/forms/instructions records (`entity=court:<id>`), judges, MDLs, stats |
| `GET /api/stats`, `GET /api/stat?id=`, `GET /api/stat-rows?id=&limit=` | Court statistics | table catalog, metadata, bounded row preview; originals through existing hash-verified asset route |
| `GET /api/firms`, `/api/firm?id=`, `/api/attorneys`, `/api/attorney?id=` | Firms & attorneys | gated by supplement readiness; return `ready:false` otherwise |
| `GET /api/related?type=&id=&rel=&limit=` | Connected-records panel, Relationship view | reads edges adapter; returns groups `{type,count,items:[{id,label,rel,direction,basis,valid_from,valid_to,as_of,route}]}` |
| `GET /api/judges` (extend) | Judges | add `jur` (circuit/district), `status` (active/senior/terminated as published), `appointed_by`, `mdl=1`, `court_id` (normalised) alongside free-text `court`; items gain `mdl_count`, `dates.in_office` |
| `GET /api/judge?id=` (extend) | Judge profile | add `mdls:[...]`, `related`, `evidence_summary:{opinions_saved,orders_saved,analyses,periods}`; no computed rates |
| `GET /api/coverage?by=state|mdl_judge` | Coverage & gaps | matrix counts by jur x family; per-MDL-judge completeness (bio, photo, orders, analysis) |
| `GET /api/counties`, `/api/county-registry` (extend) | Counties | availability facets split into rules/forms/clerk/judges; registry rows gain `court_id` and reviewed `judge_profile_id` |
| `GET /api/search?q=&types=` | global search box in the top bar | federated: returns top 5 per entity type (mdl, judge, court, county, settlement, agency, document, source) |

---------------------------------------------------------------------------------------------------

## 6. Prioritised build list (single integrator, vanilla JS, no rewrite)

Sizing: S = <= 0.5 day, M = 1-2 days, L = 3-5 days. "Data" = needs a supplement from another workstream first.

| # | Build | Size | Depends on | Why first / value |
|---|---|---|---|---|
| 1 | Restart-to-load + wire the 5 source-directory type facets (layer, task family, content kind, source type, access requirement) into `renderSourceDirectory` fields array; task-family quick row; CSV export | S | server restart by owner | Data and adapter code already on disk; closes the biggest gap vs the standalone browser |
| 2 | `#record/<id>` deep-link route reusing `renderRecord` in `main` (dialog remains quick view); "Copy link" + "Copy citation" buttons | S | none | Prerequisite for every cross-link and for platform integration |
| 3 | Show typed dates on all list cards (`Saved ...`, `Source as of ...`/Unknown) using fields the server already computes for the reader; staleness chip; vocabulary from section 4 | S | tiny `public_item` extension (needs payload join) | Temporal honesty everywhere with almost no new data |
| 4 | Mobile "Filters (n)" disclosure + sticky active pills; raise small tap targets to >= 24 px (settlement links); add `:focus-visible` to all interactive classes | S | none | Needed before adding more facets; 390 px |
| 5 | Spec-driven `filterBar()` replacing three hand-built forms; facets envelope; filtered-except-self counts on `/api/sources` (in-memory, trivial) | M | none | Makes every later page cheap |
| 6 | Settlements page promoted out of Collections: status bucket (computed from deadline vs today), deadline range, has-court / has-documents filters, standardized document-slot shelf, detail route | M | existing 848 rows; more value after settlement-document acquisition | High user priority; honest about 9/848 courts and 3/848 documents |
| 7 | MDL hub v1 for MDL-3080: parse titles into docket_no / filed date / doc_type; full 1,612-row catalog endpoint with doc-type + date filters; link to Martinotti + D.N.J. | M | local catalog only | Turns the largest unused local asset into a usable docket browser |
| 8 | Document facets sidecar (`facets.sqlite3`: record_id, family, ftype, dtype, review, captured, source_as_of, effective, bytes) + extended `/api/documents` params + extended `categories.py` families | L | build script reading payloads read-only (58,310 rows) | Delivers file type / data type / review / date filtering for the main corpus without rebuilding the 1.3 GB DB |
| 9 | Jurisdiction tree (`/api/facets` jurisdictions) + three-level dependent select; legacy `state=` mapping; court-id normalisation table for judges (collapses duplicates like "102nd District Court" / "... of Texas" only when state + number match explicitly) | M | static circuit/district table; FIPS from counties table | Federal circuit/district and state/county hierarchy across all pages |
| 10 | `entity_links` adapter + `/api/related` + "Connected records" panel on judge, county, source, record, collection pages, seeded with the edges that exist today (554 URL links, 104 source->judge, registry county->court, MDL-3080->njd->Martinotti, judge->court positions) | M | edges build script | Relationship mapping becomes visible immediately |
| 11 | Courts & courthouses area built from the 269-entry registry + 295 marks + KY/TX registry + rules/forms records via `entity=court:` | M | 9, 10 | Court rules / logos / forms / instructions by court |
| 12 | Judges upgrade: `jur` hierarchy, status, appointed-by, "MDL judges" preset, evidence summary block, MDL chips; coverage checklist of all current MDL transferee judges | M | JPML pending-MDL report packet (Data) | Addresses "judge analysis is very poor" with evidence, not invented rates |
| 13 | MDL list across all pending MDLs (JPML report) | M | Data | Multi-jurisdiction MDL coverage |
| 14 | Court statistics area (catalog + metadata + row preview + original download) | M | Data: uscourts.gov tables packet | Stats with period/denominator labels |
| 15 | Regulations & agencies area (FDA first) | L | Data: CFR/FR/FDA packets; source-directory rows available now as a reference-only v0 (S) | Agency/FDA regulation mapping |
| 16 | Relationship view `#relations` three-column neighbor browser + path breadcrumb | M | 10 | Navigation across entities |
| 17 | Coverage & gaps matrix `#coverage` | M | 8, 9 | Planning tool for further acquisition; integration-scope evidence |
| 18 | Global federated search box in the top bar (`/api/search`) | M | 8-11 | One entry point |
| 19 | Firms & attorneys | L | Data: PSC orders extraction, CourtListener attorney/party IDs | Last: highest identity-merge risk |
| 20 | Dark scheme + print stylesheet for record/citation pages | S | none | Nice-to-have |

Recommended order for one integrator: 1-4 (one day, no new data), 5-7, then 8-10 as the structural core, then 11-14.

### Implementation constraints to hold
- Stay in the existing idiom: `el()/append()/routeLink()/filterField()/setOptions()/activeFilters()/pagination()`, one
  entry in `views`, one `else if` in `render()`, one adapter module + one `if path==` line in `server.py`. No framework,
  no bundler, no external CDN, no `innerHTML` (the standalone browser uses `innerHTML` + manual escaping - do not copy that).
- Split `app.js` only by concatenation-safe sections (it is one deferred script); if it grows past ~200 KB add
  `app-areas.js` as a second `<script defer>` and one extra static path in `server.py:584`.
- Accessibility: every new tab set uses `role=tablist/tab/tabpanel` with arrow-key movement and `aria-selected`; tables get
  `<caption>` + `scope`; chips that navigate are `<a>`; counts are text, not colour-only; task-family colours must pass
  4.5:1 on `--surface` (the browser's `#8a5a12`, `#a04848` do; verify each); `announce()` on every result change (already
  the pattern); focus moves to `<h1>` on route change (currently to `main`); `prefers-reduced-motion` respected.
- 390 px: no horizontal page scroll (currently true on 7 routes - keep as a regression check); tables become stacked
  definition lists under 600 px (the existing breakpoint); filters collapsed by default; minimum target 24x24 CSS px,
  44 px for primary actions; relationship view becomes accordions; long URLs get `overflow-wrap:anywhere`.
- Security posture unchanged: loopback-only, GET-only, hash-verified bytes, sandbox CSP on served originals, all harvested
  text rendered with `textContent`.
- Integration readiness: every entity gets a stable namespaced id (section 3), every list endpoint a CSV/JSON export, every
  detail a `#<type>/<id>` permalink, every date a type + basis. That is the contract the external platform can consume.

---------------------------------------------------------------------------------------------------

## 7. Not verified
- No visual/screenshot review and no screen-reader or axe run; the 390 px check was a scripted overflow/target-size probe
  on 7 routes only (detail pages `#judge`, `#county`, `#source`, `#person` not probed).
- Did not read all of `app.js`/`styles.css`/`server.py` line by line; read the view table, filter, source, collection,
  judges, analysis, record and dispatcher sections and the route block.
- Payload date/format fill rates come from a 1-in-37 sample capped at 300 rows per dataset, not a full scan.
- Whether data exists for the new areas (JPML report, uscourts.gov tables, FDA/CFR, firms/attorneys, settlement
  documents) was not checked - those rows are marked "Data" and depend on other workstreams.
- Who edited `source_directory.py` at 04:24Z and whether its tests pass was not checked; the live/disk mismatch is reported
  as observed.
- `/api/people`, `/api/person`, `/api/datasets` responses were not inspected. Contrast ratios were not computed.
