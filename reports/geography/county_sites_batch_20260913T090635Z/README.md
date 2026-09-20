# New observed county-website entry batch

Prepared offline on September 13, 2026: **340 county/website associations, representing 334 new URLs, 340 Census GEOIDs, 34 states, and 333 exact hosts**. This directory is a new snapshot. The previous `reports/geography/county_sites_batch` and all active collection databases were left unchanged.

The catalog refresh completed at **09:06:25.842794 UTC**, processing 221 additional saved provider files without parsing errors. It contained 752 county profiles. Geography reconciliation at **09:06:41 UTC** produced 740 exact Census matches, two ambiguous profiles, and ten historical or special court scopes. Its 723 matched website associations represented 687 unique URLs before exclusions.

The preparation excluded **382 associations already enqueued or fetched in a corpus database**, plus **one association on a persisted paused/cooling host**. All statuses were excluded, including failed, inactive, and offline validation queues; this batch never implicitly retries an old URL. Five workspace `corpus.sqlite3` databases supplied 15,664 unique excluded URLs. Saved official-source attempts and captures supplied another exclusion set of 4,896 URLs. `excluded.jsonl` gives each exclusion and evidence. Canonical URL matching preserves HTTP/HTTPS and www/non-www distinctions; host-pause matching conservatively groups www and bare-host variants.

Every included URL came from an actual saved Trellis Website-field href and a reviewed exact Census-name match. The raw displayed value, link target, state/county FIPS, match method, and all provider evidence paths remain in each seed. The provider response SHA256 was checked against the saved catalog. Geographic ambiguities are preserved in `inputs/county_ambiguities.jsonl`; historical Connecticut counties and other non-Census court scopes remain in `inputs/non_census_jurisdictions.jsonl`. No fuzzy match, historical crosswalk, inferred CISA entry URL, or guessed website is introduced.

All 340 associations remain labeled `trellis_reported_government_site` with `site_authority_verified=false`. Census validates the county-name association, not website ownership or court authority. Namespace signals are 107 `.gov`, 71 state/local `.us`, and 162 other-domain associations; those signals do not change the authority label.

The exact source bytes used for reconciliation are retained under `inputs/`. `input_manifest.json` gives each original path, copied snapshot path, timestamp, and SHA256. Read-only database snapshots and an official-source file-hash inventory preserve the deduplication evidence. `summary.json`, `state_counts.json`/`.csv`, `decisions.jsonl`, and `artifact_hashes.json` describe this batch. Multiple county contexts may share one URL; the generic crawler stores those contexts while downloading one resource per canonical URL.

`config.json` reuses the existing county-entry conventions: exact hosts and per-seed host scopes, `follow_links=false`, `max_depth=0`, three workers, two-second host pacing, one bounded automatic retry, a 16 MiB response cap, robots/access checks, and a 10 GiB free-disk guard. These are entry pages; subsequent legal-document links need a separately reviewed acquisition queue.

Import into a **separate** collection using the batch config:

```powershell
python 'C:\Users\firas\Downloads\SCRAPE\pipeline\corpus_crawler.py' --root 'C:\Users\firas\Downloads\SCRAPE\corpus\county_sites_delta_20260913T090635Z' ingest --seeds 'C:\Users\firas\Downloads\SCRAPE\reports\geography\county_sites_batch_20260913T090635Z\seeds.jsonl' --config 'C:\Users\firas\Downloads\SCRAPE\reports\geography\county_sites_batch_20260913T090635Z\config.json'
```

The command only imports queue state and was not run by this preparation. If root instead adds these seeds to the existing active county collection, merge its existing allowlist with this batch's hosts before ingestion; **do not replace the active collection config with this smaller batch-only config**. Root controls launch and shared host pacing.

The snapshot has zero overlap with its recorded database and official-source exclusion sets. Other collections can advance after preparation, so reconcile exclusions again before a delayed import. Preserve this delivered snapshot when creating a later batch. Exhausting these entry URLs would not establish complete county or legal-corpus coverage.
