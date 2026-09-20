# Integration plan (DRAFT) — legal reference corpus -> Seeger Weiss litigation AI platform

Status: DRAFT for review, September 19 2026. Scoping only. Nothing was integrated, exported, deployed or
modified. No network requests were made. No `.env`/secret files were opened. SQLite opened `mode=ro`.
Author role: integration-planner (read-only). Companion pointer: `../understand/integration-planner.md`.

The user's instruction is explicit: NOT to integrate yet; quality, accuracy, contracts and scope first.
This document is therefore a contract proposal plus a gate list, not a build order.

---

## 1. What the target platform actually is (verified from source, not from memory)

Inspected: `C:/Users/firas/Downloads/SCRAPE/devvvv` (git clone, branch `codex/ui-preview-polish`, HEAD `2d27cc3`).
It is the newest local snapshot of SeegerWeissAI: it is the only copy holding `db/kb/0003_reference_courts.sql`;
the four `C:/Users/firas/Downloads/prodrepo/workingversion-*` trees stop at `0002`. `C:/Users/firas/Downloads/mco2`
(MCO docket/deadline tool, Next.js, mock data) was not opened; it is a second, separate consumer (see 1.5).

### 1.1 Stores on the platform side

| Store | Tenancy | Embedding | State | Relevance to this corpus |
|---|---|---|---|---|
| Supabase `corpus.*` (`matters`, `docket_entries`, `documents`, `parties`, `counsel`, `doc_chunks`) | firm-global, service key | `vector(1024)`; ingest contract says `voyage-law-2`, SQL comment says `voyage-3-large` | "being retired" per `db/kb/README.md` | Matter dockets only. Target for MDL filings, not for laws/judges |
| Aurora `kb.*` (`documents`, `chunks`, `hybrid_search`, `fetch_chunks`) | per-user, FORCE RLS on Cognito `sub` | Titan Text v2, 1024-d, HNSW + `tsvector`, RRF | built locally, "NO DEPLOY / NO MIGRATION" banner | Wrong tenancy for a shared reference corpus. Reuse its chunk shape only |
| Aurora `reference.*` (`courts`, `judges`, `court_documents`) | firm-global, NO RLS, `SELECT` only to `kb_app`, "populated out-of-band by the reference-library tooling" | none today | migration 0003, read by `src/lib/workspace.server.ts` | **Natural landing zone.** Already models courts, judge portraits, rules/forms |
| DynamoDB `sw-dev-app` + S3 | per-user | n/a | live | Not a target |

### 1.2 Existing contracts to respect

- `docs/ingest-contract-v1.md` + `schemas/ingest-manifest-v1.json` + `schemas/ingest-docket-v1.csv-spec.md`:
  bundle = `manifest.json` + `docket.csv` + optional `parties.csv` + PDFs. Identity =
  `(matter_id, docket_source, entry_number, attachment_number)`, `docket_source in {main,jpml,state,appellate}`.
  Rules worth copying verbatim into our contract: manifest is authoritative; filenames are opaque keys, never parsed;
  unknown fields rejected; SHA-256, byte size and real page count re-verified; totals must equal rows;
  idempotency key -> `409 duplicate_batch`; different hash in an occupied slot becomes a new version, never an
  overwrite; identical local pre-flight validator (`scripts/pipeline/validate_bundle.py`). PDF only.
- `reference.court_documents`: PK `sha256`; `court_key`, `court_keys text[]`, `jurisdiction`, `title`,
  `kind in {standing_order,local_rule,form,instruction,order,other}`, `format in {pdf,docx,doc,rtf}`, `bytes`,
  `page_count`, `s3_key`, `source_url`, `source_date` (text), `source_date_kind`, `review_status`, `fillable`, `judge_name`.
- `reference.courts.court_key`: `FD:<id>` federal district, `FS:jpml`, `ST:<st>_state`, `LC:<st>_<place>`;
  `court_id` = DocketBird/CourtListener id when 1:1. Mapping lives in `src/lib/courts.ts::courtReferenceKeys()`.
- `reference.judges`: `judge_key`, `court_key`, `name`, `surname`, `portrait_key`, `source_page`, `reuse_note`.
  Platform matches judges to dockets by surname + first name on the same court (`judgeMatches()`), portraits only.
- Canonical chunk shape (`docs/kb-ingest-design.md`): page is the citation anchor (`fileId:page`); `content` verbatim,
  `context` prefix embed-only; tables first-class; `conf` + `source` propagate; ~512-token prose chunks, overlap only
  inside a section; non-paginated text gets synthetic ~3k-char "pages"; deterministic `quoteOnPage` verifier.

### 1.3 Shared key scheme already exists (good news)

The MVP court registry (`sources/local_library_presentation_20260918/court-registries.jsonl`, 269 rows) uses the same
family prefixes as the platform because both descend from `Court-Library-Expansion-2026-09-12`:
`FD` 94, `FB` 94, `ST` 56, `F` 13, `FS` 6, `LC` 6. Platform `courtReferenceKeys()` was seen mapping `FD`, `FS:jpml`,
`ST`, `LC` only. `FB:` (bankruptcy) and `F:` (circuit) keys exist in the MVP but a platform mapping for them was not
found (not exhaustively verified).

### 1.4 Vendor and policy constraints that shape the contract

- Inference/embedding must be Bedrock-native in account, no external egress for the KB path; approved web
  backends are AgentCore gateway, Tavily, Firecrawl, Brave. No Marketplace models.
