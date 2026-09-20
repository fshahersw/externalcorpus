# DOJ JMD library directories + FindLaw caselaw scout (2026-09-19)

Scope: read-only scoping. No project file, database, server or raw capture was modified. All new files are under
`reports/corpus_upgrade_20260919/understand/` (this report, `packets/doj_state_pages.jsonl`, `doj_findlaw_scout_evidence/`).

## 1. Headline findings

1. **All 56 DOJ state/territory pages plus the index are already saved locally** (collection `official_courts`,
   captured 2026-09-13 07:29-07:30 UTC, `extraction_status=extracted`, 57 versions in `catalog/documents.sqlite3`;
   all 57 raw files re-hashed today and match `raw_sha256`). Only `/jmd/ls/federal` was missing; the scout captured it.
2. **No content drift since 2026-09-13.** Fresh fetches of `/jmd/ls/state` and `/jmd/ls/state/new-jersey` today have
   identical article text and identical link lists; byte differences (8 and 218 bytes) are only Drupal asset
   cache-buster tokens. Recapture of the 56 pages is NOT needed now.
3. **The 9,348-reference source directory already contains the DOJ tree.** 3,752 catalog entries sit in the sections
   "STATE LEGAL RESOURCES --- ALL 50 STATES + DC (FULL DOJ JMD RESOURCE TREES)" / "U.S. TERRITORIES ...". Of 2,885
   unique non-justice.gov outbound URLs I extracted from the 56 saved pages: 1,491 match the catalog by exact URL,
   **2,685 (93.1%) by normalized URL** (scheme/`www.`/trailing-slash/case-insensitive), 2,811 (97.4%) have a host
   already in the catalog; 1,435 of 1,491 hosts (96.2%) and 741 of 776 crude registrable domains (95.5%) are present.
   Only **200 URLs are new** (list: `doj_findlaw_scout_evidence/doj_links_not_in_catalog.json`; heaviest in Maryland 15,
   American Samoa 11, DC 11, Puerto Rico 11, Michigan 10, New Hampshire 10, Virgin Islands 9).
