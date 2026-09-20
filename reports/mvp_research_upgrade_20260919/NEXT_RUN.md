# Live research MVP checkpoint — September 19

This pass is deployed at localhost:8769. Server PID32440 is the checkpoint PID;
always verify the current server.json/process before a future restart. The next
active user request is to integrate Downloads/publicLaw_directory.md and its
taxonomy/API/source URL map; its work is separate from this finished pass.

Implemented: state/category law hubs; Saved text / Saved source file / Link only
filters; county Overview / Rules & forms / Courts & access subpages; 374 KY/TX
county registry pages; source/saved/effective date separation; deterministic
Library insights on judge profiles; court-facet counts that respect name and
profile-content filters. The source registry is now a county availability filter
(374 counties), and its presence is shown on county cards.

The registry contains 120 KY +254 TX county rows, 2,358 court entries,628 clerks,
and2,539 historical judge-seat associations (not unique/current judges). All167
stored evidence artifacts were freshly hash-verified; one known unsaved PDF is
documented. Snapshot generation date2026-08-22 is explicitly distinct from
current service/link availability, saved_at remains unknown. County identity is
bound by exact FIPS/state/name with capitalization normalization only.

Tests: 7 date/insight regressions,5 navigation/filter checks,10 explore tests plus
targeted publication-date regression,9 county-registry tests,6 frontend helper
checks. Final live_verification.json passed13checks across17HTTPrequests;
17requests were also rerun after the final small card-label update if the receipt
timestamp is later. Browser QA passed NY40140statute drilldown/reader, state and
availability persistence, Bowes portrait/insights, Harris county105court/2clerk
references and expanded entries, historical biography navigation, desktop and
390px layouts. No browser console errors. Root additionally verified the new
374-county registry filter and its actual visible count.

No source files, main database, judge projection, bulk index or focused publication
were rebuilt. Main DB58,310rows/1,328,373,760bytes retains22:32UTC timestamp;
judge projection10,698profiles/43portraits remains unchanged. Focused publication
16,454captures/15,837texts and OpenUSLaw2,978,617publisherrows remain as before.
County saved-information availability now includes the separate verified registry
and totals2,150; local resources remain568includingpending, not allcountyfilings.

Insights count saved references/affiliations/analysis entries and missing profile
components. They do not invent case outcomes, judge performance or predictions.
Unknown dates stay unknown, YYYY/YYYY-MM precision is preserved, and index-build
time is never treated as source publication or legal effect. Reporting periods
and sample-size availability remain source-bound.

Use the next directory request to add a mapped source collection and a reviewed
bounded parallel acquisition pilot. Do not repeat completed imports or equate
historical liveness claims with current validation/downloaded contents. Continue
the existing official queue, host locks/robots barriers,100-credit cap/reserve and
publication gates in the earlier handoffs. Update the actual localhost interface
and test it before reporting additions as live.
