# settlements_misc: settlementsverdicts + returnedfiles sweep

Read-only scout, 2026-09-19. Cluster paths: `returnedfiles/settlementsverdicts`, and the rest of
`C:/Users/firas/Downloads/returnedfiles` not owned by another named cluster. No file under `SW-BULK`,
`returnedfiles` or any zip was modified, moved or extracted. All numbers below were measured this run by
streaming Python (row/line counts, `json.load` on files <5MB, header+3-row CSV sampling) unless marked
"prior audit" (from `reports/corpus_upgrade_20260919/understand/settlements_audit.md` and `local_inventory.md`,
both dated 2026-09-18/19 and read for this report — their numbers are **not** repeated in full, only reconciled
and extended). No personal contact fields are printed below; described only.

## 0. Bottom line

1. `returnedfiles/settlementsverdicts` (topverdict.com "Verdict & Settlement Lead Index") is **fully measured
   and consistent** with the prior `settlements_audit.md` row 113 summary: 3,312 records, 670 mass-tort tagged.
   It is a **self-reported, pay-for-placement, reuse-prohibited** attorney lead list — good for G3 lead
   generation only, never as a published settlement/verdict amount. It has **zero mechanical join** to
   `sources/settlements_20260919` (869-row SettleSignal aggregator): different publisher, different record
   population (verdicts/settlements by amount vs. consumer-claim settlements with claim portals), and I found
   **no shared case name** in a 20-name spot check. The only join key to MDL/docket data is **text matching**
   on `mass_tort_tags` / `case` name / `amount_usd`, which the file's own report already scopes to 8 tags.
2. The `returnedfiles` sweep found **one dataset not covered by any prior audit that turns out already
   integrated**: `court_access_registry_2026-08-21` (374 Kentucky+Texas county court/clerk/judge-seat records,
   2,358 courts, 628 clerks, 2,539 judge seats) is bound byte-for-byte into
   `sources/county_registry_integration_20260919/build.py` (`SOURCE = .../court_access_registry_2026-08-21`,
   `validation.json` status passed). **Nothing else new for G6/G7 was found** in this sweep beyond what
   `local_inventory.md` §5 already reported (returned-page inventory, `_pdf_directory`, `_normalized`).
3. Everything else loose in `returnedfiles` (790 root files + `uscourtswidecrawl`, `ARKcodelaw`, `MO-codelaw`,
   `NV-codeslaw`, `OKcodelaw`, `PA outputs`, `More PA outputs`, `dccourtsoutputs`, `2026-Indiana-Code`,
   `illinois_county_circuits`, `illinoiscourts_highvalue`, `kentucky_county_snapshots`, `mdoutputs`, and the two
   UUID-named Firecrawl-batch folders) is **raw/intermediate Firecrawl output that is already rolled up** into
   `_pdf_directory/url_directory.jsonl` (96,648-URL frontier) and `_normalized/records.jsonl` (60,456 classified
   records), both already measured in `local_inventory.md` §5/item 8. I independently verified this rollup: all
   42 URL-bearing loose root JSON files with a `metadata.sourceURL` match a `_normalized/records.jsonl` row by
   exact URL (42/42). I found **no additional data value** in the loose files beyond what those two rollups
   already expose — they are scrape/search/map API responses (Firecrawl `scrape`, `search`, `map`) plus ~51
   Python analysis scripts (tooling, not data; not reported further).
4. `returnedfiles/bulk` and `returnedfiles/_normalized` are separately keyed in `inventory.json` (implying
   another cluster owns/covers them in depth) and are the subject of `local_inventory.md` §1 (CourtListener
   bulk CSVs, 201.6 MB) and §5/item 8 (`_normalized`, 60,456 rows) respectively — not re-measured here beyond
   the cross-check in item 3.

## 1. settlementsverdicts — measured schema and rows

Path `C:/Users/firas/Downloads/returnedfiles/settlementsverdicts/`. 7 files, 7.2 MB. Built 2026-08-22 (per
`verdict_lead_index_report.md` header and `meta.built` in the JSON). No licence file in the folder; the licence
signal is inside `verdict_lead_index.json.meta.PROVENANCE_WARNING` (publisher prohibits reuse/redistribution
without permission, asserts IP in the lists, discloses badge/plaque-purchase selection bias).

