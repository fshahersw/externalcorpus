---
name: legal-archive-api
description: Use when a question can be answered from the local Legal Archive at http://127.0.0.1:8769 - state and federal statute or regulation text, court rules, limitation periods, county court rules and filing sources, courts and seals, judges and portraits, MDLs and docket documents, counsel and firms, settlements and verdict reports, agencies, the Federal Register, what a reporter abbreviation means, or which saved documents cite an authority. Teaches the read-only JSON API, the labels every answer must carry, and the limits that must be stated. Not for drafting advice and never a claim that the collection is complete.
version: 1.0.0
author: project (built 2026-09-20)
---

# Legal Archive API

The archive is a local, read-only research library served at `http://127.0.0.1:8769` (code in `delivery/archive-directory`,
data layers in `sources/<layer>_<date>/`). Everything below is a `GET` that returns JSON. Nothing writes.

## Ground rules (these are what make an answer usable)

1. **Say where it came from.** Quote the record id (`oul:...`, court id, MDL number, FIPS) and the layer. Saved law text is a
   publisher snapshot (Open US Law v2026.08): always add "check the edition and current status at the official source".
2. **Never say the collection is complete.** A missing record means "not saved here", not "does not exist". Known holes:
   Georgia and North Carolina statutes are not in the snapshot; Pennsylvania's unconsolidated statutes are missing;
   MA, NH, MI and NC county sources are mostly blocked.
3. **Counts are counts of saved records**, not rates, rankings or importance. "Cited in 176 saved documents" is not "the
   most important case".
4. **Keep the two kinds of limitation-period data apart**: the third-party table value, and whether the saved statute text
   contains the same wording (`outcome`). If `outcome` is `different_wording_found`, report both and say the statute controls.
5. **People**: identify judges and attorneys by their native ids only. Never merge on a name. Never publish names of
   individual litigants.
6. If an endpoint answers `{"available": false, "reason": ...}` the layer is closed (hash or validation failed). Report
   that; do not work around it.

## Finding law text

| Need | Call |
|---|---|
| What a state has | `/api/law-outline?state=Texas` -> collections (statutes, constitution, court rules, regulations) + `statute_audit` (publisher's completeness verdict) |
| Browse headings | `/api/law-outline/children?state=TX&kind=statutes&parent=0` then `parent=<node id>` |
| Sections under a heading | `/api/law-outline/provisions?node=<id>&offset=0&limit=100` (citation order) |
| Read one provision | `/api/record?id=<oul id>` (`text`, `metadata.citation`, `source_url`); full text `/api/text?id=` |
| Where it sits, previous / next | `/api/law-outline/context?id=<oul id>` |
| Full-text search | `/api/documents?group=laws&state=California&category=statutes&q=limitation&limit=50` |
| Federal regulations with amendment history | `/api/regulations/search?q=`, `/api/regulation?id=` (includes `fr_history`) |
| Federal Register 1994-2026 | `/api/area/federal-register?q=&agency=&cfr_title=&cfr_part=&year=` |
| Public laws and the U.S. Code sections they change | `/api/area/public-laws?q=117-328` |

Citation strings in the law catalog are exact: `21 U.S.C. § 355 (2024)`, `21 C.F.R. § 314.80 (2026)`, `Cal. CCP § 335.1`,
`Tex. Civil Practice and Remedies Code § 16.003`, `N.Y. CVP Law § 214`, `735 ILCS 5/13-202`, `Okla. Stat. tit. 12, § 12-95`.

## Limitation periods

`/api/area/limitation-periods?state=TX&claim=personal-injury` (claims: personal-injury, wrongful-death, medical-malpractice,
written-contract, oral-contract, property-damage, fraud, defamation, debt-collection). Each row: `period` (third-party table,
CC BY 4.0, Techno Optics LLC), `section` looked up in the saved code, and `check`:
same period found / same period in a general section / **different period in the saved statute** / section not saved.
`/api/blocks?state=LA` returns the nine rows for one state under `limitation_periods`.

## Courts, judges, counsel

| Need | Call |
|---|---|
| Court registry | `/api/area/courts?q=&state=` ; one court `/api/area/courts/item?id=njd` (adds citation abbreviation, level, existence dates, seal) |
| Which court does this caption mean | `/api/court-resolve?q=United States District Court for the Southern District of Texas` (more than one result = ambiguous) |
| What does "F. Supp. 3d" mean | `/api/area/citation-guide?q=F.%20Supp.%203d` (reporters, statute citation forms, journals) |
| Judges | `/api/judges?q=&has=all` ; profile `/api/judge?id=<entity id>` (appointments, MDLs, disclosures, portrait) |
| Historical biographies | `/api/people?q=` ; `/api/person?id=<CourtListener person id>` |
| MDLs | `/api/mdls` ; `/api/mdl?number=2738` (judge, counts as printed by JPML, docket documents, counsel, state proceedings) |
| Firms and attorneys | `/api/area/counsel-directory?q=&mdl=` |
| Settlements, verdict reports, expert challenges | `/api/area/settlements`, `/api/area/verdict-reports`, `/api/area/expert-rulings` |
| Counties | `/api/counties?state=&q=` ; rules and filing sources `/api/county-filing?fips=48201` ; coverage `/api/county-filing/coverage` |

## Citations inside saved documents

`/api/area/citation-index?q=daubert` lists authorities found by eyecite in 24,289 saved documents, with
`documents` = saved documents citing it. `/api/area/citation-index/item?id=<n>` lists those documents with the passage.
`/api/citations/record?id=<oul id>` = saved documents citing one saved provision. Statute and regulation citations open the
saved text only on an exact citation match; case citations carry a CourtListener look-up address and are not saved here.

## Agencies and evidence

`/api/agency-hub` (19 agencies joined across the Federal Register, CFR, safety data, documents, addresses; parent
departments include their components, so never sum rows), `/api/agency-hub/item?key=fda`, `/api/agency/search?dataset=&q=`,
`/api/area/agency-documents?q=`, `/api/area/cpsc-injury-data?q=&dataset=neiss|saferproducts` (NEISS rows are a sample:
do not total them into national estimates without the weights).

## Generic contract for every `/api/area/<name>`

`?q=&page=&limit=` plus the filters named in the response's `filters[]`. Response: `available, total, page, limit,
qualification, filters[], columns[], results[{id,title,subtitle,cells,badges,links}]`. One record:
`/api/area/<name>/item?id=<id>` -> `title, subtitle, facts[], sections[], links[], qualification`. Always carry the
`qualification` text into the answer when it limits what the numbers mean.

## Health

`/api/supplements` lists every layer with `ready` and hash verification. Verifier:
`python reports/corpus_upgrade_20260919/verify_round2.py` (live checks). Restart: `reports/corpus_upgrade_20260919/restart.ps1`
(after a reboot use `start_server.ps1`).
