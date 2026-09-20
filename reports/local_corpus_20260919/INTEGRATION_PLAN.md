# Local corpus -> MVP integration plan (2026-09-19)

Planner scope: read-only survey of the eight scout reports in
`reports/local_corpus_20260919/understand/`, plus first-hand measurement of the candidate inputs.
Output: a ranked list of build slices for `sources/<name>_20260919/` supplements following
`reports/corpus_upgrade_20260919/BRIEF.md` (build.py + data + uniform `validation.json` + tests,
fail-closed hash-gated adapter, generic `listing()`/`detail()` contract).

Everything numbered below was measured in this session unless it says "scout-reported".

## Corrections to the scout reports (measured here, act on these)

| Scout claim | Measured reality | Where |
|---|---|---|
| AWS b2b release covers "16 MDL master matters" | **59 matters join to 59 registry MDLs (57 pending)** once the docket suffix is zero-pad-normalized (`1:17-md-02804` vs registry `1:17-md-2804`). The 16 "support_master" rows are a subset. | `releases/b2b-.../matters.jsonl.gz` vs `sources/jpml_mdl_20260919/mdls.jsonl` |
| Joining AWS to the MDL registry needs "a docket-number/MDL-number crosswalk" | A **native** bridge already exists: `matter_aliases` namespace `courtlistener_docket_id` covers **4,155 of 4,159 matters**, and **2,113 of the 2,122** SW-catalog dockets are the same CourtListener docket ids. No name or string matching required. | `matter_aliases.jsonl.gz`, `catalog/matters.json` |
| `court_expansion_file_download` is a state/county court-forms store, "30 of 56 jurisdictions" | It is **mostly federal**: 21,967 www.uscourts.gov + 7,226 federal district + 3,367 bankruptcy + 2,474 probation + 203 appellate vs 13,468 state/DC. **33,545 of 47,445 rows carry no jurisdiction code at all.** | all `wave_*/court_file_download_results_v2.jsonl` |
| Wolson / Bailey / Shelby / Singhal are "an unverified lead" in the AWS judges table | **Ruled out.** None of the four master dockets (`ded 1:12-md-2358`, `nmd 1:16-md-2695`, `mdd 8:19-md-2879`, `flsd 0:21-md-3015`) exists in the AWS release or the SW catalog, so there is no assignment row to bridge on. Name matching is forbidden. G4 stays open. | measured against both corpora |
| `catalog/documents.json` is "docket orders, no settlement amounts" — adjacent to G3 | True about amounts, but it is the **single richest MDL asset in the corpus**: 35,862 rows with real `entry_date_filed`, a 15-value `doc_category`, `page_count`, `sha1`, `pacer_doc_id`, and **16,035 direct storage.courtlistener.com PDF URLs**. 25,598 rows join to 12 registry MDLs by native `mdl_number`. | `catalog/documents.json` |
| `_normalized` (60,456 records) is the "single highest-value item" | 55,280 of the 60,456 rows (91%) are `map_url`/`crawl_log_url` — a URL frontier. Only **1,069 rows carry a payload**, and 977 of those (614 county_record + 363 judge_roster_row) duplicate `sources/county_registry_integration_20260919`. Demoted to `firecrawl_frontiers`. | `returnedfiles/_normalized/records.jsonl` |

## Ranked slices

| # | Slice | Gaps | Rows (measured) | UI surface | Effort | Tier |
|---|---|---|---|---|---|---|
| 1 | `mdl_docket_crosswalk_20260919` | G13 | 59 MDL<->master-docket pairs; 4,155 matter<->CL-docket aliases; 2,113 shared CL docket ids | none directly (spine for 2,5,7,8) | XS-S | sonnet |
| 2 | `mdl_docket_documents_20260919` | G3, G13 | 25,598 docs / 12 MDLs; 16,035 with a PDF URL | MDL detail + Settlements | S-M | sonnet |
| 3 | `court_document_library_20260919` | G7, G8, G6 | 50,940 downloaded files, 45,478 unique sha256 | Courts detail + state page + Sources | M | sonnet |
| 4 | `state_coordinated_proceedings_20260919` | G5 | 40 NJ MCL + 1,392 CA JCCP | new Courts & litigation tab + `#state/NJ`, `#state/CA` | S-M | sonnet |
| 5 | `mdl_counsel_appearances_20260919` | G1, G2 | 878 appearances, 181 attorneys, 12 firms, 503 parties | Counsel & firms + MDL detail | M | sonnet |
| 6 | `judge_financial_disclosures_20260919` | G4-adjacent | 32,336 disclosures / 1,901,720 investments | Judge profile | M | sonnet |
| 7 | `mdl_docket_activity_20260919` | G3 | 26,549 entries / 36 MDLs (6 new vs slice 2) | MDL detail | M | sonnet |
| 8 | `mdl_case_inventory_20260919` | G13, G2 | 4,159 AWS matters + 2,122 catalog dockets; 53 member edges | MDL detail + Courts detail | M | opus |
| 9 | `sd_statutes_20260919` | G8 | 71 SD code titles, full text | Laws & rules + `#state/SD` | S | fable |
| 10 | `court_document_titles_20260919` | G7 (makes 3 usable) | up to 41,874 PDFs | folds into slice 3's surfaces | L | sonnet |

---

## 1. `mdl_docket_crosswalk_20260919` — the id spine

**Why first.** Slices 2, 5, 7 and 8 all need the same mapping and would otherwise each re-derive it and
disagree. It is half a day and it is the only thing in this plan with no UI of its own.

**Inputs (all local, read-only)**
- `C:/Users/firas/Downloads/SCRAPE/sources/jpml_mdl_20260919/mdls.jsonl` (176 MDLs, 166 pending)
- `C:/Users/firas/Downloads/SW-BULK/AWS-BATCH1-DOCKETS/releases/b2b-cdbb8d040b95c7b65cfc/matters.jsonl.gz` (4,159)
- `.../b2b-cdbb8d040b95c7b65cfc/matter_aliases.jsonl.gz` (4,202: 4,186 `courtlistener_docket_id`, 16 `courtlistener_master_docket_id`)
- `.../b2b-cdbb8d040b95c7b65cfc/matter_relationships.jsonl.gz` (53, all `member_of_mdl`)
- `C:/Users/firas/Downloads/SW-BULK/catalog/matters.json` (2,122), `catalog/masters.json` (17)
- `C:/Users/firas/Downloads/SCRAPE/sources/court_spine_20260919/courts.jsonl` (5,413)

**Join keys.** `mdl:<number>` <-> `cl_court:<id>` + master docket number (normalized: lowercase, and the
segment after the last `-` reduced to `str(int(x))` so `1:17-md-02804` == `1:17-md-2804`) <-> 
`cl_docket:<int>` (from `matter_aliases.courtlistener_docket_id`, from `catalog/matters.json.docket_id`,
from `catalog/masters.json.master_docket_id`, and from the 8 `judge_links[].cl_docket_id` already in the
registry) <-> `aws_matter:<uuid>`.

**Expected rows.** 59 MDL<->master-matter pairs (57 pending, 2 terminated: 2591, 2592); 40 additional
member matters via the 53 `member_of_mdl` edges; 4,155 matter<->CL-docket alias rows; 2,113 CL docket ids
present in both corpora; 15 of 17 `catalog/masters.json` rows carry an `mdl_number`.

**Output.** `crosswalk.jsonl` (one row per resolved pair, with `basis` naming which key matched) +
`edges.jsonl` + `unresolved.jsonl`. No adapter, no route; it is a build-time input for slices 2/5/7/8.

**Risks.** The zero-pad normalization is the only string step and must be spelled out and tested in both
directions; anything that does not match exactly on `(court, normalized docket number)` or on a native
CourtListener docket id goes to `unresolved.jsonl` with a reason. `catalog/masters.json` stores
`mdl_number` as a zero-padded **string** (`"02789"`). Two of the 59 (2591, 2592) are terminated MDLs —
keep them, label the status. The SW-BULK `.worktrees/batch2-corpus-execution` copy differs from the main
tree on 39 `mdl_master_docket_id` values and was never cross-checked: **use the main tree only**.

