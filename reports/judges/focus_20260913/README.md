# Saved judge evidence audit

This baseline snapshot, taken at 2026-09-14 04:54 UTC, produced **4,458 directory fact reports** from saved Trellis HTML. They identify publisher profile URLs and reported names, court/county labels and statuses; they are not individual profile biographies or verified unique people. The baseline contains 46 saved Trellis directories, including one Markdown-only root page, and no captured Trellis individual profiles. A later profile acquisition must be reported as a separate snapshot.

The existing official package contains 145 saved sources: 137 rosters/directories across 28 jurisdictions and eight profile or office-detail pages. Existing Texas data supplies 363 county/court assignment rows, 245 distinct name strings, and all 254 county associations. These are assignments and source strings, not a national count of judges. Official profile passages support appointment, education, prior work and professional-service facts to varying degrees; the separate official-profile normalization task owns resolved fields.

The Trellis HTML combines Court and County into one `colspan=2` cell. Its Markdown has five headers but only three visible row cells. This audit retains the combined court/county label, leaves separate county null, and reads status from its proper HTML column. Observed statuses are 2,977 Active, 996 Retired, 54 Deceased and 431 not reported. Those are publisher labels within captured directory rows, not a verified current-service inventory. State directories also include some federal and tribal courts.

No numeric judge analytics were present in the audited directory cells. Analytics headings, filter switches and promotional text are not reported rates. The saved subscription notice explicitly concerns full print/download access; this evidence does not establish specific analytics pricing or account entitlement. The 11,099 pending profile URLs in the frozen frontier are known links, not downloaded profiles. Case outcomes, grant/win rates and timing statistics remain null because these sources contain no defined judge-linked decision cohort or denominator.

Useful outputs:

- `judge_reports.jsonl`: 4,458 individual directory-fact report rows with exact source/table/row evidence and explicit biography/analytics gaps.
- `trellis_directory_rows.jsonl` and `.csv`: directly reported row fields, combined-column safeguards and raw source hashes.
- `coverage.json` and `.csv`: all 50 states plus DC, distinguishing source pages, rows, profile URLs and missing fields.
- `official_profile_field_evidence.jsonl`: eight saved official profile/office pages with hash-verified source passages and line numbers; no duplicate normalization.
- `schema_audit.json`: available fields, missing analytics, and requirements for defensible independent outcome calculations.
- `analysis_results.json`: counts supported by the saved evidence; unavailable performance statistics are null.
- `judge_report_template.json` and `judge_report_template.md`: a reusable report structure keeping facts, publisher metrics and independent calculations separate.
- `trellis_source_audit.jsonl`, `judge_frontier_snapshot.jsonl`, `input_provenance.json`, `validation.json`: exact baseline provenance and 62 freshly checked source hashes.

The offline builder is `audit.py` in this folder. It makes no network requests or source changes. New profile captures and official-profile normalization belong in their separate output directories; this audit is a dated baseline rather than a claim that later acquisition has not occurred.
