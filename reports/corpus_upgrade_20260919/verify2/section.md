

## Verification 2 (skeptical re-measurement of slices 2, 4, 6 — 2026-09-19)

Read-only re-measurement of every key claim directly against the named files. Scripts:
`reports/corpus_upgrade_20260919/verify2/s2.py`, `s4.py`, `s4b.py`, `s6.py`, `s6b.py`, `s6c.py`, `s7.py`, `s8.py`.
Nothing under `SW-BULK/` or `returnedfiles/` was modified. Python
`C:/Users/firas/AppData/Local/Programs/Python/Python311/python.exe`, streaming/`json.load` only, no network.

### Slice 2 — `mdl_docket_documents_20260919`

| Claim | Measured | Verdict |
|---|---|---|
| 35,862 rows total | 35,862 | confirmed |
| 25,598 rows join 12 registry MDLs on native `mdl_number` | 25,598 across exactly those 12; per-MDL counts match to the row (2570 2,272 / 2592 3,603 / 2789 1,361 / 2804 3,074 / 2846 1,030 / 2873 2,423 / 2885 2,909 / 2913 2,193 / 2973 416 / 3047 2,811 / 3081 2,009 / 3094 1,497). MDL 2592 is `status: terminated` in `sources/jpml_mdl_20260919/mdls.jsonl` | confirmed |
| 16,035 rows carry both `download_url` and `sha1` | `download_url` 16,035; `sha1` 16,021; **both 16,021** (14 rows have a URL and no sha1). `is_available` == 16,035, `source == recap` == 16,035 | confirmed as to magnitude; number corrected to **16,021** |
| `doc_category` `settlement` 138, `case_management_order` 2,881 | 138 / 2,881 **file-wide** | confirmed |
| "the 138 settlement + 2,881 case_management_order + 258 bellwether rows **for 11 pending MDLs**" (ui_surface) | Inside the 11 pending registry MDLs: **125 settlement, 1,976 case_management_order, 126 bellwether**. Inside all 12 registry MDLs: 125 / 2,031 / 127 | **wrong** — the Settlements tab gets ~2,227 rows, not 3,277 |
| every row has `entry_date_filed`, min 2008-10-24 max 2026-08-03 | 0 nulls, min 2008-10-24, max 2026-08-03 | confirmed |
| 4,505 rows with no `mdl_number`; 0 sealed; 14,319 high_value | 4,505 / 0 / 14,319 | confirmed |

Additional measurements the plan does not state:

- **`doc_uid` is not unique.** 31,858 distinct `doc_uid` over 35,862 rows — 4,004 duplicate rows (the
  `"<master>-None-"` shape repeats). Do not use it as the record id; build a composite
  (`master_docket_id` + `entry_number` + `document_number` + row ordinal) or rows will collapse.
- **Three MDL numbers in the file are not in the registry**: 2100 (2,029), 2606 (1,557), 2641 (2,173) =
  5,759 rows that also will not join. The plan parks only the 4,505 null-`mdl_number` rows.
- 17 distinct `master_docket_id`, 12 courts; `source` is `pacer_only` 19,827 / `recap` 16,035.
- **The provenance/licence claim is wrong.** `SW-BULK/README.md` states the repo is "built on public
  CourtListener / Free Law Project data" and that it is a "Private repository. Contents include firm work
  product; do not fork, mirror, or grant external access." `SW-BULK/CLAUDE.md` places `catalog/documents.json`
  among "Large **API-derived** layers ... NOT in git", assembled by `assemble_catalog.py` from per-master
  API fetches. Provenance is documented, not inferred from field shapes — and it carries an explicit
  redistribution restriction plus a firm-work-product assertion the plan does not mention.
- `fetch_master_docs.py` (per CLAUDE.md) "detects stale (page-capped) files"; `documents.json` carries no
  internal capture timestamp. Its only as-of evidence is the file mtime **2026-08-07** plus the sibling
  `catalog_report.csv`. Label `captured_at` from that and leave `source_as_of` null.
- **`SW-BULK/recap-pdfs/` is 1,564 empty directories, 0 files, 0 bytes**, although
  `catalog/recap_pdfs_manifest.json` (3,522 selected, 695 MB) and `recap_prefix_manifest.json` (137,230
  downloaded, 240 GB) describe local files. The bytes are genuinely not here — decision 5 (link out only)
  is safe, and neither manifest may be cited as evidence that a local copy exists.

### Slice 4 — `state_coordinated_proceedings_20260919`

