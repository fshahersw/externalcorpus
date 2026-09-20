# integration-planner — pointer

Full deliverable: `../integration/INTEGRATION_PLAN_DRAFT.md` (read-only scoping; nothing integrated or exported).

Inspected (read-only): `devvvv/` platform snapshot (docs/ingest-contract-v1.md, schemas/, db/kb/0001-0003, supabase/corpus/corpus-v2.sql,
docs/kb-ingest-design.md, docs/ARCHITECTURE.md, src/lib/courts.ts, src/lib/kb/search.server.ts, `.env.example` key names only);
`delivery/archive-directory/directory.sqlite3` (mode=ro); `server.py` id function; `scripts/build_document_index.py` schema;
27 `sources/**/validation.json`; supplements for court registry, county registry, judge profiles, CourtListener people,
Open US Law catalog (immutable ro), settlements, MDL-3080, source directory links. No network, no secrets, no writes outside `reports/`.

Headline facts:
- Platform already has a firm-global `reference.*` schema (courts, judges, court_documents) keyed by `FD:/FS:/ST:/LC:` court keys;
  the MVP registry uses the same families (FD 94, FB 94, ST 56, F 13, FS 6, LC 6). This is the join point.
- Directory `records.id` is `sha256(...)[:32]` and version-bound for focused rows: not an exportable identity. Use `raw_sha256`
  (document), `record_key` (capture series), `version_id` (version).
- 48 percent of judge observations and 2,897 record URLs are Trellis-derived; 848 settlements are SettleSignal-derived: both are
  export-blocked pending entitlement review.
- Vendor conflict on the platform side: Cohere rerank default in `src/lib/kb/search.server.ts:9` vs firm no-Cohere policy.
