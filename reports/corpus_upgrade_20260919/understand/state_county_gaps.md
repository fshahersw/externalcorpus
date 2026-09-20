# State and county coverage / gap audit (saved data only)

Generated 2026-09-19 for the corpus-upgrade "understand" phase. Read-only: every SQLite database was opened
with `mode=ro`, no network request was made, no existing project file was changed. Machine-readable detail is in
`coverage_matrix.json`; the acquisition shortlist is `packets/gap_fill_candidates.jsonl` (99 exact URLs).
Builders (re-runnable, read-only): `state_county_gaps_build.py`, `state_county_gaps_candidates.py`,
`state_county_gaps_finalize.py`; intermediate data in `_work/`.

## 1. What was measured

| Layer | Source | What a count means |
|---|---|---|
| Official captures | `delivery/archive-directory/directory.sqlite3`, dataset `focused` (+ `pending_publication`) | Saved official pages/files. Tiered by record kind: **body** (chapter body, verified document derivative, text fragment), **unreviewed** (`needs_content_review`, `law_document_title_evidence_needs_review` - text exists but is often a hub/index page), **navigation**. |
| Imported collection | same DB, dataset `seeger` | 5,856 NJ statute provisions, 4,379 state court forms/other documents, 74 state rules/orders (state-labelled only; federal excluded here). |
| Third-party structured law | `sources/open_us_law_20260918/catalog.sqlite3` (Open US Law v2026.08, publisher date 2026-08-14) | Exported rows, not unique sections; not official captures; `in_force` flags are publisher assertions. |
| County layer | `records` + `record_counties` (5-char FIPS) + `counties` registry | County-linked records only. Host-based matches are reported separately and are **not** county assignments. |
| Trellis county profiles | `sources/trellis/catalog/catalog.sqlite3` | observed = distinct `coverage_county` link URLs; saved = pages with status 200. |
| Source directory | `sources/public_law_directory_20260919/catalog.json` (9,348 references) + `source_archive_links_20260919/links.jsonl` | References, not downloads. "linked" = reference already tied to a saved record by exact URL. |

Totals for the 50 states + DC: Open US Law statutes 1,919,001 rows, constitutions 13,206, regulations 303,067
(16 states only), court rules 41,692 (42 of 51); county layer 186 published + 24 pending local-rule records,
74 + 14 form/fee records, 150 clerk pages, 145 court local-resource pages, 1,572 county-site pages;
Trellis 1,432 saved of 2,505 observed county profiles (catalog-wide 1,433 of 2,510 including 2 federal and
4 malformed URLs; the directory publishes 1,438 profile records including 6 Illinois browser captures).

## 2. Headline findings

1. **Confirmed official law bodies are thin; the corpus leans on Open US Law, and a large unclassified tier
   hides real bodies.** Records *classified* as official statute bodies exist for only 6 states (NC 261 chapter
   PDFs + 53 awaiting publication, PA 148, CO 94, NE 90, IA 2, WY 1) plus the imported NJ statute export
   (5,856 provisions). 39 states have official statute captures only in the unreviewed or navigation tiers;
   GA, IN, NH, NY, SD have no official statute capture at all. But the unreviewed tier is not all hubs: by saved
   text size it holds 2,793 statute pages of >= 20,000 characters and 3,308 of 2,000-20,000 (NV 678, ID 529,
   ND 492, WI 396, CT 150 large pages) and 284 + 769 court-rule pages (KS 432 mid-size rule pages). These are
   probably section/chapter bodies waiting for classification - a review task, not an acquisition task (3.1).
2. **Georgia is the only true statute hole.** GA and NC statutes were withdrawn by the Open US Law publisher.
   NC is largely covered by 314 official chapter PDFs (incl. chs. 1, 1A, 1D, 8C, 28A, 75, 99B); GA has **zero**
   statute text from any source. Every statutory topic check returns zero for GA.
3. **Administrative regulations: 34 states have nothing from any source** (flag `ZERO_REGULATIONS_ANY_SOURCE`),
   including CA, NY, NJ, PA, FL, MO, MA, MI, GA, NC, NV, CT, WV. The only official regulation captures are
   Louisiana (302 administrative-code document derivatives). Open US Law has regulations for CO, DE, ID, IL, KY,
   ME, MD, MN, NM, OH, SC, SD, TX, VA, WA, WI.
4. **Statewide court rules: MO and OK have zero from any source**; AR, CO, KY, NJ, NM, SD, VT are absent from
   Open US Law and exist locally only as a few unreviewed pages (2-12 records each, mostly hubs). Records
   classified as official court-rule *bodies* exist for one state (NE, 6 records); the rest of the official
   court-rule layer is unreviewed (KS 444, DE 63, WV 60, HI 54 ...) and mixes hubs with real rule pages (WV's
   civil-procedure and evidence contents pages are already saved). CT, DC, LA, MI, NH, NC, TN have no official
   court-rule capture.
