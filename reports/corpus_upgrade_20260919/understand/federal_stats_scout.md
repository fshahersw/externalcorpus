# Federal court statistics, judge and MDL sources - scout report

Agent: federal-stats-scout. Scouted 2026-09-19 04:28-04:55 UTC (2026-09-18 local). Read-only; no project file modified.
No data file was downloaded. 39 HTTP requests total, all HTTP 200, no challenge/403/login page seen.

| Host | GET | HEAD | robots.txt | Notes |
|---|---|---|---|---|
| www.uscourts.gov | 22 | 3 | no Crawl-delay; `/sites/default/files/`, `/data-news/`, `/statistics-reports/` allowed; `/search/`, `/federal-court-finder/` disallowed | 25 requests = the per-host cap; 3.5 s spacing |
| www.jpml.uscourts.gov | 9 | 2 | **Crawl-delay: 10**; `/sites/jpml/files/` allowed | 10.5 s spacing |
| www.fjc.gov | 3 | 0 | **Crawl-delay: 30; Disallow `/research/idb/` and `/sites/default/files/idb`** | see Barriers (includes one spacing slip) |

Outputs
- Candidate list: `reports/corpus_upgrade_20260919/understand/packets/federal_stats_urls.jsonl` - 307 unique URLs, sha256 `5a195a79f56d9fa2245fadf731f2fd8bc1cfb1d928f29f5b4506668827f39f1f`
- Secondary list: `reports/corpus_upgrade_20260919/understand/packets/federal_hsd_order_urls.jsonl` - 98 per-court HSD order links on 95 hosts, sha256 `fe0489a12acd2a068d2b001a9bcd5ea4a2d4c4d88278d123268ce2b2ee81ac75`
- Receipts and tooling: `reports/corpus_upgrade_20260919/understand/_work_federal_stats/` (`request_log.jsonl` with URL, status, size, SHA-256 of each scouted page, HTTP Last-Modified; `fetch.py`, `tables.py`, `build_packet.py`). Scouted HTML bodies were kept in the session scratchpad only, not in the project.

Every URL in the JSONL files was read from a listing page fetched in this run. Nothing was constructed by pattern.

## 1. uscourts.gov structure

### 1.1 Data-table index (the one page that matters)
`https://www.uscourts.gov/statistics-reports/caseload-statistics-data-tables` is a Drupal view: 50 rows per page, default sort = reporting period descending, columns **Title / Table Number / Reporting Period / Publication Name / download links**. Query parameters (GET, no JS needed):

| Param | Meaning | Values observed |
|---|---|---|
| `pn` | publication | 531 BAPCPA, 32 Bankruptcy Filings, **530 CJRA**, 903 Delayed Notice, **33 Federal Court Management Statistics**, **79 Federal Judicial Caseload Statistics**, **77 Judicial Business**, **34 Judicial Facts and Figures**, **78 Statistical Tables for the Federal Judiciary**, 529 Wiretap |
| `term_node_tid_depth` | topic (hierarchical) | 36 District Courts > **68 Civil**, **810 CJRA**, 69 Criminal, 75 Magistrate Judges, **74 Trials** ...; **823 Judges** > 801 Active/Senior/Recalled, 800 Judgeships, 687 Judicial Complaints, 790 Judicial Vacancies; 217 Special Jurisdiction > **681 Judicial Panel on Multidistrict Litigation**; 37 Appeals; 38 Bankruptcy |
| `tn` | free-text table number | e.g. `C-3` |
| `m` | quarter end | 1 Mar 31, 2 Jun 30, 3 Sep 30, 4 Dec 31 |
| `y[year_between]` | year | 1990-2026 |
| `page` | pager | 0-based |

How a table is identified: **(publication, table number, reporting-period end date)**. The same table number (e.g. C-3) exists in three publications with different period ends, so table number alone is not a key. Each row also has a detail page `https://www.uscourts.gov/data-news/data-tables/YYYY/MM/DD/<publication-slug>/<table-slug>` (used as `parent_page` in the JSONL).

File URLs live under `/sites/default/files/document/` with names like `stfj_c3_630.2026.xlsx`, `fjcs_c3_0331.2026.xlsx`, `jb_c3_0930.2025.xlsx`, `jff_4.5_0930.2025.xlsx`, `fcms_na_distprofile0630.2026.xlsx`, `cjra_7_0331.2026.pdf`. The naming is **not reliable enough to generate**: STFJ uses `630.2026` without the leading zero, one June 2026 file carries a `_1` suffix (`stfj_d14_630.2026_1.xlsx`), FCMS pages link explanations as `/file/27866/download`, and pre-2015 files use names like `S19Sep14.pdf`. Always read URLs from the index.

### 1.2 Publications, cadence, formats, latest period found

