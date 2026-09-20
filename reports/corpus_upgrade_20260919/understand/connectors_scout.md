# Connectors scout (read-only) - 2026-09-19 UTC

Scope: what the user's connected CourtListener, Trellis and DocketBird connectors plus CourtListener bulk data can
supply for judge analysis, firm/attorney data, courthouses and MDL relationship mapping, at minimal usage.
All connector samples are in `understand/connector_samples/` with `manifest.json` (tool, arguments, UTC time, SHA-256).
They are **connector responses, not original HTTP bytes** (agent transcriptions; hashes are of the saved files).
The public S3 listing under `connector_samples/cl_bulk_listing/` **is** original HTTP bytes with its own `receipt.json`.

## 1. Quotas and entitlements (measured)

| Connector | Plan / identity | Quota observed | Used by this scout | Remaining |
|---|---|---|---|---|
| CourtListener MCP | "CL Membership - Tier 1", active | user scope 600/day, 150/hour, 20/min; citations 60/min; PACER fetch 30/min | 6 requests (13 used today incl. a ~7/day background baseline seen on every idle day) | 587/day at 04:39Z; day window resets 2026-09-19T11:00:03Z |
| Trellis MCP | trellis.base, has_subscription | 100 MCP views per period; **125 used, 0 remaining, reset 2027-01-01** | 0 views (coverage tools are free) | 0 - judge tools are hard-blocked |
| DocketBird MCP | user 8865786, company 13482, subscription active | `find_litigation_relationships` returned `remaining_today` 99 then 98 (whoami showed 999 - different counter, meaning not verified) | 2 counted calls + 1 un-counted translation error | 98 today |

Cost facts confirmed:
- CourtListener: `get_api_usage` and `get_endpoint_schema` are free; every `search`/`call_endpoint` = 1 request regardless of `num_results` (max 100). `count` is lazy on most endpoints (needs `get_counts`; its cost was not tested).
- Trellis: `get_usage`, `get_server_instructions`, `get_state_coverage`, `get_county_coverage` did **not** consume views and still work at zero quota. `search_judges` returned "Access denied ... account_limit_reached" with an upgrade link (recorded as data; no upgrade attempted). `get_judge_profile` / `get_judge_analytics` were therefore **not called** (would be denied; per-call view cost unknown).
- DocketBird: a question that cannot be translated to a graph query errors without decrementing the counter.

## 2. CourtListener API - what it supplies

Endpoint list exposed by the MCP (41): dockets, docket-entries, recap-documents, courts, clusters, opinions, opinions-cited,
people, positions, retention-events, educations, schools, political-affiliations, sources, aba-ratings, **parties, attorneys**,
fjc-integrated-database, originating-court-information, bankruptcy-information, financial-disclosures (+8 child tables), audio,
tags, alerts, recap-fetch, etc. **There is no `courthouses` endpoint.**

Confirmed working on Tier 1 (HTTP-equivalent success with data): courts, search(type=d), people, positions, **parties, attorneys**.

Fields useful for the corpus:
- **MDL -> judge link (1 request per MDL):** `search` type `d` returns `docket_id`, `docketNumber`, `court_id`, `dateFiled`, `dateTerminated`,
  `assignedTo` + **`assigned_to_id`** and `referredTo` + **`referred_to_id`** (CourtListener person ids), `pacer_case_id`, `suitNature`.
  MDL 3080: docket 67665081, njd, 2:23-md-03080, filed 2023-08-04, assigned_to_id 8598 (Brian R. Martinotti), referred_to_id 9389 (Leda Dunn Wettre).
  These ids join directly to the existing local layer `sources/courtlistener_people_20260918/catalog.sqlite3` (`people.id`).
- **Judge analysis (people/positions):** person id, `fjc_id` (legacy FJC jid, e.g. 3608 - not the FJC nid), slug, name parts, gender, race, dob granularity,
  `has_photo`, `is_alias_of`, nested educations (school, degree_level, degree_year), aba_ratings (year_rated, rating), political_affiliations
  (party, source, dates), sources (url, date_accessed). Positions: court, position_type, how_selected, nomination_process, date_nominated,
  date_confirmation, date_start, date_termination, termination_reason, votes_yes/no, voice_vote, appointer (a *position* URL), predecessor, supervisor.
  All of this is already in the local 2026-06-30 bulk import, so the API is only needed for deltas after 2026-06-30.
- **Parties:** id, name, extra_info, `party_types[]` (docket_id, name = Plaintiff/Defendant/..., date_terminated), nested attorneys.
- **Attorneys / firm data:** id, name, `contact_raw` (free text: firm name, street address, phone, email, and admission notes such as
  "COUNSEL NOT ADMITTED TO USDC-NJ BAR"), phone, fax, email, `parties_represented[]` (role int, docket, party URL, date_action).
  There is **no firm entity** in CourtListener; firm must be parsed from `contact_raw` line 1-2 and normalised. Role integers need the
  CourtListener choice map (use `get_choices`; not fetched here).
- **Citations:** `opinions-cited` = id, citing_opinion, cited_opinion, depth (filter by either side). Use per-opinion only; the full graph is bulk.

