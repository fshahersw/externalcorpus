# CourtListener biographical source review

This is a bounded, independent review of three named local compressed tables and the supplied SQL schema. It does not verify current judicial service, fetch new material, install portraits, or merge people into the existing judge entities. The machine-readable distributions, examples, source hashes, and row counts are in `source_semantics_review.json`; `review_source_semantics.py` reproduces them without reading the large opinion or disclosure tables.

## What the source contains

- 16,191 person rows: 15,797 without an alias reference and 394 alias rows. All 394 references target an existing non-alias row directly, with no cycles. Alias rows have no position records. These are source records, not a census of current judges or an identity-verified unique-person count.
- 51,291 position rows, including historical judicial service, government employment, private practice, law clerks, and other roles. Of these, 257 explicitly flag inferred values. The 22,183 court-linked positions include 218 clerk, 30 private-practice, six assistant district attorney, and four district attorney rows. A court link alone cannot establish a judicial role.
- 1,230 person rows have the publisher's `has_photo` flag. No portrait bytes or verified image URLs follow from that flag.
- 3,361 court reference rows. Registry `in_use` is not a person's current-service status. Preserve unrecognized categorical values, including the source's mixed-case jurisdiction code `St`, rather than silently assigning a court system.

## Display date precision faithfully

| Field | Nonempty values | Day precision | Month precision | Year precision |
| --- | ---: | ---: | ---: | ---: |
| Birth | 7,362 | 4,514 | 35 | 2,813 |
| Death | 4,449 | 4,179 | 66 | 204 |
| Position start | 50,422 | 15,377 | 1,670 | 33,375 |
| Position termination | 42,459 | 11,488 | 1,241 | 29,730 |

The CSV uses ISO-shaped dates even when only a year or month was recorded. For example, a `1986-01-01` value paired with `%Y` must display as `1986`, not January 1, 1986. Three missing death dates retain a precision marker, as do 36 missing termination dates; these remain absent. Unknown precision must be qualified, not assumed to mean a full day. A missing termination date must not become “present,” “current,” or “active.” The file snapshot date is a provenance date, not a service verification date. Birth/death locations are not office geography; education `degree_year` is not a full graduation date.

## Identity and relationship handling

Keep the native source ID and name for alias profiles, with a separately labeled target link; do not redirect or merge by name. CourtListener person IDs, legacy `fjc_id`, and FJC `nid` are different namespaces. The supplied SQL schema confirms that `positions.appointer_id` references another **position**, whereas `predecessor_id` and `supervisor_id` reference people. The importer correctly uses the position-to-person bridge for appointers. Prefer a recorded job title when present; use a neutral label and retain the raw role code when a mapping is unknown. Preserve the source's inferred-value flag on each affected position.

## Importer review

The reviewed importer preserves raw strings, uses the source's backslash-escape CSV dialect, checks hashes before and after import, and validates native keys and deferred foreign keys. It writes into a new database and publishes the readiness marker last. The no-op `already_verified` path now also verifies the ready-bound summary and validation hashes, fixing the early review finding. The adapter now rejects malformed receipt containers, missing or failed FK/FTS proofs, unknown schemas, and disagreement with pinned table counts. The importer owner reports eight passing importer tests, including a tampered-receipt fixture.

## Education follow-up and final tests

A separate bounded read of the 12,777-row education table is recorded in `education_semantics_review.json`. `degree_level` is a broad category: `ba` includes B.S., `ma` includes A.M., and `llb` includes B.L. The adapter now displays the recorded `degree_detail` verbatim when present; it uses a broad label such as “Bachelor's degree” when detail is absent. Both original fields remain separately available.

All **25 independent tests passed in 0.502 seconds** on September 18, 2026 at 23:48 UTC. The suite covers date precision, missing dates, recorded/inferred role evidence, exact award details, alias identity, distinct people with identical names, SQL parameterization, read-only connections, receipt rejection, and real-snapshot counts and examples. Three tests query the published snapshot read-only; the remaining tests use helpers or disposable fixtures. No tests write to the live archive. `adapter_review_verification.json` binds the passing result to the reviewed source-code and readiness-marker hashes, and `test_people_review.log` records each assertion group.

Run the independent suite with Python 3.11+:

```text
python delivery/archive-directory/test_people_review.py
```

This review does not attest to completeness, source accuracy beyond the recorded semantics, current service, or identity matches with the existing judge corpus. No network requests, portrait downloads, entity merges, or main-directory rebuilds were performed by this reviewer.
