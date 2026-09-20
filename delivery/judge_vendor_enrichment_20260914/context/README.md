# Context public preview: Dana M. Sabraw

This component contains **one source observation, 15 professional/methodology facts and 449 source-reported preview measurements**, extracted offline from five saved public Context captures. It is a public UI preview, not current-service verification, a complete case corpus, or an independent assessment of the judge.

The source identity is the published permalink `cd0773bb-bfaf-49d0-a14b-58a6e85d93e7`. No name-only identity match to any other judge corpus is made. California/federal court metadata comes from the profile header. The former California state-court service is retained in its own professional history row; no county is assigned from that former office. The publisher's “Present” wording and court contact details remain unverified for currency.

| Native feature | Records | Treatment |
|---|---:|---|
| Visible Opinions by Areas of Law | 5 | Five `class="hidden"` rows behind View 5 More are excluded from measurements. |
| Motion-type chart totals | 116 | Native `Cases` unit and motion names retained. |
| Explicit motion outcome buttons | 228 | Only reported outcomes; 120 absent buttons remain null in the breakdown sidecar. |
| Motion result-list count | 1 | 489 is distinct from the motion-to-dismiss chart total of 542. |
| Frequently cited opinions | 50 | Display-name duplicates remain separate native graph records. |
| Frequently cited judges | 49 | Counts belong to citing Dana M. Sabraw; cited names are unresolved referenced entities. |

No outcome rates are computed. Period, full cohort, numerator, denominator, completeness and methodology URL are null where unobserved. The Motion information tooltip says outcomes are based on trial-judge opinions and do not detect appellate reversals. Its literal AX typography concatenates `Outcomesare`; this is retained in the methodology fact. Citation tooltip interaction supplied no explanatory methodology, so none is inferred. The unquantified Opinions Per Year graphic, case-result previews, document excerpts, navigation and account controls are excluded.

Andrews v. Cervantes has two separate opinion buttons, 72 and 71; these are not merged by display name. Cited-judge buttons include Anthony M. Kennedy 834 and Dana M. Sabraw 217; they are citation frequencies attributed to the citing profile, not the cited judges' performance or resolved identity matches.

`observations.jsonl`, `facts.jsonl` and `analyses.jsonl` implement the shared vendor component contract. `motion_breakdowns.jsonl` groups referenced native analysis IDs without filling missing outcomes or deriving ratios. `exclusions.jsonl` records exclusion evidence, including hidden-row fragments; those fragments are not normalized measurements. `source_documents.jsonl` records byte hashes of the five originals; no originals are copied or modified by this normalizer.

Evidence uses original file SHA-256 and exact zero-based, end-exclusive Unicode offsets. Overview evidence first resolves `/tool_result/content/0/text`, parses that embedded JSON string, then resolves `/html`. The original wrapper remains the byte-hash authority. Browser snapshots resolve `/response/stdout` directly. Overview provenance is provider-rendered HTML; browser captures are rendered accessibility snapshots. A provider-reported HTTP status is retained separately and is not asserted to be an independently collected original HTTP response.

Run `build.py` to reproduce the exports offline, and `test_build.py` for the ten focused regression tests. Both use local Python, lxml and standard libraries, and make no network requests. All 464 claim evidence records and five excluded hidden-row fragments are reproduced from original saved sources. `validation.json` binds final JSONL output hashes. Validation applies to this finite saved preview only; it does not certify vendor accuracy or completeness.
