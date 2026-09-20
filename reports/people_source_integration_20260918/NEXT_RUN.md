# CourtListener biographies integrated — September 18, 23:38 UTC heartbeat

The local source layer is now ready and browsable at
http://127.0.0.1:8769/#people. This completes priority 1's local adapter and a clean
separate historical-biography view from the broader directory audit. It does not
complete identity bridges, photo recovery or a current-judge directory import.

## Completed

- `sources/courtlistener_people_20260918/catalog.sqlite3`: six original-string
  tables, 98,117 total rows, source manifests, real foreign keys and a name-search
  index. Counts: 16,191 people; 51,291 positions; 12,777 education rows; 6,011 schools;
  8,486 political affiliations; 3,361 courts. The UI displays professional career
  and education records, not every retained raw field.
- Default view: 15,797 non-alias source people. The explicit alias option includes
  394 additional alias records. These numbers include nonjudicial roles and must
  never be added to the 10,669 consolidated judge count.
- Name and recorded-court filtering, paging, clean biography/education detail
  pages, preserved return filters, mobile layout and collapsed source evidence.
  The Judges page links to Historical biographies.
- Date granularity is honored: `%Y` does not become January 1; blank termination
  does not become Present. Source-inferred position values are labeled. Specific
  degree text such as B.S. or A.M. is retained over broad degree category codes.
- `people.py` only opens the fixed local source DB after its DB/manifest/summary/
  validation receipt hashes and schemas match. No arbitrary file route or write
  endpoint was added. Main metadata and bulk-law indexes were not rebuilt.

The source database is 29,122,560 bytes; SHA-256:
`08d2cfa38550a1795610c32546488a336ab0d30d9e6e3f3bc6bd72b85b76abea`.
Its ready receipt binds all source metadata. The optimized first publication took
3.35 seconds after moving foreign-key indexes ahead of inserts. A prior slow
unpublished attempt is retained as isolated recovery evidence; it is not served.
The normal importer now returns already_verified for this unchanged snapshot and
checks all receipt bindings. Do not reimport or rebuild this source every heartbeat.

## Verification

- Eight importer tests and 25 independent adapter/date/alias/gate checks passed.
- Fifteen live read-only HTTP checks passed: counts, alias handling, filters,
  pagination, date precision, unchanged judge count and access boundaries.
- Desktop and 390×844 mobile pages checked in the real browser; no horizontal
  overflow, source details collapsed, name/court state preserved, and no page errors.
- Live list requests measured 0.02–0.09 seconds; example profile 0.014 seconds.
  These are local request samples, not whole-corpus throughput guarantees.

Receipts: `live_validation.json`, `adapter_review_verification.json`,
`source_semantics_review.json`, `education_semantics_review.json`, and
`sources/courtlistener_people_20260918/test_results.json`.

Only the verified loopback preview server was restarted (PID 32584 at this
checkpoint; inspect fresh process identity before any later action). Source
originals, main directory, county queues and focused publication remained unchanged.

## Next useful slice

Choose a bounded portrait recovery pass using the 29 explicit PA source/profile
references, or the 374-county KY/TX registry overlay. For portraits, follow the
existing professional-identity and content-hash gates; image references and the
1,230 source has_photo flags are not downloaded image files. Existing accepted
portrait count remains 14. FJC legacy IDs and existing nid identifiers still need
verified bridges; no automatic name merge is authorized by this import.

County acquisition was not started in this local-integration pass. The one Nelson
pending URL and its 60-second source delay remain as described in the prior county
HANDOFF. Check current processes/queues before that continuation. Larger bounded
trials from the broader audit remain available after exact source review. No
Firecrawl credits or other network acquisition were used here.
# Superseding live checkpoint

The 29 PA portraits and separate official profiles are now integrated. Read
`reports/mvp_live_reconciliation_20260919/NEXT_RUN.md` and its live validation
before repeating any portrait work. The biographical source layer described
below remains unchanged and live.
