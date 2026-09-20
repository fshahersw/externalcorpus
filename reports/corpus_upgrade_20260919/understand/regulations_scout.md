# Regulations scout — federal regulation and agency data for mass-tort research

Run: 2026-09-19 (UTC 04:20–04:45). Read-only scoping. No existing project file was modified.
Own files written:

- `reports/corpus_upgrade_20260919/understand/regulations_scout.md` (this file)
- `reports/corpus_upgrade_20260919/understand/packets/regulation_endpoints.jsonl` (53 endpoint/source rows)
- `reports/corpus_upgrade_20260919/understand/packets/regulation_probe/` — `probe.py`, `build_endpoints.py`,
  `receipts.jsonl` (49 HTTP receipts + 6 robots-skip records), `bodies/` (41 original response bodies, 16.8 MB,
  named by SHA-256 prefix), `ecfr_structure_summary.json`, `openfda_download_summary.json`,
  `openfda_first_slice_files.json`

## 1. Headline

Most of the regulation *text* the first slice needs is **already on disk and unused by the MVP**:

| Local asset | What it holds | Used in MVP today |
|---|---|---|
| Open US Law index (`sources/open_us_law_20260918/catalog.sqlite3`, read-only) | **220,018 CFR section rows across 49 titles** (title 35 is reserved), 218,712 FR final rules, 142,188 FR proposed rules, 12,364 federal guidance rows, 140 HHS-OCR enforcement rows | No federal regulation view |
| GPO eCFR Title 21 XML (`sources/seeger_import_20260918/raw/ae/aef563…c10c2.xml`, 21,714,710 bytes, captured 2026-09-13, internal amendment marker "Sept. 8, 2026") | Entire Title 21 with authority/source notes | Only 8 parts / 233 sections derived (parts 11, 50, 56, 312, 314, 803, 807, 820) → directory kind `regulatory_provision` = 233 + 2 strays (Guam, Nebraska) |
| `C:/Users/firas/Downloads/returnedfiles/Recalls.csv` (10,016,119 bytes) | 9,971 CPSC recalls 1973-06-08 → 2026 (Title, Date, Summary, Recall Number, Recall URL) | Not used |
| `returnedfiles/state_admin_agency_urls.jsonl` (118,056 URLs) | 52,758 federal-agency URL references: FTC 22,587; CFPB 9,675; SEC_rules 7,555; SEC_litig 6,395; CMS 6,239; NLRB 262; HHS_OIG 106; EPA_enf 102. 65,298 state admin-code URLs (23 states attempted). References only, no content | Not used |
| Source directory (`sources/public_law_directory_20260919/catalog.json`) | 527 `regulations_register` + 170 `agency_guidance` references; hosts: epa.gov 247, fda.gov 100, nih.gov 68, nhtsa.gov 52, cms.gov 47, govinfo.gov 38, sec.gov 31, ecfr.gov 19, cpsc.gov 11, federalregister.gov 8 | Listed as references |

So the highest-value build needs **no network**: publish a dated "federal regulation slice" from the local index
and the local Title 21 XML. Network is only needed for (a) exact point-in-time/amendment metadata,
(b) Federal Register metadata (dates, dockets, RINs), (c) agency enforcement datasets (openFDA, FDA exports, NHTSA).

## 2. Local coverage (verified by query)

### 2.1 Open US Law — regulation/administrative-code coverage by state

`kind='regulations'` = 885,121 rows: FEDERAL 582,054 + **16 states** 303,067.

| State | Rows | State | Rows | State | Rows | State | Rows |
|---|---|---|---|---|---|---|---|
| IL | 53,584 | WA | 51,026 | TX | 44,247 | SD | 28,988 |
| VA | 22,396 | OH | 19,909 | WI | 17,823 | MN | 15,447 |
| NM | 13,270 | MD | 12,863 | ID | 8,551 | SC | 6,606 |
| KY | 4,865 | ME | 1,718 | DE | 1,164 | CO | 610 |

No administrative-code rows for the other 34 states + DC + PR, including the main mass-tort state venues
**NJ, CA, NY, PA, FL, MO, LA, MA, GA**. `kind='guidance'` exists for every jurisdiction (23–1,641 rows each;
NY 1,199, TX 1,254, PR 1,641) but it is attorney-general/agency guidance, not codified regulation.
Row counts are source rows, not verified unique sections (publisher caveat). Texas regulation rows have no
source URL (publisher gap). CO (610) and DE (1,164) are obviously partial.