5. **Court-rule sets lack a rule-type field.** Open US Law rows carry only a publisher chapter name. By keyword,
   13 states show no evidence-labelled set and 6 no civil-labelled set - mostly code states where these live in
   statutes (CA, NY, KS, WI, LA, GA, OR, NE, FL, HI), but IL (Rules of Evidence), MA and DC are genuine rule gaps.
6. **Mass-tort coordination programmes are almost unrepresented.** Local full-text hits: NJ multicounty
   litigation 3 (all forms), CA JCCP 5 (forms), Philadelphia mass tort 12 (incl. General Court Regulations
   2023-01 and 02-2025 and the compiled civil local rules), NY Litigation Coordinating Panel 0, WV Mass
   Litigation Panel 6 (judge records only), medical monitoring 3. The CA JCCP coordination log PDF
   (8.4 MB, 1.74 M characters) is saved in the capture index but **not published** in the directory.
7. **High-volume venues have essentially no county-linked legal content.** None of the 10 primary venues has a
   county-linked local rule, form or clerk page. Philadelphia (42101), St. Louis City (29510) and St. Clair
   (17163) have 0 county-linked records; New York County has 1 (an unreviewed county-site page). Content that
   does exist is unlinked: 121 courts.phila.gov documents and 31 LA Superior Court documents (court blob storage) sit in the imported
   collection with no county/FIPS link.
8. **Trellis profile saving stopped alphabetically mid-state.** 31 states are partial and in 26 of them every
   saved slug sorts before every unsaved slug (PA stops at "indiana", NY at "nassau", MO at "lawrence", IL at
   "marshall"). Missing because of this: Philadelphia, New York, Queens, Suffolk, Westchester, St. Louis City,
   St. Louis County, St. Clair, Will, Wayne MI, Richland SC, Santa Fe, Tarrant, Travis, NJ Somerset/Sussex/
   Union/Warren. Seven states have no observed Trellis county pages at all (AL, AK, KY, MS, NE, UT, WY).
9. **County local rules are one-state deep.** 160 of 210 local-rule records are Washington; FL 29, OH 8, and
   40 states have none. 26 states have no county form record; 28 have no clerk page.
10. **Statewide forms are missing for 11 states** (CT, DC, FL, GA, ID, MA, MI, NC, OK, SC, TN) while WA (624),
    WY (602), NM (408), OH (383), PA (308), IL (303), TX (269) dominate the 4,379 imported state forms.
11. **The source directory can fill state-level gaps but not venue gaps.** It holds hubs for regulations, rules,
    forms, jury instructions and coordination programmes, yet has **no reference** for St. Louis City, Madison,
    St. Clair, Middlesex/Atlantic vicinages, New York County Supreme Civil, Harris County district courts/clerk,
    the LA Superior Court site, the NY Litigation Coordinating Panel, or NJ's Rules of Court hub.
12. **Many hubs are already saved - the gap is one level down.** 17 reviewed URLs were dropped from the packet
    as already saved (14 directory references such as the OSCN rules index, AR court-rules navigator, VT rules
    page, WV court-rules page, GA Supreme Court rules, NC General Statutes landing page, plus 3 WV child pages).
    The hub pages carry 500-14,000 characters of index text and no rule bodies.

## 3. Per-state matrix

Columns: OUL = Open US Law rows. "civ/evid/app" = rows whose publisher chapter name contains civil / evidence /
appellate (heuristic). Official = `focused` dataset tiers. County local rules show records (distinct counties).
Src-dir = references tagged to the state (already linked to a saved record).