| Publication | Cadence (period end) | Latest period on site | Formats | Mass-tort value |
|---|---|---|---|---|
| Statistical Tables for the Federal Judiciary (STFJ) | listed for June 30 (Dec 31 not checked) | **June 30, 2026** | **xlsx only** | freshest civil C-series, T-series, X-1A |
| Federal Judicial Caseload Statistics (FJCS) | March 31 | **March 31, 2026** | xlsx only | same tables, earlier period |
| Judicial Business (JB) | annual, Sept 30 (fiscal year) | **September 30, 2025** | pdf + xlsx | fullest civil set (28 civil/trial/JPML tables incl. C-11, C-3A, C-3B, C-12, S-19, S-20) |
| Judicial Facts and Figures (JFF) | annual, Sept 30 | **September 30, 2025** | pdf + xlsx | multi-year trend tables 4.1-4.12, 6.1-6.6, 1.1 |
| Federal Court Management Statistics (FCMS) | quarterly | **June 30, 2026** | pdf + xlsx | per-district profiles |
| Civil Justice Reform Act report (CJRA) | semiannual, Mar 31 / Sep 30 | **March 31, 2026** (report page says "Last updated: March 31, 2026"; HTTP Last-Modified of `cjra_8` is 2026-07-06, which is only a server date) | **pdf only** | the only official **per-judge** tables |

"Reporting period ending X" is what the index states. That the AO tables are 12-month periods was **not verified inside the files** (no file was opened).

### 1.3 Tables that matter most (all in the JSONL with exact URLs)

Priority 1 - civil filings/terminations by nature of suit and district, time to disposition/trial:
- **C-3** civil filings by jurisdiction, nature of suit and district (STFJ 6/30/2026 `stfj_c3_630.2026.xlsx`, HEAD 31,708 bytes; JB 9/30/2025; FJCS 3/31/2026)
- **C-11** product liability cases filed by nature of suit (JB 9/30/2025 only) and its trend twin **JFF 4.5**
- **C-3A / C-3B** civil cases pending / terminated by nature of suit and district (JB only)
- **C-4 / C-4A** terminations by nature of suit / district and action taken; **C-5** median time filing to disposition; **C-6** pending by length of time; **C-12** civil cases pending three years or more by nature of suit; **C-8** filings by origin (removals, MDL transfers); **C-2 / C-2A**, **C, C-1** totals and denominators
- **T-3** median time filing to trial (civil), **T-1/T-2/T-4/T-5** trials; **JFF 6.3** median times trend
- **X-1A** weighted/unweighted filings per authorized judgeship; **V-1** visiting judges; **JFF 1.1** judicial officers; **JFF 6.2, 6.6**
- **S-19 / S-20** JPML tables in Judicial Business (cases transferred by Panel order; cumulative MDL summary since 1968) - topic 681 has only these two tables, latest 9/30/2025
- **FCMS district profiles** `fcms_na_distprofile0630.2026.xlsx` (HEAD 255,793 bytes) and `...pdf` (listed 900.61 KB), plus "Comparison Within Circuit". One sheet/page per district with filings, terminations, pending, weighted filings per judgeship, median months filing-to-disposition and filing-to-trial (civil), civil cases over three years old, vacant judgeship months (measure list is from prior knowledge of the report; the file itself was not opened)
- **CJRA per-judge tables, as of March 31, 2026**: Table 7 civil cases pending more than three years (listed 17.97 MB), Table 8 motions pending more than six months (HEAD 5,607,056 bytes), Table 9 bench trials, Tables 1-4 summaries, Appendices A-D (code legend, 686.61 KB). Report pages exist for every March/September back to 2004 (58 links on the CJRA landing page).

Lower priority: C-7, C-9, C-10, C-13, M-5, S-22, CJRA 10/11, appellate FCMS.

## 2. JPML (jpml.uscourts.gov) structure
Old Drupal 7 site; everything is PDF under `/sites/jpml/files/`; file names carry the as-of date and are irregular (spaces, `_0` suffixes, "By_MDL_Type" vs older "By_Docket_Type").

| Page | Content | Latest found |
|---|---|---|
| `/pending-mdls-0` | 5 current reports: Pending MDL Dockets **By District, By MDL Number, By MDL Type, By Actions Pending**, and **Recently Terminated MDLs** | **As of September 1, 2026** (By MDL Number HEAD 440,352 bytes, Last-Modified 2026-09-01) |
| `/pending-mdl-reports-archive` | 120 PDFs = 24 monthly snapshots x 5 reports | September 3, 2024 - August 3, 2026 |
| `/mdl-quarterly-caseload-summary` | Pending MDL Dockets **By Circuit** | June 30, 2026 and March 31, 2026 (only two posted) |
| `/statistics-info` (4 pages, filter Type = Fiscal Year / Calendar Year / Cumulative Terminated / Legacy, Year 1992-2026) | **Calendar Year Statistics** 2006-2025; **Fiscal Year Statistical Analysis** 2018-2025 seen; **Cumulative Terminated Litigations** 2004-2025 | CY 2025 (file dated 1-16-26, HEAD 851,212 bytes), FY 2025 Statistical Analysis, FY 2025 Terminated Litigations |
| `/content/panel-judges` | roster PDF of current and former Panel judges | `Panel Judges Roster-6-3-2026.pdf` |
| `/hearing-information`, `/panel-orders` | hearing notices, transfer orders | Sept 24, 2026 session notice (already in directory DB) |

