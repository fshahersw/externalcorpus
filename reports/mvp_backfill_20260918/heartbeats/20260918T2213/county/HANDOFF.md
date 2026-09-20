# County heartbeat result — 2026-09-18 22:13 UTC

Completed one new finite official-source packet in 121.5 seconds. The runner is stopped and its crawler OS lock is released. No prior queue was reingested; no pending projection, server, UI, main index or focused publication was modified by this task.

- **24 saved PDFs**, each with verified PDF signature, raw SHA, size, metadata/fetch identity and preserved county/source context.
- **24 distinct raw payloads**, none identical to a prior captured corpus payload.
- **16 nonempty native-text derivatives**; **eight empty-native gaps**. Text digests match capture metadata and decode as UTF-8. This does not certify transcription accuracy; replacement-character counts are retained.
- **One timeout**: Monona County area-service road-maintenance ordinance. No automatic terminal-outcome retry was requested.
- **One pending URL**: Nelson County electioneering ordinance. Its observed `robots.txt` specifies `crawl-delay: 60`; the 120-second dispatch budget expired just before its next shared host slot. The pacing rule remains in force.

Data root: `corpus/county_local_backfill_20260918T2213`.

Frozen packet: `sources/counties/backfill_20260918/batches/20260918T221703694232Z`. It contains 26 literal observed URLs from 13 county associations in six states: two administrative/local-rule documents, two public circuit docket/calendar PDFs, and 22 ordinances/resolutions. The original 30-URL draft is preserved. Manual review excluded one library-help PDF and three URLs disallowed by already-saved robots rules. The existing evidence reviewer verified 28 raw/link/context proofs on 13 parent pages.

County associations retain their original unverified source-context qualification. Circuit materials are not asserted to apply exclusively to the named county. Administrative-order versions may be historical/superseded. Month-only docket filenames do not establish the year, and dockets are not pleadings. Ordinance enactment/current force remains unverified.

Evidence is in `manual_review.json`, `job_receipt.json`, `validation.json`, `resources.jsonl` and `lock_release.json` in this heartbeat directory. `resources.jsonl` SHA-256: `88be601534cd053ef47234ce6fdd907e452986f17137f1d10275cb309ae526d7`.

Root can now include this stopped collection in the qualified pending projection and perform its coordinated directory update. This task did not publish it.

For a later heartbeat, first check processes and locks. The one still-pending URL can be resumed without ingestion using:

```text
C:/Users/firas/AppData/Local/Programs/Python/Python311/python.exe pipeline/corpus_crawler.py --root corpus/county_local_backfill_20260918T2213 run --max-pages 1 --max-seconds 90
```

That command leaves the timeout terminal and preserves host/robots controls. Do not rerun the heartbeat's `run_batch.py`: it deliberately rejects an existing queue. Further documents require a new timestamped observed-link packet and review; no legacy all-URL crawl should be restarted.
