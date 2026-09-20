# Latest checkpoint — CourtListener biographies are now browsable

Read `reports/people_source_integration_20260918/NEXT_RUN.md` and its live validation
receipt before the older audit handoff. The separate source layer is integrated at
`#people`: 15,797 non-alias people plus 394 optional alias records, with career and
education pages. Do not repeat this import or add those rows to consolidated judge
counts. No identity merges, new portraits, county captures or focused publication
were performed in the 23:38 UTC heartbeat. Next: a bounded PA portrait pass or the
KY/TX county registry overlay, with source/identity gates preserved.

---

# Earlier checkpoint — broader local audit and workflow improvement

Read `sources/local_deep_audit_20260918/NEXT_RUN.md` and its linked evidence before
continuing. The broader scan found substantially more judge/county/law material.
Prioritize reviewed local adapters and targeted portrait queues; no new sources or
portraits were imported during that audit. Its larger bounded trial caps supersede
the three-browser-profile limit below, while existing source/host controls remain.
The new title-only refresh avoids a full metadata rebuild for qualifying labels.

---

# Earlier checkpoint — September 18, 22:13 UTC heartbeat

Read `heartbeats/20260918T2213/verification.json` and the adjacent county `HANDOFF.md`
before older receipts. This pass added 24 verified official PDFs (16 native texts,
eight text gaps) and three Trellis profiles: Jasper, Jeff Davis and Jefferson, Georgia.
The directory pending projection now has 301 records: 220 county resources and 81 law
resources. Six DOM-based Trellis profile snapshots are registered in two immutable
batches. Combined Trellis coverage is 1,438 / 2,508 observed URLs (57.34%); 1,070 remain.
These additions do not change the focused published totals or the 14 judge portraits.

The final small directory rebuild also cleaned 37 display titles across the two
backfill roots using exact observed source labels, literal filename spacing or removal
of producer prefixes. Original title metadata stays preserved, including empty values;
all four Butler revision dates, order versions and Garrard's DRAFT #8 remain visible.
Do not replace legal-status metadata with a cleaner but less informative label.
Title tests are in `sources/directory_pending_20260918/test_display_titles.py`.

One minor UI follow-up was observed: the reader shows a Full text link even when it
states no readable text is saved. A future small frontend pass can condition that
link on actual text availability; keep the original/PDF and publisher links available.

The new official root is `corpus/county_local_backfill_20260918T2213`. Its collector
exited and OS lock is released. **One Nelson County URL is still pending**, subject
to the saved 60-second robots crawl delay; the Monona timeout remains terminal.
At the next heartbeat inspect fresh processes/locks, then resume that existing queue
without ingestion using the one-page/90-second command in its county HANDOFF.md.
Do not rerun that frozen `run_batch.py`, which deliberately refuses an existing queue.
Only prepare another packet after the pending URL has an outcome and the source is stable.

The four remaining profiles in this small browser selection are in
`heartbeats/20260918T2213/trellis_remaining_observed_4.jsonl`. Deduplicate against the
catalog and **all** browser manifests before selection. Use at most three ordinary
sequential profile navigations, stop on access barriers, and freeze a new timestamped
batch. `delivery/archive-directory/server.py:TRELLIS_BROWSER_BATCHES` is the explicit
registry; ingestion now verifies validation receipts, artifact hashes, metadata
bindings, county identity and cross-batch uniqueness before replacing the directory.

The new official roots are visible as qualified pending material. A future focused
publication must explicitly register both backfill roots in the reviewed publication
scope/locks and the county/focused package adapters, then use the existing locked
seven-step workflow. Do not silently treat pending validation as full publication.
No large Open US Law import/index or unchanged reading-view sweep is needed.

---

# Earlier checkpoint — portraits, navigation and continuing county backfill

The latest user request combines better judge portraits and production-quality MVP
navigation with ongoing county/Trellis gap backfill. It supersedes the earlier blanket
county-collection pause. Read REQUEST.md first and current verification/agent receipts
in this folder. Do not turn the request into an unrelated general URL crawl.

## Existing library

Keep the ready 2,978,617-record Open US Law snapshot, original Seeger library, recovery
overlay, source-bound reader and conservative judge entities. Do not rerun the bulk
import/index or full hash sweeps. Full national current-law completeness remains false.
The local interface is http://127.0.0.1:8769/.

The September 18 pass is integrated: 14 verified portraits, court/availability filters,
26 new official county PDFs and three nonoverlapping Trellis profile snapshots. The
directory has 277 qualified pending records (196 county + 81 law) plus three separate
DOM-based county profiles. Its main index was refreshed once; the bulk law index was
reused. See verification.json for tests and browser evidence.

Judge filtering now supports exact saved court affiliation, state, court system,
available profile content, name query and ordering. Court labels do not certify current
service. County availability filters distinguish saved local resources, saved county
information and no saved local resources; they do not certify substantive completeness.

## Portraits

Use `sources/judge_portrait_backfill_20260918/` as the new identity-evidence layer.
The original five portraits and original source discovery records stay preserved.
Only accepted evidence-supported links may be added to the presentation manifest.
Preserve official biography/education/service/native-ID bridges and rejection of
competing candidates. Do not use facial identification or name-only automatic matches.
Serving a portrait verifies its registered content hash; changed bytes fail closed.

The known local pack's 14 portraits are now resolved. A further bounded scan inspected
1,345 saved profile captures and 125 named evaluation PDF pages without finding usable
additional portrait references. Other profiles still need new source images. Do not
rescan the same captures every heartbeat. See remaining_source_opportunities.json in
the portrait backfill folder.

## County continuation

1. Inspect fresh process and OS lock evidence, current source queues and the county
   receipt in this folder. Never duplicate a live collector or reingest a reviewed packet.
2. Existing county-local and Washington frontiers were exhausted before this pass.
   Barriers/errors/redirects remain terminal until their conditions change.
3. New official county documents must come from exact observed court/clerk/rule/form
   links with county evidence. Preserve existing robots and per-host pacing. Prefer
   substantive source bodies and original files over administrative pages.
4. A fresh signed-in Chrome visit reached the Cocke County Trellis profile. Continue
   only measured county-profile gap work through existing authenticated browser access.
   Case fields showed View Pricing; do not infer full document access, export credentials,
   or route around provider/direct access blocks. Use observed profile URLs and reconcile
   captured profiles with the actual Trellis inventory, not all Census counties.
5. Bound each continuation to finite work. Keep current county receipts and next-action
   instructions authoritative for exact invocation and remaining URLs. Newly saved data
   stays pending until validated publication; queue exhaustion is not national completion.
6. After a stable collector checkpoint, use the existing locked publication workflow
   if there are accepted new captures. Refresh pending projection and directory metadata
   only when underlying data changed; retain recovery and reader hash gates.

The 30-minute heartbeat continues bounded useful work, reports meaningful additions or
real blockers, and stays quiet when unchanged. Do not repeat failed requests, old builds,
unchanged validation sweeps or source discovery solely to show activity.
