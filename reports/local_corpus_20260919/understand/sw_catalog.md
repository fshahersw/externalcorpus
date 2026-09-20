# sw_catalog — SW-BULK catalog / parties_by_docket / matter_graph

Scope: `SW-BULK/catalog`, `SW-BULK/catalog/parties_by_docket`, `SW-BULK/.worktrees/batch2-corpus-execution/catalog`,
`SW-BULK/.worktrees/batch2-corpus-execution/matter_graph`. Read-only measurement; nothing under SW-BULK was modified.

## 0. Headline

None of this is wired into the MVP: `grep -r SW-BULK sources/ delivery/archive-directory/` finds **zero** matches
(the only "catalog" hits in `sources/` are unrelated `catalog.sqlite3`/`catalog.json` filenames in other layers). The
main `SW-BULK/catalog` tree (136 files, 177.6 MB) is a Seeger-Weiss-anchored litigation graph — matters, parties,
attorneys, firms, judges, a document index, plus regulatory/statute/clinical-trial edge tables — built from CourtListener
RECAP data (no README/manifest/licence file exists anywhere in the tree; provenance is inferred from field content: `sha1`,
`pacer_doc_id`, `courtlistener_url`, `download_url` fields on every document row, and a build tool named "recap" in the
manifests). The `.worktrees/batch2-corpus-execution` copy is a **smaller, incomplete branch** (60 vs 136 files) of the
same generation run, not a separate dataset — see section 5.

## 1. Files in scope, measured