| State | OUL statutes | OUL const. | OUL regs | OUL court rules (civ/evid/app label rows) | Official statutes body/unrev/nav | Official court rules body/unrev | Official regs | Imported forms | Imported rules/orders | Counties | Trellis saved/observed | County local rules (counties) | County forms | Clerk pages | Src-dir refs (linked) |
|---|---:|---:|---:|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---|
| AL | 45,984 | 381 | 0 | 870 (112/77/89) | 0/1/0 | 0/25 | 0 | 21 | 0 | 67 | 0/0 | 0 (0) | 1 | 1 | 113 (10) |
| AK | 17,935 | 243 | 0 | 763 (151/75/86) | 0/3/0 | 0/45 | 0 | 50 | 0 | 30 | 0/0 | 0 (0) | 0 | 0 | 124 (10) |
| AZ | 22,674 | 646 | 0 | 1,718 (300/68/99) | 0/99/47 | 0/11 | 0 | 5 | 1 | 15 | 15/15 | 0 (0) | 0 | 0 | 189 (8) |
| AR | 36,936 | 513 | 0 | 0 (0/0/0) | 0/4/0 | 0/3 | 0 | 168 | 1 | 75 | 74/75 | 1 (1) | 3 | 14 | 87 (7) |
| CA | 161,566 | 362 | 0 | 1,521 (301/0/481) | 0/1/0 | 0/39 | 0 | 155 | 13 | 58 | 51/51 | 0 (0) | 0 | 4 | 366 (20) |
| CO | 34,231 | 424 | 610 | 0 (0/0/0) | 94/102/0 | 0/2 | 0 | 79 | 0 | 64 | 64/64 | 0 (0) | 0 | 4 | 92 (9) |
| CT | 16,082 | 174 | 0 | 1,723 (0/58/0) | 0/270/0 | 0/0 | 0 | 0 | 0 | 9 | 8/8 | 0 (0) | 0 | 0 | 90 (2) |
| DE | 21,649 | 225 | 1,164 | 1,385 (535/82/0) | 0/1/0 | 0/63 | 0 | 5 | 0 | 3 | 4/4 | 0 (0) | 0 | 0 | 192 (16) |
| DC | 23,694 | 0 | 0 | 1,128 (223/0/55) | 0/5/0 | 0/0 | 0 | 0 | 0 | 1 | 1/1 | 0 (0) | 0 | 0 | 119 (2) |
| FL | 24,866 | 217 | 0 | 936 (117/0/57) | 0/52/0 | 0/1 | 0 | 0 | 0 | 67 | 65/67 | 29 (19) | 17 | 2 | 96 (4) |
| GA | 0 | 287 | 0 | 1,174 (0/0/53) | 0/0/0 | 0/12 | 0 | 0 | 0 | 159 | 75/159 | 2 (2) | 9 | 5 | 81 (4) |
| HI | 19,197 | 171 | 0 | 1,259 (222/0/120) | 0/8/0 | 0/54 | 0 | 11 | 1 | 5 | 5/5 | 0 (0) | 0 | 0 | 67 (7) |
| ID | 22,754 | 240 | 8,551 | 766 (118/82/94) | 0/1573/0 | 0/34 | 0 | 0 | 0 | 44 | 21/44 | 0 (0) | 1 | 1 | 79 (7) |
| IL | 72,456 | 170 | 53,584 | 839 (146/0/82) | 0/1/0 | 0/26 | 0 | 303 | 3 | 102 | 49/84 | 3 (3) | 7 | 13 | 98 (7) |
| IN | 83,148 | 196 | 0 | 879 (4/64/82) | 0/0/0 | 0/6 | 0 | 43 | 0 | 92 | 44/92 | 0 (0) | 3 | 2 | 155 (8) |
| IA | 28,223 | 190 | 0 | 1,294 (309/64/85) | 2/19/0 | 0/3 | 0 | 26 | 0 | 99 | 47/98 | 0 (0) | 1 | 3 | 93 (8) |
| KS | 24,361 | 229 | 0 | 434 (0/0/76) | 0/117/0 | 0/444 | 0 | 1 | 0 | 105 | 50/105 | 0 (0) | 3 | 2 | 73 (5) |
| KY | 20,894 | 274 | 4,865 | 0 (0/0/0) | 0/12/0 | 0/12 | 0 | 44 | 0 | 120 | 0/0 | 0 (0) | 5 | 2 | 141 (14) |
| LA | 43,512 | 328 | 0 | 481 (0/0/108) | 0/13/0 | 0/0 | 302 | 5 | 0 | 64 | 4/4 | 0 (0) | 1 | 1 | 71 (4) |
| ME | 25,316 | 153 | 1,718 | 722 (171/76/32) | 0/131/0 | 0/46 | 0 | 10 | 1 | 16 | 12/12 | 0 (0) | 0 | 0 | 97 (11) |
| MD | 39,552 | 312 | 12,863 | 1,220 (231/62/114) | 0/7/0 | 0/9 | 0 | 19 | 0 | 24 | 18/24 | 0 (0) | 1 | 0 | 95 (4) |
| MA | 23,152 | 104 | 0 | 970 (109/0/76) | 0/18/0 | 0/3 | 0 | 0 | 0 | 14 | 14/14 | 0 (0) | 0 | 0 | 133 (10) |
| MI | 40,658 | 307 | 0 | 1,025 (103/65/58) | 0/1/0 | 0/0 | 0 | 0 | 0 | 83 | 40/45 | 1 (1) | 5 | 0 | 70 (2) |
| MN | 27,747 | 138 | 15,447 | 958 (150/64/70) | 0/119/0 | 0/30 | 0 | 28 | 0 | 87 | 41/87 | 0 (0) | 1 | 0 | 390 (63) |
| MS | 158,688 | 318 | 0 | 794 (145/69/58) | 0/1/0 | 0/1 | 0 | 56 | 0 | 82 | 0/0 | 0 (0) | 2 | 4 | 68 (6) |
| MO | 29,309 | 445 | 0 | 0 (0/0/0) | 0/2/0 | 0/0 | 0 | 2 | 0 | 115 | 55/115 | 1 (1) | 1 | 14 | 148 (9) |
| MT | 30,514 | 196 | 0 | 238 (118/63/40) | 0/54/0 | 0/36 | 0 | 53 | 0 | 56 | 27/43 | 1 (1) | 1 | 16 | 117 (24) |
| NE | 25,997 | 448 | 0 | 734 (66/0/42) | 90/95/0 | 6/12 | 0 | 88 | 0 | 93 | 0/0 | 0 (0) | 11 | 18 | 102 (9) |
| NV | 48,190 | 234 | 0 | 1,338 (220/3/56) | 0/911/0 | 0/42 | 0 | 3 | 0 | 17 | 2/2 | 0 (0) | 0 | 0 | 61 (3) |
| NH | 25,375 | 157 | 0 | 970 (0/74/0) | 0/0/0 | 0/0 | 0 | 1 | 0 | 10 | 10/10 | 0 (0) | 0 | 0 | 139 (0) |
| NJ | 55,993 | 216 | 0 | 0 (0/0/0) | 0/0/0 | 0/3 | 0 | 91 | 0 | 21 | 17/21 | 0 (0) | 1 | 0 | 136 (17) |
| NM | 34,455 | 299 | 13,270 | 0 (0/0/0) | 0/1/0 | 0/2 | 0 | 408 | 0 | 33 | 16/33 | 0 (0) | 0 | 0 | 83 (4) |
| NY | 40,140 | 204 | 0 | 1,088 (261/0/39) | 0/0/0 | 0/0 | 0 | 5 | 1 | 62 | 30/62 | 0 (0) | 2 | 0 | 224 (0) |
| NC | 0 | 155 | 0 | 495 (89/66/157) | 261/5/0 | 0/0 | 0 | 0 | 0 | 100 | 48/99 | 0 (0) | 2 | 1 | 86 (5) |
| ND | 29,042 | 203 | 0 | 2,246 (309/187/250) | 0/2559/0 | 0/6 | 0 | 58 | 0 | 53 | 25/53 | 0 (0) | 0 | 3 | 65 (7) |
| OH | 33,161 | 266 | 19,909 | 1,167 (124/63/35) | 0/36/0 | 0/28 | 0 | 383 | 1 | 88 | 42/86 | 8 (6) | 6 | 10 | 224 (29) |
| OK | 35,329 | 545 | 0 | 0 (0/0/0) | 0/21/0 | 0/0 | 0 | 0 | 0 | 77 | 37/77 | 0 (0) | 1 | 12 | 95 (5) |
| OR | 36,202 | 415 | 0 | 632 (96/0/166) | 0/158/0 | 0/4 | 0 | 5 | 0 | 36 | 17/36 | 0 (0) | 0 | 0 | 189 (6) |
| PA | 14,571 | 186 | 0 | 1,722 (704/63/113) | 148/227/0 | 0/12 | 0 | 308 | 1 | 67 | 32/67 | 3 (3) | 1 | 13 | 117 (5) |
| RI | 21,107 | 118 | 0 | 1,033 (157/67/41) | 0/51/0 | 0/4 | 0 | 11 | 0 | 5 | 5/5 | 0 (0) | 0 | 0 | 76 (6) |
| SC | 29,947 | 245 | 6,606 | 557 (90/61/276) | 0/66/0 | 0/20 | 0 | 0 | 0 | 46 | 22/46 | 0 (0) | 2 | 5 | 98 (11) |
| SD | 39,589 | 294 | 28,988 | 0 (0/0/0) | 0/0/0 | 0/1 | 0 | 51 | 0 | 66 | 32/61 | 0 (0) | 0 | 0 | 211 (6) |
| TN | 32,693 | 152 | 0 | 626 (284/65/88) | 0/1/0 | 0/0 | 0 | 0 | 0 | 95 | 45/54 | 0 (0) | 0 | 0 | 295 (23) |
| TX | 122,535 | 401 | 44,247 | 1,007 (627/72/92) | 0/1/0 | 0/25 | 0 | 269 | 37 | 254 | 120/254 | 1 (1) | 0 | 0 | 141 (8) |
| UT | 25,880 | 189 | 0 | 919 (126/80/69) | 0/7/0 | 0/12 | 0 | 12 | 10 | 29 | 0/0 | 0 (0) | 0 | 0 | 80 (5) |
| VT | 23,521 | 120 | 0 | 0 (0/0/0) | 0/1/0 | 0/3 | 0 | 33 | 0 | 14 | 14/14 | 0 (0) | 0 | 0 | 143 (8) |
| VA | 33,857 | 134 | 22,396 | 358 (40/73/48) | 0/161/0 | 0/1 | 0 | 186 | 1 | 133 | 55/143 | 0 (0) | 0 | 0 | 109 (7) |
| WA | 51,498 | 282 | 51,026 | 1,182 (239/67/226) | 0/106/0 | 0/16 | 0 | 624 | 0 | 39 | 19/39 | 160 (36) | 0 | 0 | 184 (9) |
| WV | 25,664 | 209 | 0 | 1,116 (188/63/51) | 0/9/0 | 0/60 | 0 | 152 | 3 | 55 | 26/55 | 0 (0) | 0 | 0 | 162 (9) |
| WI | 18,158 | 175 | 17,823 | 395 (0/0/0) | 0/484/0 | 0/15 | 0 | 5 | 0 | 72 | 34/72 | 0 (0) | 0 | 0 | 110 (9) |
| WY | 20,999 | 316 | 0 | 1,010 (197/64/112) | 1/45/0 | 0/1 | 0 | 602 | 0 | 23 | 0/0 | 0 (0) | 0 | 0 | 87 (7) |

