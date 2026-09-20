# AWS-BATCH1-DOCKETS cluster — docket releases (gz shards + manifests)

Scope: `SW-BULK/AWS-BATCH1-DOCKETS/releases`, its worktree copy, `staging/unpublished-drafts`, `state/batch2a`.
All measurements below are exact counts from `manifest.json` per release, spot-verified by streaming
`gzip`+line-count on 4 datasets of the authoritative release (all matched exactly — see §5). Nothing here
was modified; no file under SW-BULK was written, moved or extracted.

## 0. TL;DR

- **5 releases exist in the main tree**, forming one lineage: `b1-2e03d6c8` (pilot) / `b1-d44f3eb7` (pilot,
  near-dup) → `b1-78fe28d8` (baseline, published) → `b2a-0ef93bb` (successor, catalog-discovery expansion) →
  **`b2b-cdbb8d04` (successor, current — 302,645 rows, built 2026-08-24T04:59:46Z)**.
- **The MVP (`sources/judge_evidence_20260919/build.py`) reads exactly 6 of `b2b`'s 19 datasets**: `judges`,
  `judicial_assignments`, `matters`, `matter_relationships`, `courts`, `source_records`. The other 13 —
  **`attorneys` (181), `firms` (12), `counsel_appearances` (878), `parties` (503), `docket_entries` (41,946),
  `documents` (13,971 — metadata only, bytes live in S3), `opinions` (900), `outcomes` (25), `citations` (2),
  `coverage` (8), `matter_aliases` (4,202), `provenance` (124,221), `review_records` (32,941)** — are **on disk,
  hash-verified, but completely unused** by any `sources/*_20260919` builder (grepped `sources/` and
  `delivery/archive-directory/`; only `judge_evidence_20260919` touches this release at all).
- **G1 (counsel/firms)**: `mdl_counsel_20260919` (the current MDL-counsel build) does **not** read this release
  at all (grep: zero hits) — it pages CourtListener instead and only got 57 full attorney records. This SW-BULK
  release independently has 181 attorneys / 12 firms / 878 appearances spanning **16 MDL/consolidated matters**
  (via `matter_relationships.member_of_mdl`) — a disjoint, unused source that could supplement G1 for those 16
  MDLs at Small-Medium effort (clean native ids, no scraping).
- **G3 (settlements/orders)**: `docket_entries` (41,946 rows, docket-entry *metadata/descriptions*, not full
  text) has keyword hits for settlement (423), pretrial order (179), case management order (1,358), leadership
  (172), steering committee (661) — real docket-entry evidence of PTOs/CMOs/leadership appointments, unused.
  `documents` (13,971 rows) carries `s3_bucket`/`s3_key`/`byte_count`/`description` for underlying filings —
  **no local bytes exist** (checked; no `objects/` tree found under SW-BULK) — these are S3 pointers only,
  not downloadable from this machine.
- **G4 (Wolson/Bailey/Shelby/Singhal)**: `judges` in `b2b` DOES contain judge-identity rows for Bailey
  (native_judge_id 148, CL person), Shelby (2942) and Singhal (15357) — but **not** Wolson. `judicial_assignments`
  shows Shelby assigned_judge on MDL 2:24-md-03102 (LDS tithing) — a real MDL match. Bailey's 19 assignments and
  Singhal's 2 assignments are all to non-`-md-` dockets in this dataset, so they do **not** by themselves resolve
  the *MDL* assignment gap for those two names; this needs a name-identity check against the JPML docket numbers
  the MVP is missing, which this report did not do (out of scope/time). Treat as a lead, not a resolution.
- **`.worktrees/batch2-corpus-execution/...releases`** is a **byte-identical git-worktree copy** of the 3 `b1-*`
  release folders in the main tree (manifest dataset SHA-256s match exactly for all 19 datasets x 3 releases).
  It does not contain `b2a`/`b2b`. Not authoritative; redundant copy, safe to ignore.
- **`staging/unpublished-drafts`** holds **2 candidate "baseline" builds that were superseded** by the published
  `b1-78fe28d84a27a8764b57` and never promoted: `b1-f7ad1130` (row-for-row identical to the published baseline
  except `review_records` file bytes differ) and `b1-1f315ddc` (diverges: 14,013 docs verified vs 13,971 in the
  published baseline, 21,410 quarantined documents per its own `pilot_summary.json`). **Do not publish from
  drafts** — the published `b1-78fe28d8` and its descendants are the accepted lineage; the drafts are pre-review
  quarantine artifacts kept for audit only.
