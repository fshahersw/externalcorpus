"""Builds ../regulation_endpoints.jsonl from probe results (regulations-scout, 2026-09-19)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "regulation_endpoints.jsonl")
fs = json.load(open(os.path.join(HERE, "openfda_first_slice_files.json"), encoding="utf-8"))["files"]
E = []
MB = 1048576


def add(**k):
    E.append(k)


# ---------------- local, no network ----------------
add(id="local-oul-cfr-slice", channel="local", network_required=False, status="verified_local",
    path="sources/open_us_law_20260918/catalog.sqlite3",
    selector="records.source_id range CFR_T{title}_P{part}_ (index records_source_id)",
    records={"title21_48parts": 1360, "title16_10parts": 182, "title49_10parts": 201,
             "title40_30parts": 3795, "all_cfr_rows": 220018},
    format="sqlite rows (text + payload JSON)",
    date_semantics="publisher snapshot 2026-08-14; payload.year=2026; last_amended_year only; NO exact as-of date; act_status is a publisher assertion",
    stable_ids="source_id CFR_T{t}_P{part}_S{section}; citation_short '21 C.F.R. § 314.80'; source_url ecfr.gov/current/...",
    priority=1)
add(id="local-gpo-ecfr-title21-xml", channel="local", network_required=False, status="verified_local",
    path="sources/seeger_import_20260918/raw/ae/aef563b3516b24060d85f48f944e7ad8776b8b92d95a916c0c9cd78ff90c10c2.xml",
    expected_bytes=21714710, sha256="aef563b3516b24060d85f48f944e7ad8776b8b92d95a916c0c9cd78ff90c10c2",
    note="Full GPO eCFR Title 21 XML captured 2026-09-13 (HTTP Last-Modified 2026-09-11; volume amendment marker 'Sept. 8, 2026'). Only 8 parts / 233 sections derived so far (parts 11, 50, 56, 312, 314, 803, 807, 820). The remaining sections can be parsed offline.",
    priority=1)
add(id="local-oul-federal-register", channel="local", network_required=False, status="verified_local",
    path="sources/open_us_law_20260918/catalog.sqlite3",
    records={"FR_RULE": 218712, "FR_PRORULE": 142188},
    note="Full text present. Metadata lacks publication_date field, agency, docket, RIN and effective date; cross_references_cfr [{title,part}] present. Notices are NOT included.",
    priority=2)
add(id="local-cpsc-recalls-csv", channel="local", network_required=False, status="verified_local",
    path="C:/Users/firas/Downloads/returnedfiles/Recalls.csv", expected_bytes=10016119, records=9971,
    note="CPSC recalls export; columns Title/Date/Summary/Recall Number/Recall URL; dates 1973-06-08 to 2026; first line is a SaferProducts disclaimer. Capture date and HTTP receipt unknown: label as user-supplied export, provenance unverified.",
    priority=1)
add(id="local-agency-url-inventory", channel="local", network_required=False, status="verified_local",
    path="C:/Users/firas/Downloads/returnedfiles/state_admin_agency_urls.jsonl",
    records={"federal_agency": 52758, "state_admin_code": 65298, "SEC_litig": 6395, "SEC_rules": 7555,
             "FTC": 22587, "CFPB": 9675, "CMS": 6239, "EPA_enf": 102, "HHS_OIG": 106},
    note="URL references only (no content). No FDA/CPSC/NHTSA layer.", priority=3)

# ---------------- eCFR API ----------------
add(id="ecfr-titles", host="www.ecfr.gov", url="https://www.ecfr.gov/api/versioner/v1/titles.json", method="GET",
    auth="none", format="json", expected_bytes=8033, status="verified_200_today", robots="allowed",
    date_semantics="per title: latest_amended_on, latest_issue_date, up_to_date_as_of (2026-09-17 today)",
    network_required=True, priority=1)
for t, date, b in ((21, "2026-09-16", 2676905), (16, "2026-09-17", 754204), (49, "2026-09-17", 2965556),
                   (40, "2026-09-17", 9395876)):
    add(id="ecfr-structure-title%d" % t, host="www.ecfr.gov",
        url="https://www.ecfr.gov/api/versioner/v1/structure/%s/title-%d.json" % (date, t), method="GET",
        auth="none", format="json", expected_bytes=b, status="verified_200_today_saved",
        saved_body_dir="reports/corpus_upgrade_20260919/understand/packets/regulation_probe/bodies",
        robots="allowed",
        stable_ids="identifier per node (title/chapter/subchapter/part/subpart/section) + size bytes + reserved flag",
        date_semantics="URL date = point-in-time (any date from 2017-01 forward)", network_required=False, priority=1)
add(id="ecfr-versions-per-part", host="www.ecfr.gov",
    url_template="https://www.ecfr.gov/api/versioner/v1/versions/title-{title}.json?part={part}",
    example="https://www.ecfr.gov/api/versioner/v1/versions/title-21.json?part=314", method="GET", auth="none",
    format="json", expected_bytes=28965,
    expected_size_basis="part 314 = 111 version rows, about 260 bytes/row. 98 selected parts = 98 requests, estimated 3-6 MB total (40 CFR 721 with 2,655 sections will be the largest).",
    status="verified_200_today (part 314 only)", robots="allowed",
    date_semantics="per section version: date, amendment_date, issue_date, substantive(bool), removed(bool); history starts 2016-12-23",
    network_required=True, priority=1)
add(id="ecfr-agencies", host="www.ecfr.gov", url="https://www.ecfr.gov/api/admin/v1/agencies.json", method="GET",
    auth="none", format="json", expected_bytes=98197, status="verified_200_today_saved", robots="allowed",
    note="153 agencies with slug + cfr_references (FDA=21/I, CPSC=16/II, NHTSA=49/V, EPA=40/I,IV,VII, SEC=17/II, OSHA=29/XVII). Slugs match Federal Register agency slugs.",
    network_required=False, priority=1)
add(id="ecfr-full-xml", host="www.ecfr.gov",
    url_template="https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title}.xml?part={part}", method="GET",
    auth="none", format="xml", status="NOT_FETCHED_robots_disallow",
    robots="robots.txt lists 'Disallow: /api/versioner/v1/full/' and '/api/renderer/v1/content/' after a blank line under User-agent:* (Python robotparser drops them; Google-style parsers apply them). Conservative reading = disallowed.",
    decision_required="Use govinfo bulk XML instead, or the user confirms those Disallow lines are index-only.",
    network_required=True, priority=9)

# ---------------- govinfo bulk ----------------
for t, b, lm, pr, note in (
        (21, 21724705, "17-Sep-2026 21:29", 3, "local copy from 2026-09-11 already exists"),
        (16, 6769171, "18-Sep-2026 23:19", 2, ""),
        (49, 33791758, "18-Sep-2026 23:35", 2, ""),
        (40, 161198000, "19-Sep-2026 00:04", 4,
         "local Open US Law already holds the section text; fetch only if an official dated XML with authority/source notes is required")):
    add(id="govinfo-ecfr-title%d-xml" % t, host="www.govinfo.gov",
        url="https://www.govinfo.gov/bulkdata/ECFR/title-%d/ECFR-title%d.xml" % (t, t),
        listing_url="https://www.govinfo.gov/bulkdata/json/ECFR/title-%d" % t,
        listing_accept_header="application/json", method="GET", auth="none",
        format="xml (GPO eCFR DIV1..DIV9 schema)", expected_bytes=b,
        expected_size_basis="size reported by the govinfo JSON listing today; file NOT downloaded",
        publisher_last_modified=lm, status="listing_verified_200_today",
        robots="allowed; robots.txt advertises bulkdata ECFR/CFR/FR sitemaps",
        date_semantics="currency = amendment marker inside the XML, not HTTP Last-Modified",
        network_required=True, priority=pr, note=note)
add(id="govinfo-cfr-annual-2025-title21", host="www.govinfo.gov",
    url="https://www.govinfo.gov/bulkdata/json/CFR/2025/title-21", method="GET", auth="none",
    format="json listing of CFR-2025-title21-vol1..vol9.xml + CFR-2025-title-21.zip", expected_bytes=3625,
    expected_size_basis="listing only; per-volume sizes are null in the listing",
    status="listing_verified_200_today; the 2026 edition listing returned 404",
    date_semantics="annual edition revision dates: titles 1-16 Jan 1; 17-27 Apr 1; 28-41 Jul 1; 42-50 Oct 1 (official point-in-time)",
    network_required=True, priority=4)

# ---------------- Federal Register ----------------
for slug, counts in (
        ("food-and-drug-administration", {"NOTICE": 18577, "RULE": 3671, "PRORULE": 1408}),
        ("consumer-product-safety-commission", {"NOTICE": 1694, "PRORULE": 354, "RULE": 325}),
        ("national-highway-traffic-safety-administration", {"NOTICE": 4320, "RULE": 868, "PRORULE": 796}),
        ("environmental-protection-agency", {"NOTICE": 27661, "RULE": 16905, "PRORULE": 13038})):
    add(id="fr-facets-type-" + slug, host="www.federalregister.gov",
        url="https://www.federalregister.gov/api/v1/documents/facets/type?conditions[agencies][]=" + slug,
        method="GET", auth="none", format="json", expected_bytes=126, status="verified_200_today",
        counts_today=counts, robots="allowed", network_required=True, priority=3)
FIELDS = ["document_number", "citation", "title", "type", "action", "publication_date", "effective_on",
          "signing_date", "comments_close_on", "dates", "docket_ids", "regulation_id_numbers", "cfr_references",
          "agencies", "html_url", "pdf_url", "full_text_xml_url", "raw_text_url", "correction_of", "corrections",
          "start_page", "end_page"]
add(id="fr-documents-by-cfr-part", host="www.federalregister.gov",
    url_template="https://www.federalregister.gov/api/v1/documents.json?per_page=1000&order=oldest&conditions[type][]=RULE&conditions[type][]=PRORULE&conditions[cfr][title]={title}&conditions[cfr][part]={part}&"
                 + "&".join("fields[]=" + f for f in FIELDS),
    method="GET", auth="none", format="json", expected_bytes_per_doc=2600,
    expected_size_basis="sample (title 21 part 314, RULE): count=66; 5,193 bytes for 2 docs. 98 selected parts = about 98 requests, metadata only, estimated 5-15 MB.",
    status="verified_200_today (one sample)", robots="allowed (only HTML search paths are disallowed)",
    rate_limit="none published; no key; per_page max 1000; deep-paging cap not verified, so partition by part or year",
    date_semantics="publication_date (authoritative); effective_on is machine-extracted (sample 2025-04978: effective_on=2024-12-26 while the 'dates' text says delayed to 2025-05-27) so never present it as verified; signing_date; comments_close_on; dates (free text)",
    stable_ids="document_number (2025-04978), citation (90 FR 13553), docket_ids, regulation_id_numbers (RIN), cfr_references[{title,part}]",
    network_required=True, priority=2)
add(id="fr-full-text", host="www.federalregister.gov",
    url_template="https://www.federalregister.gov/documents/full_text/xml/{yyyy}/{mm}/{dd}/{document_number}.xml",
    method="GET", auth="none",
    format="xml|txt|html; official PDF at govinfo.gov/content/pkg/FR-{date}/pdf/{document_number}.pdf",
    status="not_fetched; text for RULE/PRORULE through 2026-08 is already local in Open US Law",
    network_required=True, priority=6)

# ---------------- openFDA ----------------
add(id="openfda-download-manifest", host="api.fda.gov", url="https://api.fda.gov/download.json", method="GET",
    auth="none", format="json", expected_bytes=592208, status="verified_200_today_saved",
    robots="no robots.txt (404)",
    note="Lists every bulk zip with size_mb, records, export_date. Summary: regulation_probe/openfda_download_summary.json",
    network_required=False, priority=1)
FIRST = {"drug/enforcement", "device/enforcement", "food/enforcement", "drug/drugsfda", "device/pma",
         "device/classification", "transparency/crl", "drug/shortages", "drug/orangebook"}
for f in fs:
    first = f["endpoint"] in FIRST
    add(id="openfda-bulk-" + f["endpoint"].replace("/", "-"), host="download.open.fda.gov", url=f["file"],
        method="GET", auth="none", format="zip containing one JSON {meta, results[]}",
        expected_bytes=int(float(f["size_mb"]) * MB),
        expected_size_basis="size_mb from download.json today (zipped); unzipped is several times larger",
        records=f["records"], export_date=f["export_date"],
        status="listed_in_manifest; host robots NOT checked; file NOT downloaded", network_required=True,
        slice="first" if first else "second", priority=2 if first else 4)
add(id="openfda-query-api", host="api.fda.gov",
    url_template="https://api.fda.gov/{category}/{endpoint}.json?search={field}:{value}&limit={max 1000}&skip={max 25000}",
    examples=["https://api.fda.gov/drug/event.json?limit=1", "https://api.fda.gov/device/event.json?limit=1",
              "https://api.fda.gov/drug/enforcement.json?limit=1", "https://api.fda.gov/device/recall.json?limit=1",
              "https://api.fda.gov/device/510k.json?limit=1", "https://api.fda.gov/drug/label.json?limit=1"],
    method="GET", auth="none (optional free api_key)",
    rate_limit="NOT verified today (open.fda.gov docs host returned 403). From memory: no key 240/min and 1,000/day per IP; with key 240/min and 120,000/day.",
    format="json", expected_bytes="1.8-6.9 KB per record", status="verified_200_today (6 samples)",
    totals_today={"drug/event": 20692690, "device/event": 26136889, "drug/enforcement": 17965,
                  "device/recall": 59222, "device/510k": 176070, "drug/label": 262883},
    date_semantics={"drug/event": "receiptdate, receivedate, transmissiondate (YYYYMMDD strings)",
                    "device/event": "date_received, date_of_event, report_date/date_report, date_added, date_changed",
                    "enforcement": "recall_initiation_date, center_classification_date, report_date, termination_date",
                    "device/recall": "event_date_initiated, event_date_posted, event_date_terminated (ISO)",
                    "510k/pma": "date_received, decision_date",
                    "label": "effective_time (SPL effective), version"},
    stable_ids={"drug/event": "safetyreportid (+safetyreportversion)", "device/event": "mdr_report_key, report_number",
                "enforcement": "recall_number, event_id",
                "device/recall": "product_res_number, cfres_id, res_event_number, k_numbers/pma_numbers, firm_fei_number",
                "510k": "k_number", "pma": "pma_number + supplement_number", "label": "set_id, id, version"},
    note="drug/event bulk = 114 GB zipped (1,767 files); device/event = 18.4 GB (371 files). Never bulk; use per-product queries and count= aggregations, stored as dated publisher-reported query results.",
    network_required=True, priority=3)

# ---------------- FDA web ----------------
add(id="fda-warning-letters-export", host="www.fda.gov",
    url="https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/compliance-actions-and-activities/warning-letters/datatables-data?page&_format=xlsx",
    index_page="https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/compliance-actions-and-activities/warning-letters",
    method="GET", auth="none", format="xlsx (publisher export link found in the page HTML)", expected_bytes=None,
    expected_size_basis="unknown; export NOT fetched. Index page = 76,651 bytes, HTTP 200 today",
    robots="allowed; Crawl-delay: 30 for User-agent:*",
    date_semantics="Posted Date vs Letter Issue Date (distinct columns); response and close-out letters are separate dated items",
    stable_ids="letter URL slug (company + MARCS-CMS number + issue date)",
    status="index_verified_200_today; export link discovered, not fetched", network_required=True, priority=2)
add(id="fda-recalls-export", host="www.fda.gov",
    url="https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/datatables-data?page&_format=xlsx",
    index_page="https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts", method="GET", auth="none",
    format="xlsx (page link carries a randparam cache-buster)", expected_bytes=None,
    expected_size_basis="unknown; index page = 73,470 bytes, HTTP 200 today", robots="allowed; Crawl-delay: 30",
    date_semantics="press-release publish date; NOT recall initiation or classification date (those are in openFDA enforcement)",
    status="index_verified_200_today; export not fetched", network_required=True, priority=3)

# ---------------- CPSC ----------------
add(id="cpsc-recalls-rest", host="www.saferproducts.gov",
    url_template="https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallDateStart={YYYY-MM-DD}&RecallDateEnd={YYYY-MM-DD}",
    method="GET", auth="none (documented as keyless)", format="json|xml",
    status="BLOCKED_today: robots.txt returned HTTP 403 (Akamai Access Denied) for UA LegalCorpusResearch/1.0; www.cpsc.gov robots.txt also 403. Not retried, not bypassed.",
    date_semantics="RecallDate vs LastPublishDate (from memory, unverified today)",
    stable_ids="RecallID, RecallNumber (unverified today)", fallback="local-cpsc-recalls-csv (9,971 rows)",
    decision_required="User may download the CPSC recalls export in a browser, or approve another official channel.",
    network_required=True, priority=5)

# ---------------- NHTSA ----------------
for f, st, lm in (("rcl/FLAT_RCL_POST_2010.zip", 200, "2026-09-18"), ("rcl/FLAT_RCL_PRE_2010.zip", 200, "2026-09-18"),
                  ("cmpl/FLAT_CMPL.zip", 200, "2026-09-18"), ("inv/FLAT_INV.zip", 200, "2026-09-18"),
                  ("rcl/FLAT_RCL.zip", 404, None), ("tsbs/FLAT_TSBS.zip", 404, None)):
    add(id="nhtsa-flat-" + f.split("/")[1], host="static.nhtsa.gov", url="https://static.nhtsa.gov/odi/ffdd/" + f,
        method="GET", auth="none", format="zip of tab-delimited TXT (layout in companion text file, not fetched)",
        expected_bytes=None,
        expected_size_basis="HEAD returned no Content-Length; a 1-byte Range request was ignored (HTTP 200). Size unverified.",
        http_status_today=st, publisher_last_modified=lm, robots="no robots.txt (S3 404)",
        status="exists_today_size_unknown" if st == 200 else "404_today",
        stable_ids="recalls: CAMPNO (NHTSA campaign number); complaints: ODINO/CMPLID; investigations: NHTSA action number",
        date_semantics="recalls: report-received date, record-added date, manufacture begin/end; complaints: failure date, added date (from memory; verify against the layout file)",
        network_required=True, priority=3 if ("RCL_P" in f or "INV" in f) else 5)
add(id="nhtsa-api", host="api.nhtsa.gov",
    url_template="https://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={yyyy} | https://api.nhtsa.gov/complaints/complaintsByVehicle?make=..&model=..&modelYear=..",
    method="GET", auth="none (documented)",
    status="NOT_FETCHED: /robots.txt returned HTTP 403 with body {\"message\":\"Missing Authentication Token\"} (API-gateway unknown-route response). Treated conservatively as disallow. www.nhtsa.gov robots.txt = 403 Akamai.",
    decision_required="Confirm whether an API-gateway 403 on /robots.txt counts as 'no robots file'. Flat files cover the same data.",
    network_required=True, priority=6)

# ---------------- regulations.gov ----------------
add(id="regulations-gov-v4", host="api.regulations.gov",
    url_template="https://api.regulations.gov/v4/{documents|dockets|comments}?filter[docketId]={FDA-YYYY-N-NNNN}&page[size]=250&sort=lastModifiedDate",
    docs="https://open.gsa.gov/api/regulationsgov/ (HTTP 200 today, 59,455 bytes)", method="GET",
    auth="api.data.gov key REQUIRED (X-Api-Key). DEMO_KEY exists but was not used.",
    rate_limit="docs defer to api.data.gov limits; commenting API 50/min and 500/hour; GET default commonly 1,000/hour (from memory). 250 per page x 20 pages = 5,000 per query; slide the window by lastModifiedDate.",
    format="json:api", date_semantics="postedDate, lastModifiedDate, commentStartDate/commentEndDate, receiveDate",
    stable_ids="docketId (FDA-2021-N-0862), documentId (FDA-2021-N-0862-0001), objectId, frDocNum (joins Federal Register document_number)",
    status="NOTE_ONLY_not_contacted",
    decision_required="User registers a free api.data.gov key if docket/comment material is wanted.",
    network_required=True, priority=7)

# ---------------- SEC ----------------
add(id="sec-edgar-and-litigation", host="www.sec.gov | data.sec.gov | efts.sec.gov",
    url_template="https://data.sec.gov/submissions/CIK{10-digit}.json | https://data.sec.gov/api/xbrl/companyfacts/CIK{10-digit}.json | https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip | https://efts.sec.gov/LATEST/search-index?q={query} | litigation-release and administrative-proceeding index pages on www.sec.gov",
    method="GET",
    auth="none, but the SEC fair-access policy requires a declared User-Agent (organisation + contact); max 10 requests/second",
    status="BLOCKED_today: https://www.sec.gov/robots.txt returned HTTP 403 'Request Rate Threshold Exceeded' for the undeclared UA. Exactly 1 request sent; no further SEC requests. No contact data was sent.",
    stable_ids="CIK, accession number, file number, litigation release LR-NNNNN, administrative proceeding file 3-NNNNN",
    date_semantics="filingDate vs reportDate (period) vs acceptanceDateTime; litigation-release date vs complaint filing date",
    local="returnedfiles/state_admin_agency_urls.jsonl holds 6,395 SEC_litig + 7,555 SEC_rules URL references (no content)",
    decision_required="User supplies the exact declared User-Agent string (organisation + monitored contact address) before any SEC collection. devvvv/src/lib/agents/regulatory-sources.server.ts reads SEC_USER_AGENT from env and has a placeholder default that was NOT used or verified here.",
    network_required=True, priority=6)

with open(OUT, "w", encoding="utf-8") as fh:
    for e in E:
        fh.write(json.dumps(e, ensure_ascii=False) + "\n")
print(len(E), OUT)
