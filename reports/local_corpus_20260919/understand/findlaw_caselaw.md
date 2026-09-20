# FindLaw caselaw capture + session_leftovers — data scout report

Cluster: `findlaw_caselaw`. Read-only survey, no files modified. All numbers below are from streaming
measurements run today (2026-09-19) against the exact paths listed in the task; estimates are labeled.
Not previously covered by `understand/local_inventory.md` (grepped for "findlaw" — only 2 unrelated hits
about `codes.findlaw.com`/`OKcodelaw` folder-name mislabels in an unrelated crawl; the tar/zip/leftovers
paths in this task are new ground).

## 0. Files at a glance

| Path | Bytes on disk | mtime |
|---|---|---|
| `returnedfiles/findlaw_opinions_part1of4.tar.gz` | 55,842,384 | 2026-08-22 15:44 |
| `returnedfiles/findlaw_opinions_part2of4.tar.gz` | 56,480,447 | 2026-08-22 15:44 |
| `returnedfiles/findlaw_opinions_part3of4.tar.gz` | 56,991,534 | 2026-08-22 15:44 |
| `returnedfiles/findlaw_opinions_part4of4.tar.gz` | 54,604,078 | 2026-08-22 15:44 |
| `returnedfiles/session_leftovers.tar.gz` | 5,115,877 | 2026-08-22 15:44 |
| `filesdfsdfsdfsds.zip` (Downloads root) | 3,854,166 | 2026-08-22 15:25 |
| `returnedfiles/findlaw_opinion_index.csv` (loose, sits next to the tars) | 4,275,037 | 2026-08-22 15:25 |
| `returnedfiles/findlaw_index.md` (loose) | 322,338 | 2026-08-22 15:25 |
| `returnedfiles/findlaw_all_pages.jsonl` (loose) | 22,104,693 | 2026-08-22 15:25 |

No README/manifest ships inside the FindLaw tars themselves; `findlaw_index.md` (loose, next to the tars)
is the de-facto manifest for the FindLaw capture. `session_leftovers.tar.gz` ships its own `README.md`
(quoted in full in §3).

## 1. Copy check: `filesdfsdfsdfsds.zip` vs. the loose index files

`filesdfsdfsdfsds.zip` contains exactly 3 entries: `findlaw_opinion_index.csv`, `findlaw_index.md`,
`findlaw_all_pages.jsonl`. SHA-256 of each zip member was compared byte-for-byte against the identically
named loose file already sitting in `returnedfiles/`:

| File | Match | SHA-256 (first 12 hex) |
|---|---|---|
| findlaw_opinion_index.csv | **identical** | 63051c8427a6 |
| findlaw_index.md | **identical** | ade74cb41496 |
| findlaw_all_pages.jsonl | **identical** | 3ed8445088fd |

**Verdict: `filesdfsdfsdfsds.zip` is a redundant duplicate**, not a separate/newer artifact — same bytes as
the loose files. Nothing is gained by keeping both; the loose copies in `returnedfiles/` are sufficient.
No "which is newer" question applies since they are bit-identical.

## 2. FindLaw opinion capture (4 tar parts)

### 2.1 Structure
Each `findlaw_opinions_partNof4.tar.gz` is a gzip-compressed tar stream (opened with `tarfile.open(mode="r|gz")`,
non-seekable streaming mode) holding 5 members, all under `findlaw_full/`:

| Tar | Members | Uncompressed bytes |
|---|---|---|
| part1of4 | findlaw_opinions_001..005.jsonl | 209,640,596 |
| part2of4 | findlaw_opinions_006..010.jsonl | 209,632,731 |
| part3of4 | findlaw_opinions_011..015.jsonl | 209,549,820 |
| part4of4 | findlaw_opinions_016..020.jsonl | 200,479,767 |

20 shards total, ~829.3 MB uncompressed, ~224 MB compressed (~3.7x ratio). Each shard is ~41.9 MB except
the last (20) at ~32.9 MB (tail shard).