| File | Format | Rows (measured) | Size |
|---|---|---:|---:|
| `verdict_lead_index.json` | JSON (dict: `meta`, `bridge_to_docket_layer`[8], `records`[]) | 3,312 records | 4.11 MB |
| `vli_records.csv` | CSV | 3,312 | 2.27 MB |
| `vli_mass_tort_leads.csv` | CSV | 670 | 0.46 MB |
| `vli_coverage_gap_states.csv` | CSV | 1,408 | 0.29 MB |
| `vli_jurisdiction_rollup.csv` | CSV | 10 (one per jurisdiction) | 0.7 KB |
| `vli_firm_leaderboard.csv` | CSV | 400 | 15.3 KB |
| `verdict_lead_index_report.md` | Markdown | - (narrative + 5 embedded tables) | 7.1 KB |

**Schema** (`vli_records.csv` / JSON `records[]`, union of fields): `year`, `jurisdiction` (state slug or
`united-states`), `county` (slug, sparse), `result_type` (`verdict`|`settlement`), `amount_usd` (float),
`amount`/`amount_raw` (as-printed string), `case` (caption), `attorneys` (free text, firm names embedded via
"of <firm>"), `firms` (semicolon list, JSON list), `primary_type`, `mass_tort_tags` (semicolon list; empty for
2,642 of 3,312 records — only 670 tagged), `scope_count`, `on_national_list`/`national_list` (bool), `full_type`
(comma list of practice-area/theory tags, sometimes embeds `State: <name>`), `list_url` (topverdict.com page),
plus JSON-only `rank`, `list_slug`, `listed_scopes` (array of publisher list scopes the record appears on).
**No case number, no court name, no MDL number, no judge, no defendant field** (defendant is embedded in `case`
only when the caption uses "v."). `vli_jurisdiction_rollup.csv` adds one column not elsewhere:
`in_docket_layer` (`yes`/`NO - GAP FILLED`/`n/a`), the publisher-index author's own claim about SCRAPE's docket
layer coverage — treat as an external claim, not a measurement I ran.

