# Live MVP checkpoint — September 19, 00:11 UTC

Port 8769 now serves the Pennsylvania profile and portrait addition. Server PID
39928 replaced the verified prior archive process 32584. See deployment.json,
deployment_verification.json (14 checks passed), official_overlay_verification.json
(15 regression tests), and sources/pa_judge_portraits_20260919/images_ready.json.

The main judge presentation has **10,698 profiles**: 10,669 existing consolidated
identities plus 29 separate official Pennsylvania source profiles. No identities
were merged. There are 5,971 detailed profiles, **43 verified local portraits**
(14 previous plus 29 PA), and the same 708 source analysis records. Six new source
headings explicitly retain emeritus/emerita. Saved role, term and career wording
does not certify present-day service. Do not re-download or append these 29 again.

All 43 live image endpoints matched manifest hashes and local bytes. Every new
profile retained its exact source identity and published term/heading. One PA
image is PNG despite an image/jpeg response header; canonical decoded MIME and
the discrepancy are both preserved. Acquisition used 33 attempted HTTP requests
across retained attempts, 1,910,965 image bytes, and zero paid provider credits.

The source overlay is integrated only in the small judge projection, not the
entity master or main document index. Its source actions link to official pages,
without a broken main /api/record action. Historical CourtListener biographies
remain a separate collection: 15,797 non-alias people, plus 394 optional aliases.

The browser check at the actual port confirmed 43 photo results; Pennsylvania
filters to 29 and Superior Court to 18. A new Anne E. Lazarus portrait rendered
with its professional history and Career tab. The new persistent Judge profiles /
Historical biographies navigation preserves each collection's filters. Refresh
now reloads UI code and data while retaining the hash; browser reload once is
needed to pick up code in an already-open old tab. Main publication is labeled
separately from these live additions. A 390px viewport had no horizontal overflow;
viewport was reset, temporary QA tab closed, and browser error logs were empty.

Main catalog was not rebuilt: 58,310 database rows, 1,328,373,760 bytes and its
22:32 UTC modification timestamp remain unchanged. Focused publication remains
16,454 captures / 15,837 texts. Open US Law remains ready with 2,978,617 rows.
County inventory remains 3,144, and 301 pending records / six Trellis browser
profiles are still browsable under their existing scopes. The stale Trellis
"awaiting directory integration" wording is corrected in the served display;
original capture metadata remains intact. A backup of the previous small judge
projection and summary is under before_pa/.

Remaining integration work: source-bound 374-row KY/TX registry, 1,619 Illinois
section-code candidates after scope/overlap review, and verified bridges or image
URLs for the 1,230 CourtListener photo flags. Flags are not image files. Consult
sources/local_deep_audit_20260918/ for those staged discoveries. The national
corpus is incomplete; do not call every discovered asset deployed or optimized.
The existing 30-minute heartbeat remains ACTIVE. Prioritize one bounded useful
integration or reviewed county backfill, with actual localhost verification.

audit_live.py/live_verification.json are the BEFORE checkpoint (14 portraits);
they are not the new expected-count test. Use verify_deployment.py for this pass.
