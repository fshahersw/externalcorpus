## Setting this up on another machine

Git carries the code; the data (about 130 GB) is attached to the release `data-20260920` and restored with
`python bootstrap.py pull`. Start with [TRANSFER.md](TRANSFER.md). Current state of the work: `reports/corpus_upgrade_20260919/STATE.md`.

## Browse the local archive

Now available: [Historical biographies](http://127.0.0.1:8769/#people), a separate
CourtListener collection with name/court filters, career timelines and education.
It contains 15,797 non-alias people and 394 optional alias records; these are
historical source people, not additional consolidated judge identities. See the
[integration checkpoint](reports/people_source_integration_20260918/NEXT_RUN.md).

New: [broader directory audit and reuse plan](sources/local_deep_audit_20260918/README.md)
and [searchable discovery index](sources/local_deep_audit_20260918/INDEX.html).
The audit found additional judge, portrait-reference, county and law sources.
Its reports describe the discovery checkpoint; the integration checkpoint above
identifies what is now available. Portrait, county and law candidates still need review.

Open [Legal Archive](http://127.0.0.1:8769/) or launch `delivery/archive-directory/START.cmd`. See [the directory guide](delivery/archive-directory/README.md) for saved files, full-text search, counties, judges, federal sources and new downloads awaiting publication.

The personal MVP now organizes **Laws & rules, Judges, Counties and Collections**
into filtered lists and dedicated detail pages. Judge profiles open with professional
details and confirmed portraits; sources and technical metadata are tucked into
optional details. The default judge view shows **5,942 detailed profiles**, with all
10,669 conservative directory identities available through a filter. All 14 named
portraits in the local asset pack are linked through corroborated professional identity
evidence. Four curated collections reuse existing legal folders. Exact court filters,
county availability filters and removable filter chips improve browsing.

The two September 18 backfill passes added 50 official county PDFs and six Trellis
county profile snapshots; the latest pass contributed 24 PDFs and three profiles.
New documents are available with awaiting-publication labels; the validated
focused publication totals remain unchanged. Bounded collection continues every 30 minutes.

The September 18 enrichment adds the pinned **Open US Law v2026.08** export
(2,978,617 records in 229 checksum-verified Parquets) and **18,360 Seeger library
records** (11,194 originals plus 7,166 structured provisions). The bulk full-text
index is validated and searchable. These supplements remain distinct from the
earlier focused release.

Documents open in cleaned reading views, with original files, saved extraction
and provenance retained. **384 previously unreadable originals** now have recovered
text. **11,928 judge observations are organized into 10,669 conservative display
identities**, preserving biographies, facts, analysis outcomes and source records.
Ambiguous matches, historical legal statuses, missing links and text gaps remain
explicit. These counts do not establish unique current laws or nationwide completion.

[Current verification](reports/mvp_backfill_20260918/heartbeats/20260918T2213/verification.json)
· [Current continuation](reports/mvp_backfill_20260918/NEXT_RUN.md)
· [Earlier enrichment evidence](reports/enrichment_upgrade_20260918/verification.json)

# US legal corpus archive

The **[focused package](delivery/focused_legal_corpus/README.md)** was refreshed on 2026-09-18T16:50:18.240723+00:00. The official-only continuation has saved 3,885 response captures, including 3,661 with nonempty collector text and 182 verified offline document text derivatives. The package now contains 16,454 capture records and 15,837 distinct searchable texts.

All 3,144 Census county-equivalent rows are inventoried. Downloaded content remains partial; registered government agencies and candidate county associations remain explicitly labeled. The 30-minute continuation combines MVP improvements with small reviewed county-document and authenticated county-profile batches. Exhausted queues and unchanged access barriers are not restarted.

[Current official continuation](delivery/focused_legal_corpus/official_expansion_20260913/summary.json) · [Active scope and checkpoint](reports/remaining_resume_20260913/scope.json) · [Runbook](RUNBOOK.md).

| Location | Contents |
|---|---|
| `sources/trellis/browser/` | PDFs downloaded through the user's authenticated paid browser session, extracted text and provenance |
| `sources/trellis/discovery/` | Trellis coverage, state and rule entry pages and initial county URL map |
| `sources/trellis/counties/` | Saved public county-page responses |
| `sources/trellis/rules/` | State rule/code/constitution category pages |
| `sources/trellis/judges/` | Prior saved judge directories and related source pages; excluded from new acquisition |
| `sources/trellis/resume_20260913/` | Ordered county/law paid selection and its preparation evidence |
| `sources/trellis/catalog/` | SQLite catalog, CSV/JSONL indexes, links, county fields, case/judge/rule URLs, and extracted HTML/Markdown |
| `sources/official_laws/` | Primary statute, constitution and court-rule sources for 50 states plus DC; original PDFs, text and per-state coverage |
| `sources/official_courts/` | Census baseline, judiciary portals, county government domains, court/judge tables, public dockets and original documents |
| `corpus/official_law_pages/` | Continuing acquisition of official HTML law sections and additional originals |
| `corpus/official_law_recovery_pass_1/` | One additional attempt for 58 earlier failures, followed by 53 observed canonical Wisconsin PDF targets |
| `corpus/official_courts/` | Prior court-source captures, exact responses, extracted text and OCR |
| `corpus/county_sites/` | County government website entry pages with registry and observed-link provenance |
| `corpus/county_entries_resume_20260913/` | Bounded official county entry pass, captures and explicit access/failure outcomes |
| `reports/geography/` | Census reconciliation, explicit conflicts, website associations and county-domain inventory |
| `catalog/` | Unified SQLite full-text search, source URLs, capture versions and CSV/JSONL document manifests |
| `sources/open_us_law_20260918/` | Pinned publisher snapshot, verified Parquets, separate bulk full-text index, status/citation/source provenance and gap reports |
| `sources/seeger_import_20260918/` | Preserved court-library originals and exact structured provisions from the user-selected Seeger collection |
| `sources/seeger_text_recovery_20260918/` | Validated native Word/RTF and OCR derivatives attached to existing original identities |
| `sources/judge_entities_20260918/` | Conservative judge entity groups, all source memberships, fact claims and analysis records |
| `sources/reading_views_20260918/` | Derived readable content, hash-bound to source and selected text evidence |
| `delivery/archive-directory/` | Local browser interface, readable source views, grouped/source toggles, filters and downloads |
| `pipeline/` | Resumable scoped HTTP crawler and functional fixture tests |
| `reports/` | Aggregate status snapshots |

Search extracted content with `rg` against the source text directories. Query `sources/trellis/catalog/catalog.sqlite3` for URL and relationship inventories. CSV/JSONL exports are available beside the database. Dates and hashes identify captured versions; availability does not establish that legal text is current.

Use `python scripts/build_document_index.py search "summary AND judgment" --limit 20` to search across collections. `catalog/README.md` documents exact-phrase queries, historic versions, OCR derivatives and index validation.

[Requested scope](REQUEST.md) · [Continuation runbook](RUNBOOK.md) · [Crawler operation](pipeline/README.md)