- Firm policy (user memory, 2026-09-12): `cohere.rerank-v3-5:0` is NOT allowed; web rerank uses Titan v2 + RRF.
  **Conflict found:** `src/lib/kb/search.server.ts:9` still defaults `BEDROCK_RERANK_MODEL` to `cohere.rerank-v3-5:0`
  and `docs/kb-ingest-design.md` lists it as a locked decision. Must be resolved by the platform owner before any
  reference-corpus retrieval path reuses that module.
- Legacy corpus ingest embeds with Voyage (external). The reference corpus should NOT ship vectors. Export text and
  anchors; the platform embeds with Titan v2 1024-d in account. This also avoids re-embedding on model change.
- Research agent tools today: web search fan-out, `fetch_page`, RECAP, DocketBird REST. There is no local reference
  tool. Integration eventually means one new read-only tool pair (`ref_search`, `ref_read`) over `reference.*`.

### 1.5 Second consumer: MCO (`Downloads/mco2`)

Per memory, its roadmap wants scraped local/state jurisdiction rules to flip `verified` in `src/lib/mock/rules.ts`
(deadline rule engine). That needs LegalProvision/court-rule records with effective dates and court scope. Same
export bundle can serve it; no separate contract proposed. Repository not inspected in this pass.

---

## 2. How the MVP identifies things today (verified) and whether each id can leave the building

| Thing | Current identifier | Derivation | Stable across rebuild/recapture? | Verdict |
|---|---|---|---|---|
| Directory record | `records.id` 32 hex | `sid(x) = sha256(str(x))[:32]` in `server.py:60`; for focused it is `sid('focused:'+version_id)` | **No** for focused (bound to version); dataset-prefixed elsewhere | Internal UI key only. Never export as an identity |
| Capture record | `record_key` 64 hex | `sha256([collection, source_url, capture_kind])` (`scripts/build_document_index.py:793`) | Yes, but collection-scoped: same URL in N collections = N keys | Export as `capture_series_id`; add collection-independent `url_key` |
| Capture version | `version_id` 64 hex | sha256 of the version tuple incl. raw hash and retrieval time | Yes (immutable) | Export as `document_version_id` |
| Original bytes | `raw_sha256` | content hash | Yes | **Primary Document identity** (matches platform `court_documents.sha256` PK) |
| File handle | `files.id` | `sid(relative path)` | Breaks on move | Do not export |
| Source reference | `pld-<12hex>` / `registry_id` | from source registry (`public_law_directory_20260919`, 9,348 refs) | Yes within that registry version | Export, with registry version + `source_as_of` (2026-08-19 observed) |
| County | `geoid` 5-char FIPS string | Census | Yes | Export as is (3,144 rows; 8,732 record-county links) |
| Court (registry) | `F:/FB:/FD:/FS:/ST:/LC:` ids | curated registry | Yes | Export as `court_key`; same scheme as platform |
| Court (county registry KY/TX) | none: `name` + `type` strings, `evidence_id` like `KY-COUNTY-ADAIR` | observed label | n/a | Needs minted ids + resolution status (2,358 courts, 628 clerks, 2,539 judge seats) |
| Judge entity | `judge-entity-<24hex>` | minting rule NOT located in this pass | Unknown | Must be proven deterministic before export |
| Judge observation | `trellis-directory:<20hex>`, `trellis-profile:*`, `fjc:nid:<n>:csv:<hex>`, `official:*`, `co2024_*`, `vendor:*` | per-source | Yes | Keep as `member_keys`; namespaces must be registered |
| CourtListener person | native `people.id` (15,797 + 394 aliases; snapshot label 2026-06-30 from filenames) | native | Yes | Export as xref only; layer is deliberately NOT merged into judge entities |
| Open US Law row | `oul:<sha256>` + `source_id`/`act_id` (e.g. `STATE_ID_T41_C13_S41-1325`) + `content_hash` + `snapshot` | provider | `act_id` stable per provider; row id snapshot-bound (unverified) | Use `act_id` as provision key, `content_hash` as version |
| Settlement | `settlement-<20hex>`; docs `settlement-document-*`; assets `settlement-pdf-<24hex>` | derived from publisher record (hash basis not verified) | Unknown | Re-key on `(court, case_number)` where present |
| MDL-3080 doc | `mdl-<24hex>` = prefix of `raw_sha256`; metadata carries `docket_iri urn:lawgraph:us:court:njd:docket:2-23-md-03080-brm-rls`, `entry_iri ...:entry:0001`, `page_count` | content hash + external graph IRI | Yes | Keep sha256; keep IRI as xref |

Other observations that affect the contract:

1. `sources/*/validation.json`: 27 files, no common envelope. Pass flag is variously `status:"passed"`, `passed`,
   `valid`, `validated`, `ready`; only some carry a data-file hash; almost none carry `schema_version`.
   (`courtlistener_people` `ready.json` does: `courtlistener-people-catalog.v1`.) An exporter cannot gate on these
   uniformly today.
2. Temporal coverage in directory payloads (1-in-40 sample, 1,457 rows): focused rows carry only `retrieved_at`,
   `indexed_at`, `raw_hash_verified_at`; seeger/pending/federal carry only `captured_at`; judge_entities carry no
   top-level time field; Trellis directory observations have `captured_at: null`. No sampled record exposed a
   top-level `published_at` or `effective_*`. Richer dates exist only in side datasets: OUL `snapshot_date`
   2026-08-14 + `last_amended_year` + `act_status`; county registry `source_as_of` 2026-08-22; settlements
   `status_as_of` (848/848) + `claim_deadline` (614/848).