| Path | Format | Measured rows/size | Native IDs | Dates | Notes |
|---|---|---|---|---|---|
| `catalog/matters.json` | JSON array | 2,122 rows, 1.14 MB | `docket_id` (CourtListener docket int) | `date_filed`, `date_terminated` | One row per docket: court, case_name, defendant, judge (name string), firms (role-tagged), `roles` (`anchor`\|`competitor`), `mdl_master_docket_id`, `courtlistener_docket_url` |
| `catalog/parties_by_docket/*.json` | 59 JSON files (1 per docket) | 1.0 MB total | `docket_id`, `attorney_id` (CourtListener) | none per-record | `{docket_id, docket_number, court, case_name, mdl_master_docket_id, parties:[{name, party_types, attorneys:[{attorney_id, name, firm, role}]}]}`. Full party+attorney rosters, not name-only |
| `catalog/attorneys.json` | JSON array | 129 rows, 25 KB | `attorney_id` | none | name, firm (free text, sometimes a street address — data-quality risk), `docket_count`, `roles` |
| `catalog/firms.json` | JSON array | 52 rows, 12.5 KB | none (firm name is the key) | none | firm, attorney list (name variants not deduped — e.g. 5 spellings of "Christopher A. Seeger"), `attorney_count`, `docket_count`, `appearances_by_side` |
| `catalog/judges.json` | JSON array | 342 rows, 1.78 MB | `judge_id` = CourtListener person id, `fjc_id` | dob, position start/termination dates | Full FJC-style bios: educations, political_affiliations, aba_ratings, positions (court, appointer, how_selected) |
| `catalog/masters.json` | JSON array | 17 rows, 15 KB | `master_docket_id` (CourtListener), `mdl_number` (15 of 17 have one) | `date_filed` | MDL master dockets with assigned_judge (+ `assigned_judge_id`), `clusters` (defendant x court x docket-count), `document_count`, `high_value_docs` |
| `catalog/documents.json` | JSON array | 35,862 rows, 47.5 MB | `doc_uid`, `master_docket_id`, `pacer_doc_id`, `sha1` | `entry_date_filed` | RECAP docket-entry index: entry/document number, description, `doc_category` (e.g. `opinion_order`), `high_value` flag, `download_url` (storage.courtlistener.com), `is_sealed`, `is_free_on_pacer` |
| `catalog/documents_by_master/*.json` | 21 files (one per master docket, incl. `documents_by_master_partial_20260819/6224301.json`) | up to 5.6 MB each | same as documents.json, scoped per master | same | Per-MDL slice of `documents.json` |
| `catalog/map_mdl.parquet` | Parquet | 10.1 MB (valid `PAR1` header/footer; not decoded — no pyarrow/pandas confirmed installed, so schema not read; flag as **sampled/unverified** structurally beyond magic-byte check) | unknown until read with pyarrow | unknown | Likely a docket-to-MDL-number map mirroring `reg_nodes.csv`'s `master`/`mdl_number` rows |
| `catalog/njmcl_nodes.csv` | CSV | 78 rows (30 `drug`, 40 `njmcl`, 8 `njjudge`) | node id = `drug:<slug>` / `njmcl:<slug>` / `njjudge:<slug>` (no state or CourtListener id) | `designation_date` (free-text, e.g. "May 7 2018") | **New Jersey Multicounty Litigation registry** — 40 active/archived NJ MCLs with vicinage county, presiding judge name, designation date, `archived` flag, `document_count`, and a live `njcourts.gov` source URL per row. Fills part of **G5** |
| `catalog/njmcl_edges.csv` | CSV | 57 rows | src/dst = njmcl_nodes ids | none | `presides` (judge->MCL), plus MCL-to-drug edges |
| `catalog/njmcl_registry_suggestions.json` | JSON dict | 20 entries + 1 `__README__` note | drug slugs | none | Explicitly labelled "REVIEW REQUIRED, nothing auto-merged" — draft mapping of NJ MCL drugs to a `drug_registry.json`/federal master docket, listing 5 MDLs "not yet materialized" in this catalog (Roundup 16-md-02741, talc 16-md-02738, Taxotere 16-md-02740, Zostavax 18-md-02848, Physiomesh 17-md-02782) |
| `catalog/missing_mdl.csv` | CSV | header only, **0 data rows** | — | — | Empty — not a gap, just an empty run log |
| `catalog/reg_nodes.csv` / `reg_edges.csv` | CSV | 5.3 MB / 1.5 MB (row counts not fully streamed — capped by size; header + samples confirm schema) | `mdl_number` on master rows, `cfr_part`/`fr_type` on regulation rows | `date` (per reg node) | Regulatory graph: MDL master <-> CFR/Federal-Register node <-> drug/product edges. Overlaps **G8/G9** |
| `catalog/statute_nodes.csv` / `statute_cite_edges.csv` | CSV | 56 KB / 123 KB | `cfr:<title>-<section>` ids, `opinion_id` (CourtListener) | none | Opinion-to-CFR-citation edges via `eyecite`; a small slice relevant to **G8** but keyed to opinions, not statutes-as-published |
| `catalog/trial_nodes.csv` / `trial_edges.csv` | CSV | 3.05 MB / 0.92 MB | `trial:<NCT id>` (ClinicalTrials.gov) | start/completion/primary-completion dates | Drug-to-clinical-trial graph, not in any listed gap (adjacent to **G9** toxicology/science sources) |
| `catalog/citation_graph.json`, `citation_edges.csv`, `citations_verified.json`, `opinions.json`, `opinions_local.json`, `conflicts.json`, `conflicts_local.*`, `idb_mdl_report.json`, `catalog_graph.json`, `catalog_report.csv`, `parties_report.csv`, `pmc_slice.csv`, `pubmed_by_drug.json`, `pubmed_edges.csv` | mixed JSON/CSV | not deep-measured (out of FOCUS; peeked top-level keys only) | opinion ids, PMC/PubMed ids | `generated_at` on graph files (2026-08-06/07) | Secondary derived layers (citation network, conflict-of-interest checks, literature linkage) built from the same matters/masters set |
| `.worktrees/.../matter_graph/dockets.json` | JSON array | 2,122 rows, ~0.8 MB | `docket_id` | same as matters.json | Same content as `matters.json` reshaped (no `status`/`mdl_master_docket_id`/`courtlistener_docket_url` fields) |
| `.worktrees/.../matter_graph/graph.json` | JSON dict | ~0.1 MB | — | `generated_at` | Aggregate view: `filings_by_year`, `firms`, `judges`, `clusters` (rollups, not raw records) |
| `.worktrees/.../matter_graph/firms.csv` | CSV | small (<0.1 MB) | — | — | Per-firm rollup: role, `total_matters`, `pulled`, `top_courts`, `top_judges` (e.g. Levin Papantonio 6,463 total matters, 60 pulled — most matters are *counted*, not *pulled into this catalog*) |
| `.worktrees/.../matter_graph/clusters.csv` | CSV | small | — | — | Per court+defendant cluster: dockets, active count, lead_judge, firms (e.g. njd/ASTRAZENECA 176 dockets, 152 active, judge Cecchi) |