Pages 3-4 of `/statistics-info` (older fiscal-year and "Legacy" reports) were not fetched.

Why it matters: the pending "By District" report is the authoritative **MDL <-> transferee district <-> transferee judge <-> actions pending** map, refreshed monthly, which is exactly the "major litigation judges in multi-jurisdiction MDLs" list the judge UI needs. It is PDF only, so it needs table extraction and a review step.

## 3. Judges, judgeships, vacancies
- `/about-federal-courts/about-federal-judges` is a thin hub: Types of Federal Judges, **Authorized Judgeships**, Judicial Compensation, Judicial Milestones, FJC directory, vacancies.
- Authorized Judgeships page: 8 files (appeals/district additional judgeships since 1960, temporary judgeships, chronological histories, `allauth.pdf` 1789-present, 2025 Judicial Conference judgeship recommendations). The `2025-01`/`2025-03` folder in the URL is an upload path, not an effective date.
- Current Judicial Vacancies: **HTML table** (Court, Incumbent, Vacancy Reason, Vacancy Date, Nominee, Nomination Date), sortable by query string; page stated "as of 09/18/2026", Total Vacancies 26, Nominees Pending 12, 26 rows. Future vacancies, emergencies, confirmation listing and the monthly archive were listed but not fetched.
- Data-table topic 823 (Judges) currently returns only FCMS, JB S-22, JFF 1.1 and 6.6 for the latest periods; there are no downloadable per-judge tables other than CJRA.
- FJC Biographical Directory export page lists 9 files (`judges.csv/xlsx`, `categories.xlsx`, `demographics.csv`, `federal-judicial-service.csv`, `other-federal-judicial-service.csv`, `education.csv`, `professional-career.csv`, `other-nominations-recess.csv`). `judges.csv` is already the source of 8,148 directory records; the relational files were not found locally by file name.

## 4. The other user-named pages
- `/data-news/reports`: hub only. Statistical Reports (JB, FCMS, Wiretap, Bankruptcy, BAPCPA, **CJRA**, FJCS, STFJ, JFF, FISA, delayed-notice, crime victims), Annual Reports, **Handbooks & Manuals (incl. Civil Litigation Management Manual)**, Strategic Planning.
- HSD page: a directory of 214 links; after removing court home pages, **98 order/procedure links on 95 court hosts (83 PDF, 15 HTML)**: 10 courts of appeals, 66 district, 22 bankruptcy. Exported to `federal_hsd_order_urls.jsonl` with the AO page's own court label and section (not inferred from host names). A 95-host packet needs its own robots pass per host.
- `/administration-policies`: hub of 8 sections (Judicial Conference governance, judicial administration, oversight, **financial disclosure reports**, **judicial conduct & disability**, privately funded seminars, workplace conduct, **judiciary policies / Guide to Judiciary Policy**). No data files at this level; sub-pages not fetched.

## 5. Overlap with what is already saved
Read-only queries on `delivery/archive-directory/directory.sqlite3` (`records.source_url`) and `catalog/documents.sqlite3` (`versions.source_url`):
- 0 records for `/document/stfj_`, `jb_`, `fjcs_`, `jff_`, `fcms_`, `cjra_`; 0 for `uscourts.gov/statistics` or `/data-news`; 0 for `Pending_MDL`, JPML calendar-year statistics, terminated litigations, Panel roster.
- 22 JPML records exist (forms, rules, FAQ, CM/ECF manuals, MCP items, the September 2026 hearing notice); 87 `www.uscourts.gov/sites/default/files` records are AO forms/guide chapters. `documents.sqlite3` has no uscourts.gov or JPML URL.
- Result: all 307 candidates are new except `judges.csv` (flagged `already_in_directory_db: true`). The 8 "Calendar Year Statistics" matches in the DB are TXWD district files, not JPML.

## 6. Packet plan (fields `packet`, `priority`, `min_delay_s` in the JSONL)