| Claim | Measured | Verdict |
|---|---|---|
| 40 `njmcl` + 8 `njjudge` + 30 `drug` rows in `njmcl_nodes.csv` | 78 rows: njmcl 40, drug 30, njjudge 8 | confirmed |
| "each njmcl row carrying county, judge, designation_date, archived, document_count and a njcourts.gov source_url" | Fill over the 40 njmcl rows: `archived` 40, `document_count` 40, `source_url` 40 (all njcourts.gov, all distinct), **`county` 30 (75%)**, **`judge` 22 (55%)**, **`designation_date` 21 (52.5%)**. Only **3 distinct counties**: Atlantic, Bergen, Middlesex. `designation_date` is free text ("May 7 2018"); `archived` is "0"/"1" (26/14) | **wrong** |
| `njmcl_edges.csv` 57 rows | 57; columns `src,dst,type`; `concerns_product` 35, `presides` 22 | confirmed |
| 1,392 distinct `jccp_no` and 58 distinct county names | 1,392 distinct (0 null), 58 counties (the full state) | confirmed |
| 89 `masstort_candidate`, 1,258 rows with non-empty `counties` | 89; 1,258. Categories: other 952 / wage_hour 351 / masstort_candidate 89 = 1,392 | confirmed |
| logs 2017-and-older 870 / 2018-present 522 | `log` field: 870 / 522 | confirmed |
| 1,037 with case numbers, 1,392 with `date_received` | 1,037; 1,392 | confirmed |
| `judges` array is PDF-extraction noise — check 4961 and 4960 | 4961 → `['Assigning Hon. Susan I.','Marie','Marie S.','Marie S. Wiener','Marie Weiner','Susan Irene Mateo Request']`; 4960 → `['Carolyn B.','Daniel J.','Elihu','Elihu M. Berle','LASC Carolyn B.']`. File-wide 3,973 judge strings on 980 rows, ~2,512 single/two-token or trailing-initial fragments | confirmed — drop the field |
| "njmcl_registry_suggestions.json ... names five (2741, 2738, 2740, 2848, 2782)" | 19 entries; **14 carry an `mdl_number`**, written as full docket strings ("16-md-02741") — 13 distinct MDL numbers (2741, 2738, 2740, 2734, 2848, 2782, 2244, 2768, 2921, 1626, 1943, 2434, 2331), plus 2187 and 2327 inside a note string. The five in the README are only those flagged "not yet materialized" | **wrong** |

Additional measurements:

- Of those 13 MDL numbers, **7 exist in `sources/jpml_mdl_20260919/mdls.jsonl`**, all `pending`: 2741, 2738,
  2740, 2848, 2782 (the five) **plus 2768 Stryker LFIT and 2921 Allergan Biocell**. The other six (2734,
  2244, 1626, 1943, 2434, 2331) and 2187/2327 are not in the registry. The "related state proceeding" link
  lands on **7** MDL detail pages, not 5.
- The `njmcl` field in the suggestions file is **not a clean slug** in 5 of 19 entries — it carries prose
  ("pinnacle-metal-metal-mom-hip-implants (NOTE: registry may already hold a depuy ASR entry; ...)"). Only
  14 of 19 match a node id exactly; parse before matching or the cross-link silently drops.
- All 8 `njjudge` rows carry only `id`/`type`/`label`; every other column is empty. `njjudge:john-r-tunheim`
  confirmed present. Publishing NJ judge names as unlinked page text is the right call.
- `date_received` needs more than an MM/DD/YY century rule: year tokens run `99` (34 rows → 1999) through
  `26` (41 rows), and **4 rows are malformed** (`201`, `243`, `267`, plus 4-digit `2010`/`2019`). A naive
  `20%y` parse dates 34 rows to 2099. A `date_received`-derived split gives 868/524, not the `log` field's
  870/522 — use the `log` field and send the 4 malformed rows to `unresolved.jsonl`.
- `text` and `title` are non-empty on all 1,392 rows; `text` is raw concatenated PDF extraction, as stated.

### Slice 6 — `judge_financial_disclosures_20260919`

| Claim | Measured | Verdict |
|---|---|---|
| 32,336 header rows with a `person_id` column | **32,336** header rows, 32,336 distinct `id`, `person_id` present and numeric on **every** row (0 null), 3,392 distinct persons. Years 1987–2022; `report_type` 2/-1/0/3/1 | confirmed — **but only with Postgres CSV semantics** (below) |
| 1,901,720 investment rows with `description`, `gross_value_code`, `redacted`, `has_inferred_values` | 1,901,720; all four columns present; `description` non-empty 1,898,317; `redacted` true 27,404 (1.4%); `has_inferred_values` true **305,299 (16.1%)**; 28,934 distinct `financial_disclosure_id` (3,402 headers have no investment rows) | confirmed |
| overlap with `sources/judge_structured_20260919` — "MEASURE THIS" | `overlay.jsonl` carries `ids.cl_person_id` on exactly 3,701 of 10,669 entities (matches `validation.json` `bridged: 3701`). **Overlap = 1,804 person_ids (48.7% of bridged judges).** 1,588 disclosure persons are not bridged. Those 1,804 own **21,832 of 32,336 headers (67.5%)** and **1,262,064 of 1,901,720 investment rows (66.4%)** | measured |
| value fields are letter codes; no numeric dollar column | Confirmed. Money-shaped columns are `gross_value_code` (J 438,125 / K 301,232 / L 109,351 / M 94,319 / N 32,454 / O 3,924 / P1 8,859 / P2 613 / P3 64 / P4 118), `income_during_reporting_period_code` (A 794,089 / B 145,312 / C 56,949 / D 51,392 / E 20,140 / F 3,754 / G 1,693 / H1 12), plus `transaction_value_code` and `transaction_gain_code`. No amount column exists | confirmed |