3. Review debt: focused `kind` = `needs_content_review` 7,187 and `law_document_title_evidence_needs_review` 2,826 of
   16,454 (61 percent not review-cleared). Seeger import: 10,543 `court_form_or_other_document` (undifferentiated).
4. Judge evidence base: `judge_enrichment` 11,926 observations = Trellis directory 4,458 + Trellis profile 1,300
   (48 percent vendor-derived), FJC biographies 4,074, official observations 1,978, state evaluations 116.
   Profiles: 10,698; with any analysis 118; with details 5,971; biography 1,605; portraits 43. In the first 3,000
   entities, 1,072 have more than one member observation, so merge basis must be audited before identities leave.
5. Host mix for focused+seeger+pending (35,115 rows): `.gov/.us/.mil` 31,169; `trellis.law` 2,897; other 1,049
   (court blob storage, `olls.info`, circuit `.org` sites).
6. Local absolute paths leak into metadata (`C:/Users/firas/Downloads/Court-Library-Expansion-...`, recorded
   Firecrawl command lines with `C:\Users\firas\...`). Must be stripped/relativized on export.
7. No U+FFFD in any directory title or payload (checked across all 58,310 rows); apparent mojibake in console output
   is a terminal artifact.

---

## 3. Canonical entity model

Conventions for every entity:

- `id`: opaque, deterministic, lower-case, colon-namespaced. Never derived from a display title or a file path.
  Minted ids declare `id_basis` (`native`, `content_hash`, `minted_from_native_tuple`, `minted_from_observed_label`).