### 2.2 Federal content in Open US Law (`state='FEDERAL'`, 663,287 rows)

regulations 582,054 · statutes (USC) 54,853 · guidance 12,364 · ruling 7,248 · proclamation 1,832 ·
irs_notice 759 · executive_order 738 · presidential_document 655 · court_rules 589 · faq 444 · memorandum 401 ·
irs_rev_proc 377 · guideline (USSG) 302 · irs_rev_rul 245 · enforcement_action 140 · treaty 119 ·
irs_announcement 83 · constitutions 74 · administrative_guidance 10.

Federal regulations by source-id prefix: `CFR_T*` 220,018 · `FR_RULE_*` 218,712 · `FR_PRORULE_*` 142,188 ·
other ≈1,136. FR years: numbered 2010–2026 plus 191,268 older two-digit/E-series numbers (back to the mid-1990s).
**FR notices are not included.**

Federal guidance is financial/IP/labour heavy (FDIC_FIL 2,313; TMEP 2,109; MPEP 2,024; Justice Manual 1,548;
CFTC 942; OCC 1,054; USCIS 456; NLRB 639; FRB 336; CPSC advisory opinions 139 + CPSC small-entity guides).
**There is no FDA guidance, no FDA warning letter, no recall, no NHTSA and no SEC litigation content locally.**
`enforcement_action` is HHS-OCR HIPAA only.

### 2.3 Local CFR versus the recommended first slice

| Title | Selected parts | eCFR sections today (structure API) | eCFR bytes (structure `size`) | Local Open US Law rows | Parts missing locally |
|---|---|---|---|---|---|
| 21 (FDA) | 48 | 1,357 | 4,460,106 | 1,360 | none |
| 16 (CPSC) | 10 | 181 | 784,691 | 182 | none |
| 49 (NHTSA) | 10 | 196 | 3,688,832 (571 FMVSS = 3.34 MB) | 201 | none |
| 40 (EPA, selected) | 30 | 3,826 (721 SNURs = 2,655) | 16,919,560 | 3,795 | none |
| **Total** | **98** | **5,560** | **≈25.9 MB** | **5,538** | — |

Whole-title reference sizes today: T21 22.2 MB / 275 parts / 8,416 sections; T16 6.9 MB / 229 / 2,158;
T49 33.0 MB / 419 / 8,998; T40 160.1 MB / 379 / 24,651.

Local CFR row quality (sampled 21 CFR 314.80, 803.50, 16 CFR 1115.4): full text incl. the source-credit line
(`[50 FR 7493, Feb. 22, 1985 … 79 FR 33088, June 10, 2014]`), hierarchy breadcrumb, `cross_references_cfr`,
`last_amended_year`, `source_url` = `ecfr.gov/current/...`. **Weakness: no exact as-of date** — only
`year: 2026` and the publisher snapshot date 2026-08-14; `act_status: in_force` is a publisher assertion.
The § sign is stored correctly (U+00A7); the mojibake seen in a console was a terminal artefact.

Local FR rows: full text, `cross_references_cfr [{title, part}]`, `year`, URL with embedded publication date;
**no agency, docket id, RIN, effective date or explicit publication_date field**.

## 3. Remote sources reviewed (49 requests total, ≤ 9 per host, ≥ 2.6 s spacing, UA `LegalCorpusResearch/1.0`, no keys, no contact data sent)

| Host | Requests | robots.txt | Result |
|---|---|---|---|
| www.ecfr.gov | 8 | 200, parsed | titles, 4 structure files, versions (part 314), agencies — all 200 |
| www.govinfo.gov | 7 | 200, bulkdata sitemaps advertised | ECFR listings T21/16/40/49 200; CFR/2025/title-21 200; CFR/2026 404 |
| www.federalregister.gov | 6 | 200 | 4 facet counts + 1 field-selected sample, all 200 |
| api.fda.gov | 8 | 404 (none) | download.json + 6 endpoint samples, all 200 |
| open.fda.gov | 1 | **403** | docs host refused → rate-limit page not read |
| www.fda.gov | 3 | 200, **Crawl-delay: 30** | warning-letters index 200; recalls index 200 |
| www.saferproducts.gov | 1 | **403 Akamai** | CPSC recall API not contacted |
| www.cpsc.gov | 1 | **403 Akamai** | API doc page not contacted |
| api.nhtsa.gov | 1 | **403** `{"message":"Missing Authentication Token"}` | API not contacted (conservative) |
| www.nhtsa.gov | 1 | **403 Akamai** | datasets page not contacted |
| static.nhtsa.gov | 9 | 404 (S3, none) | 4 flat files exist (200), 2 old names 404 |
| open.gsa.gov | 2 | 200, allow all | regulations.gov API docs 200 |
| www.sec.gov | 1 | **403 "Request Rate Threshold Exceeded"** | stopped after 1 request |

