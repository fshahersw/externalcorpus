# Judge analysis audit and focused UI improvement

The published judge presentation has **708 saved analysis measures across 118 profiles**. This is not nationwide vendor analytics coverage.

| Saved source | Measures | Profile scope |
| --- | ---: | --- |
| Colorado judicial performance evaluations | 258 | 116 judges on the 2024 retention ballot |
| Lexis Context public preview | 449 | Dana Makoto Sabraw |
| Lex Machina public article | 1 | James Rodney Gilstrap; assigned patent cases, 2023–2025 |

All 708 presentation measures have a publisher URL and saved timestamp. The 449 Context measures have no established reporting period. They retain native counts and limitations; no rates are calculated. Citation frequencies concern the citing judge's saved preview, not the performance of cited judges.

The 1,300 Trellis profile captures contain 1,297 biography bodies and **zero directly reported numeric analytics**. Their 1,520 distinct report/dashboard URLs originate from 308 profile URLs: 1,212 preview links and 308 other dashboard/report links. These are link references, not downloaded analysis. The exact join for attaching them is their `source_url` to an existing Trellis profile member URL; never a display-name join.

The external upgrade's MDL assignments are already integrated into the judge overview. Its structured-judge adapter exists, but `sources/judge_structured_20260919` was absent at audit time, with no server or frontend integration. The handoff accurately lists that work as unfinished. This audit did not create the missing FJC/CourtListener/SW-BULK bridge.

## Approved UI change

Only judge-specific functions in `delivery/archive-directory/app.js` and judge-specific CSS in `styles.css` changed. The overview, MDL assignment block, career sections, `areas.js`, source data, and adapters were preserved.

- “Analysis & reports” is always discoverable, including an honest no-saved-analysis state.
- Large sets can be searched and filtered by source measure family; query and type persist in the profile URL.
- Source basis, source value, reporting period, saved date, and available sample/denominator fields are shown. Unknowns remain explicit.
- Report/dashboard references render in a separate link-only section through optional `profile.analysis_references`. Only entries explicitly labeled `availability: publisher_link` with a safe HTTP(S) URL render.
- Colorado's generic “Published analysis” publisher label was reported to the parent for adapter correction.

The parent added the exact-URL reference adapter. A follow-up live check confirmed five Trellis report/dashboard links on Terry L. Bannon, each explicitly link-only, separated from the no-saved-analysis state. Desktop and mobile checks passed.

## Verification

`node --check` passed. Live Chrome desktop and 390×844 checks passed on Sabraw, Allison J. Esser, Gilstrap, and biography-only A. Andrew Hauk: family/search filters, reload persistence, pagination, empty state, unknown-period and sample-size copy, 3.5/4 evaluation scale, month-precision survey dates, and 2023-through-2025 assignment count. No horizontal overflow or console errors/warnings were observed. Temporary viewport override was reset and the QA tab closed.

`audit.json` contains source counts, findings, evidence hashes, and the pre-deploy API reconciliation. `ui_verification.json` records the observed UI checks and limits.
