# Judge data audit and evidence-based profile design (judge-audit)

Date: 2026-09-18 (local). Read-only. No network requests, no connector calls, no edits to existing project files.
All SQLite opened `mode=ro`. Counts below were computed in this session unless marked "from prior summary".

## 1. Inputs inspected

| Input | Path | What it is |
|---|---|---|
| UI projection | `sources/judge_presentation_20260918/profiles.sqlite3` | 10,698 rows: `profiles(id, entity_id, name, search, has_details, has_photo, has_biography, analysis_count, score, card, profile)` + `states`, `systems`, `courts`, `images` (43). `profile` is a JSON blob of display strings. |
| Builder / API | `delivery/archive-directory/judges.py` (426 lines), `judge_insights.py` (70 lines) | Projection builder + listing/profile readers; "Library insights" = inventory of which sections exist. |
| Entity layer | `sources/judge_entities_20260918/` (`entities.jsonl` 105 MB, `facts.jsonl` 165 MB, `analyses.jsonl`, `members.jsonl`, `match_decisions.jsonl`, `possible_matches.jsonl`, `conflicts.jsonl`) | 10,669 conservative display groups from 11,928 observations; 60,849 fact claims; 708 analysis records; 1,211 possible + 885 conflicting pairs left unmerged. |
| Enrichment snapshot | `delivery/judge_enrichment_20260914/` (`SCHEMA.md`, `federal_biographies/`, `state_evaluations/`) | FJC Article III export normalized (4,074 observations); Colorado 2024 retention evaluations (116 judges). |
| Raw FJC export | `sources/judges/enrichment_20260914/federal_biographies/judges.csv` (5.45 MB, 4,074 rows x 201 columns, captured 2026-09-14) | Full FJC Biographical Directory export. Carries BOTH `nid` and `jid`. |
| Vendor probe | `sources/judges/vendor_probe_20260914/{context,lex_machina}` | One Lexis Context public preview (Judge Sabraw) and one Lex Machina article statistic (Judge Gilstrap). |
| CourtListener people | `sources/courtlistener_people_20260918/catalog.sqlite3` (29 MB) | people 16,191 (394 aliases), positions 51,291, educations 12,777, schools 6,011, political_affiliations 8,486, courts 3,361, FTS. NOT merged into entities. |
| Local CL bulk | `C:/Users/firas/Downloads/returnedfiles/bulk` (snapshot label 2026-06-30) | Loaded: people, positions, educations, schools, political-affiliations, courts. NOT loaded: financial-disclosures (32,336 disclosures / 3,392 persons) + 8 child tables (investments 1,901,720 rows), races (6,542), opinion-cluster panel (835,148 memberships / 3,285 persons), opinion joined_by (1,028), courthouses (3,361), citations (127 MB, header-only inspected), originating-court-information (20 MB, header-only), retention-events (0 rows). No ABA-ratings or sources table is present in the folder. |
| Prior audit | `sources/local_deep_audit_20260918/judges/` | Found SW-BULK release `b2b-cdbb8d040b95c7b65cfc`: 867 judge rows (850 CL native ids), 4,776 judicial assignments across 3,409 matters. |

## 2. Quantified quality of the 10,698 profiles

Computed by parsing every `profile` JSON.

| Section populated | Profiles | Share |
|---|---:|---:|
| Any source link | 10,698 | 100% |
| State label | 9,799 | 91.6% (899 have none) |
| Court label | 9,208 | 86.1% (1,490 have none) |
| Education | 5,668 | 53.0% |
| Appointments | 5,667 | 53.0% |
| Professional career | 4,099 | 38.3% |
| Service (other judicial service) | 1,655 | 15.5% |
| Biography | 1,605 | 15.0% |
| Analyses | 118 | 1.1% |
| Documents | 116 | 1.1% (all are the Colorado evaluation PDFs) |
| Portrait | 43 | 0.4% |
| `term_as_published` | 29 | 0.3% (PA official layer only) |
| **No substantive section at all** (no bio/education/appointments/service/career/analysis) | **4,727** | **44.2%** |

