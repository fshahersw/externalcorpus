# New live update — September 19, 00:11 UTC

**29 Pennsylvania official profiles and portraits are now live**, bringing the
judge presentation to 10,698 profiles and 43 installed portraits. Clear Judge
profiles / Historical biographies navigation and a full UI/data Refresh action
are deployed. All 43 live image responses matched verified saved bytes; 14
deployment checks and 15 overlay regression tests passed. The main document
catalog was not rebuilt. See [NEXT_RUN.md](NEXT_RUN.md) and
[deployment_verification.json](deployment_verification.json) for the current state.

The matrix below is the retained **before-update audit**, not the new portrait count.

# What was live at the initial audit on localhost:8769

Fresh read-only verification succeeded: **15 checks across 39 localhost requests**, including real document and image responses. The current `app.js`, `styles.css`, and `index.html` responses matched the files on disk byte-for-byte. See `live_verification.json` for the exact UTC interval, request timings/hashes, assertions, and point-in-time limitations. `audit_live.py` reproduces this bounded check; it does not import, restart, edit sources, or scan the whole corpus.

| Feature | Live now | Important scope |
| --- | --- | --- |
| Laws and rules | Yes | 16,454 records in the validated focused publication, plus separately identified later additions and imported collections. This is not all state law. |
| Open US Law | Yes: 2,978,617 rows / 229 files | The New York statute filter returned 40,140 rows and a readable saved statute. Dated v2026.08 snapshot; historical/repealed material and missing source links remain qualified. |
| Seeger collection | Yes: 18,360 records | Includes original documents and derived provisions. 384 text recoveries are integrated into their original record IDs. |
| Readable copies | Yes: 34,545 nonempty cached copies | 451 cached records remain empty. These are presentation derivatives, not new source records. |
| County directory | Yes: 3,144 inventory entries | 568 counties have published or pending local-resource associations; 563 have published local resources. Inventory does not mean all documents or filings are saved. |
| Newer county/law downloads | Yes: 301 browsable records | 220 county and 81 law resources are displayed as **awaiting publication**. They are not included in the older 16,454-record publication total. |
| Trellis browser backfill | Yes: six profiles | Two registered batches, with eight export links. Saved profile DOM/text, not complete case-file downloads. |
| Consolidated judge directory | Yes: 10,669 profiles | 5,942 have details; 708 source-bound analysis records. This is not a census of current judges. |
| Judge photographs | Yes: 14 | All 14 image URLs returned the exact manifest and local-file bytes: 137,312 bytes total. |
| Historical biographies | Yes: 16,191 source rows | 15,797 non-alias entries by default, with 394 optional aliases; 51,291 career and 12,777 education records. Separate from consolidated judge counts. |
| Curated collections | Yes: four collections | The MDL collection describes 1,612 saved PDFs but offers 24 browsable previews. A real preview PDF download passed its manifest hash. Other collections preserve their own reference/preview scopes. |

## Reviewed material that is not deployed as content

- The 29 Pennsylvania judge portrait references are an audit queue, not 29 installed photos at this checkpoint. The parent is reviewing a later portrait pass separately.
- CourtListener's 1,230 photo flags are availability hints; they are not downloaded portraits or local image URLs.
- The 374-row Kentucky/Texas court-access registry and 1,619 Illinois section-code candidates remain audit findings, with no corresponding live adapter in the inspected registry.
- The latest queue summaries report 125 Arizona URLs and one county URL still pending, alongside terminal errors. These counts do not prove a collector process is running. Full national laws, filings, county documents, and judge analytics remain incomplete.

## Concrete presentation gaps

1. The main directory build time remains September 18 at 22:32 UTC. Historical biographies were added through a separate adapter after that time. This is not an overall deployment timestamp.
2. Historical biographies are live at `http://127.0.0.1:8769/#people` and through a link on the Judges page, but are absent from the sidebar and the Sources dataset list. Their discoverability is weaker than their actual deployment state.
3. Trellis backfill item quality text still says “awaiting directory integration,” although the profiles are already indexed and live. That phrase is stale; it does not indicate missing content.

The parent is handling UI/browser review separately. This check verifies serving, API behavior, selected delivered bytes, manifests, and presentation counts; it does not independently rehash large source databases or certify full corpus completeness.
