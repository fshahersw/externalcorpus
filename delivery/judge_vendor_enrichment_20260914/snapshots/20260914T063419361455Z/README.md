# Source-specific judge vendor add-on

This staged add-on contains 2 source observations, 16 facts and 450 analyses. It has 1 vendor-published judge measures, 449 public UI preview measures and 0 historical illustrations. These classes are separate files and SQLite views. No identities are merged with the existing corpus; external matches and undownloaded reports remain candidates.

All native records, source URLs, capture dates, literal evidence and original-byte hashes survive in JSONL and SQLite. Original citations are copied into originals/ with an original-to-copy map in verified_originals.json. Facts and analyses can cite only originals explicitly owned by their source observation. Unknown cohort, method, period and counts remain null; scale maxima are separate from respondent counts. No outcome rate is independently calculated. Historical and preview data do not establish current judge performance.

Query by name with the bundled Python runtime: `python pipeline/query_judge_vendor_addon.py --database vendor_addon.sqlite --name Sabraw`. The query emits one report per source observation and separates record classes. Use --id for an exact canonical observation. No updates or network requests occur.

This snapshot is reviewable but not published. The builder requires a separate independent-review receipt bound to its exact manifest before updating latest.json. The previous sealed judge corpus is untouched. See SCHEMA.md, validation.json, component inputs and files.sha256.json.
