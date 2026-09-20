# County and state-law expansion status

Status generated 2026-09-13T21:43:07.287410+00:00. The county and state-law expansion is **delivered** in the refreshed selected package.

Scope: **selected counties and remaining state-law URLs only**. Judge rosters and profiles are prior saved package material; no judge acquisition is active. **No recurring automation is active.**

The fixed **950-URL paid selection** had **942 successful captures** and **950 terminal outcomes (100.00%)** at **2026-09-13T21:42:40.518392+00:00**. Terminal progress includes failed outcomes and does not mean all selected pages were saved. These counts come from the [resume progress snapshot](county_law_resume_progress.json), independently of the worker's later status timestamp.

| Selected category | URL count | Recorded outcomes |
|---|---|---|
| County profiles | 600 | 592 downloaded, 8 provider_error |
| State-law URLs | 350 | 350 downloaded |

Recorded law-body classifications: 2 directory_navigation, 348 observed_nonempty_legal_container. A saved directory is not counted as proof that its substantive law body was captured.

The separate direct official-county entry collection recorded **460 downloaded resources** in the progress snapshot at 2026-09-13T21:42:40.518392+00:00; these may include allowed redirect targets and are outside the paid selection denominator. Its last saved run checkpoint recorded **time_budget** at 2026-09-13T21:34:16+00:00; that earlier checkpoint may precede additional collection. Access barriers and failed requests remain in the evidence.

The latest saved worker snapshot reports **selection_exhausted_or_not_pending**, phase **None**, at **2026-09-13T21:26:34.007359+00:00**. It is a recorded snapshot, not a process-liveness check. The saved provider **final credit observation** recorded **1 credits** at **2026-09-13T21:27:35.473185+00:00** (HTTP 200; [source checkpoint](../sources/trellis/resume_20260913/credit_checkpoint.json)). This is the saved final credit checkpoint; the offline generator does not query a live balance. The selection reserve is 1 credit(s).

The worker snapshot reports **500 credits observed in this process run**, which resets after a restart. The progress report separately records **950 credits observed across the selected pass** at 2026-09-13T21:42:40.518392+00:00, from matching batch manifests with each remote job counted once. That pass observation can lag in-flight provider charges; it is not a live remaining balance.

[Open the refreshed delivery](../delivery/focused_legal_corpus/README.md). Its summary was generated at 2026-09-13T21:41:04.683183+00:00; it contains 12,387 capture records and 12,029 distinct searchable texts.

**The full underlying nationwide corpus remains incomplete.** The fixed selection and delivery have explicit limits; neither is an enumeration of every law, county document, judge profile or court record. Original captures, editions, missing-law-body classifications and access evidence remain preserved.

[Active resume control](active_county_law_resume.json) · [Fixed-selection progress](county_law_resume_progress.json) · [Detailed measured status](status.json). Run `python scripts/build_status.py` to refresh this status from saved reports; it does not collect sources or rebuild the package/index.
