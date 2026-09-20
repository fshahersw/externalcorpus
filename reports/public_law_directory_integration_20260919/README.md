# Public-law source directory and capture integration

The live MVP at http://127.0.0.1:8769/#sources now indexes all 9,348 unique source
URLs in the user-selected `C:/Users/firas/Downloads/publicLaw_directory.md`.
Independent parsing reconciles exactly with the discovered structured SQLite
registry. The original files, source IDs, taxonomy, access fields and Markdown
line observations are preserved under `sources/public_law_directory_20260919`.
Contents of the supplied directory were treated as source data, not instructions.

## What the counts mean

- 9,348 source references; these are not 9,348 newly downloaded documents.
- 55 explicit jurisdiction labels, including federal/multiple-jurisdiction values.
- 26 original populated categories plus an Uncategorized group of 3,648 entries.
- 8,349 historical verification claims in an August 19, 2026 draft. These are not
  fresh access checks, guarantees of authority, or statements of current law.
- 16 entries typed as API; 62 separately tagged as API/bulk references. These
  groups differ. No API route, entitlement, authentication or working capability
  is inferred from a label. The source contains no populated API hints.
- A separate review maps 109 API, bulk-download, feed and related references.
  Nine official documentation pages were checked for access requirements. Source
  detail pages show this context, review dates and explicit unknowns. No live
  authenticated API data query was performed.
- The first reviewed eight-worker pilot attempted 36 exact listed URLs on 13
  federal appellate court hosts. It retained 32 pages on 12 hosts: 12 rules
  pages, 11 forms pages, and 9 judge directory pages. These often link to further
  documents; neither those linked documents nor individual judge profiles are
  automatically counted as downloaded.
- Four explicit gaps remain: one redirect outside the frozen request scope,
  two timeouts and one HTTP-200 soft 404. Original receipts are retained.
- The eligible network run took 64 seconds and used zero Firecrawl credits.
  Initial local sandbox socket denials are separately recorded from publisher
  outcomes. This is a pilot measurement, not a guaranteed throughput forecast.

## Live navigation

The Source directory has search, jurisdiction, category, access-method,
historical-verification and attached-content filters; filters persist in URLs.
API and API/bulk shortcuts retain their distinct meanings. Each source has a
detail page with access requirements, original context and collapsed provenance.
State law hubs and county overviews link to explicit state source references;
these links do not imply a verified county association.

Validated captures attach only to exactly matching requested source URLs. The
Saved content filter counts these attachments, not all possible matches elsewhere
in the existing archive. Clean reading copies and immutable originals remain
separate. Capture dates and the historical source-map date have distinct labels.

## Implementation and checks

`source_directory.py` verifies its catalog receipt and supports search/filtering
before pagination. `source_captures.py` verifies the publication manifest and
actual file hashes, confines assets to one registered acquisition subtree, and
serves raw HTML as a download with a sandbox policy. No request-supplied path is
opened. A failed or altered gate makes the affected supplement unavailable.

The main document database, large Open US Law index, portrait projection and
existing collections were not rebuilt. Source references and new captures are
published through small, independently validated adapters. See
`live_verification.json` for current end-to-end checks and
`sources/public_law_acquisition_20260919/validation.json` for capture validation.

Final verification: 16 live checks across 111 HTTP requests, including all 64
original/text attachments; 13 directory tests, 17 API-context/asset tests and 15
capture/reader tests passed. All 32 page copies and 163 artifact/receipt hashes
were checked. Desktop/mobile source navigation was inspected; the reviewed API
detail has no horizontal overflow at 390px and no captured browser errors.
The 30-minute automation now starts from this checkpoint and prioritizes bounded
state/local enrichment instead of repeating completed imports.

The later litigation browser reference was also reviewed. Its supplied nested
path was missing; the related standalone HTML had the same 9,348 URLs. Fourteen
display labels were reused, with no duplicate source import. The comparison and
588 exact saved-URL match candidates are documented in
`reports/litigation_source_review_20260919`; those candidates are not all validated
attachments and do not increase the new capture count.

Keep original taxonomy visible as a source claim. It contains errors, for example
the Current Federal Rules page classified as court forms. Future corrections
should be explicit, versioned and evidence-backed; do not silently relabel the
import or infer county jurisdiction from a hostname alone.