### 3.1 Unreviewed official pages by saved text size

States with at least 40 unreviewed statute/court-rule pages of 2,000+ characters. Large pages are likely real
bodies awaiting classification (per-state numbers: `states.<ST>.directory.unreviewed_text_size`). Size is a
triage signal only; nothing here was read or legally reviewed.

| State | Statute pages >=20k / 2k-20k / <2k chars | Court-rule pages >=20k / 2k-20k / <2k chars |
|---|---|---|
| AK | 1 / 1 / 1 | 22 / 18 / 5 |
| CO | 95 / 7 / 0 | 1 / 1 / 0 |
| CT | 150 / 76 / 44 | 0 / 0 / 0 |
| FL | 0 / 52 / 0 | 0 / 0 / 1 |
| HI | 0 / 7 / 1 | 28 / 24 / 2 |
| ID | 529 / 943 / 101 | 17 / 8 / 9 |
| KS | 22 / 95 / 0 | 12 / 432 / 0 |
| ME | 62 / 41 / 28 | 25 / 16 / 4 |
| MN | 2 / 117 / 0 | 11 / 19 / 0 |
| NE | 52 / 42 / 1 | 0 / 12 / 0 |
| NV | 678 / 216 / 17 | 30 / 10 / 2 |
| ND | 492 / 1192 / 875 | 1 / 4 / 1 |
| OH | 0 / 16 / 20 | 21 / 5 / 2 |
| OR | 92 / 45 / 21 | 0 / 4 / 0 |
| PA | 76 / 33 / 118 | 0 / 11 / 1 |
| SC | 0 / 35 / 31 | 5 / 7 / 3 |
| VA | 70 / 70 / 21 | 1 / 0 / 0 |
| WA | 1 / 105 / 0 | 1 / 5 / 10 |
| WV | 0 / 9 / 0 | 16 / 29 / 15 |
| WI | 396 / 83 / 5 | 3 / 12 / 0 |
| WY | 43 / 1 / 1 | 0 / 1 / 0 |