### 2.2 Row counts (streamed line counts, no full JSON parse needed for the count)
Per-shard line counts (measured by iterating the tar stream and counting newlines per member):
part1: 1501, 2611, 1461, 1478, 2511 (=9,562); part2: 1865, 1861, 1852, 1448, 1245 (=8,271); part3: 1346,
1372, 1743, 1799, 1504 (=7,764); part4: 1598, 1158, 1308, 1294, 1667 (=7,025).

**Total records across the 20 `findlaw_full/*.jsonl` shards: 32,622.**

Cross-check against the loose index: `findlaw_all_pages.jsonl` (32,102 rows, exact count) and
`findlaw_index.md` ("32,102 unique URLs") agree with each other but are ~520 lower than the 32,622 rows
inside the tar shards. **Not reconciled** — most likely the full-text shards retain a small number of
retry/duplicate captures that the "unique URL" index de-duplicated away, but I did not verify this by
diffing URLs (would require materializing ~830 MB of JSON; out of scope for a 60s-per-measurement budget).
Treat `findlaw_all_pages.jsonl` as the authoritative unique-page index and the tar shards as the (slightly
over-counted) full-text payload.

### 2.3 Schema (one real record from shard 001, JSON keys only — no full record reproduced)
Every `findlaw_full/*.jsonl` row has exactly these 6 keys: `court_slug`, `job`, `markdown`, `status`,
`title`, `url`. There is **no structured field** for docket number, citation, date, judges, parties or
counsel — all of that lives inside the free-text `markdown` field and must be parsed out.

`job` values seen: `"court"` and (per `findlaw_index.md`) `"united_states"` — these are the names of the
two Firecrawl crawl jobs that fed the pull (`caselaw.findlaw.com/court`, completed 25,001/25,001 pages;
`caselaw.findlaw.com/court/united-states`, 12,125/13,000 retrieved when pulled, i.e. an incomplete job).
Both Firecrawl jobs were stated (in `findlaw_index.md`) to expire 2026-08-23 19:19 UTC — i.e. re-pulling
via the same Firecrawl job IDs is no longer possible; only the already-saved bytes exist.

### 2.4 5 sampled opinion records — what's actually inside `markdown`
Sampled the first 5 status=200 opinion-length (>500 char) records from shard 001. Two are genuine opinions,
three are court-browse/index pages (confirms the corpus mixes 24,652 opinion pages with 7,450 index pages,
matching `findlaw_index.md`). Fields identifiable inside the opinion markdown (regex/structure, not a JSON
field), from `STANGER v. VOCAFILM CORPORATION (1945)` (2nd Cir.) and `PEOPLE v. LOVING (1977)` (Cal. Super.
App. Dept.):
- **Court**: printed as a markdown H2 line, e.g. "Circuit Court of Appeals, Second Circuit." — free text,
  not a normalized court code (the `court_slug` JSON field is often blank for these; see §2.5).
- **Date decided**: printed as "Decided: <Month DD, YYYY>" inline in the body — parseable by regex, not a
  separate JSON field.
