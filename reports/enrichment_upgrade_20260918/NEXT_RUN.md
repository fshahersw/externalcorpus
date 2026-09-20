# Maintaining the enriched local directory

**Superseded operational priority:** the latest user direction is a clean personal
MVP, without requiring full acquisition. Follow `../mvp_cleanup_20260918/NEXT_RUN.md`.
Open US Law is now published and searchable. Preserve the source/recovery rules
below, but do not run the historical acquisition-resume step during this MVP phase.

This supplement implements the user's September 18 request to use the pinned
Vaquill open-us-law release and the Seeger staging/library collection, clean
reading views, recover text and consolidate confirmed judge identities. The
read-only local directory is `http://127.0.0.1:8769/`.

## Preserve the completed work

- Treat `sources/open_us_law_20260918/ready.json` as the bulk publication gate.
  A healthy importer holding its lock must finish; never launch a duplicate.
  Reuse the verified 229 Parquets instead of redownloading the release. Preserve
  publisher versions, historical statuses, attribution and source URL gaps.
- Keep the Seeger import and its receipts frozen. The separate validated
  `sources/seeger_text_recovery_20260918` pass overlays text on 384 existing IDs;
  it does not create documents. Its manifest, derivative hashes and parent raw
  hashes must match before use. `server.py --build` reapplies this overlay.
- Preserve the judge entity projection and all source observations. Group only
  evidenced identities; ambiguous and conflicting candidates stay separate.
  Counts describe source observations/display entities, not current judges.
  Analysis outcomes, denominators, capture dates and limitations remain sourced.
- Preserve every original and raw extraction. Reading copies are derived views
  bound to reader version, original hash and selected canonical text hash. Exact
  legal provision slices must not be replaced by their shared container body.

## Refresh procedure

1. Resume eligible official state/county work under the existing source controls
   and reviewed finite queues. Fresh process and lock evidence controls resumes.
   Broad Trellis, paid-vendor and unrelated URL acquisition remain paused.
2. Publish new focused corpus material through its existing locked seven-step
   rebuild, with the existing independent release checks. Supplements do not
   establish a newer or nationwide-complete focused release.
3. At a stable publication checkpoint, run
   `delivery/archive-directory/server.py --build`, then
   `scripts/build_reading_views.py --workers 2` using installed Python 3.11.
   Do not overlap the full build with a bulk import or large OCR job.
4. Verify directory API tests and changed data routes. Restart only the verified
   local server process if its source changed. Bind to loopback; retain indexed
   artifact allowlists and inert HTML downloads.
5. Update measured counts and the latest RUNBOOK checkpoint. Distinguish originals,
   provision rows, source observations, grouped display entities, usable text and
   county inventory. Do not add overlapping counts into a unique-document total.

## Remaining bounded quality work

- One 94 MB NJ compilation RTF did not finish native extraction. Its 5,856
  separately imported provisions already provide a searchable derivative family;
  they do not mean that the entire original RTF was recovered.
- Existing partial-text PDFs, blank pages and a truncated XML remain separately
  flagged. OCR engine confidence is not independently measured accuracy.
- The bulk publisher withdrew GA and NC statute files. Its 311,321 rows without
  original-source URLs retain Parquet provenance; do not manufacture official
  URLs, current-law status or equivalent verified citations.
- Bulk exported rows are not globally deduplicated unique provisions. Confirmed
  local duplicate groups and judge identities preserve all source memberships;
  cross-publication legal equivalence needs citation/version/authority evidence.
- County inventory coverage is not local-rule, document or filing completeness.
  Continue prioritizing substantive official rules, codes, orders and forms.

Final verification evidence is in the adjacent `verification.json` and separate
reader, recovery, identity, source-binding and bulk receipts referenced there.

## Queue snapshot after enrichment preparation

At 19:53 UTC September 18, the API queue snapshot records Arizona with 606
saved captures and 125 pending URLs; its last bounded run ended at 18:29:46 UTC.
The reviewed state follow-up (348 saved), general county (697 saved) and WA local
rules (129 saved) queues have no pending URLs. Their exhausted finite frontiers
do not establish whole-source or national completion. Evidence:
`continuation_queues.json`. Check live processes and locks before resuming Arizona,
and refresh the pending-publication projection after stable accepted acquisition.