## 2. JPML MDL coverage (166 pending MDLs, `sources/jpml_mdl_20260919/mdls.jsonl`)

Measured by exact `mdl_number` match between `jpml_mdl_20260919/mdls.jsonl` (166 rows with `status != "terminated"`) and
`catalog/masters.json` (17 master dockets, 15 carrying an `mdl_number`):

- **11 of 166 pending MDLs** are covered by a full master-docket record in this catalog, by MDL number:
  `2570, 2789, 2804, 2846, 2873, 2885, 2913, 2973, 3047, 3081, 3094`.
- The other 4 masters.json MDL numbers (`2100, 2592, 2606, 2641`) are **not** in the 166-pending list — i.e. terminated
  or otherwise off the current pending roster (not checked against the terminated list; flagged as unresolved here).
- `catalog/documents.json`/`documents_by_master/` and `catalog/parties_by_docket/` are scoped to exactly these same 17
  master dockets (their `master_docket_id`s match `masters.json` 1:1).
- `matters.json`'s wider 2,122-docket set is **not** MDL-scoped: 977 of 2,122 (46%) carry a non-null
  `mdl_master_docket_id`, joining to the 17 masters above; the remaining 1,145 are single-district "competitor"/"anchor"
  tracking dockets with no MDL link.
- The NJ MCL registry (`njmcl_nodes.csv`) separately names 5 more federal MDL numbers in its "not yet materialized"
  suggestions file (Roundup 2741, talc 2738, Taxotere 2740, Zostavax 2848, Physiomesh 2782) that are **not** present as
  master dockets anywhere in this catalog — these are gaps, not hidden coverage.
- Net: this catalog is a **deep, attorney/party/document-level build for a small hand-picked slice (11 of 166) of the
  pending MDL universe**, not a broad shallow index. It does not close G1/G4 for the other ~155 pending MDLs.

## 3. Gap mapping

| Gap | What this cluster contributes | Join key | Caveats |
|---|---|---|---|
| **G1** counsel/firms/attorneys per MDL docket | `attorneys.json` (129), `firms.json` (52), `parties_by_docket/*.json` attorney sub-records (full name+firm+role, not name-only) — but only for the 11 covered MDLs / 59 dockets | `attorney_id`, `docket_id` | Firm names not normalized (`attorney.firm` sometimes a street address, e.g. "333 Main Street"); firm attorney-name variants not deduped |
| **G2** parties per docket | `parties_by_docket/*.json` — 59 dockets with full party name + type + attorney roster | `docket_id` | Only 59 of the catalog's 2,122 dockets have a parties file; PARTY_NAME_PUBLISH_LIMIT note elsewhere in the MVP (per BRIEF/STATE) suggests party-name publishing is a live policy question here too |
| **G4** unresolved MDL judges (Wolson, Bailey, Shelby, Singhal) | None of these 4 names appear as `assigned_judge` in `masters.json` (17 rows) or as a `transferee_judge` in the 11-MDL overlap | `judge` (name string only, no native id on matters.json/masters.json judge fields except `assigned_judge_id`) | `catalog/judges.json` judge_id is a CourtListener person id — could in principle help resolve G4 by cross-checking `assigned_judge_id` against CourtListener, but none of the 4 unresolved names are present in this 342-judge slice (checked by substring on `name`, `name_last`) |
| **G5** state coordinated-proceeding judges/registries | `njmcl_nodes.csv`/`njmcl_edges.csv` — **real, usable NJ MCL registry**: 40 NJ Multicounty Litigations, 8 named vicinage judges, county, designation date, archived flag, live njcourts.gov source URL per row | none existing in MVP; would be a new `state:NJ` + `njmcl:<slug>` id space | No CA JCCP or Philadelphia mass-tort equivalent anywhere in this cluster — G5 for CA/PA is still open |
| **G13** canonical id / relationship graph | `catalog_graph.json`, `citation_graph.json`, `reg_edges.csv`, `trial_edges.csv`, `njmcl_edges.csv`, `matter_graph/graph.json` are all pre-built edge lists in a consistent `src/dst/type` or node/edge JSON shape, already keyed on CourtListener docket/person ids, `mdl_number`, and CFR/NCT ids | see per-table ids above | Not in the BRIEF's `edges.jsonl` grammar (`mdl:<n>`, `cl_person:<n>`, etc.) — would need re-keying to match the MVP's native-id grammar before reuse |
| G8/G9 (partial, adjacent) | `reg_nodes.csv`/`reg_edges.csv` (CFR/Federal-Register per MDL), `trial_nodes.csv`/`trial_edges.csv` (ClinicalTrials.gov per drug), `pubmed_by_drug.json`/`pmc_slice.csv` (literature per drug) | `mdl_number`, `cfr:<title>-<section>`, `trial:<NCT id>` | Out of FOCUS for this scope note; flagged for the G8/G9 scout to also check this tree |

