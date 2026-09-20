# Public-law directory API review and capture pilot

Delivered **32 usable court-page captures across 12 hosts**, plus **109 explicit API, download, feed, and related documentation references**. The supplied registry contains 9,348 records. Its 8,349 liveness-verified figure is the publisher's **August 19, 2026 claim**, not a fresh validation of every source.

## What was actually saved

The pilot selected 36 exact forms/rules/judge-directory URLs from the provided Markdown's federal appellate section (lines 23–132), across 13 hosts. It saved 12 rules/index pages, 11 forms/index pages and 9 judge-directory pages. These are the selected pages, **not all files or individual profiles linked from them**.

The authorized network run lasted approximately 64 seconds on September 19, 2026, 01:02:39–01:03:43 UTC. It used the existing collector, eight workers, shared host locks, at least two seconds between host starts, robots checks, no automatic retries, and no link following. Firecrawl credits used: **0**. The first sandbox attempt produced 36 local socket errors before HTTP; those receipts remain distinct from the publisher outcomes.

Four gaps remain: the CA7 judge URL is an HTTP-200 soft 404, CA9 forms redirects outside the frozen scope, and the two Federal Circuit pages timed out. Their receipts and any received bytes remain preserved. The soft 404 is excluded from the usable manifest.

`sources/public_law_acquisition_20260919/resources.jsonl` carries stable URL-based IDs, exact source/final URLs, titles, kinds, capture times, original/raw and native-text hashes, cleaned reading copies, receipt hashes, and source-file line attribution. `validation.json` is written last and binds the manifest. Main content selectors remove search/font/breadcrumb/site navigation; document links and relevant section links remain in readable Markdown. Published dates appearing in the source text remain intact. HTTP Last-Modified is recorded separately and **never treated as the law's effective date**.

## API findings that affect the next collection

The registry has 16 records typed as API and 62 assigned to an API/bulk layer, with overlap. Every `api_hint` is blank. Neither count is a count of callable APIs. The review maps 109 exact references: 5 explicit query URLs, 2 feed URLs, 1 explicit archive URL, 7 bulk directories, 61 documentation/service pages, 3 unverified service landings, 2 credential-registration pages, 2 filing-workflow pages, and 26 related references. Original source tags and caveats remain unchanged in `api_sources.jsonl`.

| Source | Practical next step and access finding |
|---|---|
| [Virginia Law developer page](https://law.lis.virginia.gov/developers/) | Strong state-law candidate: official JSON/XML services and PDF/CSV downloads are documented. Per-endpoint credential requirements were not established by the reviewed page. |
| [Vermont Legislature API](https://legislature.vermont.gov/docs/api/v1/index.html) | Requires a secret key obtained from legislature IT and HTTPS. The example uses Bearer authorization; the page also contains inconsistent Basic Auth wording. Resolve that during a small authorized test, not by guessing. |
| [GovInfo publisher API documentation](https://github.com/usgpo/api) | Uses an api.data.gov key and offers package discovery/retrieval suitable for incremental collection. Publisher modification times and publication dates are distinct. The README's agency-specific ceilings differ from the generic gateway defaults; actual response limits must govern. |
| [GovInfo bulk data](https://www.govinfo.gov/bulkdata) | Explicit bulk directory recorded in the supplied registry. Its files were not downloaded in this pilot. Select a collection and version before importing. |
| [Open States API](https://docs.openstates.org/api-v3/) | Requires a key. It covers state legislative information; its people endpoints are not a replacement for judge profiles. |
| [Regulations.gov API](https://open.gsa.gov/api/regulationsgov/) | Read endpoints require an API key header. They cover regulatory documents, comments and dockets. Comment submission endpoints are outside this collection task. |
| [eCFR API](https://www.ecfr.gov/developers/documentation/api/v1) and [Federal Register API](https://www.federalregister.gov/developers/documentation/api/v1) | Documentation pages were reachable but the extracted shells did not establish authentication or pagination. Those fields remain unverified; the registry's Federal Register registration tag is preserved as historical data. |
| [api.data.gov developer manual](https://api.data.gov/docs/developer-manual/) | Keys are private. The shared gateway's default is 1,000 requests/hour, with service-specific exceptions; DEMO_KEY has much smaller exploration limits. |

No API account was created, no credential was requested or exposed, no authenticated API data query was made, and no PACER login or case bulk acquisition was attempted.

## Verification and next scale step

`verification.json` checks all 32 captures and their five artifact classes, manifest/summary/gap hashes, source-URL binding, removed navigation controls, preserved example dates, soft-404 exclusion with original evidence retention, exact directory citations for all 109 references, and stopped collector runs. Nine focused tests cover tampering, incorrect source binding, partial/error responses, path escape, soft 404, content selectors, section links and published-date preservation.

The next useful scale increase is to batch **reviewed exact document links** from these pages, deduplicate them against saved URLs and hashes, and retain the same eight-worker host-coordinated collector. API/bulk providers should receive separate small adapters with documented pagination, checkpointing, and source-date semantics. Adding more workers to the same few hosts would not improve the permitted per-host pace. The 3,498 observed links in the crawler are evidence for selection, not an automatically approved frontier or a completeness claim.

Run the local checks with:

```powershell
& 'C:/Users/firas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m unittest discover -s sources/public_law_acquisition_20260919 -p test_export_pilot.py -v
& 'C:/Users/firas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' reports/public_law_api_review_20260919/verify_delivery.py
```