### 3.1 eCFR API (`www.ecfr.gov/api`)
- Auth none; no published rate limit; JSON/XML.
- `versioner/v1/titles.json` (8,033 B): per title `latest_amended_on`, `latest_issue_date`, `up_to_date_as_of`
  (2026-09-17 today; T21 last amended 2026-09-16).
- `versioner/v1/structure/{date}/title-N.json`: full hierarchy with `identifier`, `label`, `size` (bytes),
  `reserved`. Saved today: T21 2,676,905 B; T16 754,204 B; T49 2,965,556 B; T40 9,395,876 B. **These saved
  bodies can be reused as the hierarchy/identifier layer without any further request.**
- `versioner/v1/versions/title-N.json?part=P`: per-section version rows `date`, `amendment_date`, `issue_date`,
  `substantive`, `removed`. Part 314 = 111 rows / 28,965 B; history starts 2016-12-23. This is the only clean
  machine source for **amendment dates per section**.
- `admin/v1/agencies.json` (98,197 B): 153 agencies, slug → CFR title/chapter (FDA 21/I; CPSC 16/II; NHTSA 49/V;
  EPA 40/I, IV, VII; SEC 17/II; OSHA 29/XVII). Slugs equal Federal Register agency slugs → free join key.
- **Barrier/decision:** robots.txt contains `Disallow: /api/versioner/v1/full/` and
  `Disallow: /api/renderer/v1/content/` under a "Don't index developer tool links" comment, placed after a blank
  line below `User-agent: *`. Python's `robotparser` silently drops them (reports "allowed"); Google-style parsers
  apply them. I treated the full-text endpoint as **disallowed and did not fetch it**. Text should come from
  govinfo bulk XML (below) or the local index. Collector note: `pipeline/corpus_crawler.py` should not rely on
  `urllib.robotparser` for this host.
- Date semantics: structure/full URL date = point-in-time view; `amendment_date` = date the change took effect in
  eCFR; `issue_date` = FR issue that carried it. eCFR is "authoritative but unofficial"; the official edition is
  the annual CFR.

### 3.2 govinfo bulk data (official GPO channel, already used once locally)
- `https://www.govinfo.gov/bulkdata/json/ECFR/title-N` (send `Accept: application/json`) lists file + size + mtime.
  Today: `ECFR-title21.xml` 21,724,705 B (17-Sep); `ECFR-title16.xml` 6,769,171 B; `ECFR-title49.xml`
  33,791,758 B; `ECFR-title40.xml` 161,198,000 B. Graphics zips 2.6–45 MB (skip).
- Annual CFR: `bulkdata/json/CFR/2025/title-21` → vol1–vol9 XML + zip (sizes not reported by listing);
  `CFR/2026/title-21` = 404 today. Annual revision dates: titles 1–16 Jan 1; 17–27 Apr 1; 28–41 Jul 1; 42–50 Oct 1.
- Currency marker is inside the XML (volume amendment date), never HTTP Last-Modified.

### 3.3 Federal Register API (`www.federalregister.gov/api/v1`)
- Auth none; JSON/CSV; `per_page` ≤ 1000; no published rate limit; deep-paging cap **not verified** → partition.
- Counts today (facets/type): FDA RULE 3,671 / PRORULE 1,408 / NOTICE 18,577; CPSC 325 / 354 / 1,694;
  NHTSA 868 / 796 / 4,320; EPA 16,905 / 13,038 / 27,661.
- Filter by CFR citation works: `conditions[cfr][title]=21&conditions[cfr][part]=314` + `type=RULE` → 66 docs.
  About 2.6 KB per document with the 22 recommended `fields[]`.
- Stable ids: `document_number`, `citation` (90 FR 13553), `docket_ids`, `regulation_id_numbers` (RIN),
  `cfr_references`.