Not addressed by this cluster: G3 (settlement documents/verdicts — none of these files contain settlement amounts or
verdict outcomes), G6 (courthouse addresses), G7 (county courts/clerks/local rules — the njmcl county field is the only
county-level data point here), G10 (federal court statistics), G11 (case law/opinions — `opinions.json`/`opinions_local.json`
exist but were not deep-measured; FindLaw-terms question does not apply, this is CourtListener/RECAP-sourced), G12 (SEC),
G14 (source/URL directories).

## 4. Already used by the MVP?

`grep -r "SW-BULK" sources/ delivery/archive-directory/` returns **zero matches**. A broader `grep -r catalog` inside
`sources/` matches only unrelated filenames (e.g. `courtlistener_people_20260918/catalog.sqlite3`,
`public_law_directory_20260919/catalog.json`, `trellis/catalog/catalog.sqlite3`) — none reference this SW-BULK tree.
**This entire cluster is unused raw material**, not yet a supplement.

## 5. Main catalog vs worktree catalog — which is authoritative

- File counts: main `SW-BULK/catalog` = 136 files / 177.6 MB; worktree `.worktrees/batch2-corpus-execution/catalog` =
  60 files / 98.0 MB. Main has 79 files the worktree lacks (`njmcl_*`, `map_mdl.parquet`, `missing_mdl.csv`,
  60 more `parties_by_docket/*.json`, 15 more `documents_by_master/*.json`); the worktree has 3 `documents_by_master`
  files the main tree lacks (`16284915.json`, `4264145.json`, `65407433.json` — all masters that DO exist in main's own
  `masters.json`, so this looks like a stale leftover, not new coverage).
- Of the 57 same-named files present in both trees, **0 are byte-identical**, but every one differs only by line
  ending: main is CRLF (`\r\n`), worktree is LF (`\n`) — confirmed by head-byte comparison and by deep-equality checks
  on parsed `matters.json`/`documents.json`/`masters.json`/`attorneys.json`/`firms.json`/`judges.json` (identical row
  counts and identical id sets in every case).
- **Real content difference found**: in `matters.json`, 39 of 2,122 records differ — all 39 gain
  `mdl_master_docket_id: 18753355` (the Elmiron/MDL-2973 master) in the worktree version that is `null` in the main
  version. `mtime`: main's files are 2026-08-07T02:29, worktree's are 2026-08-23T14:14 (16 days later).
- **Verdict: neither copy is a strict superset.** The worktree is a *later, narrower, in-progress branch* that fixed
  39 MDL-master links for one MDL but was never re-run to regenerate the other 79 main-only files (njmcl, regulatory
  parquet, most of `parties_by_docket`, most of `documents_by_master`). Treat **main `SW-BULK/catalog` as the
  authoritative base** for build purposes, and treat the worktree's 39-record `mdl_master_docket_id` fix as a
  candidate patch to merge in (not verified further here — which side is "correct" for those 39 records was not checked
  against CourtListener).

## 6. Quality risks

- No README, manifest, `validation.json`, or licence file exists anywhere under `SW-BULK/catalog` or `matter_graph` —
  provenance/build-date/licence are inferred from field content and file mtimes only, not asserted by the source.