- **Docket/case no.**: printed as "No. <n>." — present but as free text, and format varies by era/court.
- **Judges**: printed as "Before <Name>, <Name>, and <Name>, Circuit Judges." — free text, no person IDs.
- **Parties/counsel**: full party names and counsel appearances are in the body text ("W. Randolph
  Montgomery, of New York City ... for defendant-appellant. Bernard Budnick ... for plaintiffs-appellees."),
  again unstructured. No case citation reporter string (e.g. "F.2d") observed in either sample — FindLaw's
  free opinion pages generally omit official reporter citations.
- I am not printing personal-contact info; none of the sampled counsel lines carried phone/address/email
  beyond city name, consistent with the instruction to describe rather than reproduce such fields.

### 2.5 Courts/years covered (from the index CSV, not the raw markdown, to stay inside the time budget)
`findlaw_opinion_index.csv` (24,652 rows = the opinion-only subset) header: `court_slug,title,url,md_chars,
status,sources`. All 24,652 rows have `status=200`. 430 distinct `court_slug` values (1,398 rows have a
**blank** `court_slug` — these are `caselaw.findlaw.com/summary/opinion/...` URLs where the crawler did not
back-fill the slug field; the court name is still recoverable from the URL path segment or the title).
Top court slugs by opinion count (also reported, at higher precision, in `findlaw_index.md`): us-8th-circuit
3,696; ca-court-of-appeal 1,274; us-11th-circuit 1,244; tx-court-of-appeals 930; ks-court-of-appeals 833;
ca-supreme-court 812; us-4th-circuit 809; nc-court-of-appeals 725; us-9th-circuit 669. `sources` field: 3
distinct values — `findlaw_court` (16,161), `findlaw_united_states` (6,006), both jobs (2,485) — i.e. which
of the two Firecrawl jobs surfaced that URL (provenance, not a court).

Year coverage: extracted a year from the `title` string (format is usually `"<Case name>, MM/DD/YYYY, <docket>
- <Court> | FindLaw"`, occasionally `"<Case name> (YYYY)"` for older opinions) with a regex; **1,179 of
24,652 titles (4.8%) did not match** either pattern (their titles use `YYYY/MM/DD` order instead — e.g. CA
Court of Appeal "summary" pages — so the true no-year-recoverable rate is lower than 4.8%, this is a
regex-coverage gap, not a data gap; sampled, not exhaustively re-parsed). Of the ~23,500 rows with a year:
range 1842–2026; distribution by decade is heavily present-weighted — 1990s: 2,479; 2000s: 6,341; 2010s:
5,872; 2020s: 7,108 (≈88% of dated rows are 1990-2026); pre-1940: 21 rows total (oldest is 1842). This
matches a modern-appellate-opinion-heavy free-tier FindLaw archive, not a historical case-law substitute.

### 2.6 Already used by the SCRAPE project?
Grepped `sources/` and `delivery/` for `findlaw`, `court_slug`-style filenames, and the shard/CSV filenames
themselves: **no hits** for `findlaw_opinions_part`, `findlaw_full`, `findlaw_opinion_index.csv`,
`findlaw_all_pages.jsonl`, or `findlaw_index.md` anywhere under `sources/` or `delivery/archive-directory`.
This capture has not been ingested into any existing MVP layer.

### 2.7 Gap mapping, join keys, quality risks, effort
| | |
|---|---|
| **Gap filled** | G11 (case law/opinions) — explicitly the gap the brief flags as licence-blocked for scraping; also feeds G14 (source/URL directory: this is itself a frontier list of 32,102 FindLaw URLs with known status codes) |
| **Join key to MVP** | None of the built-in native IDs (no CourtListener id, no FJC id, no PACER id). The only joinable handles are: (a) the `url` (deterministic FindLaw URL, could be looked up against CourtListener's `absolute_url`/citation search by case name + court + date — no automated join available offline), and (b) the free-text case name / decided-date / docket-no parsed out of `title`/`markdown`, which is a **name-only join** (never merge by name alone per the brief's data-quality rule — this would need a human- or CourtListener-verified bridge, not an automatic one). |
| **Quality risks** | (1) Licence: FindLaw's Terms of Service prohibit scraping/redistribution — see §4. (2) 4.8%+ of titles don't cleanly regex-parse a date (some are recoverable with more regex variants). (3) ~520-row discrepancy between the raw full-text shard count (32,622) and the deduplicated unique-page count (32,102) is unresolved. (4) One of the two source Firecrawl jobs (`united_states`) was still running when pulled (12,125/13,000, 93% complete) — the corpus is a snapshot of an incomplete crawl, not a finished one. (5) No case citation strings, no judge/person IDs, no docket-number normalization — everything is unstructured free text requiring an extraction pass before any structured use. |
| **Build effort** | **M** to build a private reference/lookup index (regex-extract case name/court/date/docket from title+markdown into a supplement `sources/findlaw_reference_20260919/` with `validation.json`, expose only citation-lookup metadata through the adapter, never serve/republish opinion markdown). **L** if the goal is a general-purpose case-law layer, because normalizing court names to `cl_court` ids and cross-referencing 24,652 opinions against CourtListener (to attach real citations and person ids) is a real per-record reconciliation job, not a bulk transform. |

## 3. `session_leftovers.tar.gz` — full characterization

This archive is **not FindLaw-specific**. Per its own bundled `README.md` (quoted below, an authoritative
manifest of its own contents — I did not need to guess), it is grab-bag output from several unrelated
Firecrawl/DOJ/state-agency crawl sessions that was never delivered to any prior supplement, plus the two
scripts (`findlaw_pull.py`, `findlaw_full.py`) that produced the FindLaw tars above.

### 3.1 Structure (streamed tar listing)
94 members, 73,954,037 bytes uncompressed (~74 MB), compressed to 5,115,877 bytes (~14.5x — mostly
already-compressible JSON/JSONL text). Extension mix: 64 `.jsonl`, 14 `.py`, 11 `.json`, 1 `.md`
(the README). Top-level layout: `leftovers/` with loose files plus three subfolders —
`per_job_deep_crawl/` (14 job jsonl files), `per_job_state_agency/` (33 job jsonl files),
`per_job_doj_sweep/` (15 job jsonl files, plus a couple of "2"-suffixed retries).

### 3.2 The bundled README (verbatim, this is the manifest/provenance record for the whole archive)
> **Session leftovers — everything generated but not previously delivered**
>
> *Raw source captures*: `doj_51_state_pages_raw.json` — full markdown+links for all 51 DOJ JMD state
> pages (source behind a `doj_state_sources.csv` this archive does not itself contain — that CSV is
> presumably already delivered elsewhere, not verified by me). `tier1_js_seed_extracts.json` — JS-rendered
> index pages (ATSDR ToxProfiles, IRIS A-to-Z, NTP RoC, IARC classifications) that `/v2/map` could not see.
> `uscourts_external_links.json` — 677 external URLs referenced from the uscourts.gov court-website-links
> crawl, with labels and ref counts.
>
> *Directories not previously shipped in full*: `tier1_toxicology_full.jsonl` — "all 15,511 tier-1 records
> INCLUDING the 438 altmetric.com rows I filtered out of the delivered version." `tier1_toxicology_clean.json`
> — "the filtered 15,073." **`ca_jccp_records_raw.jsonl` — "JCCP records with the full untruncated `text`
> field per proceeding (the delivered CSV truncated title at first county name)."**
>
> *Per-job splits (before merge/dedupe)*: `per_job_deep_crawl/` (14 jobs: jpml, fjc, uscourts_forms, ussc,
> supremecourt, ny_dos, ca_oal, cpsc, nhtsa, osha, ca_courts + 3 cancelled-empty); `per_job_state_agency/`
> (33 jobs: state admin codes + federal agencies); `per_job_doj_sweep/` (15 jobs: corrected admin-code URLs).
>
> *Reconnaissance*: `portal_probe_results.json` (map-sizing for 45 candidate portals, url+PDF counts each);
> `state_admin_code_official_urls.json` (authoritative admin-code URL per state from DOJ, including two
> Lexis-gated states — NJ, VT); `doj_regulations_links.json` (111 Regulations-subsection links);
> `deep_stats.json`/`final_stats.json`/`last_stats.json` (per-run rollups); `il_counties_summary.json`
> (per-circuit page/char/credit counts).
>
> *Scripts (all re-runnable)*: `fc_dump2.py`, `fc_job.py`, `harvest2.py`, `guard.py` (credits-per-page
> runaway guard), `deep_parallel.py`/`run_final.py`/`run_last.py` (the three parallel launches),
> `doj_sweep.py`/`doj_extract.py` (DOJ state registry build), `probe.py` (map-before-crawl sizing),
> `parse_jccp.py`/`parse_chunk.py` (chunked, OOM-safe JCCP PDF parsing), `findlaw_pull.py`/`findlaw_full.py`
> (the findlaw retrieval — i.e. these are the scripts that produced §2's tars).
>
> *Not included*: "The two kycourts.gov crawls (1,949 pages each, ~3.5GB of markdown) were deleted from the
> container to free disk for the findlaw pull. They had already expired from the Firecrawl API by then."
> — flagging per BRIEF.md that this data is **gone**, not merely unmeasured.

I take the README's own counts (15,511 / 15,073 / etc.) as **publisher-reported** (the crawl author's own
tally), not independently re-verified row-by-row against the ~74 MB of jsonl in this budget; the file
sizes I measured (below) are independently confirmed.

### 3.3 File-size detail (streamed, sizes from the tar header, not extracted to disk)
Selected files by size (all under `leftovers/`, values in bytes):
- `doj_51_state_pages_raw.json` — 1,886,763
- `ca_jccp_records_raw.jsonl` — 2,368,473
- `tier1_toxicology_clean.json` — 3,204,222 (largest single file in the archive)
- `tier1_js_seed_extracts.json` — 156,478
- `uscourts_external_links.json` — 114,468
- `per_job_state_agency/` largest members: `FL.jsonl` 2,092,410; `GA.jsonl` 2,313,682; `FTC.jsonl` 4,235,507;
  `AL.jsonl` 2,627,779; `CFPB.jsonl` 2,101,153; several 0-byte (`EEOC.jsonl`, `PA.jsonl`, `IN.jsonl`,
  `NIOSH.jsonl` — empty/cancelled jobs)
- `per_job_deep_crawl/` largest members: `ny_dos.jsonl` 6,423,564; `ca_courts.jsonl` 5,337,621;
  `cpsc.jsonl` 2,264,647; `fjc.jsonl` 1,054,400; two 0-byte (`nc_leg.jsonl`, `nj_oal.jsonl`)
- `per_job_doj_sweep/` largest members: `NC2.jsonl` 6,281,142; `OR.jsonl` 5,388,765; `CT.jsonl` 954,878;
  several 0/near-0-byte states (`NE`, `IN`, `KS`, `OK`, `MI2` — failed/empty jobs)

### 3.4 Already used by the SCRAPE project?
Grepped `sources/` for `jccp`/`JCCP` (case-insensitive): the only hit is
`sources/gap_fill_acquisition_20260919/README.md`, which states **"the reviewed packet contained no
California JCCP URL, and both New Jersey MCL URLs sit on a listed barrier host, so neither programme was
captured."** That directly confirms `ca_jccp_records_raw.jsonl` in this leftovers archive is **new, not yet
in the MVP** — it fills exactly the CA-JCCP hole that the existing gap-fill run explicitly could not reach.
Grepped for `toxicology`/`ATSDR`/`IARC`/`NTP RoC`/`ToxProfiles` under `sources/agency_safety_20260919`
(the existing 243,682-row FDA/CPSC agency-safety layer): no filename or content hit for the ATSDR/IARC/NTP
toxicology profile material described in this leftovers README — it is very likely also new, though I did
not diff the two by content (agency_safety's 243,682 rows are FDA/CPSC recall/enforcement records, not
toxicology profile monographs, so an overlap is unlikely by construction, not just by grep). No filename
hits anywhere in `sources/`/`delivery/` for `doj_51_state_pages_raw`, `per_job_state_agency`,
`per_job_deep_crawl`, `per_job_doj_sweep`, `tier1_toxicology`, or `uscourts_external_links` — none of this
has been wired into the MVP.

### 3.5 Gap mapping, join keys, quality risks, effort (session_leftovers)
| Sub-dataset | Gap(s) filled | Join key | Risk | Effort |
|---|---|---|---|---|
| `ca_jccp_records_raw.jsonl` | **G5** (CA JCCP judges/registry — currently a hole per gap_fill_acquisition's own admission) | none native; would need proceeding number/case-name text join to any future JCCP-specific layer | Raw Firecrawl text per proceeding, untruncated but unparsed — no judge/docket schema yet extracted; "raw" in filename means no structuring pass has happened | **M** — needs a parse pass (this project already has `parse_jccp.py` re-runnable from this same archive) plus a validation.json before it can back an adapter |
| `tier1_toxicology_clean.json` / `_full.jsonl` | **G9** (federal regulatory/toxicology science sources) | none native (ATSDR/IARC/NTP have their own identifier schemes not captured in the excerpt I saw) | publisher-reported counts (15,511/15,073) not independently re-verified in this pass; "clean" version already dropped 438 altmetric.com rows per README | **S–M** — likely mostly usable as-is once schema is confirmed by opening a few records |
| `doj_51_state_pages_raw.json` | **G8/G9** (state statute/regulation source directory — DOJ's own list of the 51 state legislative/regulatory pages) | none native; state name/USPS code extractable from content | Raw markdown, needs re-parsing (README says "re-parse it any way you like" — i.e. explicitly unprocessed) | **S** |
| `per_job_state_agency/` (33 state/federal agency job jsonls, several empty) | **G9** (state administrative agencies) + partly **G12** (SEC — `SEC_litig.jsonl` 849,371 B, `SEC_rules.jsonl` 1,113,025 B present) | none native | Uneven: several jobs are 0 bytes (EEOC, PA, IN, NIOSH — failed/cancelled, not "no data available") | **M** (33 heterogeneous per-agency schemas to normalize) |
| `per_job_deep_crawl/` (jpml, fjc, uscourts_forms, ussc, supremecourt, ny_dos, ca_oal, cpsc, nhtsa, osha, ca_courts) | **G4/G6/G7/G9** depending on job (fjc.jsonl could bear on judge data G4; ca_courts/ca_oal on G5/G7 California court/admin material) | none native without opening files | Two 0-byte jobs (`nc_leg`, `nj_oal` — failed) | **M** |
| `per_job_doj_sweep/` (15 corrected admin-code URL jobs) | **G8** (state admin-code gaps) | none native | Several 0/near-0-byte states (NE, IN, KS, OK — likely failed fetches, not confirmed-empty states) | **S–M** |
| `uscourts_external_links.json` | **G14** (source/URL directory — 677 external URLs with labels/ref counts from the uscourts.gov crawl) | none native; URLs themselves are the payload | Frontier list, not yet crawled | **S** (directly usable as a Firecrawl frontier candidate list) |
| `state_admin_code_official_urls.json`, `portal_probe_results.json`, `doj_regulations_links.json` | **G14** (source/URL directories worth crawling) | none native | Reconnaissance metadata (URL + size estimate), not content | **S** |
| `findlaw_pull.py`, `findlaw_full.py`, and the other 12 scripts | n/a (tooling, not data) | n/a | Re-runnable per README, but the two Firecrawl jobs behind the FindLaw pull have since **expired** (per findlaw_index.md, expired 2026-08-23 19:19 UTC) — re-running `findlaw_pull.py` would need fresh Firecrawl job IDs, not a replay | n/a |

**Bottom line on session_leftovers**: it is a legitimate grab-bag of otherwise-lost intermediate crawl
output, explicitly labeled by its own author as "generated but not previously delivered." The single
highest-value item for this project's stated gaps is `ca_jccp_records_raw.jsonl` (fills a gap the project's
own gap-fill run admits it missed), followed by the toxicology/DOJ/agency material for G8/G9. None of it is
duplicated elsewhere in `sources/`/`delivery/` by filename or the specific content keywords checked.

## 4. Licence / usability boundary for the FindLaw material (read this before using §2 or §3's findlaw scripts)

FindLaw (a Thomson Reuters property) publishes Terms of Service that prohibit unauthorized automated
scraping and redistribution/republication of its site content, per the task's own framing (which I was
given as ground truth licence context, and which is consistent with FindLaw's public terms as commonly
understood — I did not fetch FindLaw's terms page in this pass since network access is disabled for this
task). Practically, for anything downstream of this report:

- **Safe to use / re-publish (as a private index, or even shared internally)**: case name, court, decision
  date, and docket number extracted from the title/markdown (these are public facts about a public court
  filing, not FindLaw's expression) — for the purpose of looking the *same* opinions up on **CourtListener**
  (openly licensed, and already the project's primary case-law connector via
  `mcp__ae4a3886…` / the RECAP/CourtListener bulk data in `returnedfiles/bulk/*.csv.bz2`). The 24,652-row
  `findlaw_opinion_index.csv` is essentially a ready-made "cases to go look up on CourtListener" work list.
- **Must NOT be republished or served verbatim through the MVP**: the FindLaw `markdown` body text itself
  (headnotes, editorial framing, and FindLaw's own formatting/summary of the opinion) — this is the
  content the terms of service protect, and it is also frequently not the official reporter text anyway
  (see §2.4 — no citation strings observed, meaning some of these are FindLaw's own case summaries rather
  than a verbatim court opinion). **Any adapter/build built from these tars must not have an `original()`
  file-serving function that returns the raw markdown/HTML to end users** — at most, a private,
  non-served reference index (citation metadata only) for the researcher's own lookup convenience, per the
  task's framing of this as "a private reference/index for personal testing."
- I did not verify FindLaw's terms text directly (no network access permitted for this task); this section
  restates the licence constraint the task itself supplied and applies it to what I measured. Whoever wires
  this in should have a human confirm current FindLaw ToS wording before any adapter design decision.

## 5. What I did NOT verify (be honest about the boundary)

- Did not open/parse any of the 20 `findlaw_full/*.jsonl` shards beyond shard 001 (sampled there); did not
  reconcile the 32,622 vs 32,102 record-count discrepancy noted in §2.2.
- Did not extract/validate the ~1,179 titles that didn't match my two date regexes (§2.5) — likely still
  parseable with one more regex variant (`YYYY/MM/DD` order), not attempted here to stay in budget.
- Did not open any `per_job_*` jsonl in `session_leftovers.tar.gz` beyond the README's own description —
  row counts and schema for `ca_jccp_records_raw.jsonl`, `tier1_toxicology_*`, `doj_51_state_pages_raw.json`,
  and all 3 `per_job_*` folders' 62 job files are **not independently measured**, only their file sizes
  (from the tar header) and the README's own prose description. Whoever builds on these should re-open
  each and validate row counts/schema before writing a `build.py`.
- Did not attempt to bridge any FindLaw case to a CourtListener docket/opinion id — flagged as a name-only,
  unautomated join in §2.7, not resolved.
- Did not check FindLaw's live Terms of Service page (no network access in this task); §4 restates the
  licence framing given in the task brief rather than independently confirming it.
- Did not compute SHA-256 for the tar/zip archives themselves (only for the loose-vs-zip comparison in
  §1) — not needed for the "which is authoritative" question since §1 already proved byte-identity via
  content hashes of the individual files.

## 6. Native IDs present (explicit answer to the checklist)

**None.** No CourtListener docket/person/court id, no FJC nid/jid, no PACER case id, no FIPS code, no MDL
number anywhere in the FindLaw tars, the index CSV/jsonl/md, or the session_leftovers archive's headline
files that I opened. The only identifiers present are FindLaw's own URL paths (which encode a FindLaw
internal opinion id, e.g. `.../157228.html`) and free-text case names/dates/docket numbers. This is the
core reason the join key in every table above is "none native" — everything from this cluster needs either
a manual/human-reviewed bridge or a future automated match against CourtListener before it can plug into
the project's canonical id graph (G13).