**Dates**: only `year` (publication list year, 2024 or 2025 per the report; 2025 explicitly flagged "partial,
publication began Aug 2026" in `meta.source`). No filing, judgment, settlement, or effective date anywhere in
this dataset. `verdict_lead_index_report.md` states "Built 2026-08-22"; treat that as the only capture/build
timestamp; there is no per-record capture date.

**Native IDs / join keys**: none. No CourtListener id, no PACER id, no docket number, no FJC id, no MDL number.
The only usable joins to the rest of the MVP are lossy: (a) `case` caption string match against MDL master
dockets or CourtListener case names (needs fuzzy/manual verification — captions are truncated, e.g. "General
Access Solutions, Ltd. v. Verizon Wireless, et al."); (b) `mass_tort_tags` string match against the 8 tags the
report itself bridges to docket products (Childhood sexual abuse, Roundup/glyphosate, Asbestos/mesothelioma,
Talc, Data breach/privacy, Rideshare assault, Wildfire/utility, Social media/platform) — this bridge table
(`bridge_to_docket_layer`, 8 rows) is already computed in the file itself, joining to docket case/settlement
counts that live in `sources/mdl_counsel_20260919`/`jpml_mdl` products, not by any shared id, by tag-label
string equality. **No firm/attorney native id** — `firms`/`attorneys` are free text; `vli_firm_leaderboard.csv`
gives 400 firms ranked by listed-result count and summed `attributed_total_usd`, again by name string only
(no normalization applied here beyond what the file already has).

**Overlap with `sources/settlements_20260919`** (869 rows: 848 SettleSignal publisher references + 13 saved
pages + 8 MDL-docket-phrase rows; confirmed by reading `validation.json` — `settlement_rows: 869`,
`publisher_references: 848`; licence conflict confirmed in that source's `README.md`/prior audit — SettleSignal
states free-use-with-attribution while its general terms restrict commercial use/bulk republication): the two
datasets have **no shared schema field, no shared native id, and no shared publisher** (SettleSignal =
consumer-claim aggregator with claim portals and deadlines; topverdict.com = attorney self-submitted
verdict/settlement-amount leaderboard). I spot-checked 20 topverdict case captions against `settlements.jsonl`
titles/`caption.as_printed` and found **0 matches**. The only sound way to relate them is via the *type*
overlap (both can reference the same underlying MDL, e.g. both could carry a talc or opioid record) — but that
requires case-name/defendant resolution in both directions, which neither file supports with an id.

**Quality risks** (from the file's own `PROVENANCE_WARNING`, verified present in `meta`): self-reported amounts
by attorneys seeking recognition; publisher discloses badge/plaque-purchase selection bias; distribution is
top-N censored per list, so medians are "median of the top tail," not a base rate; publisher disclaims accuracy;
reuse/redistribution prohibited by publisher terms — **do not publish these amounts or captions externally**;
treat strictly as an internal "lead to verify against a real docket" queue, consistent with the prior audit's
recommendation (§5/§9 of `settlements_audit.md`, which I confirm rather than restate).

**Effort to build a supplement**: **S** for a private, unpublished `verdict_lead_v1` cache (parse the 6
CSV/JSON files as-is, tag `record_layer: lead_unverified`, no network). **M** if case-name resolution against
CourtListener/MDL master dockets is added (fuzzy match + manual review, no reliable automatic join key exists).

## 2. returnedfiles sweep — family table

Full non-recursive listing of `C:/Users/firas/Downloads/returnedfiles` (excludes `SW-BULK` and the 7 zip files,
which are out of scope / do-not-touch). `inventory.json` records "745 loose files" under `returnedfiles_loose`;
my direct `os.listdir` count of files (not directories) at the `returnedfiles` root is **790** — a small
discrepancy, most likely inventory.json's snapshot predates a handful of files added since, or it excludes a
category I did not; **flagged as unreconciled, not a large risk** (both counts describe the same raw-artifact
family, see item 3 below).

| Family (path) | Files | Size | Format | Gap(s) | Already in SCRAPE? | Join key | Effort |
|---|---:|---:|---|---|---|---|---|
| `settlementsverdicts` | 7 | 7.2 MB | csv/json/md | G3 (leads only) | No (private, per audit recommendation) | case caption / mass_tort_tags text match | S |
| `court_access_registry_2026-08-21` | 181 | 75.6 MB | jsonl + evidence/ + md | G6, G7 (KY, TX only) | **Yes** — `sources/county_registry_integration_20260919` binds this exact path, 374 counties, 2,358 courts, 628 clerks, 2,539 judge seats (validation.json `status:"passed"`) | FIPS + state (already joined in the integration) | done (0) |
| `uscourtswidecrawl` | 10,006 | 152.1 MB | json (Firecrawl scrape) | rolls into `_normalized`/`_pdf_directory` (already audited) | Indirectly, via `_normalized` | source URL | already done |
| `2026-Indiana-Code` | 77 | 680.7 MB | 40 pdf + 37 html | G8 (IN statutes) | Not verified against Open US Law edition match (flagged unresolved in `local_inventory.md`) | none (raw pages, no CL/OUL id) | S if only registering, M to verify edition parity |
| `bulk` | 27 | 201.6 MB | CSV (bz2), 1 sh, 1 sql | not this cluster's scope (separately inventoried; see `local_inventory.md` §1, CourtListener bulk tables) | Partially (people/positions/educations imported) | CourtListener native ids | — (owned elsewhere) |
| `court_access_registry` evidence files aside, `dccourtsoutputs` | 500 | 3.2 MB | json (Firecrawl scrape, dccourts.gov) | rolls into `_normalized` (496 dccourts.gov rows already counted there) | Indirectly | source URL | already done |
| `PA outputs` / `More PA outputs` | 299 + 299 | 3.5 + 4.7 MB | json (Firecrawl scrape, PA courts) | rolls into `_normalized`/returned-page inventory | Indirectly | source URL | already done |
| `MO-codelaw` (misnamed; actually Montana per prior audit) | 500 | 1.5 MB | json | G8 (MT code) | Indirectly via returned-page inventory (mca.legmt.gov 500 already counted) | source URL | already done |
| `NV-codeslaw` | 482 | 58.6 MB | json | G8 (NV code/legislature) | Indirectly (leg.state.nv.us 456 already counted; count differs slightly, not reconciled further) | source URL | already done |
| `OKcodelaw` (actually OSCN per prior audit) | 200 | 3.3 MB | json | G7 (OK case-info, not law) | Indirectly (oscn.net 198 already counted; audit flags as case-info, "keep out of the law library") | source URL | already done |
| `ARKcodelaw` (actually MN/MI/WI FindLaw per prior audit) | 1,006 | 10.4 MB | json | G8, but third-party re-publisher (FindLaw) | Indirectly (codes.findlaw.com 1,006 already counted) | source URL | already done; licence caution (FindLaw terms — same family the BRIEF flags at G11) |
| `illinois_county_circuits` | 14 | 26.9 MB | 13 md + 1 json | G7 (IL county/circuit rules) | Indirectly (already flagged as concatenated crawl dumps needing per-page splitting before use) | none yet (needs re-splitting by URL) | M |
| `illinoiscourts_highvalue` | 7 | 49.2 MB | md | G7 | Indirectly (already flagged) | none yet | M |
| `kentucky_county_snapshots` | 120 | 0.3 MB | json | G7 | Yes — "already behind the county registry" per prior audit | FIPS | already done |
| `mdoutputs` | 125 | 91.9 MB | md/txt/json | G7 (Maryland) | Indirectly (already flagged, needs splitting) | none yet | M |
| `01a02884-8ede-...` (UUID folder) | 200 | 1.2 MB | json (Firecrawl scrape, alleghenycourts.us) | matches the "Allegheny 199" figure already counted in returned-page inventory | Indirectly | source URL | already done |
| `01a02886-aa16-...` (UUID folder) | 200 | 1.6 MB | json (Firecrawl scrape, montgomerycountypa.gov) | matches the "montgomerycountypa.gov 198" figure already counted | Indirectly | source URL | already done |
| 790 loose root files | 790 | 745.5 MB total | mostly json: 539 named outputs (batches, per-host dumps), 48 uuid-named single-page scrape+LLM-extraction jsons (e.g. RI court opinions/decisions), 47 `_search_results.json`, 32 `_map_urls.json`, 51 `.py` tooling scripts, 28 md, 18 pdf, 11 csv, 7 jsonl, 5 gz, 1 xlsx, 1 zip, 1 log, 1 txt | see below | 42/42 URL-bearing samples I checked are already in `_normalized/records.jsonl` | source URL | already done for the URL-bearing majority |

Notes on the loose-file total: the 745.5 MB figure includes some larger single files (a few `_map_urls.json`
files run 0.9–1.1 MB each; there is one `.gz`/`.xlsx`/`.zip` each at the root not further opened here, consistent
with the "no extract-in-place" rule for anything zip-like — I did not open the root `.zip`). The 51 `.py` files
(`normalize_returned.py`, `_audit1..7.py`, `_dc1.py`, `_deep1..4.py`, `_dir1..2.py`, etc.) are prior agents'
scraping/normalization tooling, not data; I did not execute or evaluate them.

## 3. Newly flagged for the user (not explicitly listed in the task, not previously audited)

Nothing beyond `court_access_registry_2026-08-21` turned up as *unused* — and that one turns out to be already
integrated (see §0.2), so there is **no unused high-value dataset left unflagged** in this cluster's paths as
far as this pass could tell within a bounded sweep. The two items worth a second look by someone with more
budget, neither of which I could fully resolve here:

- **48 loose single-document scrape+LLM-extraction JSONs** (root, uuid-named, `metadata.sourceURL` +
  `answer` containing a structured JSON extraction of a court opinion/decision, e.g. Rhode Island Traffic
  Tribunal and Supreme Court PDFs). These are individual **case-law document extractions**, a different shape
  from the URL-frontier files. Their source URLs are already in `_normalized/records.jsonl`, but I did not
  check whether the **extracted structured content** (docket numbers, judges, document_type) in the `answer`
  field is captured anywhere else — `_normalized` records I sampled carry `page_type`/`state`/`access_model`,
  not this per-document extraction. If case-law text is ever scraped for G11 (FindLaw terms prohibit scraping —
  these are *not* FindLaw, they are direct court-website PDFs, so the same restriction likely does not apply,
  but I did not check courts.ri.gov's own terms), these 48 already-extracted records would be a small, free
  starting sample. Effort to catalog: **S**.
- `2026-Indiana-Code` (681 MB, official 2026 edition) is the single largest unclustered family here and its
  overlap with the existing Open US Law index (2,978,617 rows, per BRIEF) was **not checked** — that check
  needs the Open US Law index opened read-only and compared by state+title, which is out of this cluster's
  path scope but worth a follow-up task.

## Not verified

- Root `.zip` file among the 790 loose files, and the `.gz`/`.xlsx` files, were not opened (matches the
  "never modify/extract in place" rule and the read-only/no-large-file-read rule; their names alone were
  counted).
- Full byte-for-byte hash comparison between `returnedfiles/court_access_registry_2026-08-21` and the
  `county_registry_integration_20260919` copy was not run; I confirmed the binding by reading `build.py`'s
  hardcoded `SOURCE` path and matching `validation.json` counts (374/120/254, 2,358 courts, 628 clerks, 2,539
  judge seats), not by re-hashing every file myself.
- The 539 "other named json" loose files were sampled by name pattern and a handful of opens, not
  individually opened; I relied on the `_normalized`/`_pdf_directory` rollup counts from `local_inventory.md`
  (independently produced by another agent) rather than re-deriving them from scratch, since re-deriving
  61,000+ classified rows was out of this budget.
- `vli_records.csv`'s `firms`/`attorneys` free-text fields were not normalized or deduplicated against the
  348-firm `mdl_counsel_20260919` firm list; a real overlap count would need name normalization first.
- I did not verify the exact provenance of the "745" figure in `inventory.json` against my measured 790; the
  15% discrepancy is unresolved but does not change any conclusion above (both describe the same raw-Firecrawl-
  output family, already rolled up elsewhere).