Score distribution (`100*photo + 30*bio + 25*analysis + 10*education + 10*career`): 0 -> 4,727; 10-19 -> 89; 20-29 -> 4,233; 30-39 -> 23; 40-49 -> 122; 50-59 -> 1,461; 120 -> 43.
The default sort is `score DESC`, so the first screen is decided by "has a portrait" (43 profiles), not litigation relevance.

By system (from `systems` table): Federal 4,454 (4,150 with details, 125 with biography); State 4,413 (1,297 with details, 1,267 with biography); no system 1,831 (524 with details).
`role` is the literal string "Judicial profile" on all 10,669 consolidated profiles. There is no title (district / circuit / magistrate / bankruptcy / state trial / appellate), no status (active / senior / terminated / deceased), no appointing president, no commission date as a field: everything is flattened into `{"text": "..."}` strings.

Source mix of entities (members per entity): federal_biographies only 4,023; trellis_directory only 3,340; official_observation only 1,887; trellis_directory+trellis_profile 1,070; trellis_profile only 180; state_evaluations only 116; FJC+trellis (2 or 3 classes) 50; other 3.
Multi-source federal profiles are rare: only 44 of the 1,134 currently serving district judges have more than the FJC row.

### State coverage is a flat sample, not a census
45 states have state-system profiles, almost all between 61 and 113 per state (Texas 346, Colorado 209, West Virginia 143). California has 99 state-judge profiles, New York 74, New Jersey 93, Pennsylvania 113, Illinois 93, Missouri 97, Delaware 61. Roughly 25-28 per state have details (the Trellis profile sample). This is a ~100-per-state directory sample; it must not be presented as state judiciary coverage.

Spot test of state mass-tort coordination judges (analyst-supplied surnames, state-filtered search; NOT an official list): New Jersey Porto, Padovano, Kaplan, Harz; California Kuhl, Cheng, Riff, Schulman; Pennsylvania Roberts -> **0 state-court hits for all nine**. State coordinated-proceeding judges (NJ MCL, CA JCCP, Philadelphia Complex Litigation Center, etc.) are effectively absent.

## 3. Federal Article III district judges

Derived from the local FJC `judges.csv` (snapshot 2026-09-14) joined to entities through the `fjc:nid:<nid>` member key (exact native id, no names):

| Measure | Count |
|---|---:|
| Entities with an FJC member (one nid each; 0 entities with multiple nids) | 4,074 |
| Ever held a U.S. District Court appointment | 3,317 |
| FJC-reported serving (an appointment with empty Termination Date and no death year) - any Article III court | 1,464 |
| ... serving on a U.S. District Court | **1,134** (648 active + 486 senior-status) |
| ... serving on a U.S. Court of Appeals | 303 |
| ... Supreme Court / other (CIT etc.) | 11 / 16 |
| Serving district judges with a second source class | 44 |
| Serving district judges with a biography | 43 |
| Serving district judges with any analysis | **1** (Sabraw, vendor preview) |
| Federal-system entities with NO FJC member (magistrate / bankruptcy / Trellis stubs) | 380 |

Status is *available but unused*: the structured FJC appointment facts already in `facts.jsonl` carry `Senior Status Date`, `Termination`, `Termination Date`, `ABA Rating`, `Seat ID`, `Senate Vote Type`, `Ayes/Nays`, hearing/committee dates, `Party of Appointing President`. The UI string keeps only president / nomination / confirmation / commission / chief-judge dates (senior status is printed when present), and sets `current_service_verified=false` for everyone. A truthful label "FJC-reported status as of 2026-09-14: active | senior | terminated (reason, date) | deceased" is derivable today with zero network.

## 4. Analyses: what actually exists (708 records, 118 profiles)