- Judge/attorney/firm identity is by **name string** in `matters.json`/`masters.json`/`firms.json` (only `judges.json`
  and `attorneys.json` carry a native id); the BRIEF's "never merge people by name alone" rule would need enforcement
  before wiring this into judge/firm profiles.
- `attorneys.json`'s `firm` field is sometimes a street address, not a firm name (data-entry defect from the source
  attorney-of-record field, not a parsing bug in this catalog).
- `firms.json` attorney lists contain multiple un-deduplicated name-casing variants of the same person.
- Party-name publication above 1,000/docket is a stated policy question elsewhere in this MVP (`PARTY_NAME_PUBLISH_LIMIT`
  in `sources/mdl_counsel_20260919/build.py`); this cluster's `parties_by_docket` files are all small (largest 59 KB,
  ~well under any such limit) so the policy is unlikely to bind, but was not re-checked here.
- `map_mdl.parquet` could not be decoded (no pyarrow/pandas import attempted/verified in this environment within the
  session's tooling); only the file's magic bytes (`PAR1`...`PAR1`) were checked to confirm it is a well-formed Parquet
  file — **treat its row/column claims as unmeasured**, not merely sampled.
- `catalog_report.csv`, `citation_graph.json`, `conflicts*.json`, `opinions*.json`, `idb_mdl_report.json`, PubMed/PMC
  files were only peeked at top-level keys (out of the FOCUS for this scout) — not row-counted; a future scout should
  measure them directly if they become relevant to G8/G9/G11.

## 7. Build effort guesses

| Dataset -> target | Effort |
|---|---|
| NJ MCL registry (`njmcl_*`) -> new G5 supplement `sources/nj_mcl_registry_20260919/` | S (78+57 rows, already clean, one source domain) |
| `matters.json`/`masters.json`/`parties_by_docket`/`attorneys.json`/`firms.json` -> G1/G2 supplement for the 11 covered MDLs | M (needs id-grammar re-keying, name-dedup pass on firms/attorneys, and a decision on which of main-vs-worktree's 39-record patch to keep) |
| `documents.json`/`documents_by_master` -> servable-document layer for G3-adjacent (docket orders, not settlements) | M (47.5 MB source file, needs hash-gated original-serving plumbing per the BRIEF's adapter contract) |
| `reg_edges.csv`/`reg_nodes.csv`, `trial_edges.csv`/`trial_nodes.csv`, `statute_cite_edges.csv` -> G8/G9 adjacency | L (large CSVs, cross-references CFR/NCT ids not yet in the MVP's id space, needs its own scoping pass) |
| `map_mdl.parquet` | Unknown until decoded (needs pyarrow/pandas availability check first) |

## Unmeasured / not verified

- `map_mdl.parquet` schema and row count (only magic-byte check).
- Full row counts for `reg_nodes.csv`, `reg_edges.csv`, `statute_nodes.csv`, `statute_cite_edges.csv`, `trial_nodes.csv`,
  `trial_edges.csv` (capped at header + 3 sample rows per the streaming-measurement rule; sizes are exact, row counts are not).
- Content of `citation_graph.json`, `catalog_graph.json`, `conflicts.json`/`conflicts_local.*`, `opinions.json`/
  `opinions_local.json`, `idb_mdl_report.json`, `pubmed_by_drug.json`, `pmc_slice.csv`, `pubmed_edges.csv`,
  `citation_edges.csv`, `citations_verified.json`, `catalog_report.csv`, `parties_report.csv`, `recap_dedup_manifest.json`,
  `recap_pdfs_manifest.json`, `recap_prefix_manifest.json`, `regs_docket_batch_summary.json`, `regs_docket_pull_list.json`
  — top-level keys only, out of FOCUS.
- Whether the worktree's 39-record `mdl_master_docket_id` fix is itself correct (not cross-checked against CourtListener).
- Which of the 4 unresolved masters.json MDL numbers (2100, 2592, 2606, 2641) are terminated vs. simply absent from the
  166-pending list for another reason.
- No licence/terms statement exists for this data anywhere in the tree; licence risk is unassessed because no signal was found (RECAP/CourtListener content generally carries CourtListener's terms, but nothing in this tree states them).