Flag lists (full per-state flags in `coverage_matrix.json` -> `states.<ST>.flags`, index in `flag_index`):

- `open_us_law_statutes_absent_publisher_withdrawn`: GA, NC
- `ZERO_COURT_RULES_ANY_SOURCE`: MO, OK
- `open_us_law_court_rules_absent`: AR, CO, KY, MO, NJ, NM, OK, SD, VT
- `no_official_court_rule_capture`: CT, DC, LA, MI, NH, NC, TN
- `no_official_statute_capture`: GA, IN, NH, NY, SD
- `ZERO_REGULATIONS_ANY_SOURCE` (34): AL, AK, AZ, AR, CA, CT, DC, FL, GA, HI, IN, IA, KS, MA, MI, MS, MO, MT, NE,
  NV, NH, NJ, NY, NC, ND, OK, OR, PA, RI, TN, UT, VT, WV, WY
- `no_evidence_labelled_rule_set`: CA, DC, FL, GA, HI, IL, KS, LA, MA, NE, NY, OR, WI
- `no_civil_labelled_rule_set`: CT, GA, KS, LA, NH, WI (CT Practice Book and NH court-level sets are unlabelled, not absent)
- `no_statewide_forms`: CT, DC, FL, GA, ID, MA, MI, NC, OK, SC, TN
- `trellis_no_county_profiles_observed`: AL, AK, KY, MS, NE, UT, WY

## 4. Topical coverage for mass torts (Open US Law full-text)

Phrase queries are recorded verbatim in `coverage_matrix.json` -> `topic_gaps_open_us_law`. Zero hits means the
phrase set was not found; it does not prove the state lacks such law.

