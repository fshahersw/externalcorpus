# Saved Trellis judge profiles

`normalize.py` creates evidence-backed profile reports from already saved public Trellis responses. It reads `sources/trellis/judge_focus_20260913/judges/*.json` and, when present, the initial `.firecrawl/judge-terry-l-bannon.json` probe. It makes no requests, uses no credentials, follows no links, and does not change original captures or shared indexes. Rerun it after each stable acquisition batch; `summary.json` identifies the exact snapshot.

The parser reads real HTML headings, biography paragraphs and About, Court Info and Career History tables. It handles duplicated mobile/desktop About values by reading the explicit label span and separate value cell. Every fact retains the original file/hash and a rehashed HTML substring with character offsets and literal text. Full source/scrape/cache metadata and hashes of decoded HTML/Markdown strings are retained separately from original-file hashes.

Names, states, courts, appointments, education and work history remain **Trellis assertions**. The parser does not certify current service or match people to official records. A county is reported only from an explicit county field or a single unambiguous county printed in a judicial Career History location; that latter basis is labeled and does not establish a current assignment. Conflicting or absent locations remain null. Source spelling and career dates remain literal; no tenure or demographic/ideology inference is made.

Dashboard/report links are an **observed-link inventory**, with access unknown to this offline parser. Preview links and promotional images are not metrics. Numeric publisher analytics are emitted only when a single analytics table row provides an explicit metric label, value, period and denominator. Incomplete numeric rows are retained separately for review. Publisher metrics are never relabeled as independent computations. Independent win/grant/outcome rates remain null because this parser does not build or analyze a decision-level case cohort.

Recent-case and document sections are not normalized as judge performance evidence. Their link counts and subscription placeholders are recorded only as limitations; no cases/documents are acquired. Access prompts in Biography are excluded from factual biography text. Missing fields, metadata errors and unrecognized structures remain explicit gaps or failures.

Run from `C:\Users\firas\Downloads\SCRAPE`:

```powershell
& 'C:/Users/firas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' delivery/judge_intelligence_20260913/trellis_profiles/test_normalize.py
& 'C:/Users/firas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' delivery/judge_intelligence_20260913/trellis_profiles/normalize.py
```

Optional `--input-dir` and `--probe` arguments select other existing saved files. No network or installation is required; the parser uses the Python standard library. The earlier Python311 executable was unavailable in the current sandbox, so the supported bundled executable is shown explicitly.

Outputs:

- `profiles.jsonl` / `.csv`: one record per unique original profile payload, including provenance, biography, direct fields and gaps. Multiple saved versions may represent the same publisher URL.
- `facts.jsonl` / `.csv`: literal, individually traceable facts and passages. Other About labels remain explicit publisher-labeled facts; no inference from them is made.
- `report_rows.jsonl`: report-ready profile records with supporting fact IDs and limitations.
- `dashboard_report_links.jsonl`: exact observed dashboard/report URLs and source evidence; access unverified.
- `reported_analytics.jsonl` and `unpromoted_analytics_candidates.jsonl`: complete publisher metric rows versus incomplete candidates; empty files mean no qualifying observations in this snapshot.
- `source_table_rows.jsonl`: original table labels/cells with source evidence, including duplicated mobile text for review.
- `gaps.jsonl`, `failures.jsonl`, `input_manifest.jsonl`, `summary.json`, `validation.json`, `files.sha256.json`: missingness, snapshot counts and fresh original/substring hash verification.

This package reports saved evidence, not a count of unique current judges or completion of the national judge corpus. The baseline directory audit is separately frozen under `reports/judges/focus_20260913/`; new biographies do not retroactively change that earlier snapshot.