- **Date trap verified today:** doc 2025-04978 returns `effective_on = 2024-12-26` while its `dates` text says the
  effective date is delayed to 2025-05-27. `effective_on` is machine-extracted → store as
  "publisher-extracted effective date, unverified" next to the raw `dates` string; `publication_date` is the only
  authoritative date.
- Both sample documents (2025-04978, 2024-30261) are already in the local index with full text → **only metadata
  needs fetching**, not text.

### 3.4 openFDA (`api.fda.gov`, bulk at `download.open.fda.gov`)
- Auth none; optional free key. Rate limits not re-verified today (docs host 403); from memory 240/min and
  1,000/day without key, 120,000/day with key. `limit` ≤ 1000, `skip` ≤ 25,000.
- `download.json` (592,208 B, saved) gives exact bulk sizes/export dates. Records / zipped MB today:

| Endpoint | Records | Zip MB | Slice |
|---|---|---|---|
| drug/enforcement | 17,965 | 3.8 | first |
| device/enforcement | 39,949 | 90.2 | first |
| food/enforcement | 29,406 | 5.6 | first |
| drug/drugsfda | 29,335 | 8.9 | first |
| device/pma | 57,101 | 21.1 | first |
| device/classification | 7,093 | 3.1 | first |
| transparency/crl (complete response letters) | 458 | 1.0 | first |
| drug/shortages | 1,603 | 0.4 | first |
| drug/orangebook | 48,761 | 2.4 | first |
| **first slice total** | **231,671** | **≈136.5 MB, 9 files** | |
| device/510k | 176,070 | 237.0 | second |
| device/recall | 59,222 | 274.2 | second |
| cosmetic/event | 85,511 | 3.6 | second |
| food/event (CAERS) | 151,589 | 8.7 | second |
| drug/label | 262,883 | 1,773.8 (14 files) | per-product only |
| device/udi | 5,182,695 | 1,903.4 | skip |
| device/event (MAUDE) | 26,136,889 | 18,433.5 (371 files) | per-product queries only |
| drug/event (FAERS) | 20,692,690 | 114,173.8 (1,767 files) | per-product queries only |

- Verified identifiers and dates (one live record each):
  drug/event `safetyreportid`; `receivedate`, `receiptdate`, `transmissiondate` (YYYYMMDD) ·
  device/event `mdr_report_key`, `report_number`; `date_received`, `date_of_event`, `report_date`, `date_added`,
  `date_changed` · enforcement `recall_number` (D-321-2016), `event_id`; `recall_initiation_date`,
  `center_classification_date`, `report_date`, `termination_date`; `classification`, `status` ·
  device/recall `product_res_number` (Z-0001-04), `cfres_id`, `res_event_number`, `k_numbers`, `firm_fei_number`;
  `event_date_initiated/posted/terminated` · 510k `k_number`; `date_received`, `decision_date` ·
  label `set_id`, `id`, `version`; `effective_time`.
- `meta.last_updated` differs per endpoint (drug/event 2026-07-30; label 2026-09-18) → store per capture.
- FAERS/MAUDE are spontaneous reports: any count is "publisher-reported, query X, as of date Y, no denominator,
  not proof of causation" (FDA disclaimer in `meta`).

### 3.5 FDA web (`www.fda.gov`, Crawl-delay 30)
- Warning letters index 200 (76,651 B). Table is a Solr view (`warning_letter_solr_index`); the page itself links a
  publisher **XLSX export**: `…/warning-letters/datatables-data?page&_format=xlsx` (not fetched; size unknown).
  Columns: Posted Date, Letter Issue Date, Company Name, Issuing Office, Subject, Response Letter, Closeout Letter.
- Recalls/market withdrawals/safety alerts index 200 (73,470 B); same pattern:
  `/safety/recalls-market-withdrawals-safety-alerts/datatables-data?…&_format=xlsx`. This list is press releases
  (publish date), not the classified recall record (that is openFDA enforcement).
- At 30 s/request, individual warning-letter pages must be a bounded, product/defendant-driven list (≤ 100 URLs ≈ 50 min).

### 3.6 CPSC
- `saferproducts.gov/RestWebServices/Recall` is documented as keyless JSON, but **robots.txt returned 403 Akamai
  "Access Denied" for our UA**, as did `www.cpsc.gov/robots.txt`. Not retried, not bypassed.
- Fallback: local `Recalls.csv` (9,971 rows through 2026; provenance/capture date unknown → label it so).

