# Settlements audit and standardized settlement-document plan

Scope: read-only audit, September 18, 2026 (local clock). No project file, database, receipt or server was modified.
Files written by this audit (all under `reports/corpus_upgrade_20260919/understand/`):

- `settlements_audit.md` (this file)
- `packets/settlement_urls.jsonl` - 91 exact URLs, 43 hosts, sha256 `e3d265792ae9b0f2d7ef6c1376eabba546fcb6652f3083fb36c160d1e49cea66`
- `packets/settlement_robots_check.json` - 80 robots.txt responses (one GET per host) + 41 held-out URLs with reasons
- `packets/build_settlement_packet.py` - the builder. **Do not rerun it casually: a rerun repeats the 80 robots requests.**

## 1. Bottom line

1. The "settlements" collection is **not a mass-tort settlement corpus**. All 848 records are one third-party consumer
   feed (SettleSignal, snapshot sha256 `76ffad1e...05ba`, generated 2026-09-13T02:48Z). Text search across title, payout text
   and publisher fields finds **0 records mentioning "MDL" or "multidistrict", 0 "product liability", 0 "opioid", 1 "personal injury"
   (a PIP insurance case)**. It is dominated by data-breach (240 text hits / 212 category), wage (112), securities (79),
   FTC refunds (78) and false-advertising matters.
2. The feed has **no structured defendant, amount, court, case number, MDL number, judge, or approval-date fields**. Those exist
   only for the 9 records that received a bounded manual review on 2026-09-12.
3. **0 of 848 official settlement URLs have a saved capture** in `directory.sqlite3` (58,310 `records` rows scanned) or
   `catalog/documents.sqlite3` (19,008 `versions` rows; `source_url` and `final_url`), by exact match and by a
   www/trailing-slash-normalized match. Only **4 underlying documents** exist locally (2 class notices, 1 court order,
   1 blank claim form; 30 pages, 989,737 bytes); all 4 are present in `directory.sqlite3` as `seeger`/`reference_original`
   records and absent from `documents.sqlite3`.
4. The most valuable uncaptured settlement *documents* already referenced locally are **240 NAAG multistate-settlement PDFs**
   in the source directory (consent judgments, settlement agreements, AVCs, plus the Mallinckrodt plan, confirmation order,
   NOAT II trust agreement and trust distribution procedures). None is saved. 32 are in the first packet.
5. Court-approved administrator sites are a real barrier: **30 of 80 hosts answered robots.txt with HTTP 403** to the
   `LegalCorpusResearch/1.0` user agent (including JUUL, Flint, East Palestine, Payment Card, Kroll/Purdue). They were held
   out, not rerouted.

## 2. Provenance chain

| Layer | Path | Notes |
|---|---|---|
| Raw publisher feed (byte-for-byte) | `C:/Users/firas/Downloads/Court-Document-Library/07-Settlement-References/catalog/publisher-feed.json` (842,709 B) | also `Seeger-Corpus-Enrichment-2026-09-13/inputs/wfiles/settlesignal.json` |
| Normalized catalog (the source of the 848) | `.../07-Settlement-References/catalog/catalog.json` (1,254,983 B; `records[]` = `id`, `publisher{}`, `publisher_record_sha256`, `source_positions`, `source_snapshot_sha256`, `review`, `quality_notes`) | importer `import_catalog.py`, schema `catalog.schema.json`, provenance in `catalog/provenance/` (ROW-IDENTITIES, DUPLICATE-REVIEW, EDGE-CASES, NORMALIZATION-CONTRACT) |
| Manual reviews | `.../07-Settlement-References/verified-records.json` (9 records; typed `deadlines[]` with `type`, `date`, `as_published`, `source_url`, `source_locator`, `time_as_published`, `timezone_*`, `status_as_of_review`; `discrepancies[]`) | `FINDINGS.md`, `INTEGRATION.md` |
| Saved originals | `.../07-Settlement-References/documents.json` + `documents/` (4 PDFs, SHA-256, http status, retrieval method, page count) | `document-download-results.json`, `.firecrawl/`, `evidence/text/` named in FINDINGS.md are **not present** in this folder |
| Staging copies | `Seeger-Corpus-Enrichment-2026-09-13/staging/SETTLEMENTS.html`, `.../staging/11-Platform-Corpus/provenance/SETTLEMENT-FEED-ACCOUNTING.json`, `.../data-review/SETTLEMENT-FEED-AUDIT.json` | same input hash |
| Presentation layer | `sources/local_library_presentation_20260918/settlements.jsonl` (848 lines) built by `build.py` lines 169-198 | flattens to title/status/claim_deadline/status_as_of/official_url/proof_requirement + full `metadata.publisher` and `metadata.review` |
| Adapter | `delivery/archive-directory/local_library.py` | `collection(id, params)` supports only `q`, `family`, `kind`, `page`, `page_size`; every settlement has `resource_kind=settlement_reference`, so **no usable filter** for status, deadline, type, category or state |

