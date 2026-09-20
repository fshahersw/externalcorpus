# Source directory: links to existing saved archive records (September 19, 2026)

This pass turned the 588 exact saved-URL candidates from the litigation source review into
validated links inside the live MVP, without downloading anything. Source references at
`http://127.0.0.1:8769/#sources` now show a second, separately labelled availability,
**Saved in archive**, alongside the pilot's **Saved content attached**.

## What was added

| Measure | Value | Meaning |
|---|---|---|
| Source references linked | 554 | Entries with at least one validated link to an existing saved record; exact URL match only |
| Directory records linked | 370 | 153 published focused-release captures, 214 imported Seeger originals, 3 federal-supplement captures; every original re-hashed against its recorded SHA-256 |
| Retained captures linked | 204 | Successful canonical captures (official_courts roots) that were never selected for the published release; raw and text re-hashed, served only as verified bytes |
| Judge profiles linked | 104 | Consolidated profiles whose source observation came from three court judge-directory pages (Alaska 71, Delaware Family 19, Delaware Chancery 14) |
| Final-URL matches | 6 directory + 9 retained | References citing the address a capture was redirected to; labelled as redirect matches with the requested address retained |
| Excluded candidates | 4 | 2 official_laws final-URL matches outside the registered asset roots, 1 canonical capture with empty indexed text, 1 zero-byte original (Ballotpedia) that the canonical index still marks searchable |
| Pilot captures | 32 | Unchanged; no overlap with the 554 linked references |

Reconciliation with the review: 554 linked + 32 pilot = 586 of the 588 candidates are now
reachable in the MVP; the remaining 2 are the empty-text and zero-byte exclusions above
(the two unregistered-root cases were not part of the review's 588 because that review
did not count final-URL matches into the directory).

These are links to records already saved by earlier collections. They do not establish
that a publisher page is available today, do not make the source map current, and do not
imply anything about references left unlinked.

## Where it is visible

- Filter **Saved content → Saved in archive** (`#sources?has=archived`, 554 results); card
  badges show the number of linked records; the summary bar links both availabilities.
- Each source detail page has a **Saved records in this archive** section: publication
  status, collection, saved date, review flags, redirect notes, and buttons to open the
  saved record, original file or saved text. Judge-directory pages list the linked judge
  profiles with a show-all control.
- Retained captures are served from `/source-assets/archive:<version>/original|text`
  with the same hash-verified, sandboxed delivery as the pilot captures.

## Implementation

- `sources/source_archive_links_20260919/build.py` builds `links.jsonl`, `excluded.jsonl`
  and the `validation.json` gate (source-catalog hash, directory build receipt, canonical
  index validation, asset roots). `test_build.py` covers publication classes, soft-404
  rejection and capture-date evidence.
- `delivery/archive-directory/source_archive_links.py` loads the manifest fail-closed,
  re-checks every directory-backed target against the live database per request, exposes
  path-free records, and serves retained captures only as verified bytes.
  `test_source_archive_links.py` covers the gate, root confinement, live re-check,
  tampering and unknown tokens.
- `source_directory.listing()` accepts `archive_counts`; `has=archived` is a third
  availability with its own facet count and summary figure.
- `server.py` wires the adapter into `/api/sources`, `/api/source` and `/source-assets/`.
  `app.js` and `styles.css` add the filter option, badges, summary links and detail section.

No main database, judge projection, bulk index or focused publication was rebuilt. The
server was restarted with `restart.ps1`; `deployment.json` records the process change,
`live_verification.json` the 19 end-to-end checks (39 requests) and `browser_qa.json`
the interface checks at desktop and 390px widths.

Tests: `test_source_archive_links.py` (6), `test_build.py` (3), `test_source_directory.py`
(14, including the new availability test), the unchanged capture-pilot suite (15), the
API-context and capture adapters (17), explore/evidence/navigation/library suites (35)
and the 19-test HTTP suite all pass. Running the whole `delivery/archive-directory`
folder (172 tests) also surfaces two pre-existing stale expectations in `test_mvp.py`
(10,669 judges and 14 portraits, versus the 10,698 profiles and 43 portraits integrated
on September 19); they are unrelated to this change and were left for a separate fix.
One HTTP test errored only while two test runs hit the server concurrently and passes
alone.

## Also in this pass

- The server had crashed before this session; it was restarted and verified. The previous
  instance's parent process no longer existed, so it was most likely terminated with its
  launcher session; no application error was logged.
- `Downloads/registry_v06_1.jsonl` was reconciled against the preserved registry: identical
  in all 9,348 rows and 23 fields (`registry_jsonl_reconciliation.json`). Nothing imported.