---

## 2. `mdl_docket_documents_20260919` — court documents on the MDL page

**The highest-value slice in the corpus.** The MDL detail page is the page a mass-tort litigator opens.
Today it has judge links, counts and reports. This gives it the actual master-docket paper trail with
real dates, a category facet, and a working link to each PDF.

**Input.** `C:/Users/firas/Downloads/SW-BULK/catalog/documents.json` (35,862 rows, 47.5 MB, single JSON array).

**Join keys.** `mdl_number` is native in the file (zero-padded string) -> `mdl:<number>`;
`court` -> `cl_court:<id>`; `master_docket_id` -> `cl_docket:<int>`; `pacer_doc_id`; `sha1`.
No name matching anywhere.

**Expected rows.** 25,598 rows across 12 registry MDLs — 2570 (2,272), 2592 (3,603, terminated),
2789 (1,361), 2804 (3,074), 2846 (1,030), 2873 (2,423), 2885 (2,909), 2913 (2,193), 2973 (416),
3047 (2,811), 3081 (2,009), 3094 (1,497). 4,505 of the 35,862 rows carry no `mdl_number` (park them in
`unresolved.jsonl`); the rest belong to MDLs 2100, 2606, 2641 which are not in the pending registry.
Dates run 2008-10-24 to 2026-08-03 and **every row has `entry_date_filed`**. Category split:
other 14,602 / opinion_order 7,674 / motion 3,289 / case_management_order 2,881 / complaint 1,658 /
remand_transfer 1,319 / motion_to_dismiss 1,196 / transcript 909 / daubert_expert 803 /
summary_judgment 477 / master_complaint 412 / bellwether 258 / answer 228 / **settlement 138** /
class_cert 18. 16,035 rows have a `download_url` and a `sha1`; 0 sealed.

**UI.** MDL detail page: a "Master-docket documents" section (filters: category, date range, search) and
the generic area `/api/area/mdl_documents`. **Second surface: the Settlements tab**, which STATE.md
records as having "no agreements/orders" — the 138 `settlement` + 2,881 `case_management_order` +
258 `bellwether` rows are exactly that missing evidence, for 11 pending MDLs.

**Risks.**
- **Licence.** There is no licence file anywhere under `SW-BULK/`. Provenance is inferred from the field
  shapes (`source: "recap"`, `storage.courtlistener.com` URLs, `pacer_doc_id`). Link out to
  CourtListener; do **not** mirror or re-host bytes. See decision 5.
- `doc_category` and `high_value` (14,319 rows) are the vendor pipeline's own classification, not the
  court's. Label them "categorised by the source pipeline, not by the court".
- `entry_date_filed` is the **docket entry** filing date, not a document date and not an effective date.
  It maps to `published_at` at best; `effective_from` stays null.
- `is_available` (16,035) means a RECAP copy exists, not that the link will resolve today. Do not re-check
  over the network in this slice; label it "as recorded by the source on capture".
- MDL 2592 is terminated. Show the status, do not silently mix it into pending-MDL counts.

**Key claims to re-verify in build:** 35,862 rows and 25,598 joining to 12 MDLs
(`C:/Users/firas/Downloads/SW-BULK/catalog/documents.json`); 16,035 rows with both `download_url` and
`sha1`; `settlement` category count 138.

---

## 3. `court_document_library_20260919` — the only corpus where the bytes are local

**Why it matters.** Every other candidate is a URL list. This is 50,940 government court documents
already downloaded, each with a SHA-256, so the MVP can actually serve an original. For an MDL
practitioner the payload is federal district-court local rules, standing orders and forms — the
documents you need before you file in a transferee court.

**Inputs**
- `C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/court_expansion_file_download_v2_4_2026-08-20/wave_*/court_file_download_results_v2.jsonl` (19 wave folders; 47,445 rows: 47,230 downloaded, 194 `download_error`, 21 `signature_rejected_body_removed`) + the `files/` tree beside them
- `C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/state_trial_court_acquisition_v1_2026-08-20/artifact_download_results_v1.jsonl` (3,718 rows, 3,710 downloaded — scout-reported) + its `files/`
- `C:/Users/firas/Downloads/SCRAPE/sources/court_spine_20260919/courts.jsonl` (5,413, each with a `website`)

**Join keys — three tiers, evidence-based, no inference.**
1. **Federal single-court domain -> `cl_court:<id>`.** Compare the manifest host to the host of
   `court_spine.website`. 62 district + 58 bankruptcy + 9 appellate domains. This is the court's own
   domain, so it is evidence, not a guess. One ambiguity: `txs.uscourts.gov` (825 files) is the shared
   site for `txsd` **and** `txsb` — emit both edges or neither, never pick one.
2. **State judiciary host -> `state:<USPS>` only.** A host like `vacourts.gov` or `txcourts.gov` matches
   dozens of court_spine rows (measured: 7,612 ambiguous rows, `txcourts.gov` alone fans out to
   `texbizct`, `texjpml`, `txctapp1..13B`, ...). Do **not** emit a court edge for these.
3. **`www.uscourts.gov` -> national, no court edge.** 21,967 files. court_spine has 9 defunct records
   whose `website` is the bare placeholder `http://www.uscourts.gov/` (`californiad`, `illinoisd`,
   `ohiod`, `okwd`, `pennsylvaniad`, `tennessed`, `bapma`, `usjc`, `reglrailreorgct`). **Exclude this
   host from the court join** or you will attach 22k files to nine dead courts.

**Expected rows.** 47,445 + 3,718 manifest rows; 50,940 downloaded. 41,355 match some court_spine
website host; excluding the `uscourts.gov` placeholder, **19,287 downloaded files reach 184 court_spine
courts**, of which ~13,270 are on unambiguous single-court federal domains. Extensions: 41,874 pdf,
3,254 xlsx, 914 docx, 839 doc, 533 xls, 15 zip, 6 txt. 45,478 unique SHA-256 of 47,230 (3.7% duplicate
bytes). 222 distinct hosts. Jurisdiction codes present on only 13,900 rows, across 31 codes
(ak 2,480 / va 1,653 / al 1,547 / wv 1,475 / ky 1,202 / md 992 / tx 637 / ... / id 1).

**UI.** Courts detail page: "Local rules, forms and orders (local copies)" with a lane facet
(federal district / bankruptcy / appellate / probation / state judiciary / national). State page:
the same list scoped to `state:<USPS>`. Sources tab: the 222 hosts as a provenance roll-up.
`original(file_id)` serves the saved bytes after re-hashing against the manifest SHA-256.

**Risks.**
- **No title.** The manifests carry `source_url`, `sha256`, `bytes`, `content_type` and a `local_path` —
  no document title and no document type. The honest fallback is the URL's last path segment, labelled
  "title taken from the file name in the URL". Slice 10 fixes this properly.
- **No county field anywhere.** Do not infer a county from a host (BRIEF rule).
- `authority_lanes` is the source pipeline's label, not the court's. Label it as such.
- Snapshot is 2026-08-20; `completed_at` is a download timestamp, never an effective date.
- robots/ToS was not checked for the 222 hosts. See decision 6.
- `local_path` values are Windows-relative and contain backslashes; they are filesystem paths and must
  never appear in a public dict.

**Key claims:** 47,445 manifest rows / 47,230 `download_status == "downloaded"` and 45,478 unique
sha256 across `.../court_expansion_file_download_v2_4_2026-08-20/wave_*/court_file_download_results_v2.jsonl`;
19,287 downloaded files join to 184 courts once the bare `uscourts.gov` host is excluded, against
`sources/court_spine_20260919/courts.jsonl`.

---