4. **The value left in DOJ is labelling and provenance, not URLs.** Of the 2,663 matched catalog entries, **1,679 are
   `category=uncategorized`** although DOJ publishes a section label for every one (e.g. 493 under "State Agencies &
   Offices", 429 under "State and Local Courts", 233 under "Local Government"). Catalog `subsection` equals the DOJ
   label for 2,129 entries and differs for 534 (e.g. 96 Attorney-General links filed under "Governor's Office"; 179+
   relabelled "Commercial & Third-Party Resources"). Catalog entries carry `source_as_of=2026-08-19` and no pointer to
   the saved DOJ page bytes. A deterministic, no-network "state legal resource map" built from the saved captures fixes
   category, section label, jurisdiction evidence and provenance for ~2,700 references.
5. **FindLaw is reachable without a challenge, robots.txt is permissive, but the terms prohibit scraping.** Treat
   FindLaw as link-only reference metadata; do not build a FindLaw opinion-capture packet (details in section 5).

## 2. Network log (all curl, UA `LegalCorpusResearch/1.0`, no retries)

| # | Host | URL | Time (UTC) | Result |
|---|------|-----|-----------|--------|
| 1 | justice.gov | /robots.txt | 04:36:57 | 200, 2,651 B |
| 2 | findlaw.com | caselaw.findlaw.com/robots.txt | 04:37:01 | 200, 141 B |
| 3 | justice.gov | /jmd/ls/federal | 04:42:37 | 200, 94,683 B decoded |
| 4 | findlaw.com | caselaw.findlaw.com/court/united-states | 04:42:41 | 200, 298,339 B decoded, Cloudflare cache HIT |
| 5 | justice.gov | /jmd/ls/state | 04:42:50 | 200, 99,968 B (same size as saved) |
| 6 | findlaw.com | caselaw.findlaw.com/sitemapindex.xml | 04:42:54 | 200, 239,982 B decoded |
| 7 | justice.gov | /jmd/ls/state/new-jersey | 04:43:03 | 200, 87,450 B (same size as saved) |
| 8 | findlaw.com | www.findlaw.com/company/findlaw-terms-of-service.html | 04:45:31 | 200 |
| 9 | internetbrands.com | /ibterms (linked from #8 as the governing terms) | 04:46:26 | 200 |

Totals: justice.gov 4 of 15 allowed (>= 13 s apart after robots was read); findlaw.com 4 of 5; 1 request to the parent
company terms page. Bodies, header dumps and `receipts_1..4.json` (URL, timestamp, curl status line, SHA-256) are in
`doj_findlaw_scout_evidence/`. Bodies were saved with `curl --compressed`, i.e. decoded bytes, not wire bytes.

## 3. justice.gov robots rules

- `User-agent: *` ... **`Crawl-delay: 10`**; `/jmd/ls/` is not disallowed. Disallowed: Drupal admin/search/user paths,
  `/*?page=`, facet queries (`?f[...]`), legacy paths (`/cgi-bin/`, `/ojp/`, `/opa/pr/support/`, `/civil/frauds/` ...).
  Allowed explicitly: `/api/*?page=`, sitemaps. `Sitemap: https://www.justice.gov/sitemap.xml`. `usasearch` gets delay 2.
- **Compliance note:** the 2026-09-13 capture fetched 57 justice.gov pages at ~1 s spacing. Any future justice.gov packet
  must use >= 10 s per request. 58 URLs x 10 s = ~580 s, which is at the BRIEF's 600 s packet cap, so a full recapture
  must be split into two packets (29 URLs each). Set the shared host lock for `www.justice.gov` to 10 s.
- HTTP `Last-Modified` on these pages is a cache timestamp (2026-09-17/18) and changes without content change; never use
  it as a page date. Use the in-page "Updated <Month D, YYYY>" footer line instead (label it as publisher page-update date).

## 4. DOJ JMD structure (from saved captures; parser rules in section 7)

### 4.1 Index `https://www.justice.gov/jmd/ls/state`
- Two H2 sections: "Court Resources by State" (56 jurisdiction links + 1 in-page anchor) and "Federal Courts & Resources"
  (6 links, all to `/jmd/ls/federal.htm`).
- The index publishes **legacy `.htm` URLs** (`/jmd/ls/newjersey.htm`, `/jmd/ls/nmariana.htm`, `/jmd/ls/districtcolumbia.htm`)
  which redirect to canonical slugs `/jmd/ls/state/<slug>` (per saved `source_url` -> `final_url`; status code not re-checked). Both forms are in the packet (`legacy_source_url`, `url`).
- 56 pages = 50 states + District of Columbia + American Samoa, Guam, Northern Mariana Islands, Puerto Rico, Virgin Islands.
  Full list with USPS, state FIPS, version ids and hashes: `packets/doj_state_pages.jsonl`.

### 4.2 State page section taxonomy (3,055 section-scoped links, 2,888 unique URLs, 1,550 hosts, 56 pages)

| H2 (as published) | H3 sub-labels (as published) | Links | Pages |
|---|---|---|---|
| U.S. Appellate Courts | - | 55 | 55 |
| U.S. District Courts | - | 93 | 54 |
| U.S. Bankruptcy Courts | - | 93 | 54 |
| State and Local Courts | State Judiciary 78; Supreme Court 87; Courts of Appeal 114; Local/Lower Courts 137; Court Forms and Administration 111; Criminal Information 118 (+ state-specific variants: Court of Criminal Appeals, Superior Court, Court of Special Appeals, Supreme Court of Appeals, District Judiciary) | 661 | 54 |
| Legal Ethics and Attorney Regulation | - | 432 | 54 |
| Legislature and Laws | Laws, Codes and Statutes 159; Legislative Materials 134 | 299 | 55 |
| State Executive and Regulatory Information | Governor's Office 134; Office of the Attorney General 104; Regulations 109 (DC: Mayor's Office) | 354 | 52 |
| Local Government | County & Municipal Information 214; Municipal Codes 130 | 357 | 53 |
| State Agencies & Offices | - | 588 | 53 |
| General Resources | - | 86 | 38 |
| Territory variants | "Agencies & Offices" (2 pages), "State and Local" (1), "Executive and Regulatory Information" (2), "Local Courts" (1), "U.S. District and Bankruptcy Courts" (1) | 37 | - |

- Links per page: states 45-82 (Texas 82, California 77, Washington 76, New York 73; Nevada/New Mexico 45); DC 36;
  territories 11-32 (American Samoa 11, N. Mariana 13, Guam 15, Virgin Islands 31, Puerto Rico 32). 17-20 labelled
  sub-sections per state page, 6-12 for territories.
- There is **no "open data" section** on DOJ pages. Open-data portals (e.g. `data.nj.gov`) appear, when present, under
  "State Agencies & Offices" or "General Resources"; do not invent an open-data label - derive a separate
  `resource_type` facet from host/text evidence and keep the published label untouched.
- Attorney General material is an H3 ("Office of the Attorney General") under "State Executive and Regulatory
  Information": typically AG home, Opinions, Reports/Statistics, Forms. Regulations H3 typically = Administrative
  Code + Register + OAL/administrative hearings decisions.
- Scheme mix: 1,717 https / 1,338 http (many legacy http links; link liveness NOT verified). 61 within-page duplicate URLs.
- In-page "Updated" footer: present on 56 of 57 pages; 28 pages dated 2026, 27 dated 2025, Virginia April 17, 2024;
  newest September 1, 2026 (Connecticut, Georgia, New York, Vermont).
- Most frequent outbound hosts: publicrecords.netronline.com 51, library.municode.com 46, codelibrary.amlegal.com 40,
  www.findlaw.com 33, www.generalcode.com 30, www.in.gov 30, law.indiana.libguides.com 25, www.mass.gov 22,
  www.txcourts.gov 21, www.oscn.net 16, caselaw.findlaw.com 14.
- New Jersey example (60 links, 19 sub-sections, "Updated January 6, 2026"): every URL named in the user request is on the
  page with a published label - Statutes (`lis.njleg.state.nj.us/nxt/gateway.dll/statutes/1...`, Laws, Codes and Statutes),
  AG Reports and Statistics (`nj.gov/oag/library_reports_stats.html`, Office of the Attorney General), Register
  (`lexisnexis.com/hottopics/njoal/`, Regulations), NJ County and Municipal Web Sites
  (`nj.gov/nj/gov/county/localgov.shtml`, County & Municipal Information). NJ overlap with catalog: 56 of 59 URLs.

### 4.3 Federal page `https://www.justice.gov/jmd/ls/federal` (captured by scout; "Updated April 30, 2026")
- 146 links / 143 unique. H2 "U.S. Appellate Courts" with H3 per court: U.S. Supreme Court 12, General Information 2,
  First-Eleventh Circuit (6-17 each), DC Circuit 4, Federal Circuit 3; H2 "District/Bankruptcy Courts" 1; "Special
  Courts" 5; "Federal Court Rules and Procedures" 5; "General Federal Resources" 12.
- 56 of the 143 are links back to the state pages (circuit -> member states: a free, published circuit-to-state mapping).
  Of the ~87 external URLs, 86 are already in the catalog by normalized URL; all 143 hosts are in the catalog.

## 5. FindLaw caselaw

- **Reachability:** HTTP 200 to plain curl with the research UA, served from Cloudflare cache (`CF-Cache-Status: HIT`);
  no interstitial. The HTML contains a Cloudflare Turnstile widget in the footer form only (not a page gate). Real content
  present: H1 "United States legal research", H2 "Browse United States Courts".
- **Structure:** one flat alphabetical list, 306 anchors / **277 unique court slugs**, relative hrefs resolving to
  `https://caselaw.findlaw.com/court/<slug>`; by label 75 federal-looking (SCOTUS, circuits, BAPs, judicial councils,
  16 district-court slugs, CIT, CCPA, military commission review) and 202 state/territory. No grouping by state and no
  dates on the index. Slugs are machine-generated and duplicative (at least 6 Fifth Circuit variants, e.g.
  `us-5th-circuit`, `us-crt-app-fif-ct`, `us-crt-app-fif-cir`, `...-uni-a`), so a slug is NOT a court identifier; map to
  CourtListener court ids by reviewed label only. Extracted list: `doj_findlaw_scout_evidence/findlaw_court_index_extracted.json`.
- **Scale:** `sitemapindex.xml` lists 1,677 child sitemaps (`/sitemapcases/<court-slug>/sitemapN.xml`,
  `/sitemapsupremecourt/sitemapN.xml`) - opinion-level URLs number in the millions (not counted; children not fetched).
- **robots.txt (caselaw.findlaw.com):** `Disallow: /cdn-cgi/`, `/wp-admin/` (allow admin-ajax); sitemap declared; no
  crawl-delay. Everything under `/court/` is robots-allowed.
- **Terms:** the FindLaw Terms of Use page delegates to the Internet Brands Terms of Use (page says updated August 30, 2023).
  Those terms prohibit copying, aggregation or derivative use of site content by spiders, robots, crawlers or scrapers,
  with a limited exception for general-purpose search engines and noncommercial public archives that link back, use a
  stable IP and identifiable agent, and obey robots.txt. A law-firm research corpus is neither.
- **Barrier recorded:** contractual (terms), not technical. Recommendation: keep FindLaw as **reference-only** directory
  entries (court name + URL, `access_requirements=terms_restrict_automated_copying`); source the opinions themselves from
  CourtListener bulk data / Caselaw Access Project / official court sites. The catalog already holds 66 findlaw URLs
  (15 on caselaw.findlaw.com; only 1 of the 277 court index URLs). DOJ pages link to findlaw 47 times (33 www + 14 caselaw).

## 6. Proposed record schema: `state_legal_resource_map` (one row per published link occurrence)

```
record_id                 "slrm-" + sha256(page_url | section_path | url | ordinal)[:12]
jurisdiction_label        as published in H1 ("New Jersey"); never inferred from the outbound host
usps / state_fips         "NJ" / "34" (2-char strings; territories AS 60, GU 66, MP 69, PR 72, VI 78; DC 11)
jurisdiction_class        state | federal_district(DC) | territory | federal (federal page)
directory_publisher       "U.S. Department of Justice, Justice Management Division, Library Staff"
page_url / legacy_page_url  canonical slug URL / .htm form published on the index
section_h2 / section_h3   labels exactly as published (nullable H3)
section_path              "Legislature and Laws > Laws, Codes and Statutes"
section_norm              controlled value (see mapping below); published label is never overwritten
ordinal_on_page           integer document order (keeps duplicates distinct)
link_text                 anchor text as published
url / url_normalized / host / scheme
evidence_line             enclosing li/p text, <= 240 chars
federal_court_ref         for the three U.S. court sections: circuit number / district name as published
page_updated_label        "January 6, 2026" as published + page_updated_date ISO; basis="publisher in-page footer"
capture_version_id / capture_raw_sha256 / capture_raw_path / capture_date   from documents.sqlite3 versions
source_snapshot_date      = capture_date (date the directory page was observed)
directory_ref_ids         [pld-...] catalog ids matched by exact or normalized URL; match_basis exact|normalized|none
link_status               "not_checked" until a separate bounded liveness packet runs
```
Relationships this enables: reference -> jurisdiction (published evidence), reference -> resource type, circuit -> states
(federal page), district/bankruptcy court -> state, saved DOJ page -> every reference it lists.

Suggested `section_norm` mapping (DOJ label -> existing catalog category): Laws, Codes and Statutes -> `statutes_codes`;
Legislative Materials -> `legislative_materials`; Regulations -> `regulations_register`; Office of the Attorney General ->
`attorney_general`; Governor's Office -> `executive_orders_governor`; Court Forms and Administration -> `court_forms`
(split rules vs forms by link text only when the text says "Rules"); State Judiciary / Supreme Court / Courts of Appeal /
Local/Lower Courts -> `courts_state` with court_level; U.S. Appellate / District / Bankruptcy Courts -> `courts_federal`;
Legal Ethics and Attorney Regulation -> `attorney_admission_discipline`; County & Municipal Information ->
`local_government`; Municipal Codes -> `municipal_codes`; Criminal Information -> `corrections_criminal_records`;
State Agencies & Offices -> `state_agencies`; General Resources -> `general_reference`. Category names not already in
`source-category-v1` need the taxonomy owner's sign-off.

## 7. Parser rules used (reproducible, lxml)
Root = first `<article>` (fallback `<main>`); walk in document order; `h2` sets section and clears H3; `h3` sets
sub-section; keep `a[href]` only after the first H2; drop `#` anchors, `mailto:`, Facebook/X/LinkedIn share links;
resolve relative hrefs against the canonical page URL; evidence = nearest `li|p|td|div` ancestor text; page date =
regex `Updated <Month D, YYYY>` in the article text. The "Disclaimer" H2 carries no links. Full preview output
(3,118 rows incl. 63 index rows): `doj_findlaw_scout_evidence/doj_state_links_extracted_preview.jsonl`
(sha256 b3851e5b6f2bab52b9e5aa8c2787341e8ca2cf9cb13b9216eeeb875e35ee8d94) - a scout preview, not a validated supplement.

## 8. Capture packet `packets/doj_state_pages.jsonl` (58 lines; sha256 eaa2c69c...87b98401)
- 57 lines `action=reuse_saved_capture` (index + 56 pages) with version_id, raw_path, raw_sha256, bytes, retrieved_at,
  published update label, link/section counts, USPS, FIPS, jurisdiction class, robots facts.
- 1 line `action=ingest_scout_capture_or_recapture` for `/jmd/ls/federal` (scout copy is decoded bytes + header dump; the
  integrator may prefer one clean recapture through `pipeline/corpus_crawler.py` to get a standard receipt).
- No FindLaw packet is proposed (terms barrier).

## 9. Not verified
- Liveness/redirect status of the 2,885 outbound URLs (no outbound link was requested).
- The 54 state pages other than New Jersey were not re-fetched; "no drift" is shown for the index and NJ only.
- FindLaw child sitemaps, per-court pages and opinion pages (not fetched); opinion counts are not measured.
- Whether `www.findlaw.com/robots.txt` differs from the caselaw host's (not fetched; request budget).
- Registrable-domain overlap uses a crude suffix rule, not the Public Suffix List.
- DOJ label -> category mapping is a proposal; no catalog entry was changed.
- Scout working files `_work_*.json` in the evidence folder are intermediate and can be ignored.