| analysis_type | Records | Profiles | Source |
|---|---:|---:|---|
| public_preview_motion_count (metrics `motion_outcome_cases` 228, `motion_type_cases` 116) | 344 | 1 | Lexis Context public preview, Judge Dana Sabraw (S.D. Cal.) |
| public_preview_citation_frequency | 99 | 1 | same |
| public_preview_area_of_law_count | 5 | 1 | same |
| public_preview_result_list_count | 1 | 1 | same |
| commission_performance_evaluation | 116 | 116 | Colorado OJPE, 2024 retention ballot |
| commission_vote | 114 | 114 | same |
| survey_overall_rating | 28 | 28 | same |
| vendor_reported_case_assignment_count | 1 | 1 | Lex Machina article: Gilstrap, 2,276 patent-related assignments 2023-2025 |

So 449 of 708 records belong to one judge; 258 are Colorado state retention evaluations; 1 is a patent statistic. **No analysis record exists for any MDL transferee judge.** `judge_insights.derive()` is a section-presence inventory ("Distinct source pages", "Saved court affiliations", "Published analysis records"); it contains no litigation-relevant measure. The user's complaint that judge analysis is "very poor" is accurate and is a data gap, not a rendering bug.

## 5. Major MDL transferee judges: resolution test

Method: analyst-supplied list of 57 (first name, surname, court) triples - NOT an official JPML list. Match = normalized surname in profile name AND exact court string in courts/appointments/service. Richness columns: education / appointments / service / career entries, biography, analyses, portrait, source classes.

Requested names:

| Judge (court) | Resolves | Richness |
|---|---|---|
| M. Casey Rodgers (N.D. Fla.) | Yes, as "Margaret Catharine Rodgers" | FJC only; score 20; no bio/analysis/portrait. Common name "Casey" is not an alias, so a search for "Casey Rodgers" will not find her. |
| Vince Chhabria (N.D. Cal.) | Yes | FJC only + portrait (score 120) |
| Yvonne Gonzalez Rogers (N.D. Cal.) | Yes | FJC only + portrait |
| Denise Cote (S.D.N.Y.) | Yes | FJC only, score 20 |
| Joseph R. Goodwin (S.D. W.Va.) | Yes | FJC only, score 20 |
| Dan A. Polster (N.D. Ohio) | Yes | FJC only, score 20 (senior status 2021-01-31 present in text) |
| Brian R. Martinotti (D.N.J.) | Yes | FJC only, score 20; not linked to the local MDL-3080 collection (1,612 PDFs) |
| Michael A. Shipp (D.N.J.) | Yes | FJC only, score 20 |
| **Rukhsanah L. Singh (D.N.J., magistrate judge)** | **MISS** | Not in profiles; not in the local CourtListener people table either (only "Singhal"). Magistrate judges are outside the FJC Article III directory. |
| Robin L. Rosenberg (S.D. Fla.) | Yes | FJC only, score 20 |
| Denise J. Casper (D. Mass.) | Yes | FJC + Trellis directory + Trellis profile; biography; score 50 |

Other tested judges, all resolved, all FJC-only score 20 unless noted: Fallon, Gergel, Rowland, Rosenstengel, Sargus, Rufe, Marston, Kugler, Wolfson, Milazzo, Dever, Furman, Saylor, Kinkeade (listed as "James E. Kinkeade"; "Ed" not an alias), Levy, Ericksen, Tunheim, Kennelly, Pallmeyer, May, Land, Cogan, Brodie, Crenshaw, Ruiz, Caldwell, Neals, Quraishi, Conti, Vance, Doherty, Thrash. With Trellis biography (score 50): Brody, Barbier, Campbell, Blake. With portrait (score 120): Breyer, Orrick III, Chen, Corley.

Defects surfaced by the test:
1. **Unmerged duplicates**: Bumb, Arleo, Castner (D.N.J.), Bough (W.D. Mo.), Chambers (S.D. W.Va.) each appear twice: an empty Trellis-directory stub (score 0) plus the FJC profile. Corpus-wide: 304 federal Trellis-directory-only stubs; **142** have exact normalized first+last name + exact court equal to a currently serving FJC district-judge entity (merge *candidates*, not yet verified).
2. **Same-name hazard**: "William Horsley Orrick" Jr. and III both sat on N.D. Cal. Name + court is insufficient by itself; suffix and service dates must gate any join.
3. **Common-name gap**: FJC legal names differ from docket names (M. Casey Rodgers, Ed Kinkeade, F. Dennis Saylor IV). Alias evidence exists only if taken from an official source (court website, JPML report); do not invent nicknames.
4. **Magistrate judges, bankruptcy judges, special masters and state coordination judges are structurally missing.**