- **`state/batch2a`** is **process/build state, not a dataset**: `plan.json`, `bulk-preflight.json`,
  `baseline-crosswalk.json`, raw firm-website `discovery/` captures (Beasley Allen, Motley Rice, Seeger Weiss),
  and `current.json` (`"status":"building"`, `"release_id":null`). It is the scratch/input state that produced
  release `b2a-0ef93bbef92cff5b3532` (matched via `descriptor.run_scope.discovery_run_id` == the
  `480b1a28ae14...` state folder). **Not safe to publish as-is**: unreviewed raw scrapes, no validation envelope,
  one of its 3 run folders (`3e80b5c3...`, `76caebda...`) was not the one actually accepted into a release.

## 1. Release lineage (main tree `AWS-BATCH1-DOCKETS/releases/`)

| release_id | status | built_at (UTC) | predecessor | total rows (19 datasets) | target dockets / support masters |
|---|---|---|---|---|---|
| `b1-2e03d6c8b8189fab6f09` | pilot | 2026-08-23T14:39:20Z | none | 1,625 | 25 target / 11 support masters |
| `b1-d44f3eb792b161b74dfd` | pilot | 2026-08-23T14:23:40Z | none | 1,625 | 25 target / 11 support masters (near-dup of above; `documents`=0, `review_records`=24 vs 2 — a failed/retried doc fetch of the same pilot) |
| `b1-78fe28d84a27a8764b57` | **baseline (published)** | 2026-08-23T16:42:30Z | none | 169,444 | 57 target / 16 support masters |
| `b2a-0ef93bbef92cff5b3532` | successor | 2026-08-24T04:16:52Z | b1-78fe28d8 (verified: predecessor.manifest_sha256 matches b1-78fe28d8's own manifest hash) | 201,358 | catalog-discovery expansion: `matters` jumps 73→4,159, `courts` 13→116 |
| `b2b-cdbb8d040b95c7b65cfc` | **successor (current, authoritative)** | 2026-08-24T04:59:46Z | b2a (verified) | **302,645** | `judges` 25→867, `judicial_assignments` 68→4,776, `docket_entries` 29,340→41,946, `opinions` 0→900 |

**Newest/authoritative = `b2b-cdbb8d040b95c7b65cfc`** (largest, latest `built_at`, `validation.status:"pass"`,
zero errors, already the one path the MVP references). `b1-2e03d6c8`/`b1-d44f3eb7` are early 25-docket pilots
superseded by the 57-docket baseline; keep only for provenance history.

Row counts per dataset for **b2b** (the release to build against), all confirmed against `manifest.json` and
4 of them re-counted by streaming gzip (matched exactly):

| dataset | rows | native ids present | notes |
|---|---|---|---|
| judges | 867 | CourtListener `native_judge_id` (int) on 850+ rows | identity only: judge_id (uuid), name, native_judge_id, record_status |
| judicial_assignments | 4,776 | judge_id, matter_id (uuids) | role: assigned_judge (3,422) / referred_judge (1,354); no assignment date field |
| matters | 4,159 | court_id = CourtListener court slug (e.g. `njd`); docket_number | case_name, case_status, date_filed, date_terminated, matter_key = `court\|docket` |
| matter_aliases | 4,202 | — | not inspected in depth this pass |
| matter_relationships | 53 | from/to matter_id | all `relationship_type:"member_of_mdl"`; 16 distinct `to_matter_id` = MDL/consolidated master matters |
| courts | 140 | CourtListener court id | name only |
| attorneys | 181 | attorney_id (uuid) | name only, no bar number, no address |
| firms | 12 | firm_id (slug, e.g. `seeger_weiss`) | canonical_name |
| counsel_appearances | 878 | attorney_id + firm_id + matter_id + party_id | role field un-normalised (`LEAD ATTORNEY` vs `attorney_to_be_noticed`) |
| parties | 503 | party_id, matter_id | name, party_types (e.g. `["Plaintiff"]`) — no address/contact fields present |
| opinions | 900 | CourtListener `cluster_id`/`native_opinion_id`/`docket_id` | date_filed, precedential_status, per_curiam |
| citations | 2 | citing/cited opinion_id | negligible |
| outcomes | 25 | `fjc_case_disposition` raw codes | evidence_level `official_dataset_reported`; no dollar amounts (`amount`, `amount_disclosed` all null in sample) |
| coverage | 8 | — | scope statements: seeger_weiss / competitor / mdl_member / fjc_linked / active / terminated; bankruptcy explicitly `not_available` |
| docket_entries | 41,946 | docket_entry_id, entry_number, matter_id | `description` text field only — no attached filing text |
| documents | 13,971 | doc_uid, `s3_bucket:"FORAWS"`, `s3_key` | metadata only: description, byte_count; **no bytes present locally** |
| source_records | 72,860 | — | CourtListener docket URLs / catalog hashes |
| provenance | 124,221 | — | large; not opened this pass beyond size |
| review_records | 32,941 | — | large; not opened this pass beyond size |

Top MDL/consolidated master matters by member count (from `matter_relationships`, `to_matter_id` joined to `matters`):

| MDL matter | members | docket_number | court |
|---|---|---|---|
| In Re: Juul Labs Marketing/Sales/Products Liability | 4 | 3:19-md-02913 | cand |
| In Re: 3M Combat Arms Earplug Products Liability | 4 | 3:19-md-02885 | flnd |
| In Re: Bard Implanted Port Catheter | 4 | 2:23-md-03081 | azd |
| In Re: Bard IVC Filters | 4 | 2:15-md-02641 | azd |
| In Re: Hair Relaxer Marketing/Sales/Products Liability | 4 | (1:23-cv-00818) | ilnd |
| In Re: National Prescription Opiate Litigation | 3 | 1:17-md-02804 | ohnd |
| AstraZeneca (Goodstein) | 3 | 2:17-md-02789 | njd |
| In Re AFFF Products Liability (MDL 2873) | 3 | 2:18-mn-02873 | scd |
| In Re: Yasmin/Yaz | 3 | 3:09-md-02100 | ilsd |
| In re: Bard Polypropylene Hernia Mesh | 3 | 2:18-md-02846 | ohsd |
| In Re: Testosterone Replacement Therapy | 3 | 1:14-cv-01748 | ilnd |
| GLP-1 RAs (Ozempic etc.) | 3 | 2:24-md-03094 | paed |
| In Re: Cook Medical | 3 | 1:14-ml-02570 | insd |
| In Re: Xarelto | 3 | 2:14-md-02592 | laed |
| In Re: Benicar | 3 | 1:15-md-02606 | njd |

16 total MDL/master matters covered (all with `node_role:"support_master"`); 57 matters have `node_role:"target_matter"`;
4,086 have `node_role:"public_docket"`. Separately, 194 matters have a `-md-`/`-ml-`/`-mc-` docket number
(broader MDL-shaped set than the 16 explicitly linked via `matter_relationships`).

Firms by distinct matter count in `counsel_appearances` (all 12 firms, all with clean `firm_id` slugs):
seeger_weiss 38, beasley_allen 10, motley_rice 5, simmons_hanly_conroy 5, awko 3, burg_simpson 3,
weitz_luxenberg 2, hausfeld 2, lieff_cabraser 2, levin_papantonio_rafferty 2, grant_eisenhofer 1, keller_postman 1.

`docket_entries` keyword scan (41,946 rows, full scan, description-text substring match, case-insensitive):
"settlement" 423 hits, "pretrial order" 179, "case management order" 1,358, "leadership" 172,
"steering committee" 661. Examples confirm real content (Pretrial Order No. 13/43 in MDL 2885, Case Management
Order No. 3 leadership-duties order, Plaintiffs' Steering Committee filings, joint settlement-approval motions).
This is docket-entry-description evidence (who filed what, when, in which case), **not** the underlying filed
text — no settlement dollar amounts appear in any sampled row.

`documents` keyword scan (13,971 rows): "settlement" 3 hits (minute-order/conference entries, not settlement
agreements), "order" 3,077 hits (mostly routine procedural orders, plus one "Case Management Order (Agreed
Qualified Protective Order..." exhibit). Every document row carries `s3_bucket:"FORAWS"` + `s3_key` — **no local
`objects/` tree exists anywhere under `SW-BULK`** (checked via recursive directory search) — bytes are not on
this machine; only S3 pointers + description/byte_count metadata are.

## 2. G4 judge check (Wolson / Bailey / Shelby / Singhal)

| name searched | found in `b2b` `judges`? | native_judge_id (CL person) | assignment evidence in `b2b` |
|---|---|---|---|
| Wolson | **no match** | — | — |
| Bailey (John Preston Bailey) | yes | 148 | 19 assignments, all `wvnd` non-`-md-` dockets (e.g. Dolgencorp, Purdue Pharma cases) — no MDL docket number seen |
| Shelby (Robert James Shelby) | yes | 2942 | 2 assignments incl. **2:24-md-03102** (In Re: Church of Jesus Christ of LDS Tithing Litigation) — a real MDL match |
| Singhal (Anuraang H. Singhal) | yes | 15357 | 2 assignments, both `flsd` non-`-md-` dockets (Managed Care of North America) — no MDL docket number seen |

**Caveat, not verified further**: this only confirms these 3 names exist as CourtListener-identified judges
with *some* assignment evidence in this dataset's 4,159-matter sample; it does not confirm each is the specific
judge assigned to the JPML MDL the MVP currently shows as unresolved for that surname (there may be more than
one federal judge with these surnames; Singhal in particular reads as a different first name pattern than a
typical JPML transferee-judge entry). Shelby/MDL-3102 looks like a genuine resolution candidate; Bailey and
Singhal need a name-identity cross-check against the specific JPML docket numbers before use. Do not treat this
as resolved — it is a lead for the judge-alias-resolution workflow, from a source not yet consulted by it
(that workflow used CourtListener assigned-judge lookups directly, not this SW-BULK release).

## 3. Worktree copy — byte-identical, not authoritative

`SW-BULK/.worktrees/batch2-corpus-execution/AWS-BATCH1-DOCKETS/releases/` contains only the 3 `b1-*` release
folders (no `b2a`/`b2b`). Compared all 19 dataset SHA-256 hashes per release from each copy's `manifest.json`:
**all three (`b1-2e03d6c8`, `b1-78fe28d8`, `b1-d44f3eb7`) are byte-identical** to the main-tree copies (every
dataset hash matches). This is a stale git-worktree mirror frozen at an earlier point in the pipeline; it is
missing the two newest, most complete releases. Not authoritative, safe to ignore for corpus-building purposes.

## 4. `staging/unpublished-drafts` — two superseded baseline candidates

| release_id | manifest status | rows | vs. published `b1-78fe28d8` |
|---|---|---|---|
| `b1-f7ad1130c93f528dd23a` | baseline | 169,444 | Same run_scope (57 target dockets), same row counts per dataset, `documents`/`docket_entries`/`matters`/`courts`/`provenance` hashes byte-identical to the published baseline; only `review_records` file bytes differ (same row count 21,454, different content — likely timestamps/reordering) |
| `b1-1f315ddc43e47b8df148` | baseline | 169,444 (manifest) but its own `pilot_summary.json` reports **14,013 documents_verified / 21,410 documents_quarantined**, vs the published baseline's 13,971 documents and (implicitly) fewer quarantined | A distinct, non-identical baseline run with a different document-review outcome |

Both sit under `staging/unpublished-drafts/<id>/release/` (same 19-file layout as a real release) plus a
`quarantine/review_records.jsonl` and, for `b1-1f315ddc`, a `report/pilot_summary.{json,md}` explaining
`documents_quarantined: 21410`. **These are pre-acceptance candidate builds that did not become the canonical
release** — the pipeline picked `b1-78fe28d84a27a8764b57` as the published baseline instead. They are safe to
read for provenance/audit (e.g., to see what got quarantined and why) but **not safe to publish as a dataset
source** without first reconciling why `b1-1f315ddc` disagrees with the accepted baseline on document counts.

## 5. `state/batch2a` — build/process state, not a dataset

Three run folders plus `current.json`:

- `current.json`: `{"run_id":"480b1a28ae14...","release_id":null,"status":"building", ...}` — points at run
  `480b1a28ae149e6631c27e719a667ca004c64527f8491eb9b792e26ae0ac1dac` as the (at-the-time) in-progress run.
- `480b1a28ae14.../plan.json`: confirms this run consumed `SW-BULK/catalog/matters.json`, firm/source-policy
  configs, and a **630,894-object / 266.7GB Supabase storage inventory**
  (`gate_b1_supabase_inventory_v1_2026-08-23/evidence/.../storage.objects.jsonl.gz`) against predecessor
  `b1-78fe28d84a27a8764b57`. Its `discovery_run_id` (`480b1a28ae14...`) is exactly the `descriptor.run_scope
  .discovery_run_id` recorded in release `b2a-0ef93bbef92cff5b3532`'s manifest — **this run folder is the
  accepted input that produced `b2a`**, with 2,274 discovery observations across 27 queries.
- `3e80b5c36d67...` and `76caebda571e...`: sibling run folders (`plan.json`, `bulk-preflight.json`,
  `baseline-crosswalk.json`) with a `discovery/` subtree of raw per-firm-per-URL JSON captures (`beasley_allen`,
  `motley_rice`, `seeger_weiss` subfolders, files named by URL/query hash) — earlier or alternate attempts of
  the same discovery step; not referenced by any release manifest's `discovery_run_id` found in this cluster,
  so treat as superseded/unused attempts.

**Conclusion: `state/batch2a` is pipeline scratch state (plans, preflight checks, raw un-reviewed law-firm-site
scrapes), not a dataset with its own validation envelope.** It has no `validation.json`, no row-count manifest
in the uniform sense, and its `current.json` literally says `"status":"building"`. Do not publish from it
directly; if the raw `discovery/` captures are wanted later, they would need the same review/quarantine step
that turned `state/batch2a` discovery output into the reviewed `b2a`/`b2b` releases.

## 6. Gap mapping, join keys, effort

| Gap | What this cluster has | Join key to MVP | Effort |
|---|---|---|---|
| G1 (counsel/firms/attorneys) | 181 attorneys / 12 firms / 878 appearances across 16 MDL masters + 4,159 matters, in `b2b`, **currently unused** | `counsel_appearances.matter_id` → `matters.matter_id` → `matters.court_id`+`docket_number` (needs a join to MVP's JPML/court records, which key on docket number/MDL number, not this uuid) | S–M: parse+load is trivial (already clean JSON), but joining `matter_id` (uuid) to the MVP's canonical MDL numbering needs a docket-number crosswalk |
| G2 (parties) | 503 parties, `party_types` (Plaintiff/Defendant), no address/contact — unused | `parties.matter_id` → `matters.matter_id` | S |
| G3 (settlement docs/orders) | `docket_entries` descriptions only (423 settlement-text hits, 1,358 CMOs, 179 PTOs); `documents` are S3 pointers with no local bytes | `docket_entries.matter_id` → `matters.matter_id` | S for the entry-text layer (no new fetch needed); **not possible** to get real document bytes from this machine (S3-only) |
| G4 (Wolson/Bailey/Shelby/Singhal) | Bailey/Shelby/Singhal exist as judges with assignment rows; Wolson absent; only Shelby's MDL-3102 link looks solid | `judges.native_judge_id` (CourtListener person id) | S to re-check, but unresolved until docket-number cross-check done |
| G13 (relationship graph) | `matter_relationships` (member_of_mdl, 53 edges / 16 masters) is a ready-made docket↔MDL edge set with clean uuids | needs a `matter_id` → `mdl:<number>` crosswalk via `matters.docket_number` pattern matching | S |

## 7. What was not verified / out of scope this pass

- `provenance` (124,221 rows) and `review_records` (32,941 rows) in `b2b` were not opened beyond size/row-count
  from the manifest — no schema sampling done.
- `matter_aliases` (4,202 rows) not sampled.
- The Wolson/Bailey/Shelby/Singhal match was a name-substring search only; no cross-check against JPML's specific
  docket numbers for these 4 unresolved MDLs was performed (would require the JPML registry file, out of this
  cluster's scope).
- Did not open `citations.jsonl.gz` beyond the 2-row sample already shown (dataset is negligible size).
- Did not attempt to reconcile exactly why `b1-1f315ddc` and the published `b1-78fe28d8` disagree on document
  counts (42-document delta) — flagged, not root-caused.
- Byte-for-byte diff of `provenance`/`review_records`/`source_records` between drafts and published baseline was
  done only via manifest SHA-256 comparison (not content diff), which is sufficient to say "identical" or
  "different" but not "how they differ" beyond row counts already reported.