Quirks to design around:
- `fields` filters top-level keys only. Including `person` or `court` in a positions query expands the **full nested objects** (dob, race, etc.);
  omit them and join locally instead. Nested `educations` inside that expansion came back as empty `{}` objects.
- `has_more` + `get_more_results(query_id)` paginates; each page is presumably another request (not tested).
- Party/attorney rows on MDL 3080 were modified 2026-09-03, i.e. RECAP-refreshed recently; coverage of other MDLs was not checked.

## 3. CourtListener bulk data

Source: doc page (redirects to `https://wiki.free.law/c/courtlistener/help/api/bulk-data/bulk-legal-data`) and bucket
`com-courtlistener-storage` (us-west-2), prefix `bulk-data/`. Listing fetched 2026-09-19: **1,076 keys, 45 snapshot dates (2022-08-01 .. 2026-06-30)**.
Regenerated quarterly on the last day of Mar/Jun/Sep/Dec -> **next snapshot expected 2026-09-30**. CSV via PostgreSQL COPY, UTF-8, header row,
bz2, plus `schema-<date>.sql` and `load-bulk-data-<date>.sh`. Stated as free of known copyright restrictions (Public Domain Mark).
**No parties, attorneys, docket-entries or recap-documents tables exist in bulk** - those are API-only.

Latest snapshot 2026-06-30 (35 files). **27 of the 35 are already on disk** at `C:/Users/firas/Downloads/returnedfiles/bulk/` with byte sizes
identical to the bucket listing, so **no download is needed before 2026-09-30**.

| File (2026-06-30) | Size | Local? | Imported into a source layer? | Value |
|---|---:|---|---|---|
| courts | 81 KB | yes | yes (`courtlistener_people_20260918`) | HIGH: 3,361 courts; 2,618 ST, 127 F, 125 FD, 111 SA, 95 FB; 2,819 have parent_court_id -> court hierarchy / jurisdiction facets |
| people-db-people / positions / educations / schools / political-affiliations | 0.07-1.0 MB | yes | yes | HIGH (16,191 people rows incl. aliases) |
| people-db-races (6,542) + people_db_race (8) | 26 KB | yes | **no** | small add-on |
| people-db-retention-events | 118 B | yes | no | **empty (0 rows)** |
| courthouses | 17 KB | yes | **no** | **LOW: 3,361 rows but only 4 have address1, 9 a city, 1 a county, 3 a building name** - effectively a court->state stub. NJ: 94 rows, 0 addresses |
| court-appeals-to | 118 B | yes | no | LOW: only 8 rows (all -> cafc/com). Do not build appellate routing from it |
| search_opinioncluster_panel | 5.0 MB | yes | no | MEDIUM: 835,148 (opinioncluster_id, person_id) rows -> per-judge opinion counts without any API call |
| search_opinion_joined_by, ..._non_participating_judges | 6 KB / 65 B | yes | no | low |
| originating-court-information | 20.6 MB | yes | no | MEDIUM: 973,419 rows with assigned_to_id / ordering_judge_id, date_filed, date_disposed, date_judgment -> trial judge <-> appeal linkage |
| financial-disclosures (+ agreements, debts, gifts, non-investment-income, positions, reimbursements, spousal-income) | 0.07-5.6 MB | yes | no | MEDIUM: judge disclosure metadata keyed by person_id (conflict/recusal context) |
| financial-disclosure-investments | 36.6 MB | yes | no | medium; aggregate only |
| citations | 127 MB | yes | no | MEDIUM: reporter citation -> cluster_id lookup; useful only with clusters |
| schema.sql, load script | 0.5 MB | yes | used | column contract |
| unmatched-citations | 216 MB | no | - | link-only |
| fjc-integrated-database | 280 MB | no | - | OPTIONAL single-file download (court statistics by district / nature of suit / disposition); needs user approval, stream-aggregate, never load whole |
| parentheticals | 288 MB | no | - | link-only |
| citation-map | 526 MB | no | - | link-only (full citation graph) |
| oral-arguments | 684 MB | no | - | link-only |
| opinion-clusters | 2.46 GB | no | - | link-only |
| dockets | 5.01 GB | no | - | link-only |
| opinions | 54.6 GB | no | - | link-only |

Parsed listing: `connector_samples/cl_bulk_listing/parsed_keys.json` (key, last_modified, size for all 1,076 keys).

## 4. Trellis

- NJ state coverage flags: civil, family, probate, documents, verdicts, judge_bios, judge_analytics, court_comparison, state_law, motion_and_issues = true;
  tentative_rulings = false. 21 counties listed, all `has_documents: true`, all `courthouse_count: 0`.
- Middlesex County coverage: population 860,807, area 311 sq mi, seat New Brunswick, established 1683, website, main phone, administration address,
  17 practice areas (incl. Torts, Consumer, Insurance); `courthouses: []`, `court_address: null`. So Trellis county coverage gives **county metadata and
  practice-area presence, not courthouse addresses** (at least for NJ).