### 3.7 NHTSA
- `static.nhtsa.gov/odi/ffdd/`: `rcl/FLAT_RCL_POST_2010.zip`, `rcl/FLAT_RCL_PRE_2010.zip`, `cmpl/FLAT_CMPL.zip`,
  `inv/FLAT_INV.zip` all 200 (Last-Modified 2026-09-18, refreshed daily). `rcl/FLAT_RCL.zip` and
  `tsbs/FLAT_TSBS.zip` are 404 (renamed). HEAD gives no Content-Length → **sizes unverified**.
- **Disclosure:** to get a size I sent two 1-byte `Range` GETs (FLAT_CMPL, FLAT_RCL_POST_2010); the server
  ignored Range and answered HTTP 200, so the full bodies were streamed into memory and discarded (the first completed
  within about 13 s; byte counts were not recorded; nothing was saved to disk). This was an unintended
  bulk transfer and is recorded in `receipts.jsonl` as `GET range 0-0` with status 200. No further requests were made to that host. A future collector must
  stream-to-disk with a byte cap rather than probe with Range.
- `api.nhtsa.gov` answers `/robots.txt` with an API-gateway 403; I treated that as "do not fetch". Decision needed;
  the flat files carry the same recall/complaint/investigation data anyway.

### 3.8 regulations.gov (note only, not contacted)
- v4 JSON:API at `api.regulations.gov/v4/{documents,dockets,comments}`; **api.data.gov key required**
  (`X-Api-Key`); DEMO_KEY exists, not used. 250/page × 20 pages = 5,000 per query, window by `lastModifiedDate`.
  Ids: `docketId` (FDA-2021-N-0862), `documentId`, `frDocNum` (joins FR). Dates: `postedDate`,
  `lastModifiedDate`, `commentEndDate`. Docs page (open.gsa.gov) 200 today.