License note carried from FINDINGS.md/INTEGRATION.md: the feed states free use with attribution, while the publisher's general terms
(June 3, 2026) restrict commercial use and bulk republication. That conflict is unresolved; treat the 848 as a discovery layer.

## 3. What the 848 records contain

Populated publisher fields: `title`, `url`, `settlement_type`, `status`, `proof_required`, `official_settlement_url`,
`verification_status`, `accepted_official_evidence`, `last_verified` 848/848; `category` 793; `estimated_payout` 663;
`official_claim_url` 639; `claim_deadline` 614; `applicable_states` 76. In `settlements.jsonl`: `court_label` 9, `excerpt` 9,
`documents` 3 records (4 PDFs), `asset_id` 3.

| Publisher `settlement_type` | n | | Publisher `category` | n |
|---|---:|---|---|---:|
| other_consumer_compensation | 534 | | Data Breach Settlements | 212 |
| data_breach_settlement | 111 | | Employment & Wages | 103 |
| class_action_settlement | 99 | | Class Action Settlements | 96 |
| government_refund | 41 | | False Advertising & Labeling | 90 |
| privacy_settlement | 27 | | Subscription & Fees | 62 |
| financial_fee_settlement | 15 | | Securities & Investors | 57 |
| consumer_product_settlement | 14 | | (empty) | 55 |
| state_ag_refund | 6 | | Privacy & Tracking | 50 |
| regulatory_compensation_program | 1 | | Defective Products & Recalls 30; Insurance 24; Banking 21; Vehicles 20; Telecom 16; Gov refunds 8; ESOP 3; Civil rights 1 | |

Mapped to the four requested families: private class/consumer settlements 800; AG/government 48 by publisher type
(95 by `.gov` official host: ftc.gov 77, consumerfinance.gov 9, sec.gov 5, azag.gov 2, cbp.gov 1, richmondhill-ga.gov 1);
**MDL global settlements 0 labelled** (the NFL concussion program is present as one unlabelled row; a handful of MDL-linked
class settlements such as sartan, generic drugs, Hyundai/Kia are identifiable only by title); **bankruptcy trusts 0 labelled**
(one Zonolite attic-insulation row is a candidate).