## 4. `state_coordinated_proceedings_20260919` — NJ MCL + CA JCCP

**Why.** G5 is completely empty today. New Jersey Multicounty Litigation and California JCCP are the two
state systems that matter most in mass tort, and the firm this MVP is built for is a New Jersey firm.
Both datasets are small, clean and a pure local transform.

**Inputs**
- `C:/Users/firas/Downloads/SW-BULK/catalog/njmcl_nodes.csv` (78 rows: 40 `njmcl`, 8 `njjudge`, 30 `drug`)
- `C:/Users/firas/Downloads/SW-BULK/catalog/njmcl_edges.csv` (57 edges)
- `C:/Users/firas/Downloads/SW-BULK/catalog/njmcl_registry_suggestions.json`
- `C:/Users/firas/Downloads/returnedfiles/ca_jccp_registry.jsonl` (1,392 rows)
- `C:/Users/firas/Downloads/SCRAPE/sources/counties/` (for the FIPS crosswalk)

**Join keys.** New id spaces `njmcl:<slug>` and `jccp:<number>`, plus `state:NJ` / `state:CA`, plus
`fips:<5char>` derived from the county **names** already in the data via the existing counties layer
(exact name match only; unmatched county names go to `unresolved.jsonl`). MDL cross-links **only** where
`njmcl_registry_suggestions.json` itself names an MDL number — it names five (Roundup 2741, talc 2738,
Taxotere 2740, Zostavax 2848, Physiomesh 2782) and explicitly says they are "not yet materialized".

**Expected rows.** NJ: 40 proceedings, each with county, presiding-judge name, designation date, an
`archived` flag and a live `njcourts.gov` `source_url`; 30 drug nodes; 57 edges. CA: 1,392 unique
`jccp_no`, 1,258 with counties, 1,037 with case numbers, 1,392 with `date_received`, 58 distinct CA
counties (the full state), categories `other` 952 / `wage_hour` 351 / `masstort_candidate` 89, split
`2017-and-older` 870 / `2018-present` 522. Top counties Los Angeles 511, Alameda 339, San Diego 302.

**UI.** A new "State coordinated proceedings" tab in the Courts & litigation hub (generic listing:
filters = state, county, category, archived, date range), a block on `#state/NJ` and `#state/CA`, and a
"related state proceeding" link on the five MDL detail pages the NJ registry itself names.

**Risks — read these before building.**
- **The CA `judges` array is garbled PDF-extraction noise.** Measured example, JCCP 4961:
  `["Assigning Hon. Susan I.", "Marie", "Marie S.", "Marie S. Wiener", "Marie Weiner", "Susan Irene Mateo Request"]`
  — fragments and a misspelling of one judge. **Drop the field entirely.** Do not publish it, do not
  name-match it to `judge_structured` or `judge_aliases`.
- `njjudge:john-r-tunheim` is in an 8-row New Jersey judge list but reads as the federal D. Minn. judge.
  Publish NJ presiding-judge names as **text from the njcourts.gov page**, with no entity link at all.
  NJ state judges are not FJC judges and have no `cl_person_id`.
- `date_received` in the JCCP file is `MM/DD/YY` — expand with an explicit century rule and record the
  basis; it is a filing-receipt date, not an effective date.
- The `text` field is raw concatenated PDF extraction. Keep it out of the listing; a detail page may show
  it labelled "raw extracted text, unedited".
- Neither CSV records a capture date. The `source_url` per NJ row is live; the capture is approximately
  2026-08. State this as an unknown rather than guessing.
- The CA registry is California-court-sourced with no stated licence. Low risk (public docket index), but
  it is not federal public-domain material.

**Key claims:** 40 `type == "njmcl"` rows in `SW-BULK/catalog/njmcl_nodes.csv`; 1,392 distinct `jccp_no`
and 58 distinct counties in `returnedfiles/ca_jccp_registry.jsonl`; 89 rows with
`category == "masstort_candidate"`.

---

## 5. `mdl_counsel_appearances_20260919` — fix the weakest live layer

**Why.** `sources/mdl_counsel_20260919` is the MVP's most compromised layer: 6 MDLs, only 57 full
attorney records, 4,375 name-only rows, and 2,213 firm rows that needed bar-admission notes and street
addresses stripped out. The AWS release has a *different* pipeline's output with canonical firm ids.

**Inputs** (all under `.../releases/b2b-cdbb8d040b95c7b65cfc/`)
`attorneys.jsonl.gz` (181), `firms.jsonl.gz` (12), `counsel_appearances.jsonl.gz` (878),
`parties.jsonl.gz` (503), plus slice 1's crosswalk.

**Join keys.** `aws_matter:<uuid>` -> `mdl:<number>` via slice 1; `firm:<firm_id>` (the source's own
canonical slug: `seeger_weiss`, `weitz_luxenberg`, `beasley_allen`, ...); `attorney:<uuid>`;
`party:<uuid>`. **These attorney ids are internal UUIDs, not CourtListener attorney ids.** Never merge
them with `mdl_counsel_20260919`'s CourtListener attorneys by name — publish the two layers side by side
with their sources named.

**Expected rows.** 878 appearances over 62 matters, of which **607 land on MDL-linked matters**;
503 parties over 62 matters, 369 MDL-linked; 181 attorneys; 12 firms. Firm split:
seeger_weiss 478, weitz_luxenberg 141, beasley_allen 60, simmons_hanly_conroy 56, hausfeld 53,
motley_rice 46, awko 11, lieff_cabraser 10, burg_simpson 10, grant_eisenhofer 9, keller_postman 2,
levin_papantonio_rafferty 2.

**UI.** Counsel & firms: a firm roster with a real canonical firm id and an appearance count per MDL.
MDL detail: a counsel block beside the existing `mdl_counsel` block, each labelled with its source.

**Risks.**
- **`role` is not normalised.** Measured values: `attorney_to_be_noticed` 397, `ATTORNEY TO BE NOTICED`
  205, `LEAD ATTORNEY` 140, `lead_attorney` 64, `PRO HAC VICE` 43, `terminated` 19, **`10`** 8,
  `TERMINATED: 06/29/2010` 1. The `10` is a raw CourtListener role integer ("Unknown" in the code table
  already documented in `sources/mdl_counsel_20260919/coverage.json`). Publish the raw value plus a
  normalised label with an explicit mapping table; do not silently collapse them.
- **12 firms is not a bar.** These are the plaintiff-side firms this pipeline targeted. The listing
  qualification must say "firms this source pipeline tracked, not every firm appearing in these MDLs",
  or a litigator will read absence as evidence.
- `raw_firm_name` occasionally differs from the canonical firm's name; keep both.
- Party names: `PARTY_NAME_PUBLISH_LIMIT` in `sources/mdl_counsel_20260919/build.py` exists for a reason.
  See decision 9.
- Attorney names carry no bar number, no contact detail — good. Keep it that way: no emails, no phones.

**Key claims:** 878 rows in `counsel_appearances.jsonl.gz` with 12 distinct `firm_id`; 607 of them on
matters that slice 1's crosswalk maps to an MDL; 181 rows in `attorneys.jsonl.gz`.

---

## 6. `judge_financial_disclosures_20260919` — conflict screening on the judge profile

**Why.** A mass-tort litigator drawing a transferee judge wants to know whether that judge holds stock in
the defendant. Nothing in the MVP answers that today. The join is native and already proven: the MVP
bridged 3,701 judges to CourtListener person ids, and these files key on the same id.

**Inputs** (`C:/Users/firas/Downloads/returnedfiles/bulk/`)
`financial-disclosures-2026-06-30.csv.bz2` (32,336 headers; columns include `person_id`, `year`,
`report_type`, `is_amended`, `page_count`, `sha1`, `download_filepath`, `addendum_content_raw`),
`financial-disclosure-investments-2026-06-30.csv.bz2` (1,901,720 rows; `description`,
`income_during_reporting_period_code`, `gross_value_code`, `transaction_*`, `redacted`,
`has_inferred_values`, `financial_disclosure_id`), and optionally the positions / non-investment-income /
gifts / reimbursements / debts / agreements / spousal-income siblings.

