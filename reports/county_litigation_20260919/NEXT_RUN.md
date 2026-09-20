# County litigation resources — active September 19, 2026

Current user direction supersedes the earlier portrait-focused follow-up and Firecrawl credit reserve: use the saved Trellis county profiles and other saved county sources to discover, download, extract and standardize useful official county/court resources across states. The user explicitly authorizes using the remaining Firecrawl balance; no credit purchases or overages are authorized.

Project: `C:/Users/firas/Downloads/SCRAPE`. Live MVP: `http://127.0.0.1:8769/`.

## Data flow

1. Reuse saved sources and their exact observed links. `sources/county_litigation_20260919` owns the offline inventory, standard resource schema, classifier and publication. `seeds.jsonl` supplies source-bound discovery work.
2. `sources/county_litigation_firecrawl_20260919` owns the finite provider/direct-download frontier, costs, originals, extracted text and checkpoints. The pilot passed acquisition review: 31 captures, including 14 original PDFs (255 native-extracted pages), for 17 credits. The broader phase is authorized and running; the old temporary 50-credit pilot limit is superseded. Never launch a duplicate worker or touch its actively written files.
3. Local parsers classify and clean saved content. Keep original bytes/representations and their SHA-256 evidence. Exact PDF/document downloads use local extraction where practical, avoiding paid per-page parsing. No navigation/case-link spam in the default reader.
4. Publish verified records into the county litigation supplement, read-only adapter and actual county UI. Preserve the main directory database, external agent's law/MDL layers and every frozen prior batch.

## Schema and quality

Types distinguish local rules, actual court forms, standing/admin orders, filing guidance, fee schedules, court information, public court contacts/staff, source directories and unknowns. Keep indexes separate from document bodies. Dates distinguish captured, published and explicitly effective; an access date cannot become a legal effective date. Draft/proposed status and unknown currency must remain explicit.

Source county association is not proof of court territorial applicability. Validate state/FIPS and observed county/court evidence; preserve statewide/shared-court scopes, historical geography and unresolved associations. Never turn a general government personnel page into court staff, recreational courts into judicial courts, election filing into court filing, or a directory's available-document flag into downloaded documents.

An LLM may propose labels or extract evidence from difficult pages, but cannot invent missing facts, dates or jurisdiction. Deterministic checks and exact source excerpts control publication. No legal advice or unsupported analytical conclusions.

`scripts/audit_county_litigation_20260919.py` provides independent read-only checks for manifest/asset integrity, confinement, FIPS/state consistency, classification/authority/date evidence and document MIME signatures. Its fixtures are in `scripts/test_audit_county_litigation_20260919.py`.

## Operation

Use existing DPAPI Firecrawl credentials only; never print or save plaintext keys or pass them in command lines. Basic public fetching, max five concurrent provider calls unless a fresh account check changes the allowed limit. No login bypass, CAPTCHA solving, proxy escalation, purchase, unchanged-barrier retries or duplicate requests. The previous 3,000-credit reserve is superseded by the user's latest explicit instruction, but spend only on relevant new work with per-run and total accounting.

Check process/collector locks and fresh progress before doing anything. Let an active worker own its queue and credit accounting. The 30-minute automation should validate/publish stable checkpoints, inspect yield/quality, and advance only eligible remaining work. Quiet unchanged progress; notify meaningful additions, completion, failures or required user action.

Restart only the verified 8769 server with `reports/corpus_upgrade_20260919/restart.ps1` after backend edits. Verify live resource filters, county assignments, clean reader text and original/text downloads. Record exact downloaded/parsed/published/linked/held/gap counts separately; do not claim a complete nationwide county corpus from a successful finite batch.

## Worker and next publication

The approved hidden collector was launched at 2026-09-19T10:14:26Z as PID 13840. Treat that PID as a historical observation: verify its command and `worker_launch.json` before any process operation. It runs at five workers, one request per host, two-second host pacing, depth at most two, county frontier cap 250, maximum 6,000 resources or one hour. Its 4,000-request ceiling was clamped to the fresh 3,990-credit balance; no reserve or overages. Direct original-document work can continue when provider credits reach zero.

- Current source-bound seeds: `sources/county_litigation_seed_review_20260919/seeds.jsonl`, SHA-256 `71b25436db204c3934392aebbc4c702058c7b95ea51268b3697624a1f3855a15`: 3,239 URLs associated for discovery with 714 counties in 46 states. Parent bytes and exact links were reproduced. This is a finite candidate queue, not verified county applicability or comprehensive coverage. Existing barriers, unrelated legislative/quorum-court content and obvious other-county URL conflicts were excluded.
- `sources/county_litigation_firecrawl_20260919/summary.json` is current acquisition progress. `latest.json` points to an immutable, hash-verified checkpoint; use only that checkpoint for normalization. Do not read the live changing JSONL during publication.
- The collector writes a checkpoint every 100 completed attempts or five minutes. Publication is separate. Never claim its latest saved count is already in the UI.
- Graceful stop: create `sources/county_litigation_firecrawl_20260919/STOP_REQUESTED`; the worker drains inflight requests. Do not terminate it routinely. Five requests interrupted during the initial scope tightening remain `uncertain_interrupted`; they must not be automatically retried.
- When the worker has completed, inspect its final status/cost and only then ingest additional reviewed seeds or restart it. Do not reset blocked/uncertain URLs just to force completion.

For a new checkpoint, run `sources/county_litigation_20260919/build.py --checkpoint <absolute checkpoint directory>`. This reuses all four existing saved county-local collections plus the checkpoint. Then run `scripts/audit_county_litigation_20260919.py` and `scripts/verify_county_litigation_live_20260919.py`. The data adapter reloads a changed valid gate without restarting the server; backend Python edits require the verified restart script. Preserve source originals and all prior snapshots.

The local parser is `scripts/county_litigation_sections.py`; it binds document outlines, header date observations and opening status observations to exact reading-copy offsets and a text hash. An issued date is not an effective date; an effective date does not prove current force. Old PDF metadata may contain authors, GUIDs or stale dates, so use publisher link labels/captions with provenance.

Remaining quality work: reprocess older PDFs with missing native text using local OCR where suitable; retain the originals and explicit text-gap status meanwhile. Resolve county associations only from strong evidence; old crawl-context FIPS alone is insufficient. Expand useful rule/form/order/fee indexes into their exact linked original documents using the separate child-seed helper; most broad unreviewed hosts intentionally do not autoexpand. Document downloads and local parsing do not need provider credits. Continue to distinguish rule bodies, indexes, change notices, prefaces, repealed material, blank forms and actual filed pleadings.