| Topic | Total hits | States with zero statute hits | States with zero court-rule hits |
|---|---:|---|---|
| sol_any | 7,887 | 2: GA, NC | n/a (statutory topic) |
| sol_personal_injury | 2,444 | 2: GA, NC | n/a (statutory topic) |
| repose | 109 | 18: AR, CA, DC, GA, IN, KY, ME, MS, MT, NY, NC, RI, SD, UT, VT, WV, WI, WY | n/a (statutory topic) |
| product_liability | 1,255 | 2: GA, NC | n/a (statutory topic) |
| comparative_fault | 712 | 2: GA, NC | n/a (statutory topic) |
| joint_several | 3,276 | 2: GA, NC | n/a (statutory topic) |
| damages_any | 3,544 | 2: GA, NC | n/a (statutory topic) |
| damages_caps | 768 | 3: GA, NC, RI | n/a (statutory topic) |
| udap | 7,462 | 2: GA, NC | n/a (statutory topic) |
| wrongful_death_survival | 1,468 | 2: GA, NC | n/a (statutory topic) |
| class_action | 1,530 | 2: GA, NC | 11: AR, CO, GA, KY, MO, NJ, NM, OK, SD, VT, VA |
| expert_evidence | 1,297 | 2: GA, NC | 13: AR, CA, CO, GA, KS, KY, MO, NJ, NM, OK, SD, VT, WI |
| complex_coordination | 636 | 27: AL, AK, DC, GA, ID, IL, IA, KY, ME, MD, MS, MO, MT, NE, NJ, NM, NY, NC, ND, PA, RI, SD, TN, UT, WV, WI, WY | 16: AR, CO, IN, KY, LA, ME, MI, MO, NJ, NM, NC, OK, RI, SD, VT, VA |
| medical_monitoring | 389 | 19: AK, AR, DC, GA, HI, KY, LA, ME, MD, MA, MS, MT, NJ, NM, NY, NC, OR, RI, VA | n/a (statutory topic) |
| asbestos_silica_claims | 965 | 11: CA, DE, GA, IL, MD, NE, NM, NY, NC, RI, VT | n/a (statutory topic) |
| affidavit_certificate_of_merit | 53 | 33: AL, AK, AZ, AR, CO, CT, DC, FL, GA, ID, IN, KS, ME, MA, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NC, ND, OR, PA, SC, SD, TN, VA, WI, WY | n/a (statutory topic) |
| forum_non_conveniens_venue | 186 | 2: GA, NC | n/a (statutory topic) |

Reading the table:

- SOL, product liability, comparative fault, joint/several, damages, UDAP, wrongful death/survival, class
  action and forum non conveniens phrases are found in the statutes of **every state except GA and NC** - i.e.
  the only statutory blind spot is the withdrawn pair, and NC is covered by official PDFs outside this index.
- Statutes of repose: 18 states return nothing under the "repose" wording; these need citation-level mapping
  (many states phrase repose as an outer limitation period), not new acquisition.
- Class-action and expert-testimony **court rules** are missing exactly where court rules are missing
  (AR, CO, GA-label, KY, MO, NJ, NM, OK, SD, VT, VA for class actions), confirming finding 4.
- Coordination rules: CA (CRC 3.500 series and CCP 404) and TX/NY text is present in Open US Law, but NJ
  (R. 4:38A, Directive 02-19), PA, MO, IL and WV return nothing - these are programme pages, directives and
  general court regulations that live outside codified sets.
- Medical monitoring: 389 hits, 216 of them federal regulations; statutory hits are incidental (occupational
  health). This is case-law doctrine; do not expect statutes. Same for affidavit/certificate of merit outside
  the 18 states that codify it.

Recommended topic tags for the platform (derive from citations + phrase hits, keep the query as provenance):
`sol`, `repose`, `product_liability`, `comparative_fault`, `joint_several`, `damages_cap`, `punitive`, `udap`,
`wrongful_death_survival`, `class_action`, `expert_evidence`, `complex_coordination`, `medical_monitoring`,
`asbestos_silica`, `merit_affidavit`, `forum_venue`.

## 5. Complex-litigation programmes: what is saved vs. referenced

| Programme | Saved locally | Source-directory references (not yet saved unless noted) |
|---|---|---|
| NJ Multicounty Litigation | 3 forms mention it (Civil CIS, notice of appearance, CBLP guidelines); no MCL page, order or case list; NJ court rules absent everywhere | `pld-30ed683d1495` njcourts.gov/attorneys/multicounty-litigation; `pld-a4e45ac43145` Directive 02-19 (historical HTTP 403) |
| CA JCCP | 5 forms; CRC civil rules in Open US Law (301 rows); JCCP log PDF saved but unpublished | `pld-6f290c940224` (already saved - publish it) |
| Philadelphia Complex Litigation Center | GCR 2023-01, GCR 02-2025 mass tort protocols, compiled civil local rules, civil cover sheets (imported, no county link) | `pld-346a82441b38` mass-tort docket and liaison counsel list; `pld-3f9b910c4849` civil programme page; `pld-a5205c841d48` local rules; `pld-5cb50ae53478` forms |
| TX MDL Panel | 4 imported Texas documents mention it; Rules of Judicial Administration (20 rows) in Open US Law | `pld-1b17513c52f3` panel page; `pld-a7d059e8c6fc` available MDL cases |
| WV Mass Litigation Panel | Only judge records mention it; WV Trial Court Rules in Open US Law (258 rows) | `pld-b1ec3b0a8b5f` Supreme Court orders; annual reports 2023-2025 (`pld-8a55b4a80050`, `pld-fa071038cf85`, `pld-dc1556930c52`); MLP page and TCR contents observed on the saved WV rules hub |
| NY Litigation Coordinating Panel | 0 hits | No reference in the directory; nearest are Part 202 pages (`pld-1359137cbfb3`, `pld-e8f3adde33db`) |
| CT Complex Litigation Docket | none | `pld-8234b24db4c2` (historical HTTP 503) |
| IL, MO (St. Louis City), DE (Superior Court complex/asbestos), MA, MN | none found | **No directory reference** - needs new source discovery |

