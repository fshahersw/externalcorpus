# Public judge vendor add-on

Published and independently validated snapshot: [20260914T063419361455Z](snapshots/20260914T063419361455Z/README.md). Two separate source observations, 16 professional/source facts and 450 source-reported measurements are available in JSONL, CSV and SQLite. All 62 snapshot files and 27 original receipts passed fresh checks; 443 rendered graph counts were independently compared.

Lexis Context's public Dana M. Sabraw preview supplied 449 measurements: five visible law-area counts, 116 motion-category counts, 228 reported outcomes, one separately labeled result-list count, 50 cited-opinion entries and 49 cited-judge entries. Missing outcomes and unknown periods/denominators remain null. These are preview-corpus measurements, not independently calculated performance rates. Cited people remain referenced names attributed to Sabraw's citation activity.

Lex Machina's public article supplied one publisher-reported measure: James Rodney Gilstrap was assigned 2,276 patent-related cases during 2023–2025. The underlying report and case list were not acquired. [Publisher article](https://www.lexisnexis.com/community/insights/legal/lex-machina/b/lex-machina/posts/patent-litigation-trends).

Full licensed feeds and gated report exports were not acquired. No identities were merged with the existing judge corpus. Older undownloaded report candidates are excluded from actual measures. Further vendor acquisition is paused under the user's renewed state-law/county priority.

Query the published database from the workspace:

```powershell
python -X utf8 scripts/query_judge_vendor_addon.py --database delivery/judge_vendor_enrichment_20260914/snapshots/20260914T063419361455Z/vendor_addon.sqlite --name Sabraw
```

[Schema](SCHEMA.md) · [Publication receipt](reviews/20260914T063419361455Z.json) · [Current pointer](latest.json) · [Context component](context/README.md) · [Lex Machina component](lex_machina/README.md).