**Join key.** `person_id` == `cl_person:<int>` -> the existing `judge_structured` / `judge_entities`
bridge. Nothing else; no name matching.

**Expected rows.** 32,336 disclosure headers, 1,901,720 investment rows. Expect coverage on a subset of
the ~3,701 bridged judges (exact overlap to be measured in build — it was **not** measured here).

**UI.** Judge profile: a "Financial disclosures" block — years filed, report type, and a searchable
holdings list. The differentiating feature is a free-text search over `description` so a user can look up
a defendant name (e.g. a pharmaceutical manufacturer) across judges.

**Risks — this slice has the sharpest rules.**
- **Never publish a dollar figure.** `gross_value_code` and `income_during_reporting_period_code` are
  letter bands (A, K, L, T ...). Publish the **code and its published band label**, never a midpoint,
  never a total, never a computed portfolio value. That is "publisher-reported numbers stay labelled"
  taken to its limit.
- `has_inferred_values` marks rows where CourtListener's extraction guessed. Surface the flag; exclude
  those rows from any count the UI presents as a fact.
- `redacted` rows exist. Honour them.
- These filings include **spouse and dependent** holdings. Publish the holding description only; never a
  spouse or dependent name, and never present a holding as the judge's personal property without the
  filing's own wording. See decision 7.
- A holding is not a conflict. The qualification sentence must say the layer reports what was filed for a
  stated year and draws no conclusion about recusal.
- `filepath`/`download_filepath` point at CourtListener S3; the PDFs are **not** local. Link out only.
- Snapshot is 2026-06-30 and the disclosure years run years behind. Label both dates separately.

**Key claims:** header row count 32,336 and presence of a `person_id` column in
`returnedfiles/bulk/financial-disclosures-2026-06-30.csv.bz2`; 1,901,720 rows and a `has_inferred_values`
column in `financial-disclosure-investments-2026-06-30.csv.bz2`; the overlap between those `person_id`
values and `sources/judge_structured_20260919`'s `cl_person_id` set (measure it, do not assume it).

---

## 7. `mdl_docket_activity_20260919` — master-docket entries

**Input.** `.../releases/b2b-cdbb8d040b95c7b65cfc/docket_entries.jsonl.gz` (41,946 rows) + slice 1.

**Join keys.** `matter_id` -> `mdl:<number>` via slice 1; `entry_number` is the docket entry number.

**Expected rows.** 26,549 entries land on MDL-linked matters across 36 MDLs; 18 MDLs have real depth:
2323 (2,000), 2873 (1,997), 2570 (1,988), 3060 (1,980), 2592 (1,967), 2243 (1,920), 1570 (1,835),
2804 (1,807), 3047 (1,760), 2913 (1,628), 2885 (1,473), 3081 (1,219), 2789 (1,103), 2904 (936),
2846 (930), 3094 (839), 2921 (764), 2973 (356). Text hits across all 41,946: case management order 1,358,
steering committee 661, settlement 423, bellwether 403, pretrial order 179, leadership 172, common
benefit 106, Daubert 105.

**Marginal value over slice 2.** Slice 2 already covers 2570, 2592, 2789, 2804, 2846, 2873, 2885, 2913,
2973, 3047, 3081, 3094 with better metadata. This slice's unique contribution is **six MDLs slice 2 does
not reach at all**: 2323 (2,000 entries), 3060 (1,980), 2243 (1,920), 1570 (1,835), 2904 (936),
2921 (764). Build it for those; for the overlapping twelve, keep the two sources separate and labelled,
never merged.

**Risks.**
- **There is no date field.** The only date is embedded in the description as `(Entered: MM/DD/YYYY)`.
  Parse it, store it as `published_at` with `published_at_basis = "entered date parsed from the trailing
  '(Entered: ...)' text of the docket entry"`, and leave it null when the pattern is absent. Never infer.
- `entry_number` is a string and is not always numeric.
- Entry text contains attorney names as filers (e.g. `(SEEGER, CHRISTOPHER)`). That is the court's own
  docket text — publish verbatim, never parse it into a person entity.
- 15,397 of the 41,946 entries attach to matters with no MDL link. Park, do not guess.

**Key claims:** 41,946 rows in `docket_entries.jsonl.gz`, none with a date field; 26,549 joining to 36
MDLs via slice 1's crosswalk; 1,358 descriptions containing "case management order".

---

## 8. `mdl_case_inventory_20260919` — member cases and the G13 edge set

**Inputs.** `.../b2b-.../matters.jsonl.gz` (4,159), `matter_relationships.jsonl.gz` (53),
`matter_aliases.jsonl.gz` (4,202), `SW-BULK/catalog/matters.json` (2,122),
`SW-BULK/catalog/parties_by_docket/` (59 files), `sources/court_spine_20260919/courts.jsonl`.

**Join keys.** `cl_docket:<int>` (the shared spine — 2,113 of 2,122 catalog dockets are also in the AWS
release), `cl_court:<id>`, `mdl:<number>` via slice 1, `aws_matter:<uuid>`.

**Expected rows.** 4,159 AWS matters (4,086 `public_docket`, 57 `target_matter`, 16 `support_master`);
2,122 catalog dockets of which 977 carry an `mdl_master_docket_id`; 53 `member_of_mdl` edges yielding 40
member matters; 59 catalog `parties_by_docket` files. Court x defendant rollups should be **recomputed
from the 2,122 rows held locally**, not copied from `matter_graph/clusters.csv`.

**UI.** MDL detail: "Member cases in this corpus (N)". Courts detail: "Cases in this court held locally".

**Why opus.** This slice owns the canonical-id grammar for everything downstream. Getting an edge type or
a basis string wrong here propagates into four other layers.

**Risks.**
- `catalog/matters.json` has **no `court_id` key** — the field is `court`, and `judge` is free text
  ("Dwight H Williams"). Never build a judge edge from it.
- `firms` in `catalog/matters.json` is an array of free-text firm names with no ids. Do not reconcile
  them against slice 5's 12 canonical firm ids by name; emit them as text or not at all.
- 1,145 of 2,122 catalog dockets have no MDL master link. That is the data, not a defect.
- The worktree copy's 39 extra `mdl_master_docket_id` links were never cross-checked. Main tree only.
- `parties_by_docket` covers only 59 of 2,122 dockets, and its `attorney.firm` field is sometimes a
  street address.

**Key claims:** 4,159 rows and exactly three `node_role` values in `matters.jsonl.gz`; 53 rows in
`matter_relationships.jsonl.gz`, all `member_of_mdl`; 2,113 of 2,122 `docket_id` values in
`SW-BULK/catalog/matters.json` also present as `matter_aliases.courtlistener_docket_id`.

---

## 9. `sd_statutes_20260919` — close a named gap state

**Input.** `C:/Users/firas/Downloads/SW-BULK/publiclaw_registry_v2/staging/sd_statutes_cache_2026-08-20/`
— 71 `title_N.json.gz` files, each an API response with a full `retrieval` receipt
(`request_url`, `retrieved_at`, `http_status`, `content_type`, `content_length`) and a `payload` carrying
`StatuteId`, `Type`, `CatchLine` and a full-title `Html` body.

**Join keys.** `state:SD`; native `StatuteId` (e.g. 2030342 for Title 1) — propose
`sdcl:<StatuteId>` in the id grammar.

**Expected rows.** 71 titles. **Measured: 142 `StatuteId` nodes total, all of `Type == "Title"`, 71 with
an `Html` body — the cache is title-level only.** Section-level records do not exist in these files; they
would have to be parsed out of the HTML (lxml is installed). Scope the first pass as 71 title records
with full text; treat section extraction as a separate, later decision.