- `xrefs[]`: `{scheme, value, basis, observed_at}`. Native ids are never rewritten or merged
  (`fjc_nid` is not `fjc_legacy_id`; `cl_person_id` is CourtListener's).
- `resolution_status`: `resolved | candidate | unresolved | conflicting`. Only `resolved` may be the target of an
  identity edge in an export.
- Envelope on every row: `schema_version`, `dataset_id`, `record_class` (`source_reference | saved_page |
  downloaded_file | extracted_text | published_record`), `provenance[]`, `quality{}`, temporal block (section 4),
  `license_ref`.

| Entity | Proposed `id` | Native/xref ids | Key fields | MVP source today | Gap |
|---|---|---|---|---|---|
| Jurisdiction | `jur:us`, `jur:us-fed`, `jur:us-nj`, `jur:us-nj:34013` | USPS, FIPS state (2), county GEOID (5-char string), Census place later | `level` (country/federal/state/county/municipal/tribal/territory), `parent_id`, `name` | `counties` table 3,144; state list 51 | Municipal/tribal absent. Federal districts are Courts, not Jurisdictions; district-to-county coverage edge missing |
| Court | platform `court_key` verbatim (`FD:njd`, `FB:njb`, `F:ca3`, `FS:jpml`, `ST:nj_state`, `LC:nj_essex`); else `court:x:<16hex>` minted from `(state, geoid, court_type, normalized label)` with `resolution_status=unresolved` | CourtListener court id, PACER court code, DocketBird id, Trellis court label (string only) | `level`, `system` (federal/state/local), `jurisdiction_id`, `parent_court_id`, `website`, `forms_pages[]`, divisions | 269 registry rows; 2,358 KY/TX county courts unnamed-id | State trial courts outside 6 `LC:` keys have no ids. CL `courts` table (in people catalog) is the best resolver |
| Courthouse | `courthouse:cl:<id>` or `courthouse:x:<16hex>` of `(court_id, normalized address)` | CourtListener courthouse id, GSA building id | address, geo, `court_id`, `county_geoid`, phone (public switchboard only) | none held | Entire entity is a gap; CL courthouses API is the intended source |
| Judge | existing `judge-entity-<24hex>` IF minting is proven deterministic; else re-mint `judge:<16hex>` from the sorted set of authoritative native ids | `fjc_nid`, `fjc_legacy_id`, `cl_person_id`, official roster URL, Trellis slug (internal only) | `name`, `aliases[]`, `positions[]` (court_id, role, start, end, basis), `education[]`, `current_service_verified` (bool + as_of), `member_keys[]`, `merge_basis[]` | 10,669 entities / 10,698 profiles | Export only entities with at least one non-vendor authoritative member. MDL transferee-judge coverage not yet measured |
| JudgeEvidence (child) | `jev:<sha256 of canonical json>` | source observation id | `judge_id`, `evidence_type` (order, opinion, standing_order, evaluation, assignment, publisher_stat), `period`, `denominator`, `publisher_reported` flag, `document_id`, quote + anchor | 118 profiles with analyses | No predictions, no invented rates; publisher numbers keep label, period, denominator |
| MDL | `mdl:<number>` (JPML number, e.g. `mdl:3080`) | JPML docket, transferee `case_id` | title, transferee `court_id`, transferee `judge_id`, status, created/terminated dates, pending-count series (as Statistic) | MDL-3080 only | JPML pending/terminated tables not held |
| Case | `case:<court_key>:<normalized docket no>` e.g. `case:FD:njd:2:23-md-03080` | `courtlistener_docket_id`, `pacer_case_id`, `lawgraph` IRI, DocketBird id, platform `matters.slug` | caption, `mdl_id`, `node_role` (mdl_master/member/public_docket to match platform), nature of suit, filed/terminated | 1 MDL collection; 436,005 docket metadata rows noted in deep audit (unused) | Docket-number normalizer needed (judge initials suffixes) |
| Settlement | `settlement:<court_key or jur>:<case_no>` when case number known; else `settlement:x:<16hex of official_url host+path>` | publisher record sha256, administrator site URL | `case_id`, fund amount (as stated, with basis), `class_definition`, `claim_deadline`, `status` + `status_as_of`, `official_url`, `administrator`, `documents[]` | 848 refs (SettleSignal-derived), 9 bounded reviews, 4 official PDFs | 844 lack any saved official document; state field null in sample; third-party text (see 8) |
| Document | `doc:sha256:<raw_sha256>` | `record_key` (series), `version_id`, platform `document_id` later | `doc_type` (controlled list, superset of platform `kind`), `format`/`mime`, `bytes`, `page_count`, `language`, `court_ids[]`, `jurisdiction_ids[]`, `source_url`, `final_url`, `capture_kind`, `reading_copy_ref`, `is_sealed`, `fillable` | focused 16,454; seeger 18,360; pending 301; MDL 1,612 PDFs | `doc_type` for 10,543 seeger rows undifferentiated; platform `format` enum has no `html`/`txt` |
| LegalProvision | `prov:<jur>:<code_slug>:<section_path>`; for OUL rows use provider `act_id`. Version = `content_hash` | official citation string, OUL `act_id`, USC/CFR cross-refs | `provision_type` (constitution, statute, court_rule, rule_of_evidence, ordinance), `citation`, `hierarchy[]`, `heading`, `text_ref`, `status` (in_force/repealed/reserved/renumbered/unknown), `last_amended_year` | OUL 2,978,617 rows; seeger provisions 6,695 + rule 238; focused law chapters | Effective dates mostly absent; OUL `currency_verified=false` |
| Regulation | same id grammar, `provision_type=regulation`; federal `prov:us:cfr:<title>:<part>.<section>`; rulemaking docs `fr:<document_number>`; dockets `regdocket:<id>` | CFR cite, FR doc number, RIN, Regulations.gov docket id, FDA guidance id | `agency_id`, `authority_cites[]`, `effective_from`, `comment_period`, guidance `level` | seeger regulatory 233; OUL state admin codes; federal CFR size-screened only | FDA/agency layer essentially not built yet |
| Agency | `agency:us:<slug>` using Federal Register agency slug; states `agency:us-nj:<slug>` minted | FR agency id, USA.gov id, parent | name, parent, `jurisdiction_id`, website, enforcement/recall feeds | none as entities | New |
| SourceReference | existing `pld-<12hex>` | registry line number, section/subsection, tags | `url`, `title`, `tags[]`, `verbatim`, `source_as_of`, `link_status` (unknown until checked), `linked_document_ids[]` | 9,348 refs; 554 linked (370 directory records, 204 retained captures, 104 judge entities); 32 pilot captures | 8,794 references have no saved capture |
| Firm | `firm:x:<16hex>` minted from `(normalized name, state)` and ALWAYS `resolution_status=candidate` until a native id exists | CourtListener attorney-organization id, state business entity no. | names as observed per case, offices | none | No stable public native id. Treat as observed strings on a Case edge, like platform `corpus.counsel` |
| Attorney | `atty:<usps>:bar:<bar_no>` when bar number evidenced; else CL attorney id; else do not create an entity | state bar no., CL attorney id | name as observed, firm as observed, role, leadership appointments (PSC/PEC/lead/liaison) with order `document_id` | none | Leadership-appointment extraction from MDL orders is the high-value path |
| Statistic | `stat:<publisher>:<table_id>:<period_end>:<dims_hash>` e.g. `stat:uscourts:c-3:2026-03-31:<h>` | table number, report name | `measure`, `value`, `unit`, `period_start`, `period_end`, `dimensions{court_id, nos, ...}`, `publisher_reported=true`, `denominator`, `source_document_id`, `cell_anchor` | 170 monthly court records + eFileIL codes noted in deep audit | uscourts.gov caseload tables not captured |

---

## 4. Temporal model (mandatory block on every exported row)

```json
"temporal": {
  "captured_at":        "2026-09-18T16:55:35Z",   "captured_at_basis": "collector_clock | connector_response | import_time | unknown",
  "source_as_of":       "2026-08-14",             "source_as_of_basis": "publisher_snapshot_label | registry_header | page_statement | unknown",
  "published_at":       null,                     "published_at_basis": null,
  "effective_from":     null,  "effective_to": null, "effective_basis": "text_statement | enactment_clause | official_table | unknown",
  "superseded_by":      null,                     "supersedes": null,
  "observed_http_last_modified": "…",             // stored, NEVER mapped to any legal date
  "date_precision":     "day | month | year | unknown",
  "currency_verified":  false, "currency_checked_at": null
}
```

Rules: unknown stays `null` with basis `unknown`; never back-fill a legal date from capture time, file mtime,
URL path year, or HTTP headers. `superseded_by` points to an entity `id` (provisions, rules, standing orders,
settlement notices) or a `document_version_id` (same URL, new bytes). Snapshot-style sources (OUL `v2026.08`,
CourtListener bulk `2026-06-30`, FJC CSV) carry `source_as_of` from the publisher label and one row per snapshot, so
as-of queries ("rule text on the filing date") are answerable only where `effective_*` is evidenced; otherwise the
API must answer "as captured on X", not "in force on X". Platform mapping: `reference.court_documents.source_date`
+ `source_date_kind` receive exactly one of these with its kind named; do not collapse.

---

## 5. Relationship edges

Edge row: `{edge_id, type, from_id, to_id, valid_from, valid_to, basis, evidence_document_id, evidence_anchor,
confidence_class (explicit_source | native_id_join | curated | inferred_prohibited), dataset_id}`.
`inferred_prohibited` exists so validators can reject it: no hostname-to-county, no name-only person joins.

| Edge | From -> To | Evidence required |
|---|---|---|
| `within` | Jurisdiction -> Jurisdiction | Census hierarchy |
| `sits_in` / `serves` | Court -> Jurisdiction (many counties per district) | official district/county table |
| `part_of` / `appeals_to` | Court -> Court | official structure page |
| `located_at` | Court -> Courthouse | CL courthouse or official address page |
| `holds_position` | Judge -> Court (role, start, end) | FJC / CL positions / official roster |
| `same_as_candidate` | Judge <-> external person record | shared native id only; name match alone = `candidate`, never exported as identity |
| `presides_over` / `referred_to` | Judge -> Case / MDL | docket or JPML order document |
| `member_of` | Case -> MDL | transfer/CTO order or CL docket relation |
| `filed_in` | Case -> Court | docket |
| `entry_of` | Document -> Case (`docket_source`, `entry_number`, `attachment_number`) | matches platform v1 identity |
| `issued_by` | Document -> Court / Judge (standing orders, local rules, forms, instructions) | document caption or host page |
| `applies_in` | LegalProvision/Document -> Court / Jurisdiction | explicit scope text |
| `cites` | Document/Provision -> Provision/Case/Document | extracted citation + resolver (eyecite/CL citation lookup) |
| `implements` / `authorized_by` | Regulation -> Statute | authority note |
| `administers` | Agency -> Regulation / Program | FR / CFR |
| `amends` / `supersedes` | Provision -> Provision; Document -> Document | session law / order text |
| `resolves` | Settlement -> Case / MDL | court + case number |
| `has_document` | Settlement -> Document (`role`: notice, agreement, prelim/final approval order, claim form, plan of allocation, fee motion) | official administrator or docket |
| `represents` / `appointed_to` | Attorney -> Party/Case; Attorney -> MDL leadership role | docket counsel block / leadership order |
| `affiliated_with` | Attorney -> Firm (as observed, dated) | docket counsel block |
| `measures` | Statistic -> Court / Judge / MDL / Jurisdiction | table dimension |
| `captured_as` / `derived_from` | SourceReference -> Document; reading copy -> original | exact URL match (as in `source_archive_links_20260919`), hash lineage |

---

## 6. Export contract (`refcorpus` bundle, contract_version `0.1-draft`)

Deliberately mirrors the platform's ingest-contract-v1 behaviour so one mental model covers both.

```text
export/<bundle_id>/
  MANIFEST.json            authoritative; unknown fields rejected
  CHECKSUMS.sha256         every file in the bundle
  schemas/<entity>.v<semver>.schema.json
  datasets/<dataset_id>/
      DATASET.json         license, attribution, redistribution class, source_as_of, producer validation hash
      <entity>.jsonl.gz    default interchange (one object per line, UTF-8, NFC, LF)
      <entity>.parquet     for > 250k rows (provisions, statistics); same logical schema, zstd
      edges.jsonl.gz
      REJECTS.jsonl        rows withheld + reason code (kept out of data files)
  blobs/sha256/<aa>/<sha256>          original bytes, no extension trust; mime in metadata
  reading/<sha256>.<extractor>-v<ver>.md|txt   cleaned reading copies, separate from originals
  anchors/<sha256>.anchors.jsonl      page/section offset maps for reading copies
```

`MANIFEST.json` (required keys): `contract_version`, `bundle_id`, `idempotency_key`, `created_at`, `mode`
(`full | incremental`), `producer {repo_commit, exporter_version, directory_build_receipt_sha256}`,
`datasets[] {dataset_id, entity_files[{path, rows, sha256, bytes, schema}], blob_count, blob_bytes, license_ref}`,
`totals {rows, blobs, bytes}`, `exclusions_summary {reason_code: count}`, `previous_bundle_id`, `tombstones_file`.

Behaviour:

- Filenames are opaque; identity lives in rows. Totals and hashes must match or the whole bundle fails validation.
- Incremental bundles carry upserts + `tombstones.jsonl` (`id`, `reason`, `superseded_by`). An occupied `id` with a
  different content hash becomes a new version; never a silent overwrite.
- Schema versioning: semver per entity schema. Minor = additive optional field; major = rename/removal/semantic
  change. Consumer rejects unknown major. A `schemas/CHANGELOG.md` travels with the bundle.
- Paths inside the bundle are relative POSIX; absolute local paths and command lines are scrubbed (finding 2.6).
- No embeddings, no secrets, no connector tokens, no user email. Connector-derived rows carry
  `capture_kind: connector_response_not_original_http_bytes` with tool name, arguments hash, timestamp, response hash.
- Local pre-flight: `validate_refcorpus_bundle.py` (to be written, offline, stdlib + pyarrow optional) reproduces
  every consumer rule and exits non-zero with a reject table, as `validate_bundle.py` does for v1.

`DATASET.json` licensing block (required, per dataset):

```json
{ "dataset_id": "open_us_law.v2026_08",
  "license_id": "CC-BY-4.0", "license_evidence": ["evidence/LICENSE.md sha256:…"],
  "attribution_text": "Open US Law by Vaquill AI (CC BY 4.0); indexed and re-keyed locally",
  "attribution_url": "https://github.com/Vaquill-AI/open-us-law",
  "changes_made": "checksum verification, separate search index, source/quality metadata",
  "redistribution_class": "open_with_attribution | public_domain_gov | internal_only | excluded | unknown",
  "display_requirements": "attribution string must reach the end-user citation card",
  "source_as_of": "2026-08-14", "currency_verified": false }
```

`redistribution_class = unknown` is treated as `excluded` by the exporter (fail closed).

Docket-shaped material (MDL-3080 and future MDLs) should NOT go through this bundle. It fits the platform's
existing ingest-contract-v1 (matter + `docket.csv` + PDFs). The 1,612 PDFs already have `raw_sha256`,
`page_count`, entry IRIs; what is missing for v1 is an explicit `filed_date`, `docket_source`, `availability`
(`locally_supplied`), per-slot `attachment_number`, and a reviewed manifest. The date and entry number currently
live inside the title string (`"0001. (08-04-2023) ORDER..."`); v1 forbids deriving identity from filenames, so
these must be lifted into reviewed columns from the external graph metadata, not regexed at ingest.

---

## 7. Retrieval readiness

| Content | Chunk unit | Citation anchor | Notes |
|---|---|---|---|
| Statute / regulation / rule section | one provision = one chunk; split only above ~1,200 tokens at subsection boundaries, repeating citation + heading | official citation + subsection path + `content_hash` | `context` line = display path ("Idaho Code / Title 41 / Chapter 13 / 41-1325"); `status` and `source_as_of` as filter columns |
| PDF orders, notices, forms, standing orders | platform canonical: page-anchored blocks, ~512 tokens, overlap only inside a section, tables as own chunks with header repeated | `doc:sha256:<h>#page=<n>` (+ bbox when available) | reuse `quoteOnPage` verifier; keep `conf` and extraction `source` |
| HTML court pages / local rules pages | heading-scoped sections from the reading copy | `doc:sha256:<h>#sec=<heading-path>&chars=<start>-<end>` against the reading copy hash | platform convention of synthetic ~3k-char pages is the fallback |
| Judge profile | one chunk per evidenced fact group (positions, education, each evaluation/analysis) | `judge_id` + `jev` id + underlying document anchor | never a single blended biography chunk; vendor text excluded |
| Settlement | one chunk per official document section + one structured "facts" chunk from verified fields | document anchor; facts chunk cites the notice page | deadlines carried as typed columns for date filtering |
| Statistic | not embedded; structured rows with `cell_anchor` (table, row, column) | table id + period + cell | served by SQL/tool call, optionally a short generated caption chunk |
| SourceReference | not embedded; lexical index on title/tags/section | `pld-` id | navigation aid only |

Reading copies vs originals: originals are immutable bytes addressed by SHA-256 with receipt; reading copies are
versioned derivatives (`extractor`, `extractor_version`, `text_sha256`, `derived_from`) and are the only thing
chunked. Every chunk must round-trip: `chunk.content` is a verbatim substring of the reading copy at the stated
offsets, and the reading copy's page map points back into the original. Filter columns to denormalize onto
chunks (as the platform does on `corpus.doc_chunks`): `jurisdiction_ids`, `court_ids`, `doc_type`,
`provision_type`, `status`, `source_as_of`, `effective_from/to`, `captured_at`, `license_ref`, `review_status`,
`is_sealed`.

---

## 8. What must NOT be exported (fail-closed list)

1. Any row whose `redistribution_class` is `internal_only`, `excluded` or `unknown`.
2. All `trellis.law` captures and connector responses: 2,897 URL-bearing records, 4,458 + 1,300 judge observations,
   county coverage profiles, motion-type analytics. Facts may be exported only when independently evidenced by an
   official source, and then the official source is the provenance.
3. Lexis Context / Lex Machina previews (`judge_vendor`, 2 records) and anything behind login, paywall or preview.
4. SettleSignal editorial text (descriptions, excerpts, status wording) for the 848 settlement references. Export
   only re-verified official facts and official documents; keep attribution where any SettleSignal-derived field remains.
5. Unresolved or conflicting identities: judge entities lacking a non-vendor authoritative member; any multi-member
   entity whose `merge_basis` is name-only; `candidate` firm/attorney entities as identities.
6. Records not review-cleared: `needs_content_review`, `*_needs_review`, `Awaiting publication validation`,
   `county_government_website_to_verify`, soft-404/challenge shells, empty extraction.
7. Portraits and court marks with `permission_status: not_established` (currently all). Export the metadata row
   and source page link, not the image bytes, until cleared.
8. Sealed, restricted or highly-sensitive-document material; anything a docket marks sealed.
9. Personal data beyond public professional contact details. No home addresses, personal phones, family members
   (federal judicial security and privacy law makes this a hard line for federal judges).
10. Local absolute paths, usernames, command lines, API keys, connector tokens, the user's email.
11. Predictions, scores or rates computed by us about judges; publisher statistics without period and denominator.
12. Embeddings and any third-party-model derived text summaries (platform regenerates in account).

---

## 9. Licensing and entitlement risk register (plain statement)

| # | Dataset / source | Position | Risk | Required action before export |
|---|---|---|---|---|
| L1 | Open US Law v2026.08 (2,978,617 rows) | CC BY 4.0 for data, Apache-2.0 scripts; license files pinned in `sources/open_us_law_20260918/evidence/` | Low-medium. Attribution must reach end users; "indicate changes"; third-party normalization, `currency_verified=false`; publisher separately sells a commercial "retrieval-ready" license (attribution waiver, warranty) | Carry attribution to citation cards; label as normalized secondary copy; spot-verify against official sites for anything quoted in a filing |
| L2 | CourtListener bulk people/positions/courts (snapshot label 2026-06-30) | Free Law Project bulk data is published for open reuse; exact license text was NOT pinned locally and NOT verified in this pass | Medium until evidenced | Pin license/terms evidence the way OUL did; keep native ids; record snapshot date |
| L3 | CourtListener / DocketBird / Trellis / Legal Data Hunter via MCP connectors | Governed by the user's account terms, API rate limits and quotas | Medium-high for bulk reuse. Connector responses are not original bytes | Treat as lookup/enrichment, not as a redistributable dataset; store response hashes; counsel review of each subscription's reuse clause |
| L4 | Trellis (site captures + connector) | Commercial vendor; proprietary analytics and compiled state trial court data; redistribution restrictions are standard in such agreements (terms not read in this pass) | **High** | Internal reference only. No export. Do not expand scraping; "further Trellis scraping" in the request needs an entitlement decision first |
| L5 | Lexis Context / Lex Machina public previews | Proprietary | High | Exclude |
| L6 | SettleSignal-derived settlement library (848) | Third-party aggregator, editorial content; attribution currently displayed | Medium-high | Rebuild from official administrator sites and court dockets; standardize official document set per settlement; keep SettleSignal only as a discovery pointer |
| L7 | MDL-3080 PDFs (1,612) and future PACER/DocketBird pulls | Court filings are public records; `source_url` is null on these rows so acquisition route is undocumented | Medium (provenance, sealed items, vendor download terms) | Record acquisition route per file; sealed screen; ship through ingest-contract-v1 not the reference bundle |
| L8 | Court seals/marks, judge portraits | `permission_status: not_established` everywhere; official seals can be use-restricted | Medium | Metadata only until a per-source reuse note exists (platform already has `reuse_note`) |
| L9 | State codes hosted by commercial publishers (e.g. Lexis-hosted official code portals, municipal code vendors) and annotated codes | Statutory text is a government edict; annotations, headnotes and site terms are not free | Medium | Capture from legislature-hosted sources or OUL; never capture annotations; record the host class |
| L10 | FindLaw case law (requested) | Commercial site terms typically bar bulk harvesting (not read in this pass) | High for scraping | Use CourtListener opinions/citations bulk data or Caselaw Access Project instead; keep FindLaw as a SourceReference link only |
| L11 | uscourts.gov statistics/reports, justice.gov/jmd/ls directories, FJC, FDA, Federal Register, eCFR | US government works | Low | Respect robots and crawl-delay; store table period and report name |
| L12 | SEC EDGAR | Public; fair-access policy expects a declared User-Agent with contact details | Low, but conflicts with the BRIEF rule "do not send the user's email" | User decision needed on a firm-generic contact string before any EDGAR packet |
| L13 | Firecrawl/provider-rendered captures of official pages | Content is official; bytes are provider output | Low (provenance class, not license) | Keep `provider_response_not_original_http_bytes` label through export |
| L14 | Platform side: Cohere rerank default in `kb/search.server.ts` vs firm policy; Voyage embeddings in legacy ingest | Vendor-approval conflict | Medium | Platform owner decision; reference path should assume Titan v2 + RRF only |

---

## 10. Quality gates and acceptance tests (all offline, deterministic, run before any bundle is accepted)

Structural
- G1 Every file hash in `CHECKSUMS.sha256` and `MANIFEST.json` re-verifies; totals equal actual rows/blobs/bytes.
- G2 100 percent of rows validate against their JSON Schema; unknown fields = fail. Parquet and JSONL row counts agree.
- G3 Every `id` unique per entity; re-running the exporter on unchanged inputs yields byte-identical data files
  (determinism test) and identical ids (stability test across a simulated recapture).
- G4 Referential integrity: 0 dangling `from_id`/`to_id`/`document_id`/`superseded_by`.

Identity and jurisdiction
- G5 FIPS GEOIDs match `^[0-9]{5}$`, are strings, and exist in the county table; state/county pairs agree.
- G6 0 edges with `confidence_class = inferred_prohibited`; 0 county assignments whose only basis is hostname.
- G7 0 exported Judge identities built on name-only merges; every exported judge has >= 1 authoritative native id or
  official-roster member; `fjc_nid` and `fjc_legacy_id` never share a field.
- G8 Every `court_key` either exists in the platform key grammar or is `court:x:*` with `resolution_status != resolved`.
- G9 MDL judge coverage report: for every active JPML MDL, transferee judge resolves to a Judge `id`
  (target 100 percent of active MDLs; measured, not assumed; JPML list not yet held).

Temporal
- G10 Temporal block present on 100 percent of rows; every non-null date has a non-`unknown` basis; 0 rows where
  `effective_*` equals `captured_at` or an HTTP header value; `effective_to >= effective_from`.
- G11 `superseded_by` chains are acyclic and terminate.

Content and retrieval
- G12 Reject shells: soft-404, login/challenge, empty or near-empty extraction (< 200 chars for a multi-page PDF),
  duplicate-boilerplate ratio above threshold.
- G13 Round-trip: 100 percent of sampled chunks are verbatim substrings at stated offsets; page anchors resolve.
- G14 Citation resolver: >= 95 percent of a 500-citation hand-checked sample resolves to the right Provision/Case id;
  unresolved citations stay unresolved (no nearest-match guessing).
- G15 Golden retrieval set: >= 50 mass-tort research questions (venue/local rule, standing-order requirement, state
  SOL/repose provision, FDA regulation, settlement deadline, MDL leadership) with expected source ids; BM25-only
  baseline recorded locally; platform hybrid must not regress it.
- G16 Encoding: NFC, no U+FFFD, no control characters; section signs and em dashes preserved.

Licensing and privacy
- G17 0 rows from `excluded/internal_only/unknown` datasets; grep gate for `trellis.law`, `lexis`, `settlesignal`
  in exported text fields and URLs (pointer fields allowed only in SourceReference).
- G18 Attribution string present for every CC BY row and survives to the chunk metadata.
- G19 PII screen: no emails/phones outside designated professional-contact fields; no street addresses on person rows.
- G20 Path/secret scrub: no `C:\`, `/Users/`, drive letters, tokens, or command lines anywhere in the bundle.

Supplement hygiene (pre-condition inside the MVP)
- G21 Every `sources/*/validation.json` adopts one envelope: `schema_version`, `status in {passed, failed}`,
  `ready` (bool), `validated_at`, `data_files[{path, sha256, rows}]`, `counts`, `checks[]`, `qualification`,
  `license_ref`. Exporter refuses datasets without it.

---

## 11. Phased milestones (nothing past M3 without the user's explicit go-ahead)

| Phase | Outcome | Touches platform? | Exit criteria |
|---|---|---|---|
| M0 Contract review | This draft reviewed; decisions on open questions (section 12); entity schemas frozen at `0.1` | No | Signed-off schema files + exclusion list |
| M1 Identity and temporal backfill (inside MVP) | Additive supplement `sources/canonical_ids_<date>/` with crosswalk `directory id <-> record_key <-> version_id <-> raw_sha256 <-> canonical id`; court-key resolution for county registry; judge merge-basis audit; temporal block populated with `unknown` where unknown; uniform validation envelope | No (and no rebuild of `directory.sqlite3`; adapter-only, hash-gated) | G3, G5-G8, G10, G21 pass |
| M2 Dry-run exporter + validator | Offline `export_refcorpus.py` + `validate_refcorpus_bundle.py`; three pilot datasets: (a) court registry + court rules/forms/standing orders shaped to `reference.court_documents`, (b) Open US Law New Jersey + one more state, (c) FJC-evidenced federal judges for courts with active MDLs | No | G1-G4, G12, G13, G16, G20 pass on pilots |
| M3 Licensing and entitlement sign-off | Risk register items L1-L14 each closed, accepted or excluded by the user/firm | No | G17-G19 pass; written decisions recorded |
| M4 Retrieval readiness | Chunk + anchor generation, golden question set, BM25 baseline, citation resolver evaluation | No | G14, G15 recorded |
| M5 Platform landing design (paper + PR draft only) | Proposed `db/kb/0004_reference_corpus.sql` (`reference.documents`, `reference.provisions`, `reference.chunks` with Titan v2 1024-d + tsv, `reference.edges`, `reference.datasets` for license/attribution), loader via RDS Data API constraints (single statements, 1 MiB/64 KB caps), `ref_search`/`ref_read` tool spec, court-key additions for `FB:`/`F:` | Design only | Platform owner review; Cohere/Voyage question settled |
| M6 Staging load | First bundle into a non-production Aurora cluster; MDL-3080 via ingest-contract-v1 as a separate track | Yes, dev only | All gates green on the loaded copy; attribution visible in UI |
| M7 Incremental operations | Delta bundles, tombstones, supersession, freshness monitors, connector-quota budgeting, quarterly OUL snapshot roll | Yes | Two consecutive clean incremental cycles |

---

## 12. Open questions and what this pass did NOT verify

- Judge `entity_id` minting rule (determinism across rebuilds) was not located; `settlement-<hex>` hash basis likewise.
- CourtListener bulk-data license text, Trellis/DocketBird/Lexis/SettleSignal/FindLaw terms were not read (no network);
  risk levels above are conservative defaults, not legal conclusions. Counsel review is required.
- Whether the platform maps `FB:` and `F:` court keys anywhere outside `courtReferenceKeys()` (only that function was read).
- Whether `reference.*` has been applied to any live Aurora cluster, and which "reference-library tooling" populates
  it today (not found in `devvvv`; likely the external `Court-Library-Expansion-2026-09-12` project).
- `C:/Users/firas/Downloads/mco2` and the four `prodrepo/workingversion-*` trees were not inspected beyond directory listing.
- `catalog/documents.sqlite3` (1.9 GB) was not opened; its schema was read from `scripts/build_document_index.py`.
- Temporal-field coverage figures come from a 1-in-40 payload sample of top-level keys, not a full scan or nested keys.
- Multi-member judge entity count (1,072) covers only the first 3,000 entities.
- MDL transferee-judge coverage, the unused 436,005 docket metadata rows, and the 120,464-node legal graph
  (`urn:lawgraph:` IRIs) were not examined; the IRI grammar is known only from MDL-3080 metadata.
- No export code was written or run; every gate above is a specification, not a result.