Result: 56 of 57 tested federal names resolve; 1 miss (magistrate judge). 0 of 9 tested state coordination judges resolve. Richness for MDL judges is uniformly the bare FJC row.

## 6. A verified native-id bridge that is not yet used

The prior audit (correctly) warned that FJC `nid` and CourtListener `fjc_id` are different namespaces. The FJC export itself carries both: column `nid` and column `jid`. Tested here:

- FJC rows: 4,074; distinct `jid`: 4,074; distinct `nid`: 4,074.
- CourtListener people with `fjc_id`: 3,711 (all distinct). `fjc_id` == FJC `jid` for **3,710** (1 CL id, 9288, has no FJC row).
- Agreement on the bridged pairs: last name equal 3,707 / 3,710; first name equal 3,695; birth year equal 3,702 of 3,708 comparable.
- Of 1,134 serving district judges, 833 bridge to a CL person id; 301 do not (the CL snapshot's latest position start is 2024-12-31, latest position row created 2025-05-21, so 2025-2026 appointees lack `fjc_id`).

Therefore: `entity -> fjc:nid member -> judges.csv row -> jid -> CL people.fjc_id -> CL person id` is an exact, name-free crosswalk for 3,710 people. Disagreeing rows (3 surname, 6 birth year) go to a review queue, not auto-link. This unlocks CL positions (incl. 721 people with open `mag` positions in federal district courts, 1,244 with open `jud` positions), educations, political affiliations, aliases, `has_photo` flags (1,230), financial disclosures and the SW-BULK assignment release (850 CL native ids) for existing entities.

## 7. Official, citable per-judge statistics that can be added

| Source | What it gives per judge | Format / cadence | Join key | Notes |
|---|---|---|---|---|
| **JPML "Pending MDLs by District" report** (jpml.uscourts.gov) | District, transferee judge name, MDL number, caption, actions pending, total actions ever | PDF, roughly monthly; also "by MDL type", "by actions pending", and the cumulative Terminated MDLs report + calendar-year statistics | (district -> court) + judge name as printed -> FJC row restricted to judges with an appointment on that court whose service interval covers the report date; require a unique hit | Highest value. Produces the definitive "major MDL judges" list, removing the analyst-list guesswork in section 5. Report date is the as-of date. Only JPML CM/ECF manuals/rules are in the corpus today (22 records); no pending-docket report is saved. |
| **CJRA (Civil Justice Reform Act) reports**, 28 U.S.C. 476 (uscourts.gov) | Per judge incl. magistrate judges: motions pending > 6 months, bench trials submitted > 6 months, bankruptcy appeals and Social Security appeals > 6 months, civil cases pending > 3 years | Semiannual (March 31 / September 30), per-district tables | district + printed name -> FJC (Article III) or CL `mag` position; period = reporting date | Publisher-reported counts; display with period and "as of" date; no rate (no denominator is published per judge). Note MDL member cases inflate three-year counts - state that caveat verbatim. Only two D. Md. CJRA appendices (2021) are local. |
| **FJC Biographical Directory export** (already local) | ABA rating, Senate vote, hearing/committee dates, seat id, predecessor seat, senior status, termination, chief-judge service, party of appointing president | CSV, single file | `nid` (native) | Zero network. Re-fetch periodically as one bounded URL; keep snapshot date. |
| **U.S. Courts judicial vacancies / confirmations / emergencies** (uscourts.gov/judges-judgeships) | Court-level vacancy list, nominee, confirmation listing by Congress; judicial emergencies | HTML tables + monthly archive | court + incumbent name + vacancy date vs FJC termination/senior date | Court-level context (bench strength) and a freshness check on FJC status. |
| **U.S. Courts caseload tables** (Table C-series, Federal Court Management Statistics) | NOT per judge: per-district filings, pending, weighted filings per judgeship, median time to disposition/trial | XLSX/PDF, quarterly/annual | court id | Use as *court context* beside a judge, labelled as district-level. |
| **CourtListener financial disclosures** (already local, 2026-06-30 label) | Disclosure years, report type, page count, investment descriptions, gifts, reimbursements, positions | CSV.bz2 | CL person id -> `jid` bridge | Conflict/recusal research for corporate defendants. Show as source-linked historical records only; no inference. Needs PostgreSQL CSV dialect (`escapechar='\\'`, `doublequote=False`). |
| **CourtListener dockets/opinions via the user's connector** | MDL docket assignment, authored opinions list, citations | connector responses | CL person id | Small, quota-checked, recorded as connector responses. Not needed for phase 1. |
| **SW-BULK release b2b** (already local) | 4,776 judge-to-matter assignments across 3,409 matters | jsonl.gz | CL native id (850) | Counts must stay bounded to "within the 3,409 saved matters". |
| FJC Integrated Database (civil) | No judge identifier in the public file | - | - | Cannot support per-judge metrics; do not plan on it. |

## 8. Conservative join rules (proposed, deterministic)

1. **Tier A - native id**: FJC `nid` (entity member key) ; FJC `jid` == CL `fjc_id` ; CL person id == SW-BULK release native id. Auto-link. Log name/birth-year disagreement as a review item and withhold that link.
2. **Tier B - printed name + court + time** (JPML, CJRA, vacancies): normalize (NFKD, casefold, strip punctuation), parse `LAST, FIRST M. SUFFIX`; candidate set = FJC rows with an appointment on exactly that court whose `[commission date, termination date or open]` covers the report date. Link only if exactly one candidate matches surname AND (first name OR first initial + middle initial) AND suffix does not conflict. Two candidates (Orrick Jr./III pattern) or zero -> `unresolved`, shown on the MDL/court page as the printed name with no profile link.
3. **Magistrate / bankruptcy judges**: no FJC nid. Tier B against CL positions (`position_type in ('mag','c-mag')`, court id, open or covering interval). Otherwise create a *source observation* profile keyed by `(source, court, printed name)`; never merge into an Article III entity.
4. **Never**: name alone; cross-court name matches; equating numeric `nid` with `fjc_id`; inferring "current" from presence in a directory. Every link row stores `basis`, `evidence_path`, `evidence_sha256`, `as_of`.
5. **Duplicate Trellis stubs** (142 candidates): merge only under the existing `match_decisions` regime with basis `exact_name_and_court_with_serving_fjc_interval`; suffix conflict or two FJC candidates blocks the merge.

## 9. Proposed profile sections (only what evidence supports)

1. **Identity header**: display name, printed-name variants with source, title (District Judge / Senior District Judge / Circuit Judge / Magistrate Judge / state title as published), court, native ids (FJC nid, FJC jid, CL person id) shown as provenance chips.
2. **Status (source-reported, dated)**: "FJC-reported as of <snapshot date>: active | senior since <date> | terminated <reason> <date> | deceased <year>". Replaces the blanket "not verified" note for 4,074 federal profiles. State judges keep "not verified" unless an official roster capture exists.
3. **Appointment and confirmation**: structured rows per appointment: court, seat id, appointing president + party, nomination, hearing, committee action, Senate vote type and ayes/nays, confirmation, commission, ABA rating, chief-judge service, senior/termination.
4. **Career and education**: structured FJC/CL rows (degree, school, year; career segments), keeping source wording.
5. **MDL assignments** (new): MDL no., caption, role (transferee judge), pending and total actions, report date, link to local MDL collection/docket/settlement records when ids match (e.g. MDL-3080 -> Martinotti).
6. **Official caseload indicators** (new): CJRA counts by reporting period, labelled publisher-reported with period; district-level context stats in a visually separate "Court context" block.
7. **Financial disclosures** (new, optional phase): years available, report types, link to source record; searchable holdings text with a neutrality note.
8. **Evaluations and published analytics**: existing Colorado/vendor records, unchanged, each with period/denominator or "not published".
9. **Saved documents and orders**: documents in the corpus attributed to the judge by explicit metadata only.
10. **Provenance and gaps**: per-section source, capture date, source as-of date, hash; explicit list of unresolved candidates.

## 10. Deterministic metrics justified by the evidence

All are counts or dates copied or computed from a single named source with its as-of date; none is a rate, score or prediction.

- `fjc_status`, `fjc_status_as_of`; `years_since_commission` (as of FJC snapshot date); `senior_since`; `chief_judge_intervals`.
- `article_iii_appointments_count`; `aba_rating_as_reported`; `senate_vote_as_reported`.
- `mdl_pending_count`, `mdl_pending_actions_sum`, `mdl_total_actions_sum` (JPML report date X); `mdl_history_count` (terminated report) - each listing the MDL numbers behind it.
- `cjra_motions_over_6mo`, `cjra_cases_over_3yr`, `cjra_bench_trials_over_6mo` per reporting period; trend = the series itself, no smoothing.
- `disclosure_years_available` (list), `disclosure_count`.
- `saved_assignments_in_local_release` (with denominator "3,409 saved matters").
- `source_class_count`, `native_id_links` (which of nid/jid/CL are linked) as a data-confidence indicator replacing the portrait-driven `score`.
- Proposed list ranking: `has_pending_mdl DESC, mdl_pending_actions_sum DESC, fjc_status active/senior, richness` - documented as a relevance sort, not a quality ranking.

New facets made possible: title/court type, status, circuit/district, appointing president/party (source-reported), has pending MDL, MDL number, has CJRA data, has disclosures, has native-id bridge.

## 11. Recommended build order

1. `judge_federal_structured` (no network): re-project FJC structured appointment facts + jid/CL bridge into a hash-gated supplement; adds title/status/ABA/vote/ids + facets for 4,074 profiles.
2. `jpml_mdl_assignments` (network, ~5-10 URLs): pending-by-district PDF + terminated report + latest annual stats; parse; Tier B join; emits judge<->MDL edges and the authoritative priority-judge list.
3. `cjra_judge_reports` (network, <= 100 URLs per packet): latest 2-4 reporting periods; per-judge counts.
4. `cl_people_bridge_enrichment` (no network): positions/educations/affiliations/aliases + magistrate source-observation profiles via Tier A/B.
5. `trellis_stub_dedup` (no network): adjudicate the 142 candidates.
6. `financial_disclosures_index` (no network): load disclosure header table + searchable holdings.
7. `judicial_vacancies_confirmations` (network, < 10 URLs).
8. `state_coordination_judges` (network, small): official NJ MCL, CA JCCP, Philadelphia CLC rosters and assignments.

## 12. Not verified

- No external URL was fetched: the exact current file names, formats and availability of the JPML pending report, CJRA tables, and vacancy pages are from general knowledge and must be confirmed in the acquisition packet (robots, format, as-of date).
- The 57 federal + 9 state judge names are an analyst-supplied test list; MDL assignments were not checked against JPML. Spelling of state-judge surnames was not verified against official rosters, so the 0/9 state result shows absence of those surnames, not proof about specific individuals.
- The 142 Trellis-stub duplicates are exact name+court candidates; middle names, suffixes and service intervals were not adjudicated.
- The 3 surname / 15 first-name / 6 birth-year disagreements in the jid bridge were not individually reviewed (likely punctuation or married-name variants).
- "Serving" is FJC-reported as of the 2026-09-14 capture, not independently verified current office.
- Financial-disclosure, opinion-panel, citations and originating-court bulk tables were not opened here; counts are from `local_deep_audit_20260918/judges/report.json`.
- SW-BULK release contents (which matters, whether MDL-related) were not opened.
- Trellis / CourtListener / DocketBird connectors were not called (no quota used); their judge-analytics coverage for MDL judges is unknown.
- `server.py` / `app.js` rendering of the judge page was not reviewed; UI observations derive from the projection JSON and `judges.py` only.