**UI.** Laws & rules (a South Dakota Codified Laws entry) and the `#state/SD` page.

**Risks.** Title-level granularity only — say so in the qualification rather than implying section
coverage. The HTML is Word-generated with megabytes of inline CSS and hashed class names; sanitise to a
reading copy and keep the original bytes separately (BRIEF rule). `retrieved_at` 2026-08-20 is a capture
date; the API returns no effective date, so `effective_from` stays null. `last_modified` and `etag` are
empty strings in the receipts.

**Key claims:** 71 `.json.gz` files in the cache directory; 142 `StatuteId` nodes, all `Type == "Title"`;
every file carries a `retrieval.http_status` of 200.

---

## 10. `court_document_titles_20260919` — makes slice 3 actually usable

**Input.** The 41,874 PDFs under the two `files/` trees from slice 3, plus slice 3's manifest rows.

**What it does.** Extract each PDF's embedded title and first-page text (pypdf; `pip install --user`
allowed by BRIEF if missing) to give every file a real title and evidence for a document-type facet
("Local Rules", "Standing Order", "Form AO-...", "Administrative Order"). Without this, slice 3 ships a
list of URL filenames.

**Join keys.** `sha256` back to the slice 3 manifest row. No new external ids.

**Expected rows.** Up to 41,874; realistically fewer — scanned PDFs and image-only forms will yield
nothing. Emit a `text_extracted` boolean and never fabricate a title.

**Risks.** Long-running (L). Some files are 13 MB+. Document type must come from the document's own text,
not from the URL path. Do not OCR. Run it as its own packet with a resumable per-file receipt so a
cut-off leaves a usable partial layer.

**Key claims:** 41,874 `.pdf` rows in the slice 3 manifests; `local_path` resolves for a sampled 100
of them under `.../wave_*/files/`.

---

## Relationship-graph note for G13 (canonical ids)

The BRIEF already fixes the grammar: `cl_person:<int>`, `fjc_nid:<int>`, `judge_entity:<entity_id>`,
`cl_court:<id>`, `mdl:<number>`, `fips:<5char>`, `state:<USPS>`, `source:<pld-id>`,
`record:<directory record id>`, `cfr:<title>:<part>[.<section>]`, `fr_doc:<number>`, `settlement:<id>`,
`firm:<normalized domain or slug>`, `attorney:<source-native id>`.

**This plan adds six id types. Register them once, in slice 1, before slices 2/5/7/8 run:**

| New id | Source of truth | Used by |
|---|---|---|
| `cl_docket:<int>` | `matter_aliases.courtlistener_docket_id`, `catalog/matters.json.docket_id`, `catalog/masters.json.master_docket_id`, `mdls.jsonl judge_links[].cl_docket_id` | 1, 2, 7, 8 |
| `aws_matter:<uuid>` | `matters.jsonl.gz matter_id` | 1, 5, 7, 8 |
| `pacer_doc:<id>` | `catalog/documents.json.pacer_doc_id` | 2 |
| `njmcl:<slug>` / `njjudge:<slug>` | `catalog/njmcl_nodes.csv` | 4 |
| `jccp:<number>` | `ca_jccp_registry.jsonl.jccp_no` | 4 |
| `sdcl:<StatuteId>` | `sd_statutes_cache_2026-08-20` payload | 9 |

**Rules that this corpus specifically stress-tests.**

1. **`cl_docket` is the real spine, not the docket number string.** 2,113 of 2,122 SW-catalog dockets and
   4,155 of 4,159 AWS matters carry a CourtListener docket id. Prefer it over `(court, docket_number)`
   everywhere. The zero-pad normalization exists only to reach the JPML registry, which stores the master
   docket as printed by JPML.
2. **Never merge people by name — and this corpus is full of traps.** `catalog/matters.json.judge`,
   `catalog/firms.json` (five casing variants of one Seeger Weiss partner under `attorney_count: 1`),
   `matter_graph/firms.csv.top_judges`, the CA JCCP `judges` array (fragments), and the NJ `njjudge`
   nodes (one of which looks like a federal judge in a state list) are all free text. None of them may
   produce a `cl_person` or `judge_entity` edge.
3. **Two attorney id spaces, deliberately unmerged.** `attorney:<uuid>` from the AWS release and the
   CourtListener attorney ids in `mdl_counsel_20260919` describe overlapping people. Leave them separate,
   each labelled with its source, until a native id bridges them.
4. **Court edges only where the domain identifies one court.** Slice 3's tiering (federal single-court
   domain -> `cl_court`; state judiciary host -> `state:<USPS>`; `www.uscourts.gov` -> no edge) is the
   pattern. `court_spine`'s nine `http://www.uscourts.gov/` placeholder websites are the counterexample
   that proves it.
5. **Separate the dates.** `entry_date_filed` (docket filing), `completed_at` (download),
   `retrieved_at` (API capture), `date_received` (JCCP receipt), `designation_date` (NJ MCL) and
   `(Entered: ...)` (parsed from text) are six different things and none of them is an effective date.
   Each gets its own `*_basis`.
6. **Publisher counts stay publisher counts.** `documents.json.high_value` and `doc_category`,
   `authority_lanes`, `firms.csv.total_matters`, and every financial-disclosure value code are the
   source's own labels. Never derive a rate from them.
7. **Unresolved joins go to `unresolved.jsonl` with a reason**, not to a best guess. Expected volumes:
   4,505 documents with no `mdl_number`; 1,145 catalog dockets with no MDL master; 33,545 download rows
   with no jurisdiction code; 15,397 docket entries with no MDL link.

---

## Not worth building

- **`b2b documents` (13,971 rows).** S3 pointers (`s3_bucket: FORAWS`) with no local bytes and no
  reachable bucket. Nothing to render. `catalog/documents.json` (slice 2) covers the same ground with
  actual links.
- **`b2b provenance` (124,221), `review_records` (32,941), `source_records` (72,860).** An internal audit
  trail. Useful for verifying a build, worthless on a page.
- **`b2b opinions` (900) and `outcomes` (25).** Measured: only **46 opinions** attach to MDL-linked
  matters, and 851 of 900 have `precedential_status: "Unknown"`. All 25 `outcomes` rows have
  `amount: null` — there are no settlement amounts here, despite the name.
- **`b2b coverage` (8 rows).** Pilot-criterion bookkeeping.
- **CL bulk `courthouses` (3,361 rows).** Only 4 have a street address. G6 is not fillable from this file;
  the scout already ruled it out and I concur.
- **CL bulk `citations` (>12M rows).** `cluster_id` points at opinion clusters that were never shipped
  locally. A citation graph with no nodes.
- **CL bulk `originating-court-information` (973,419).** Sparse appellate-origin rows with no MDL bearing.
- **CL bulk schema-only tables** (`people_db_attorney*`, `people_db_party*`, `recap_fjcintegrateddatabase`,
  `search_opinion` full text, `people_db_abarating`). Zero rows shipped. G1/G2/G10/G11 cannot be filled
  from `returnedfiles/bulk` — that needs a network fetch, not a build slice.
- **`SW-BULK/stateurls` (58 DOJ markdown pages).** Superseded: `sources/doj_state_resource_map_20260919`
  holds the same 58 justice.gov URLs re-captured 2026-09-13 with fuller provenance.
- **`returnedfiles/doj_state_sources.jsonl` (2,965 rows).** 99.7% domain overlap with that same live
  layer. Four new domains. Not a slice.
- **`_normalized` payload rows.** 614 `county_record` (KY 360 + TX 254 — KY has 120 counties, so that is
  roughly three copies) and 363 TX `judge_roster_row` duplicate
  `sources/county_registry_integration_20260919` (2,358 courts, 628 clerks, 2,539 judge seats, already
  validated). The roster rows also carry `court_email`, `phone` and `fax`, which the public-dict contract
  forbids. The remaining 55,280 rows are a URL frontier — see below.