Additional measurements:

- **Parse trap (build blocker).** These CSVs are Postgres `COPY ... WITH (FORMAT csv, ENCODING utf8,
  ESCAPE backslash, HEADER)` (`returnedfiles/bulk/load-bulk-data-2026-06-30.sh` line 217). A plain
  `csv.DictReader` splits on an escaped quote inside `addendum_content_raw` and returns **108,948 header
  rows** with `year` values like `'$100'` and `'& 103: Trust #s 14'`. Read with
  `csv.DictReader(f, doublequote=False, escapechar=chr(92))` — that returns exactly 32,336 / 1,901,720,
  matching `SW-BULK/manifest.json` `parquet_expected`.
- **`-1` is a sentinel, not a band**: `gross_value_code` `-1` on 29,682 rows, `income_..._code` `-1` on
  20,240, and `gross_value_code` is empty on 882,979 rows (46%). Label these "not reported" explicitly.
- **Recency is worse than "years behind."** For the 1,804 bridged judges the filed years run 1987–2020 in
  volume and collapse after (2021: 14, 2022: 12). Against a 2026-06-30 snapshot that is a ~6-year wall.
  Label "most recent filing year on file" per judge; never "current holdings."
- Provenance for this slice **is** stated: `SW-BULK/manifest.json` ("bulk/*.csv.bz2 are public CourtListener
  bulk data", snapshot 2026-06-30, per-file sha256 and the public S3 URL); the recorded sha256 and byte
  sizes match the local copies in `returnedfiles/bulk/`.
- 1,897 of 3,701 bridged judges have **no** disclosure row at all. The profile block must read "no filing
  found in the 2026-06-30 CourtListener snapshot", which is not "no holdings".

### Blockers

1. **`SW-BULK/README.md`: "Private repository. Contents include firm work product; do not fork, mirror, or
   grant external access."** This covers `catalog/documents.json` (slice 2) and `catalog/njmcl_*` (slice 4),
   which both publish derived records into the MVP. Add it to "Decisions for the user" before either builds
   — it is a stronger constraint than "no licence file anywhere."
2. **Slice 2's Settlements-tab volume is overstated by ~47%** — 2,227 rows for the pending MDLs, not 3,277.
3. **`doc_uid` is not a primary key** (4,004 duplicate rows in `documents.json`).
4. **NJ fill rates** (county 30/40, judge 22/40, designation_date 21/40, 3 distinct counties) leave the
   proposed county/FIPS filter nearly empty; the `#state/NJ` block resolves to at most 3 FIPS codes.
5. **The disclosures header CSV silently mis-parses 3.4x** without the Postgres escape character.

### Valuable data in the same input paths that no slice uses

- **`documents.json`'s 4,505 "park" rows are exactly two masters**: `4261857` / `1:14-cv-01748` Testosterone
  Replacement Therapy (2,263 rows) and `66801859` / `1:23-cv-00818` Hair Relaxer (2,242 rows). **Hair Relaxer
  is registry MDL 3060, `pending`** — recovering it by `master_docket_id`/`case_name` (the mapping is in
  `catalog_report.csv` and `masters.json`, no name matching needed) takes slice 2 to **27,840 rows across 13
  registry MDLs**.
- **The seven disclosure sibling tables** (`positions` 37,050, `reimbursements` 33,472, `spousal-income`
  20,174, `debts` 18,775, `non-investment-income` 15,302, `agreements` 10,007, `gifts` 2,025 — counts from
  `SW-BULK/manifest.json`). All join on `financial_disclosure_id`, inheriting the same 1,804-judge bridge for
  free. `positions`, `gifts` and `reimbursements` are the stronger conflict-screening signals (outside
  directorships, third-party-paid travel); slice 6 builds UI for investments only.
- **`SW-BULK/catalog/conflicts_local.json` (1.2 MB) + `conflicts_local.csv` (356 KB)** — an existing local
  judicial conflict screen built by `screen_conflicts_local.py` from these very disclosure tables and
  explicitly labelled "attorney-review candidates, not findings". Directly on slice 6's subject, unused.
- **`SW-BULK/catalog/catalog_report.csv`** — per-master `document_count` and `high_value_docs`; an
  independent QA cross-check for slice 2's per-MDL counts (its numbers match mine exactly).
- **`SW-BULK/catalog/documents_by_master/`** (34 per-master JSON files) — the per-master source layer behind
  `documents.json`; the way to spot page-capped masters.
- **`SW-BULK/catalog/njmcl_graph.json`** (14.9 KB) — the assembled NJ MCL graph sitting beside the two CSVs
  slice 4 does use; not read.
- **`returnedfiles/bulk/people-db-positions`** (51,291 rows) — places a disclosure year against the judge's
  court/seat in that year, which is what makes a holding legible.