- Status: Claim window closed 449; Open for claims 373; Published record 21; Payment pending 2; Payments started 2; Pending final approval 1.
- Verification (publisher's own assertion, not independent): official_source_found 496; needs_recheck 342; third_party_only 5; administrator_verified 4; court_verified 1. `accepted_official_evidence` true 810.
- Proof: unknown 301; no 200; optional 181; yes 166.
- States: only 76 records carry a list (CA 29, IL 16, WA 12, PA 7, NY 6...). An empty list is "nationwide per feed", not a class definition.
- Defendants: no field. 121 titles contain a `v.` caption, 4 contain "In re". Defendant must be parsed from title and is unreliable.
- Amounts: no field. 192 titles contain `$`, 109 a million/billion figure; `estimated_payout` is free text mixing fund size, per-person caps and vouchers (INTEGRATION.md forbids summing).
- Courts / case numbers: 9 (reviewed records only). MDL numbers: 0. Judges: 0. Court-hosted official URLs (`uscourts.gov` or state courts): 0.

### Dates and their semantics

| Field | Meaning | Coverage |
|---|---|---|
| `publisher.claim_deadline` | publisher-reported claim date, date only, no time zone, no cut-off method | 614; years 2003-2030, 491 in 2026 |
| `publisher.last_verified` | publisher workflow-check date (not an official-source date) | 848; 585 in 2026-06, 79 in 07, 111 in 08, 73 in 09 |
| feed `generated` / `dateModified` | feed build 2026-09-13T02:48Z / last catalog change 2026-09-12 | snapshot level |
| `review.assessment_date`, `reviewed_at` | date of the bounded manual review | 9 records (2026-09-12/13) |
| `review.deadlines[]` | typed claim / exclusion / objection / final_approval_hearing with `as_published`, locator, time and zone as published | 9 records |
| `status_as_of` (presentation) | `assessment_date` else `last_verified` | 848 |
| `source_date` (presentation) | always null | - |

Missing everywhere: filing date, preliminary-approval date, final-approval date, effective date, payment/distribution dates,
capture date of any official page. Temporal staleness as of 2026-09-18: of 365 rows shown "Open for claims" in
`settlements.jsonl`, 131 have a future deadline, 225 have no deadline and **9 have a deadline already past**.

## 4. URL and capture coverage

- 848/848 have `official_settlement_url` (684 distinct hosts; 651 are site roots, 197 deep paths, 0 PDFs). 639 have an
  `official_claim_url` (145 identical to the settlement URL; top hosts forms.ksacms.com 45, cptgroupcaseinfo.com 23,
  strategicclaims.net 18, veritaconnect.com 12) - claim pages are excluded from any capture by rule.
- 2,179 distinct URLs (official, claim, publisher page) were matched against both databases: **exact 0, normalized 0**.
  Host-level hits outside shared government/administrator hosts: 2 (`seniorcarecopaysettlement.com`,
  `genericdrugsendpayersettlement.com`) - these are the saved PDFs, not the site pages.
- The 4 document URLs in `documents.json`: 4/4 present in `directory.sqlite3.records` (dataset `seeger`, kind
  `reference_original`), 0/4 in `documents.sqlite3`.
- Prior document attempts (FINDINGS.md): 4 of 10 succeeded; Pork, CRST and Google PDFs returned 403; Farmers and the Amazon
  administrator order failed TLS; AmTrust carried AI-use reservation signals and was deliberately not acquired.

## 5. Other local settlement-relevant material (mostly unused by the UI)

| Material | Location | Size | Caveat |
|---|---|---|---|
| Verdict and Settlement Lead Index | `C:/Users/firas/Downloads/returnedfiles/settlementsverdicts/` (`vli_records.csv`, `vli_mass_tort_leads.csv`, `verdict_lead_index.json`, report) | 3,312 results (1,755 verdicts, 1,557 settlements; 2024: 2,137, 2025: 1,175); 670 mass-tort tagged (337 settlements): medical malpractice 398, childhood sexual abuse 124, toxic exposure 80, rideshare assault 75, nursing home 66, pharmaceutical 45, asbestos 18, talc 9 | Self-reported attorney amounts from a pay-for-placement publisher that prohibits reuse. Its own report says internal research leads only, top-tail censored, never base rates. Keep out of the published corpus; usable only as a private "lead to verify" layer with amount fields labelled publisher-reported. |
| NAAG multistate settlement documents | `sources/public_law_directory_20260919/catalog.json` (246 naag.org references, 240 PDFs) | filename detection: consent judgment/decree 87, settlement agreement 74, AVC 32, complaint 28, other 19 | references only; 0 saved |
| Government settlement indexes | same catalog: `ftc.gov/enforcement/refunds`, NAAG multistate and antitrust databases, EPA cases-and-settlements (6 pages), JPML pending MDLs / panel orders / archive, HRSA vaccine compensation, 10 state AG press-release indexes | 34 URL/title matches, 3 saved (all court settlement-conference rules) | references only |
| DOJ ATR / CRT settlement agreements and orders | `returnedfiles/uscourtswidecrawl/01a02a3f-.../www.justice.gov_*settlement*.json` | about 30 connector JSON files | connector responses, not original bytes; antitrust and civil-rights, not mass tort |
| Court settlement *procedure* forms | `directory.sqlite3` (95 title/URL hits: 72 seeger court forms, 15 statutory provisions, 4 reference originals) and `Court-Document-Library/01-Federal`, `02-State` (86 filenames) | settlement-conference orders, Rule 9019 forms, minor's compromise petitions, LASC model class-action settlement agreement and notice | a different sense of "settlement"; label as `settlement_procedure_form`, never as a settlement record |
| MDL 3080 Insulin Pricing | 1,612 PDFs catalogued, 24 previewed | no settlement documents identified in the 24 previews; full manifest not scanned for settlement filings here | |
| Seeger Weiss agent contracts | `Seeger-Corpus-Enrichment-2026-09-13/staging/10-Agent-Skills-Library/Seeger-Weiss-Agents/contracts/settlement-valuation-analyst.*.schema.json` | input requires `comparison_question`, `comparable_sources`, `selection_protocol` (must state whether the set is selected/censored) | the record schema below is shaped to feed this contract |

## 6. Standardized settlement document taxonomy

Classification runs in three passes and records which pass decided (`type_basis`): (1) link text on the official page,
(2) filename/URL, (3) first-page text of the saved document. A lower pass may only overrule a higher one when first-page text
contains a caption-level title. Anything unmatched stays `unclassified`; nothing is guessed.

| `document_type` | Link text / filename cues (case-insensitive) | First-page text cues |
|---|---|---|
| `settlement_agreement` | "settlement agreement", "stipulation (and agreement) of settlement", "class action settlement agreement", "amended settlement agreement" | caption + "SETTLEMENT AGREEMENT" / "STIPULATION OF SETTLEMENT"; "This Settlement Agreement is entered into" |
| `master_settlement_agreement` | "master settlement agreement", "MSA", "global settlement" | "MASTER SETTLEMENT AGREEMENT"; participation thresholds, "Eligible Claimant" |
| `settlement_term_sheet` | "term sheet", "memorandum of understanding" | "TERM SHEET" |
| `preliminary_approval_order` | "preliminary approval order", "order granting preliminary approval", "order directing notice" | "ORDER" + "preliminarily approv" / "directing notice to the class" |
| `final_approval_order` | "final approval order", "final order and judgment", "order granting final approval" | "FINAL" + "approv" + "fair, reasonable, and adequate" |
| `final_judgment` | "final judgment", "judgment" | "FINAL JUDGMENT" without approval language |
| `consent_judgment_or_decree` | "consent judgment/decree/order", "stipulated (final) judgment", "agreed final judgment", "judgment upon stipulation", "stipulated order for permanent injunction" | "CONSENT JUDGMENT", "CONSENT DECREE" (government plaintiff) |
| `assurance_of_voluntary_compliance` | "assurance of voluntary compliance", "assurance of discontinuance", "AVC", "AOD" | same headings |
| `administrative_order` | "order instituting", "cease and desist", "consent order" (agency) | agency caption (SEC, CFPB, FTC) + file number |
| `long_form_notice` | "long form notice", "detailed notice", "class notice", "notice of proposed settlement" | "A court authorized this notice", question-and-answer headings, more than 3 pages |
| `short_form_notice` | "short form notice", "summary notice", "postcard notice", "email notice", "publication notice" | same legend, 1-2 pages |
| `claim_form` | "claim form", "proof of claim", "registration form" (blank PDF only) | "CLAIM FORM", claimant fields; `pdf_form_field_count` > 0 is supporting evidence. **Blank forms only; online claim portals are never captured** |
| `opt_out_or_objection_form` | "exclusion request", "opt-out form", "objection form" | "REQUEST FOR EXCLUSION" |
| `plan_of_allocation` | "plan of allocation", "distribution plan", "allocation methodology", "settlement matrix", "injury grid" | "PLAN OF ALLOCATION"; points/tier tables |
| `fee_motion` | "motion for attorneys' fees", "fee petition", "fee and expense application", "service awards" | "MOTION FOR ... ATTORNEYS' FEES" |
| `fee_order` | "order awarding attorneys' fees", "fee order", "common benefit order" | "ORDER" + "awarding attorneys' fees" / "common benefit" |
| `approval_motion` | "motion for preliminary/final approval", "memorandum in support" | "MOTION FOR (PRELIMINARY\|FINAL) APPROVAL" |
| `complaint_or_petition` | "complaint", "consolidated amended complaint", "petition" | "COMPLAINT" heading |
| `case_management_or_settlement_order` | "CMO", "pretrial order", "order appointing special master/claims administrator/QSF" | MDL caption + "PRETRIAL ORDER NO." |
| `trust_distribution_procedures` | "trust distribution procedures", "TDP", "claims resolution procedures" | "TRUST DISTRIBUTION PROCEDURES" |
| `trust_agreement` | "trust agreement" | "TRUST AGREEMENT" |
| `bankruptcy_plan` / `plan_confirmation_order` / `disclosure_statement` | "plan of reorganization", "chapter 11 plan", "confirmation order", "disclosure statement" | bankruptcy caption + those headings |
| `faq_page` | page/link "FAQ", "frequently asked questions" | HTML page |
| `deadlines_page` | "important dates", "key dates", "deadlines" | HTML page; every date goes to typed events, never to a free-text field |
| `settlement_website_home` / `court_documents_index` | site root; "court documents", "important documents", "case documents" | HTML page; index pages are the link source for pass 1 |
| `status_report_or_claims_report` | "status report", "claims administrator report", "distribution report" | periodic statistics |
| `press_release` / `executive_summary` | "press release", "summary", "highlights", "Q&A" | never authority for terms |

Test on the 240 NAAG filenames (pass 2 only): 230 classified, 10 unclassified ("Final Judgement" spelling, "Amended Order",
"Memorandum Opinion", "Notice of Agreement", "Order of Dismissal"). Add `judge?ment`, `memorandum opinion -> court_opinion`,
`order of dismissal -> dismissal_order` before use; keep the residue unclassified.

Standardized storage per document: original bytes + SHA-256 + HTTP receipt; `document_type`, `type_basis`, `type_evidence`
(the matched string and where); `title_as_published`; `document_date` with `date_semantics` in {`signed`, `filed`, `entered`,
`executed`, `effective`, `published_on_site`, `filename_hint`, `unknown`}; `docket_entry_number` if printed; `page_count`;
`language`; `is_blank_form`; `supersedes` / `amended_by`; rights note. Reading copies and extracted text are separate derivatives.

## 7. Settlement record schema (proposed `settlement-record-v1`)

```json
{
  "settlement_id": "stl-<sha256(normalized case key + settlement round)[:20]>",
  "record_layer": "published_record | reviewed_reference | publisher_reference | lead_unverified",
  "settlement_family": "mdl_global_settlement | mdl_class_settlement | class_action | mass_tort_class_settlement | state_ag_multistate | state_ag_single | federal_agency_enforcement | government_compensation_program | bankruptcy_trust | bankruptcy_plan",
  "matter": {
    "caption": null, "short_name": null,
    "mdl_number": null, "jpml_docket": null,
    "case_numbers": [{"value": null, "court_id": null, "basis": "document|docket|publisher"}],
    "courtlistener_docket_ids": [], "related_settlement_ids": [], "round_label": null
  },
  "court": {"court_id": null, "name_as_published": null, "system": "federal|state|bankruptcy|agency", "state": null, "county_fips": null, "basis": null},
  "judges": [{"role": "presiding|transferee|magistrate|special_master|bankruptcy", "name_as_published": null,
              "judge_entity_id": null, "fjc_nid": null, "courtlistener_person_id": null, "link_basis": "native id only; never name alone"}],
  "parties": {
    "defendants": [{"name_as_published": null, "normalized_name": null, "sec_cik": null, "basis": null}],
    "plaintiff_class_definition": {"text": null, "source_document_id": null, "locator": null},
    "lead_counsel": [{"firm": null, "attorneys": [], "role": "co-lead|class counsel|PSC|liaison", "basis": null}],
    "administrator": {"name": null, "site_host": null}, "special_master_or_trustee": null
  },
  "subject": {"product_or_conduct": null, "injury_or_harm": null, "practice_area": null, "tags": []},
  "amounts": [{"kind": "total_fund|uncapped_program|per_claimant_cap|per_claimant_estimate|attorney_fees|expenses|service_award|injunctive_value|abatement_payment",
               "value": null, "currency": "USD", "as_published": null, "reported_by": "court_order|agreement|administrator|agency|publisher|attorney_self_report",
               "source_document_id": null, "locator": null, "as_of": null}],
  "events": [{"type": "filed|agreement_executed|preliminary_approval|notice_date|claim_deadline|opt_out_deadline|objection_deadline|final_approval_hearing|final_approval|effective_date|appeal_resolved|payments_started|payments_completed|registration_deadline|trust_effective",
              "date": null, "as_published": null, "time_as_published": null, "timezone_as_published": null, "timezone_converted": false,
              "source_url": null, "source_document_id": null, "locator": null, "status_as_of_capture": "future|past|unknown"}],
  "status": {"value": null, "as_of": null, "basis": "captured official page | document | publisher assertion"},
  "geography": {"scope": "nationwide|states|single_state|unknown", "states": [], "basis": null},
  "official_sources": [{"url": null, "host_class": "court|government|court_approved_administrator|claims_agent|trust|publisher", "capture_id": null, "captured_at": null, "access_result": null}],
  "documents": [{"document_id": null, "document_type": null, "type_basis": null, "source_url": null, "raw_sha256": null, "document_date": null, "date_semantics": null}],
  "provenance": {"source_snapshot_date": null, "capture_date": null, "publisher_record_sha256": null, "review": {"id": null, "assessment_date": null, "scope": []}},
  "quality_flags": [], "rights_note": null
}
```

Rules: (a) four date kinds stay separate - snapshot, capture, publication, effective; (b) a claim deadline never implies current
eligibility and is never refreshed by the display clock; (c) amounts are never summed across kinds and always carry `reported_by`;
(d) judge and court links use native identifiers only (`judge_entities` id, FJC nid, CourtListener person id, CourtListener
`court_id`); (e) `publisher_reference` and `lead_unverified` layers must never be displayed as verified settlements; (f) one
record per settlement round (Pork, generic drugs and opioid matters have several rounds with different defendants and dates).

Filters the UI/API should gain (none exist today): `settlement_family`, `status` + `status_as_of`, event-date ranges by event type,
`court_id` / `mdl_number`, state scope, defendant, `practice_area`, `record_layer`, has-saved-documents, `document_type`.

## 8. First capture packet (`packets/settlement_urls.jsonl`)

91 exact URLs on 43 hosts; every line carries `evidence`, `robots`, `capture_rules` (GET exact URL, no link following, no forms,
no claim submission, 0 retries, per-host delay = max(2 s, crawl-delay)).

| `source_family` | URLs | Evidence |
|---|---:|---|
| `settlement_catalog_official_url` | 37 | catalog record id + `publisher_record_sha256` + publisher verification status (labelled as publisher assertion); includes NFL concussion, sartan, generic drugs, Tracleer, QVAR, Deere, RealPage, NCAA, Hyundai/Kia ACU and theft, GM fuel pump, NIBCO PEX, CertainTeed Horizon, Zonolite, 12 FTC/CFPB/SEC redress pages, AZ AG, CBP |
| `public_law_directory_reference` | 42 | source-directory entry id + catalog sha256: FTC refunds index (2), NAAG databases (2), JPML pending MDLs / panel orders / archive / August 3, 2026 district report PDF (4), HRSA vaccine compensation (2), **32 NAAG settlement PDFs** (16 consent judgments, 6 settlement agreements, 4 complaints, Mallinckrodt plan + confirmation order + NOAT II trust agreement + TDP, FL opioid term sheet, national opioid executive summary) |
| `mass_tort_program_site_candidate` | 12 | **model general knowledge + a robots response only** - PFAS water, national and tribal opioid, Fire Victim Trust, Scouting Settlement Trust, BCBS, real-estate commission, Equifax, VCF, Syngenta corn, VW, Deepwater Horizon. Matter/MDL/court text on these lines is unverified; 7 served no robots rules and carry a `risk` note (possible expired or repurposed domain). Reject parked pages. |

Robots results (80 hosts, one GET each, no retries): parsed 29, no robots file (404) 9, HTML returned instead of rules 6,
**HTTP 403 30**, TLS/timeout/reset 6. Crawl-delays to honor: jpml.uscourts.gov 10 s, nationalopioidsettlement.com 10 s,
sartanmedicationsettlement.com 10 s, hazdovacemissionswarrantysettlement.com 10 s, ftc.gov 5 s, pfaswatersettlement.com 3 s.
For the 32 NAAG PDFs the host robots file was parsed once (sha256 recorded) but the body was not kept, so the path decision is
marked `deferred`; `pipeline/corpus_crawler.py` (`respect_robots=True`) must evaluate it at fetch time. One URL
(speedcontroldialsettlement.com) was disallowed by parsed robots rules and held.

41 held URLs with reasons are in `settlement_robots_check.json` (`held[]`): 3 deliberate exclusions (AmTrust AI-use reservation,
Heckathorn prior TLS failures, a law-firm-hosted page), 30 hosts answering 403 (JUUL, pork, beef, homebuyer, Toyota ACU, FCA,
Mercedes, Flint, East Palestine, Payment Card, EcoDiesel, Facebook, Kroll/Purdue, the three previously reviewed Lighthouse /
CRST / Google sites, and others), 7 URLs on 6 hosts with connection failures (epa.gov x2 via bare host, CertainTeed organic, Generac, Amazon
subscription site, Takata trust, GM ignition switch), 1 robots disallow.

Deliberately not in the packet because exact paths could not be evidenced locally: district-court MDL pages (E.D. Pa. NFL,
D.S.C. AFFF, N.D. Fla. 3M, N.D. Ohio opiate), DOJ Camp Lejeune, 3M Combat Arms and Philips CPAP program sites, asbestos trust
sites, NAAG tobacco MSA page. Discover them from the captured JPML and NAAG index pages in a second packet.

## 9. Recommended build order

1. Run the packet with the existing collector; classify each saved PDF with the section 6 rules; publish as a hash-gated
   supplement (`sources/settlement_documents_<date>/`).
2. Build `settlement-record-v1` records: 9 reviewed records first (they already hold typed events), then government/AG records
   from captured NAAG/FTC/CFPB/SEC pages, then MDL program records. Keep the 848 as `publisher_reference` with filters.
3. Second packet: document links discovered on captured index pages (NAAG remaining 208 PDFs, JPML reports, administrator
   "court documents" pages that allowed access), still <= 100 URLs.
4. For the 403 administrator hosts, obtain the same court documents from the court side through the user's CourtListener/RECAP
   connector (small, quota-checked, recorded as connector responses) instead of touching the blocked sites.
5. Keep the verdict lead index private and unpublished; if used, only as `lead_unverified` pointers for docket verification.

## 10. Not verified

- No settlement page or document was fetched; only robots.txt. Whether any packet URL returns real content, a soft 404, a
  challenge page or a parked domain is unknown.
- The 12 knowledge-sourced program sites: domain ownership, court-approved status, MDL numbers and courts are unverified.
- `publisher-feed.json` was not re-hashed against `source_snapshot_sha256`; `catalog/VALIDATION.json` and the JS catalog UI were not executed.
- The full MDL 3080 manifest (1,612) and the full Court-Document-Library were not scanned for settlement filings; only names/titles were sampled.
- The roughly 30 DOJ settlement JSON files in `returnedfiles/uscourtswidecrawl` were counted by filename only.
- `documents.sqlite3` was matched on `source_url`/`final_url` only; text-level duplicates of settlement documents were not searched.
- The feed's license conflict and the verdict index's reuse prohibition need a human decision before any external platform integration.
- Whether 403 responses are user-agent based, geo based or blanket was not probed (no second request was made).
