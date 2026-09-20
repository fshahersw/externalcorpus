# Judge data snapshot

Built 2026-09-14T05:55:23.380206+00:00. This snapshot has 1,978 official source-specific judge observations, 1,300 Trellis profile captures and 4,458 Trellis directory rows. These are separate observations, with repeated and historical people possible; they are not a unique current-judge count.

Biographies, education, appointment/service history, court/county labels and professional contacts are available where the saved source supplies them. `reports.jsonl` contains evidence-linked individual reports. Component JSONL/CSV files retain full literal fact evidence, original paths and SHA-256 hashes. `state_coverage.csv` shows the actual coverage and gaps.

Search from the workspace with `python scripts/search_judge_intelligence.py Bannon --state AZ --source trellis_profile`. Optional filters include state, source class, court and county. `judge_search.sqlite3` provides SQLite full-text search; it is an index of source observations and does not merge identities.

Observed dashboard/report links are in `trellis_profiles/dashboard_report_links.jsonl`. Verified numeric analytics rows: 0. Missing metrics stay null. Saved biographies and recent-case snippets do not establish win rates, motion grant rates, decision timing or predictions. Paid dashboard access remains dependent on the authorized browser session.

The signed-in browser confirms full Judge Analytics is an additional subscription on the current account. `report_sample/` preserves the publisher's 12-page marketing sample PDF and preview evidence separately; its sample content is not attributed to the profiled judge. The PDF has negligible embedded text; accepted offline OCR derivatives, when included, are under `report_sample/offline_ocr/` with their extraction limits.

Originals stay in their cited workspace locations; this snapshot freezes normalized evidence and manifests. Fresh source hashes, component validation and the independent semantic sample are included. Acquisition can continue outside this dated snapshot. The full national judge corpus remains incomplete.
