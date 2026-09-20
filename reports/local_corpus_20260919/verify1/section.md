
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