## 6. High-volume mass-tort venues

`*` = secondary venue. "Saved docs on court host" counts directory records whose source URL is on the venue's
court host; they are statewide-labelled and carry no FIPS link, so the county page cannot show them today.

| Venue (FIPS) | Trellis profile | County-linked records | Local rules / forms / clerk linked | Saved docs on court host (not county-linked) | Src-dir refs on court host |
|---|---|---:|---|---:|---:|
| Philadelphia County, PA (42101) | observed_not_saved | 0 | no / no / no | 121 | 11 |
| Cook County, IL (17031) | saved | 3 | no / no / no | 0 | 3 |
| Los Angeles County, CA (06037) | saved | 3 | no / no / no | 31 | 0 |
| St. Louis City, MO (29510) | observed_not_saved | 0 | no / no / no | 1 | 0 |
| Madison County, IL (17119) | saved | 1 | no / no / no | 0 | 0 |
| St. Clair County, IL (17163) | observed_not_saved | 0 | no / no / no | 0 | 0 |
| Middlesex County, NJ (34023) | saved | 1 | no / no / no | 0 | 0 |
| Atlantic County, NJ (34001) | saved | 1 | no / no / no | 0 | 0 |
| New York County, NY (36061) | observed_not_saved | 1 | no / no / no | 1 | 0 |
| Harris County, TX (48201) | saved | 1 | no / no / no | 0 | 0 |
| Bergen County, NJ (34003) * | saved | 1 | no / no / no | 0 | 0 |
| St. Louis County, MO (29189) * | observed_not_saved | 1 | no / no / no | 0 | 0 |
| San Francisco County, CA (06075) * | saved | 2 | no / no / no | 6 | 0 |
| Alameda County, CA (06001) * | saved | 3 | no / no / no | 8 | 0 |
| Miami-Dade County, FL (12086) * | saved | 2 | no / no / no | 0 | 7 |
| Clark County, NV (32003) * | saved | 3 | no / no / no | 0 | 0 |
| New Castle County, DE (10003) * | saved | 1 | no / no / no | 1 | 13 |
| Orleans Parish, LA (22071) * | saved | 2 | no / no / no | 0 | 0 |
| Kanawha County, WV (54039) * | saved | 2 | no / no / no | 0 | 3 |
| Allegheny County, PA (42003) * | saved | 1 | no / no / no | 0 | 0 |
| Cuyahoga County, OH (39035) * | saved | 2 | no / no / no | 0 | 0 |
| Fulton County, GA (13121) * | saved | 5 | yes / no / no | 0 | 0 |
| Dallas County, TX (48113) * | saved | 3 | yes / no / no | 2 | 0 |
| Kings County, NY (36047) * | saved | 1 | no / no / no | 0 | 0 |
| Wayne County, MI (26163) * | observed_not_saved | 1 | no / no / no | 0 | 0 |
| Suffolk County, MA (25025) * | saved | 2 | no / no / no | 0 | 0 |
| Hennepin County, MN (27053) * | saved | 1 | no / no / no | 0 | 0 |
| Jackson County, MO (29095) * | saved | 1 | no / no / no | 0 | 0 |

Weakest primary venues, in order: **St. Clair IL, St. Louis City MO** (nothing saved, nothing referenced, Trellis
profile unsaved) -> **Philadelphia PA** (no county link, Trellis unsaved, but 121 imported documents and 11
directory references ready) -> **New York County NY** (Trellis unsaved, 1 site page, NY forms hub only) ->
**Madison IL, Harris TX, Middlesex NJ, Atlantic NJ** (Trellis profile only) -> **Cook IL, Los Angeles CA**
(Trellis + site pages; LA has 31 unlinked imported documents).

A safe linking rule for existing documents: attach a FIPS only when the imported metadata `source_courts`
explicitly names a single-county court (e.g. "Philadelphia County Court of Common Pleas"); never from hostname.
`county_territorial_assignment_verified` is `False` on all imported originals today.

## 7. Gap-fill packet

`packets/gap_fill_candidates.jsonl`: 99 exact URLs, 30 states, 56 hosts, priority 1/2/3 = 13/53/33. 97 are
existing source-directory references (id included); 2 are WV links (Mass Litigation Panel page, Trial Court Rules contents) parsed from a saved official hub
page (marked, not in the directory). Every URL was checked (exact and loose) against the directory DB, the capture
index (`records.source_url`, `versions.final_url`), the pilot acquisition and the link layer; 17 reviewed
references were dropped as already saved (listed under `gap_fill_candidates_summary.reviewed_but_already_saved`).

