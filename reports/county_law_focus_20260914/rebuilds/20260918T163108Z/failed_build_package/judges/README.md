# Official judge sources

This package contains 145 saved official source records: 137 judge rosters or directories and 8 individual judge profiles. Roster sources cover 28 of the 50 states plus DC. The coverage table includes all 51 jurisdictions and records gaps; this is not a complete national judge inventory.

The package preserves the original 99 saved sources and adds 46 reviewed exact URLs downloaded once on September 13, 2026, from 19:56:13 to 19:57:10 UTC. Every URL had one attempt. The run followed no links and left no pending resources. Raw source files remain at their original workspace paths.

## Files

| File | Contents |
| --- | --- |
| `sources.jsonl` / `sources.csv` | 145 saved sources with state, source URL, type, title, edition note, capture times, original/text paths and hashes, and discovery and authority evidence |
| `artifacts.jsonl` / `artifacts.csv` | 293 unique original, extracted-text, and OCR artifact files with SHA-256 hashes, sizes and source associations |
| `index_selection_urls.jsonl` | 149 verified source and final-URL aliases mapping back to the saved sources, for matching the shared archive index |
| `tables.jsonl` and `table_rows.jsonl` / `.csv` | 117 previously extracted HTML tables containing 693 verbatim rows |
| `spreadsheet_rows.jsonl` / `.csv` | 480 preserved spreadsheet rows with worksheet and cell coordinates |
| `judge_assignments.jsonl` / `.csv` | 363 existing Texas local administrative judge, county and court assignment records |
| `names.jsonl` / `.csv` | 245 distinct state/name strings from those assignments, with assignment references; these are not a verified count of unique people |
| `state_coverage.json` / `.csv` | Availability and gaps for all 51 jurisdictions |
| `gaps.jsonl` / `.csv` | 54 records documenting unavailable sources, coverage, editions, and extraction limitations |
| `source_outcomes.jsonl` / `.csv` | Original-source and focused-run outcomes |
| `summary.json`, `schema.json`, `acquisition_recipe.json`, `validation.json` | Counts, field descriptions, bounded acquisition provenance, and validation results |

JSONL source paths are relative to the workspace root, `C:\Users\firas\Downloads\SCRAPE`. Artifact records also carry absolute paths. Keep this folder with the referenced `sources` and `corpus` directories to retain access to the underlying content. These metadata files do not duplicate source payloads.

## Reading the results

Names in other states remain available in saved full text and verbatim tables. This package preserves existing structured extraction; it does not claim to have resolved every judge's identity or converted every roster into person records.

Editions and capture dates are separate. Alabama's membership register includes historical service dating to 1820 alongside entries marked Present. Older roster editions are retained with notes. Ohio's JudgeSearch interface downloaded successfully but has an empty extracted-text file, so its roster contents are an explicit extraction gap. A downloaded source does not establish that its membership is current or complete.

The focused run used source family `official_judges_phase2`. Existing discovery evidence identifies the official source; general court inventory pages and speculative URLs were not added to this saved-source manifest. Existing blocked sources remain documented as gaps.

## Validation and rebuild

Validation on September 13, 2026 at 20:03:55 UTC verified all 293 artifact hashes, checked that preserved structured rows equal their original datasets, confirmed 145 unique saved URLs, and confirmed one bounded run with 46 downloads, no pending work, and at most one attempt per resource. It reported zero issues.

The offline builder is `scripts/build_focused_judges.py` under the workspace root. It rebuilds the judge metadata and structured exports from saved files without making network requests or changing original content. `index_selection_urls.jsonl` and `validation.json` additionally record the final independent index-alias and integrity checks. Acquisition is complete for this focused package; rerunning the collector is not part of rebuilding it.