| Packet | URLs | Formats | Delay | Est. run | Est. size | Notes |
|---|---|---|---|---|---|---|
| P1_uscourts_tables_xlsx | 69 (40 p1, 20 p2, 9 p3) | xlsx | 3 s | ~4 min | ~1.5 MB (listed sizes 8-50 KB each) | `alt_pdf_url` holds the PDF twin for JB/JFF; not counted as separate URLs |
| P2_uscourts_fcms_cjra | 23 | 10 FCMS pdf+xlsx, 10 CJRA pdf, 3 methodology links | 3 s | ~2 min + transfer | ~35 MB (CJRA 7 alone 17.97 MB) | 3 methodology links are redirect/media URLs to resolve at capture |
| P3_jpml_current | 11 | pdf | **10 s** | ~2 min | few MB | Sept 1, 2026 reports, June 30, 2026 by-circuit, CY/FY 2025, roster |
| P4_jpml_history | 167 (120 monthly archive + 47 older annual) | pdf | **10 s** | must be split into 4 sub-packets of <= 50 URLs to fit 600 s | unknown | priority 3; archive gives temporal tracking |
| P5_judgeships_vacancies | 14 | 8 pdf/redirect, 6 html | 3 s | <1 min | small | vacancy pages are live HTML: store the page's own "as of" date separately from capture date |
| P6_fjc_export | 9 | csv/xlsx | **30 s** | ~4.5 min | unknown | robots-compliant path only |
| P7_context_pages | 14 | html | 3 s / 10 s | <1 min | small | JB 2025 JPML and District Courts narratives, report pages, index |

Refresh rule: monthly re-read of `/pending-mdls-0`; quarterly re-read of the data-table index filtered by `pn` (one request per publication) and diff on (publication, table number, period).

## 7. Modelling recommendations for the supplement
- Record type `court_statistic_table`: `publication`, `table_id`, `period_end` (explicit), `period_basis` (leave unknown until read from the sheet header), `geography_level` (national / circuit / district), `format`, `source_url`, `detail_page_url`, `sha256`, `capture_ts`. Do not store HTTP Last-Modified as a publication or effective date.
- Districts: key on the AO court code that appears inside the tables, mapped to the project's existing court registry; do not derive from file names.
- CJRA and JPML reports name judges as text. Treat them as **publisher-reported rows "as of <date>"** and link to judge entities only through (court + name) candidates with a review queue; never merge on name alone; keep FJC nid / CourtListener person id separate. Present counts (cases pending > 3 years, motions > 6 months, actions pending per MDL) with their as-of date and no derived rates or predictions.
- MDL entity key = MDL number from the JPML "By MDL Number" report; relationships: MDL -> transferee district -> transferee judge -> docket type -> actions pending (time series from the archive) -> existing local MDL collections (e.g. MDL-3080) and settlements.
- Nature-of-suit codes (365, 367, 368, 245, 385 ...) should become a small reference table so C-2/C-3/C-4/C-11 rows can be filtered as "product liability / personal injury".

## 8. Barriers
1. **FJC Integrated Database (case-level civil data with nature of suit, the natural source for per-district tort filings over time): robots.txt disallows `/research/idb/` and `/sites/default/files/idb`.** Not collected and not to be automated; a manual download by the user is the only compliant route. The IDB landing page itself only linked a research guide PDF.
2. JPML `Crawl-delay: 10` and FJC `Crawl-delay: 30` cap packet size under the 600 s rule (about 55 and 19 URLs).
3. Spacing slip: the two FJC page GETs were sent 3.5 s apart because they were queued in the same batch as the robots.txt request; the 30 s crawl-delay was read afterwards. No further FJC requests were made. The packet must use >= 30 s.
4. CJRA per-judge data and all JPML reports are **PDF only**; per-judge/per-MDL rows need PDF table extraction and QA (CJRA Table 7 is ~18 MB).
5. STFJ and FJCS are xlsx only (no PDF reading copy); FCMS explanation files are behind `/file/<id>/download` redirects that were not resolved.
6. File names are irregular across years, so historical backfill requires paging the index (the pager exposes at least 9 pages of 50 rows; the total was not determined), not URL generation.
7. uscourts.gov: no challenge, 403 or rate-limit response in 25 requests.

## 9. Not verified
- Contents/layout of any xlsx or PDF (no file downloaded): 12-month basis, sheet structure, whether FCMS xlsx has one sheet per district, CJRA table column layout, JPML report columns.
- 302 of 307 candidate URLs were taken from listings without a HEAD check (5 HEAD-checked, all 200).
- STFJ December 31 edition and whether newer-than-listed periods exist for JB (FY2026 is not yet published as of the scout).
- `/statistics-info` pages 3-4, `/panel-orders`, vacancy sub-pages, JB 2025 narrative/table-index pages, Civil Litigation Management Manual, administration-policies sub-pages, authorized-judgeship `/file/ID/download` targets.
- Whether the FJC relational CSVs exist locally under another name (only a file-name glob for `federal-judicial-service*.csv` was run: no match).
- Whether `openpyxl` is installed for xlsx parsing.
- robots.txt for the 95 court hosts in the HSD list.