- **`SW-BULK/catalog/attorneys.json` (129) and `firms.json` (52).** `attorney.firm` is sometimes a street
  address (measured: `"firm": "333 Main Street"`), and `SEEGER WEISS LLP` lists five casing variants of
  one partner while reporting `attorney_count: 1`. Slice 5's canonical `firm_id` supersedes this entirely.
- **`matter_graph/firms.csv`.** `top_courts` and `top_judges` are computed from the 60 dockets the catalog
  pulled, printed in the same row as `total_matters: 6463`. It reads as a firm's litigation footprint and
  is a 1% sample of one. Recompute rollups from the 2,122 dockets in slice 8 instead.
- **`SW-BULK/catalog/judges.json` (342).** Rich FJC-style bios, but `sources/judge_structured_20260919`
  already carries 10,669 rows with 4,074 FJC and 3,701 CourtListener bridges. Redundant.
- **`map_mdl.parquet` (10.1 MB, never decoded; pyarrow not installed).** `matter_aliases` already supplies
  the MDL<->docket bridge natively. Decode only if slice 1 comes up short. See decision 10.
- **G4's four unresolved judges.** Measured and closed: none of `ded 1:12-md-2358`, `nmd 1:16-md-2695`,
  `mdd 8:19-md-2879`, `flsd 0:21-md-3015` exists in the AWS release or the SW catalog, so there is no
  assignment row to bridge on and no local native-id path. Name matching is forbidden. This is a small
  CourtListener docket lookup, not a build slice.
- **`AWS-BATCH1-DOCKETS/staging/unpublished-drafts/` and `state/batch2a/`.** Pre-acceptance quarantine
  artifacts and a mid-build scratch tree (`current.json` literally says `status: building`). See decision 4.
- **`publiclaw_registry_v2/archive/superseded_staging_runs/release_v21` (354.9 MB, 195 files).**
  Explicitly archived and superseded run-by-run. The promoted versions live in
  `publiclaw_registry_v2/current/`, which no scout was assigned. Do not build from the archive; scope
  `current/` separately if anyone wants it.
- **`phase1_directory_contract_v3_2026-08-22`.** Zero ingestible rows,
  `status: phase1_dry_run_not_promoted`, authorises no writes. Interesting as an identity-grammar
  reference, not as data.
- **`publiclaw_registry_v2/analysis` (64 files).** QA logs for a month-old pipeline.
- **The three superseded AWS releases** (`b1-78fe28d84a27a8764b57`, `b1-2e03d6c8b8189fab6f09`,
  `b1-d44f3eb792b161b74dfd`) and the worktree mirror of them. `b2b` is the authoritative end of the
  lineage; the worktree mirror does not even contain b2a/b2b.
- **`returnedfiles` zip duplicates.** `filejaaas.zip`, `filejhs.zip`, `filesjhg.zip`, `filestoxxx.zip`,
  `filesdee.zip`, `filesdfsdfsdfsds.zip` are byte-identical (SHA-256 verified by scouts) to loose files
  already present. Only `filesccsdfsdfs.zip` has unique content (see frontiers).

## Firecrawl frontiers (URL lists only — no payloads, so no slice)

| Frontier | Rows | Gap served | Note |
|---|---|---|---|
| `SW-BULK/source_gap_reconciliation_2026-08-22/state_map_group{1,2,3}.jsonl` | 19,245 (12,198 core_directory + 6,726 secondary_official + 321 quarantined) | G7 county courts / clerks / local rules / forms, secondary G5, G6 | The best frontier here. Its "9,436 novel" figure is novel only against that project's two internal baselines — **dedup against `sources/public_law_directory_20260919/catalog.json` (9,348 refs) and `court_spine` before spending a credit.** Full 50-state coverage tally was never done. |
| `returnedfiles/deep_crawl_urls.jsonl` | 178,961 URLs / 63,684 docs | G9, G14 | Broadest and least curated; CDN and file-hosting domains dominate. Needs per-`sources`-tag triage (fjc, ca_oal, ...). |
| `returnedfiles/state_admin_agency_urls.jsonl` | 118,056 URLs / 26,784 docs | G9 | Misnamed: sampled rows are federal CMS/FTC/GPO under `layer: federal_agency`. Duplicate-hostname noise (akamaitech.net variants). |
| `returnedfiles/doj_sweep_urls.jsonl` + `doj_sweep_documents` | 55,711 URLs / 18,849 docs (10,676 pdf, 8,172 doc) | G7, G8 | Covers only 13 states (AK AR CT KS MI MO NC ND NV OK OR WV WY) despite the name. Not deduped across near-duplicate domains. |
| `returnedfiles/_normalized/records.jsonl` (`map_url` + `crawl_log_url`) | 55,280 of 60,456 | G14 | Already classified by `page_type` and `state` with `content_sha256` back-references — the cheapest frontier to prioritise from. ~5% self-flagged cache-stale/throttled. |
| `returnedfiles/tier1_toxicology_directory.jsonl` | 15,073 | G9 | ATSDR/CDC. Strip social-share and tracking URLs first. |
| `filesccsdfsdfs.zip -> uscourts_crawl_1404.tar.gz` | 1,404 pages + 677 external links | G6, G14 | The only zip with unique content. 57,642 Firecrawl credits already spent; page bodies sit in 13 concatenated `.md` parts (84.5 MB) not yet split by URL. Split locally before re-crawling anything. |
| `SW-BULK/source_gap_reconciliation_2026-08-22/sources_*.jsonl` + `direct_machine_endpoints.jsonl` | 134 + 49 | G9, G12, G7 | Metadata only; every row is `phase_gate: directory_record_only_no_payload_download`. Valuable for its identifier grammar (FDA ApplNo/NDC, SEC CIK/accession, EPA DTXSID/CASRN). `rights_access` is a flag, not a resolved licence. |
| `publiclaw_registry_v2/staging/govinfo_novel_urls_2026-08-20.jsonl` (7.75 GB), `govinfo_granules_2026-08-20.jsonl` (5.0 GB), `federal_granule_files_large_delta_2026-08-20.sqlite` (9.5 GB) | not counted | G8, G14 | README marks most as `derived_unverified` or superseded. Would introduce a new id class (`govinfo_package:<id>` / `govinfo_granule:<id>`). Only open under the README's canonical-version discipline. |

Firecrawl balance is 3,649 credits (STATE.md). The Trellis county retry is CLOSED — do not re-queue it.

## Decisions for the user (not slices until answered)

1. **FindLaw (32,622 records / 24,652 opinions, ~829 MB).** ToS prohibits scraping and redistribution.
   Option A: a **private** citation-lookup index holding only regex-extracted case name / court / decided
   date / docket number, never serving the markdown, used as a bridge list into CourtListener.
   Option B: leave it untouched. Nothing ships FindLaw text either way.
2. **`returnedfiles/settlementsverdicts` (3,312 topverdict.com leads, 670 mass-tort tagged).** Self-
   reported, top-N censored, reuse-prohibited, and it collides with the settlements-feed licence conflict
   already open in STATE.md. Private lead cache, or drop? Zero case names or ids are shared with the
   existing 869-row settlements feed, so it cannot be validated against anything.
3. **`session_leftovers.tar.gz -> leftovers/ca_jccp_records_raw.jsonl` (2.37 MB).** Overlaps the loose
   `ca_jccp_registry.jsonl` that slice 4 uses. Confirm slice 4 uses the loose registry and ignores the tar
   copy (a bundled `parse_jccp.py` is stated re-runnable if the raw version is ever preferred).
4. **AWS `staging/unpublished-drafts/b1-1f315ddc43e47b8df148`** reports 14,013 documents verified /
   21,410 quarantined against the published baseline's 13,971 — a 42-document disagreement that was never
   root-caused. Confirm this stays out of every build.