| Gap type | URLs | Notes |
|---|---:|---|
| complex_litigation_program | 17 | NJ MCL, Phila CLC, TX MDL panel, WV MLP, CT CLD; FL CBL at priority 3 |
| regulations_zero_any_source | 16 | Official hubs for CA, NY, NJ, PA, FL, MO, MA, MI, NV, AL, TN, IN, AR, OK, AZ; CA/NY/NJ codes are vendor-hosted (terms review first) |
| civil_jury_instructions | 12 | CACI 2026 PDF, NJ model civil charges, IL IPI civil, DE, FL, MO MAI, CT, MA, LA, SC; paid PA/TX/NC products excluded |
| statewide_forms_absent | 11 | CT, MA, MI, NC, OK, SC, TN, GA, DC, ID, MO |
| statutes / constitution no official capture | 11 | NY, IN, NH, SD (IN/NH/SD hubs failed to index in an earlier pass - script-rendered sites) |
| court rules (zero / absent / no official) | 11 | MO, NM, KY, DC, LA, NH, NC, TN, MI, CT |
| civil_procedure_evidence_rules | 8 | NY Part 202 and rules index, IL Rules of Evidence, FL rules of court + 2026 civil-procedure PDF, AL Rules of Evidence (WV civil/evidence pages turned out to be saved already) |
| venue_* | 11 | Philadelphia (7), Cook orders, NY forms + NYC Supreme page, MO circuit list |
| statutes_publisher_withdrawn | 2 | GA official code landing page; NC legacy statutes page (priority 3) |

Packet rules still apply (BRIEF): <= 100 URLs and 600 s per packet, >= 2 s per host, no retries. Hosts with a
historical non-200 status in the directory (treat as a barrier, do not route around): courts.mo.gov 403 (4 URLs),
mass.gov 403 (3), jud.ct.gov 503 (4), njcourts.gov 403, nycourts.gov 403, courts.nh.gov 403,
judicial.alabama.gov 503, alabamaadministrativecode.state.al.us 503, govt.westlaw.com 403.

## 8. Data-quality observations found on the way

- 89 published county records carry a multi-state `state` string (71 with a 26-state list, 18 with a 10-state
  list) and 49 county records have a blank state; they fall out of any state filter. 5 law records have no state.
- 30 imported law records belong to territories (Guam 26, Northern Mariana Islands 3, Virgin Islands 1) and are
  outside the 51-jurisdiction matrix.
- 4 Trellis "county" URLs are malformed hostnames (e.g. `/coverage/pennsylvania/www.alleghenycounty.us`).
- Open US Law `kind=court_rules` mixes statewide rules, local rules (IL Article XII 418 rows, AZ local superior
  court rules 196, NV district rules) and professional-conduct rules with no type field.
- 311,321 Open US Law rows lack a source URL (all MS, AR, NM, TN statutes; TX regulations) - those states cannot
  deep-link to an official page from that layer.
- The source directory's `category` is noisy for state law (e.g. Alabama Rules of Civil Procedure filed under
  `regulations_register`; Oklahoma administrative code under `court_rules`), so gap queries must use title/URL
  patterns, not category alone.

## 9. Recommended builds (detail in the structured summary)

1. Jurisdiction coverage supplement + UI matrix from `coverage_matrix.json` (no network).
2. Court-rule set typing for the 41,692 Open US Law rows (civil / evidence / appellate / local / conduct).
3. Mass-tort topic tagging over Open US Law + NJ provisions + NC chapter PDFs (saved queries as provenance).
4. Venue linking: FIPS links for imported documents whose `source_courts` names a single-county court.
5. Publish saved-but-unpublished captures (JCCP log; retained captures on court hosts).
6. Hub expansion: parse child links from the 14 saved hub pages into an exact-URL packet (no crawl).
6a. Classify the unreviewed official tier (6,101 statute and 1,053 court-rule pages of 2,000+ characters) into body / hub / navigation so real bodies surface in filters (no network).
7. Network packets from `gap_fill_candidates.jsonl` (priority 1 first), then Trellis profile resume for the
   1,073 unsaved county pages with the 20 venue-critical ones first.
8. New source discovery for venue courts and coordination programmes absent from the directory.
9. Georgia statutes decision (official vendor-hosted code vs. another lawful public copy) - needs user input.

## 10. Not verified

- No URL liveness, robots or terms check was made; directory verification fields are historical claims.
- "Unreviewed" official pages were not opened one by one; some may contain real law bodies (KS 444 court-rule
  pages, ND 2,559 and ID 1,573 statute pages are likely section pages rather than hubs).
- Topical results are phrase matches in a third-party export; no legal-currency or completeness review.
- NC chapter PDFs were matched by URL pattern, not read; completeness against the full chapter list not checked.
- Venue host patterns are a convenience check and may miss documents stored on other hosts (blob storage, PDFs
  on state judiciary domains). St. Clair and Madison host patterns are assumptions and matched nothing.
- `catalog/documents.sqlite3` was used only for URL dedupe; retained captures outside the directory were not
  inventoried by state.