### 3.9 SEC (robots only; blocked)
- `https://www.sec.gov/robots.txt` → HTTP 403 "Request Rate Threshold Exceeded" page = the undeclared-UA block.
  One request, then stopped. **User decision:** SEC fair-access requires a declared UA "Organisation contact@domain"
  and ≤ 10 req/s. I did not invent or send any address. Note: `devvvv/src/lib/agents/regulatory-sources.server.ts`
  (the external platform's live-query agent for openFDA / FR / eCFR search / EDGAR full-text / ClinicalTrials)
  reads `SEC_USER_AGENT` from env and carries a placeholder default; whether that mailbox exists is unverified.
- When approved, the bounded first slice is: `data.sec.gov/submissions/CIK##########.json` for the ~50 public
  MDL defendants already in the corpus (10-K/10-Q/8-K index → Legal Proceedings/contingency disclosures), plus the
  litigation-release and administrative-proceeding index pages. Local inventory already lists 6,395 SEC litigation
  and 7,555 SEC rule URLs (references only).

## 4. Recommended mass-tort first slice (point-in-time: eCFR 2026-09-16 for T21, 2026-09-17 for T16/40/49)

**Title 21 (48 parts, 1,357 sections, 4.46 MB):** general/enforcement 1, 7, 10, 11, 20 · human subjects 50, 54, 56 ·
off-label 99 · drugs 200, 201 (labeling), 202 (advertising), 203, 207, 208 (medication guides), 210, 211 (cGMP),
310, 312 (IND), 314 (NDA incl. 314.70 CBE, 314.80/.81 postmarketing reporting), 316, 320, 330 (OTC) · biologics
600 (600.80 AE reporting), 601, 606, 610 · cosmetics 700, 701, 740 (talc/hair-relaxer matters) · devices 800, 801
(labeling), 803 (MDR), 806 (corrections/removals), 807 (510(k)), 808 (**preemption exemptions**), 810 (recall
authority), 812 (IDE), 814 (PMA), 820 (QMSR), 821, 822, 830 (UDI), 860 · radiological 1002–1004 · HCT/P 1271.
Second wave: 21 CFR 862–892 device classification regulations (joins openFDA `device/classification`
regulation numbers), 1100–1150 tobacco/ENDS, 7 subpart C recalls is already in part 7.

**Title 16 (10 parts, 181 sections, 0.78 MB):** 1101 (§6(b) disclosure), 1102 (public database), 1115 (substantial
product hazard reports, §15(b)), 1116 (§37 lawsuit reports), 1117, 1118, 1119 (civil penalty factors), 1120, 1130,
1500 (FHSA).

**Title 49 (10 parts, 196 sections, 3.69 MB):** 554, 556, 557, 565 (VIN), 571 (FMVSS — 3.34 MB), 573 (defect
reports), 576, 577 (owner notification), 578 (penalties), 579 (TREAD early-warning reporting).

**Title 40 selected (30 parts, 3,826 sections, 16.9 MB):** SDWA 141 (incl. PFAS NPDWR), 142, 143 · FIFRA 152, 155,
156 (labeling), 158, 159 (§6(a)(2) adverse-effects reporting), 160 · RCRA 261 · CERCLA 300, 302 (hazardous
substance designations incl. PFOA/PFOS), 355, 370, 372 (TRI) · TSCA 702, 704, 707, 710, 711, 712, 716, 717, 720,
721, 723, 751 (§6 rules), 761 (PCBs), 763 (asbestos), 792. Part 721 alone is 5.5 MB / 2,655 SNUR sections — keep
but collapse in the UI. Excluded on purpose: part 63 NESHAP (huge), part 180 tolerances.

**Agency data first slice:** openFDA 9 bulk files (≈136.5 MB zipped, 231,671 records) → FDA warning-letter XLSX
export + recalls XLSX export (2 requests, 30 s apart) → FR metadata for the 98 parts (~98 requests, ≈5–15 MB) →
eCFR versions for the 98 parts (~98 requests, ≈3–6 MB) → NHTSA recall + investigation flat files (3 files, size
unknown, stream with a cap) → CPSC from local CSV.

## 5. Record model recommended for the supplement (integration-ready)

- Ids: `cfr:{title}:{section}@{as_of}` (e.g. `cfr:21:314.80@2026-09-16`); `fr:{document_number}`;
  `openfda:{endpoint}:{native_id}`; `fda-wl:{marcs_cms_id}`; `nhtsa:rcl:{campaign_no}`; `cpsc:rcl:{recall_number}`;
  `sec:{cik}:{accession}`; `regsgov:{documentId}`. Keep Open US Law `oul:` ids as provenance, not as the public id.
- Date fields (all nullable, never merged): `as_of_date` (point-in-time of text), `amendment_date`,
  `issue_date`, `publication_date`, `effective_date_publisher_extracted` + `dates_text_raw`, `capture_date`,
  `source_snapshot_date`, `export_date`; per-event dates keep native names.
- Data types: `cfr_section`, `cfr_part`, `fr_rule`, `fr_proposed_rule`, `fr_notice`, `agency_guidance`,
  `enforcement_recall`, `warning_letter`, `adverse_event_query_result`, `device_clearance_510k`, `device_pma`,
  `drug_application`, `complete_response_letter`, `vehicle_recall`, `vehicle_investigation`, `consumer_recall`.
- Relationships that are computable from fields already seen: CFR section → FR docs (parse the source-credit
  line + FR `cfr_references`); FR doc → docket id → regulations.gov; FR doc → RIN; agency slug → CFR chapter
  (agencies.json); openFDA recall → firm (FEI) → 510(k)/PMA (`k_numbers`, `pma_numbers`) → device classification
  → 21 CFR 8xx regulation number → CFR section; drugsfda application number ↔ label `set_id` ↔ enforcement;
  MDL/settlement record → product/defendant → application number / firm name (curated mapping table, manual
  review required; never name-merge firms automatically).
- Jurisdiction: `US-federal` with `agency_slug`; no state/county inference.

## 6. Not verified

- openFDA rate limits and eCFR/FR rate limits (no published header; docs host blocked).
- Sizes of NHTSA flat files, FDA XLSX exports, annual CFR volumes; robots for `download.open.fda.gov`.
- FR deep-paging cap; whole-title `versions` response size.
- CPSC and NHTSA API field names (from memory only); `Recalls.csv` provenance/capture date.
- No semantic diff between Open US Law CFR text (snapshot 2026-08-14) and eCFR 2026-09-16; section counts differ
  slightly (local 5,538 vs eCFR 5,560), not reconciled.
- State admin-code URL inventory quality (23 states) was not sampled; that belongs to the state-codes scout.
- Nothing was checked on SEC beyond robots.txt; nothing on regulations.gov API itself; EPA ECHO/enforcement,
  OSHA, CDC/ATSDR, ClinicalTrials.gov were out of scope and not reviewed.