5. **No licence file exists anywhere under `SW-BULK/`.** CourtListener/RECAP provenance is inferred from
   field shapes (`source: "recap"`, `pacer_doc_id`, `storage.courtlistener.com`). Confirm: slice 2 links
   out to CourtListener and never re-hosts RECAP bytes.
6. **Slice 3 serves local originals.** 47,230 government files were downloaded 2026-08-20; robots/ToS was
   never checked for the 222 hosts. Serve originals from the local MVP (they are government documents and
   the server is loopback-only), or index-only with link-out to the source URL?
7. **Judge financial disclosures include spouse and dependent holdings.** Confirm the rule: publish
   holding description + year + value **code** only; never a dollar estimate, never a total, never a
   spouse or dependent name.
8. **Main tree vs worktree.** `SW-BULK/.worktrees/batch2-corpus-execution/catalog` has 39 extra
   `mdl_master_docket_id` links and 79 fewer files than the main tree, and the 39 were never cross-checked
   against CourtListener. Confirm: main tree only, everywhere.
9. **`PARTY_NAME_PUBLISH_LIMIT`** (in `sources/mdl_counsel_20260919/build.py`) withholds party names above
   1,000 per docket. Does it apply to slice 5's 503 AWS party rows? They are far under the limit, but the
   policy was written for a reason.
10. **`map_mdl.parquet` (10.1 MB).** Decoding needs `pyarrow`, which BRIEF does not permit installing.
    `matter_aliases` already gives the bridge natively, so the recommendation is skip. Confirm, or
    authorise the install.

## Suggested order

Slice 1 first (everything else joins on it). Then 2 and 4 in parallel — they share no inputs and land on
different pages. Then 3, and 5/7 against slice 1's crosswalk. 6 is independent of all of them and can run
any time. 8 after 1. 9 any time. 10 only after 3 ships and someone has looked at it.


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

## Verification 1 (independent re-measurement, 2026-09-19)

Read-only skeptical re-measurement of slices 1, 3 and 5 against the named files. Method: streaming Python
over `matters/matter_aliases/matter_relationships/attorneys/firms/counsel_appearances/parties.jsonl.gz`
in `SW-BULK/AWS-BATCH1-DOCKETS/releases/b2b-cdbb8d040b95c7b65cfc/`, `sources/jpml_mdl_20260919/mdls.jsonl`,
`sources/court_spine_20260919/courts.jsonl`, `SW-BULK/catalog/{matters,masters}.json`, the 11
`court_file_download_results_v2.jsonl` manifests and `artifact_download_results_v1.jsonl`. Scripts:
`reports/local_corpus_20260919/verify1/`. Nothing under `SW-BULK` or `returnedfiles` was modified.

### Slice 1 — `mdl_docket_crosswalk_20260919`

| Claim | Measured | Verdict |
|---|---|---|
| 176 MDLs, 166 pending in `mdls.jsonl` | 176 rows; 166 pending, 10 terminated | confirmed |
| 59 matters join 59 MDLs, 57 pending, after zero-pad normalization | 59 pairs / 59 matters / 59 MDLs; 57 pending, 2 terminated (**2591, 2592**) | confirmed |
| zero-pad normalization is load-bearing | exact-string join on (court, docket_number) yields **0** pairs; all 59 require it | confirmed |
| `matter_aliases` 4,186 `courtlistener_docket_id` + 16 `courtlistener_master_docket_id`, covering 4,155 of 4,159 matters | 4,202 rows = 4,186 + 16; 4,155 matters have a `courtlistener_docket_id`; all 4,159 have some alias | confirmed |
| 2,113 of 2,122 `catalog/matters.json` `docket_id` values appear as `matter_aliases.courtlistener_docket_id` | **2,122 of 2,122 (100%)** — 2,122 distinct ids, all present | confirmed, number corrected to 2,122 |
| `matter_relationships` has exactly 53 rows, all `member_of_mdl` | 53 rows, all `member_of_mdl` | confirmed |
| 40 additional member matters via the 53 edges | 40 — but only when edges are filtered to parents inside the 59-matter crosswalk | confirmed with caveat |
| 15 of 17 `catalog/masters.json` rows carry an `mdl_number`, zero-padded string | 15 of 17; all 15 are str ("02570", "02789", ...) | confirmed |
| worktree copy differs on 39 `mdl_master_docket_id` values | exactly 39 differ; main tree 977 non-null, worktree 1,016 | confirmed |

**New finding (gap, not in the plan).** The 53 `member_of_mdl` edges point at **16** distinct parent
matters, and **4 of those parents are not in the 59-matter crosswalk**; the 13 member matters hanging off
them get no MDL. `unresolved.jsonl` must carry these with a distinct reason
("member_of_mdl parent not resolvable to an MDL"), otherwise slices 5/7/8 silently drop them.

### Slice 3 — `court_document_library_20260919`

| Claim | Measured | Verdict |
|---|---|---|
| 19 wave folders, 47,445 rows | 47,445 rows, but from **11** folders holding a `court_file_download_results_v2.jsonl`; the other 8 `wave_*_followup` / `_cumulative_followup` folders hold only retry/review queues | row count confirmed; folder count wrong (11) |
| 47,230 `download_status == "downloaded"` | 47,230 (plus 194 `download_error`, 21 `signature_rejected_body_removed`) | confirmed |
| 45,478 unique sha256, 3.7% duplicate bytes | 45,478 unique of 47,230; 1,752 duplicate-extra rows = 3.71% | confirmed |
| 3,718 state-trial rows; 50,940 downloaded overall | 3,718 rows (3,710 downloaded); 47,230 + 3,710 = 50,940 | confirmed |
| extensions 41,874 pdf / 3,254 xlsx / 914 docx / 839 doc / 533 xls | identical | confirmed |
| 33,545 of 47,445 rows have an empty `jurisdiction_codes` | 33,545; 13,900 rows carry one or more codes | confirmed |
| across 31 codes | **30** distinct codes | wrong (minor) |
| `authority_lanes` 21,967 / 13,468 / 7,226 | identical (plus bankruptcy 3,367, probation 2,474, territorial 432, appellate 203) | confirmed |
| 222 distinct hosts | 222 — court-expansion manifest only, `final_url` host, no `www.` stripping. **Adding the state-trial manifest takes it to 310.** | confirmed for that definition; understated for the slice as scoped |
| 41,355 downloaded files match a court_spine website host | **41,246** (court-expansion only, `www.`-stripped) | confirmed within tolerance, corrected to 41,246 |
| 19,287 downloaded files once the bare `uscourts.gov` host is excluded | **19,287 exactly** | confirmed |
| ...reach **184** court_spine courts | **206** courts. 184 is the number of single-court `*.uscourts.gov` domains in the spine, not the number of courts reached. Only **107** of those 184 federal courts have a downloaded file at all. | **wrong** |
| ~13,270 on unambiguous single-court **federal** domains | 19,287 - 7,612 = **11,675** files on single-court hosts of any kind (13,184 if the state-trial manifest is folded in, which is probably where 13,270 came from). Files on single-court `*.uscourts.gov` domains: **7,715**, reaching 107 courts (50 district, 50 bankruptcy, 7 appellate). | **wrong** |
| tier 1 = 62 district + 58 bankruptcy + 9 appellate domains | spine has **82 FD + 83 FB + 10 F** single-court `*.uscourts.gov` domains (184 total, with FBP 4, FS 3, MA 1, T 1). Restricted to domains that actually appear in the manifests: 50 / 50 / 7. Neither reading gives 62/58/9. | **wrong** |
| measured 7,612 ambiguous rows (tier 2) | **7,612 exactly** (court-expansion, `www.`-stripped). Combined with state-trial: 9,426. | confirmed |
| exactly 9 court_spine rows have website host `uscourts.gov`, all defunct placeholders, ids as listed | exactly those 9 ids | count and ids confirmed; **"all defunct" is wrong** |
| `txs.uscourts.gov` shared by txsd and txsb | txsd -> `http://www.txs.uscourts.gov/`, txsb -> `http://www.txs.uscourts.gov/bankruptcy/` — same host. **17** such multi-court federal hosts exist (arb, ca8/bap8, ca9/bap9, meb/bapme, cafc/ccpa, fisc/fiscr, idb/idd, insd/indianad, mow...) | confirmed and **wider than stated** |
| `local_path` values are Windows-relative paths | true for all 47,445 court-expansion rows; **all 3,718 state-trial rows carry absolute `C:\Users\...` paths** | partly wrong — higher leakage risk |