- Judge tools (documented return shapes, not exercised): `search_judges` -> judge_id, fullname, state, county_name, court_name, judge_url, has_analytics, status;
  `get_judge_profile` -> bio, appointed_by, clerk_phone, bar_certifications, articles_about, courtroom_rules, career_history;
  `get_judge_analytics` -> case_analysis (caseload, avg case length, motion grant rate, plaintiff/defendant grant rates, practice-area mix), opt-in
  motion_analysis, case_milestones, matter_type_outcomes with county/state benchmarks and `last_updated`. These are publisher-reported numbers and must stay
  labelled as such with period and denominator.
- **Blocked until 2027-01-01** unless the user changes the plan (their decision; nothing was purchased). Until then Trellis value must come from
  existing local captures: `sources/trellis/judge_focus_20260913/judges` (1,300 Firecrawl captures, 2.1 GB), `sources/trellis/counties` (1,432 files, 749 MB),
  `sources/trellis/judges` (47 state lists), `sources/trellis/catalog/catalog.sqlite3` (977 MB folder).

## 5. DocketBird

`find_litigation_relationships` is a natural-language -> graph query tool (federal civil). Verified return fields:
- judge rows: `judge_id` (UUID), `judge_full_name`; firm rows: **`law_firm_id` = firm web domain (e.g. `seegerweiss.com`, `jonesday.com`)**, `law_firm_name`,
  `attorney_count`, `sides`; case context on every row: `case_id` (`njd-2:2023-md-03080`), `case_title`, `year_filed`, `date_filed`,
  `complaint_document_id`, `complaint_status`, `complaint_downloaded`; attorney rows: `attorney.attorney_id`, `attorney.full_name`;
  plus `interpretation` (the graph query restated) and `truncated`.
- MDL 3080 sample: judges Brian R. Martinotti and Leda D. Wettre; top firms by distinct attorneys: Jones Day 16, Alston & Bird 13, Morgan Lewis 12,
  Williams & Connolly 12, Kirkland & Ellis 11, Forman Watkins & Krutz 9, Keller Rohrback 8, Baron & Budd 7, Levin Papantonio 7, Arkansas AG 7.
  Seeger Weiss attorneys in MDL 3080: Christopher A. Seeger, David R. Buchanan (two attorney_ids: 727387 and 272857), Steven J Daroci II, Parvin Kristy Aminolroaya.
- Data-quality caveats seen: the magistrate judge is returned as "presided" with no role flag; `sides` was empty for every firm; firm names carry PACER noise
  ("COUNSEL NOT ADMITTED TO USDC-NJ BAR, LEVIN PAPANTONIO ..."; AG office name includes a building); the same attorney name appears under two ids -
  **never merge by name**; open-ended "which MDLs has firm X appeared in" failed to translate, so questions must name a specific MDL/court.
- The domain-style `law_firm_id` is the best available firm key across connectors and can be matched against e-mail domains parsed from CourtListener `contact_raw`.

## 6. Safe per-run budget (proposal)

| Connector | Per-run cap | Pacing | Notes |
|---|---|---|---|
| CourtListener API | <= 100 requests (17% of day), never below 300/day remaining | <= 12/min (5 s spacing), well under 20/min and 150/hour | always `fields`, `num_results=100`, omit nested `person`/`court`; call `get_api_usage` before and after |
| CourtListener bulk | 0 downloads now; after 2026-09-30 one packet of the ~27 small files (< 60 MB total excluding citations) | >= 2 s per file, UA LegalCorpusResearch/1.0 | large files stay link-only; FJC IDB only with explicit approval |
| Trellis | 0 view-consuming calls until reset; optional <= 51 `get_state_coverage` + <= 50 `get_county_coverage` per run (free) | 2 s spacing | re-check `get_usage` every 10 calls and stop on any increment |
| DocketBird | <= 25 relationship questions per run (25% of the ~100/day counter) | sequential | one named MDL per question; <= 5 named cases per question (tool limit) |

Worked sizing: one MDL = 1 search request + ceil(parties/100) + ceil(attorneys/100) CourtListener requests + 2 DocketBird questions
(judges+top firms; one firm's attorneys). A 30-MDL judge/firm map is therefore roughly 30 search + an unmeasured number of party/attorney pages
(MDL 3080's totals were not counted) and 60 DocketBird questions -> 3 DocketBird days, 1-3 CourtListener runs.

## 7. Not verified
- Per-call view cost of Trellis judge tools; whether `get_judge_profile`/`get_judge_analytics` are also blocked (assumed yes).
- Meaning of DocketBird `remaining_today: 999` from whoami vs 99/98 from the relationship tool; limits of other DocketBird tools.
- CourtListener `get_counts` / `get_more_results` cost; total parties/attorneys on MDL 3080; role-integer choice map; party/attorney coverage on other MDLs.
- Verbatim text of the courts/people/parties/attorneys/opinions-cited schemas (saved as an agent digest only; positions schema is verbatim).
- Exact per-call timestamps (connectors do not expose them; bounded by agent clock checks 04:22Z-04:40Z).
- The 2026-09-30 regeneration date is from the documentation, not observed. Embeddings files and the `eyecite`/`randoms` prefixes were not examined.
- Whether `courthouses` is better populated in older/newer snapshots (only 2026-06-30 inspected).
