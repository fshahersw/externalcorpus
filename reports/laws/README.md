# Official-law jurisdiction coverage

This **offline snapshot, 2026-09-13 12:31:33–12:32:09 UTC**, reconciles all 50 states plus DC across the original official-law map/captures, law-page queue, recovery, Nebraska chapters, completed DOCX/Word XML/EPUB derivatives and saved PDF/OCR coverage. It excludes Trellis and the separate court/county collections. No fetching, retrying, OCR, indexing, source-manifest edits or worker changes occurred.

`jurisdiction_coverage.json` contains jurisdiction totals and **154 jurisdiction/category rows**. The CSV provides their scalar counts. The original map has 153 slots: statutes and court rules for 51 jurisdictions, constitutions for 50 states, and DC's Home Rule Act. A separate observed Vermont legislative-rules category adds the 154th row.

| Deduplicated across this snapshot | Count |
|---|---:|
| Observed resource URLs | 10,670 |
| URLs with accepted saved downloads | 7,976 |
| Unique downloaded payload hashes | 7,926 |
| URLs with verified nonempty text artifacts | 7,929 |
| Verified completed document parsers: DOCX / Word XML / EPUB | 48 / 75 / 1 |
| XML body or EPUB reading-order coverage checks | 76 |
| Selected OCR pages completed / required | 515 / 515 |
| Sparse/other PDF pages flagged for review | 1,254 |
| Categories with no downloads / no verified nonempty text | 14 / 24 |

**Downloads, searchable text and full legal coverage are different measures.** Text verification reuses the production index's successful hash validation and checks that current file sizes/mtimes still match its fingerprints; all checked fingerprints matched. That index completed at 11:46:22 UTC, so later Arizona downloads are retained as downloads without being prematurely called verified text. No blanket payload rehash was repeated. Full legal-text correctness is unknown, represented by `null`; body/spine checks establish the parser's stated scope, with recorded formatting/revision limits. Whole-state and whole-category completeness are **not established anywhere**, and expected corpus totals remain unknown.

URLs retain query order and path spelling; only host/scheme casing and fragments are normalized. Payload/text hashes deduplicate byte-identical artifacts. Derivatives attach to their parent resource rather than increasing download counts. Three Colorado ZIPs contain 144 legal members already hash-matched to saved standalone files; their containers do not count as new member documents. Category attribution preserves the original source/seed context and does not certify a discovered link's content category. Per-category/state totals can overlap; use the global deduplicated totals for archive-wide counts.

Important retained gaps include:

- **613 pending URLs with known access barriers:** 566 South Carolina cached robots denials, 39 Illinois blob-storage robots-401 pauses and eight Hawaii target-403 pauses. Another 17 Arizona title URLs were pending under the 120-second pace. The underlying queue records were not changed.
- **Arizona:** five ancillary PDFs and 31 title/article navigation captures are explicitly separated. The title listings are not statute bodies. The saved constitution entry contains article headings and an outdated compilation notice; only its preamble body is identified, while 29 observed article redirects remain uncollected. Its saved constitution notice references the session convening in January 2022. The saved statute notice references the 57th Legislature, 2nd Regular Session, a subsequent update after the session convening in January 2027, and compilation for legislative drafting. Exact statements and hashes are retained.
- **Other sources:** New York has no accepted downloads in these audited law collections. Connecticut court rules, DC court rules, and several other constitutional/rule source slots retain explicit access, transport or source errors. Every affected category and exact URL appears in the JSON and `resource_gaps.jsonl`.
- **Editions and extraction:** the Iowa EPUB identifies itself as **2022 Code of Iowa**; its saved MOBI is unparsed and is not assumed equivalent. Pennsylvania XML generation statements and other observed titles, retrieval times and HTTP modification dates remain attached to their sources. Such dates do not establish current law. Completed selected-page OCR does not certify transcription correctness.

`resource_inventory.jsonl` provides URL/capture/text hashes, source contexts, source entries, observations, content-role labels and derivative/OCR evidence. `resource_gaps.jsonl` lists unresolved observed resources. `edition_observations.jsonl` retains dates/titles and the Arizona statements. `source_map_snapshot.json` and `input_evidence.json` preserve the map, input hashes, read-only database snapshot fingerprints and index-verification basis. `validation.json` records the reconciliation checks. All downloaded records without direct content review remain explicitly marked for review; empty bounded queues do not prove exhaustive law enumeration.

The local report can be refreshed with `python reports/laws/reconcile.py`. It writes only this report directory and reads each SQLite database in its own read-only transaction. Live collection may advance between those sequential snapshots.