Detail on the 9 placeholders: all 9 have `in_use: true`; only 6 carry an `end_date` (californiad 1886,
illinoisd 1855, ohiod 1855, pennsylvaniad 1818, tennessed 1839, reglrailreorgct 1996). `bapma`, `okwd` and
`usjc` have `end_date: null`, and `reglrailreorgct` / `usjc` do not use the bare URL at all. Also note the
recorded host is `www.uscourts.gov`; excluding it requires `www.` stripping, and every number above that
matches the plan was reproducible only with that stripping — the plan should say so.

Bytes are real: a 200-row random sample of court-expansion `local_path` values is 100% present on disk and
15 re-hashed files matched their manifest `sha256` exactly; a 100-row state-trial sample is 100% present.

### Slice 5 — `mdl_counsel_appearances_20260919`

| Claim | Measured | Verdict |
|---|---|---|
| 878 appearances over exactly 12 `firm_id` values, with the listed per-firm counts | 878 rows, 62 matters, 12 firms; seeger_weiss 478, weitz_luxenberg 141, beasley_allen 60, simmons_hanly_conroy 56, hausfeld 53, motley_rice 46, awko 11, lieff_cabraser 10, burg_simpson 10, grant_eisenhofer 9, keller_postman 2, levin_papantonio_rafferty 2 | confirmed, exact |
| 607 of 878 appearances and 369 of 503 parties land on MDL-mapped matters | 607 and 369 — **only with the crosswalk extended through the `member_of_mdl` edges**. On the 59 direct matches alone it is **192 appearances / 67 parties**, touching 3 MDLs instead of 14. | confirmed, with a hard dependency |
| 181 attorneys, 12 firms, `attorney_id` a UUID, no CourtListener attorney id | 181 / 12; all 181 ids are UUIDs; no CourtListener field anywhere in `attorneys.jsonl.gz` | confirmed |
| `role` has 8 distinct raw spellings including the bare string '10' | **9** spellings. The 8 listed, plus `unknown` (1 row). Counts: attorney_to_be_noticed 397, ATTORNEY TO BE NOTICED 205, LEAD ATTORNEY 140, lead_attorney 64, PRO HAC VICE 43, terminated 19, '10' 8, 'TERMINATED: 06/29/2010' 1, 'unknown' 1. | **wrong** — enumeration incomplete |
| MVP layer is 6 MDLs / 57 attorney records / 4,375 name-only / 2,213 firm rows | `sources/mdl_counsel_20260919/validation.json`: mdls 6, attorney_records 57, attorney_name_only_rows 4,375, firm_rows 2,213 | confirmed |

Role mapping trap: `sources/mdl_counsel_20260919/coverage.json` publishes the CourtListener Role choices,
where **code 10 = "Unknown"**. So '10' and the literal 'unknown' are the same concept arriving by two
routes. The explicit mapping the plan asks for must say that, and must not fold 10 into `terminated`.

### Draft / unpublished / licence status

- `releases/b2b-cdbb8d040b95c7b65cfc/manifest.json`: status `successor`, validation `pass` with no errors,
  built 2026-08-24, predecessor `b2a-0ef93bbef92cff5b3532`. Not a draft. Its own row counts match every file
  measured here. `descriptor.run_scope` records requested_docket_aliases 4,186, returned_docket_aliases 4,160,
  selected_canonical_matters 4,129 — worth surfacing as the coverage qualification for slices 1 and 5.
- Decision item 4 confirmed: `staging/unpublished-drafts/b1-1f315ddc43e47b8df148/report/pilot_summary.json`
  reports documents_verified 14,013 and documents_quarantined 21,410 (the quarantine file itself holds
  21,412 rows) against the published baseline's 13,971 — a 42-document disagreement. That draft is labelled
  release_status `baseline`, covers only 57 target matters / 489 appearances / 10 firms, and must not be
  mixed with b2b.
- Decision item 5 confirmed: no data licence exists anywhere under `SW-BULK/`. The only LICENSE files are
  Python wheel licences under `publiclaw_registry_v2/.deps/`. Neither court manifest has any licence, terms,
  robots or rights field — `authority_lanes` and `authority_statuses`
  (`inherited_from_reviewed_or_reviewable_host_seed_not_promoted`) are pipeline scope labels, not permissions.

### Valuable data in the same input paths that the plan ignores

1. **`staging/court_expansion_file_preflight_v2_4_2026-08-20/court_file_preflight_results_v2.jsonl`
   (49,647 rows) and `staging/court_expansion_corpus_v2_4_2026-08-20/court_expansion_file_url_corpus_v2.jsonl.gz`
   (52,798 rows).** All 47,230 downloaded court-expansion artifacts join 1:1 to these on `artifact_id` /
   `url`, and **19,866 of them carry a `source_families` classification across 18 families** —
   forms_instructions_and_filing_packets 3,591, rules_local_rules_and_procedures 1,592,
   orders_administrative_orders_and_notices 1,804, opinions_decisions_and_tentative_rulings 1,276,
   judges_justices_magistrates_and_chambers 1,664, statistics_reports_data_api_and_bulk 5,691, and 12 more.
   This is exactly the "no document type in the manifests" gap slice 3 declares and defers to slice 10 —
   it already exists as source-pipeline evidence and needs no new fetching. The same join also supplies
   `discovery_methods`, `quality_flags`, `canonical_url`, `etag` and an HTTP `last_modified` on 47,075 rows
   (a transport header, never an effective date). `associated_court_ids` is present as a field but is
   **empty on every row**, so it cannot replace the host tiering.
2. **The 8 ignored `wave_*_followup` / `wave_*_cumulative_followup` folders** — retry and review queues
   (`court_file_download_review_queue_v2.jsonl.gz`, `court_file_download_complete_continuation_v2.jsonl.gz`).
   They explain the 194 download_error and 21 signature_rejected rows and would let the qualification state
   what is missing rather than only what was kept.
3. **`releases/.../judicial_assignments.jsonl.gz` (4,776) + `judges.jsonl.gz` (867, with `native_judge_id`)** —
   matter-level judge assignments for all 4,159 matters, joinable to the slice-1 spine on `matter_id` and to
   the judge layer on a native id. No slice uses either.
4. **`releases/.../docket_entries.jsonl.gz` (41,946) and `documents.jsonl.gz` (13,971, all
   verification_status `verified`, each with a `sha256` and an `s3_key`)** — slices 2 and 7 work from the
   SW catalog; this release-side pair covers the same ground with per-row hashes and is the only place the
   document/entry linkage is expressed as matter_id -> docket_entry_id -> document_id.
5. **`releases/.../outcomes.jsonl.gz` (25 rows)** — evidence_level `official_dataset_reported`, every
   `amount` and `amount_disclosed` null. Directly relevant to `settlements_20260919`: 25 termination events
   with no money attached, a useful negative control for the settlement layer's qualification.
6. **`releases/.../coverage.jsonl.gz` (8 rows, with `represented_docket_ids`) and `opinions.jsonl.gz` (900)** —
   the release's own statement of what it covers; nothing in the plan reads it.
7. **`releases/.../provenance.jsonl.gz` (124,221), `source_records.jsonl.gz` (72,860),
   `review_records.jsonl.gz` (32,941)** — the receipt chain behind every row slices 1 and 5 publish.
