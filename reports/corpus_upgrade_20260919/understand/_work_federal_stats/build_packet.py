"""Build packets/federal_stats_urls.jsonl (+ federal_hsd_order_urls.jsonl) from the saved scouting pages.
Every URL below was read from a listing page fetched on 2026-09-18/19 (UTC); nothing is guessed.
No data file was downloaded; 5 files were HEAD-checked (see request_log.jsonl)."""
import sys, os, re, json, datetime
from urllib.parse import urljoin, urlparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tables import parse, load

OUT = os.path.join(os.path.dirname(HERE), "packets", "federal_stats_urls.jsonl")
OUT_HSD = os.path.join(os.path.dirname(HERE), "packets", "federal_hsd_order_urls.jsonl")
DT = "https://www.uscourts.gov/statistics-reports/caseload-statistics-data-tables"
HEAD = {}
for line in open(os.path.join(HERE, "request_log.jsonl"), encoding="utf-8"):
    r = json.loads(line)
    if r["method"] == "HEAD" and r.get("status") == 200:
        HEAD[r["url"]] = {"bytes": int(r["clen"]), "http_last_modified": r["last_modified"]}

WHY = {
    "C": "National and per-district civil filings/terminations/pending totals; denominator for every district-level comparison.",
    "C-1": "Civil filed/terminated/pending by basis of jurisdiction (diversity vs federal question) per district; mass-tort cases are overwhelmingly diversity.",
    "C-2": "Civil filings by jurisdiction and nature of suit (NOS 365/367/368 product liability, 245, 385, asbestos) nationally.",
    "C-2A": "Civil filings by nature of suit, multi-year comparison; trend line for personal-injury product liability.",
    "C-3": "Civil filings by jurisdiction, nature of suit AND district; the core table for where tort/product-liability volume sits.",
    "C-3A": "Civil cases PENDING by nature of suit and district; shows MDL-driven pending inventories (annual only).",
    "C-3B": "Civil cases TERMINATED by nature of suit and district (annual only).",
    "C-4": "Civil terminations by nature of suit and action taken (no court action / before pretrial / during-after pretrial / trial); disposition-stage mix for tort categories.",
    "C-4A": "Civil terminations by district and action taken (annual only).",
    "C-5": "Median time from filing to disposition of civil cases by action taken, per district; key time-to-disposition benchmark.",
    "C-6": "Civil cases pending by length of time, per district (annual only).",
    "C-7": "IP, securities/commodities and bankruptcy-appeal filings by district; securities class-action context (annual only).",
    "C-8": "Civil filings by origin (original, removed, remanded, reopened, transferred, MDL transfer) ; removal/MDL-transfer volume.",
    "C-9": "Recovery/enforcement filings; low relevance, kept for completeness of the C series.",
    "C-10": "Social Security filings; low relevance, kept for completeness of the C series.",
    "C-11": "Product liability cases filed by nature of suit (asbestos, pharma/health-care PI, other PI, property); the single most mass-tort-specific AO table.",
    "C-12": "Civil cases pending three years or more by jurisdiction and nature of suit; MDL aging signal.",
    "C-13": "Civil pro se vs represented filings by district.",
    "T-1": "Civil and criminal trials completed per district; trial-capacity context.",
    "T-2": "Lengths of civil and criminal trials completed.",
    "T-3": "Median time from filing to trial for civil cases, per district.",
    "T-4": "Trials resulting in verdicts or judgments (annual only).",
    "T-5": "Lengths of trials resulting in verdicts or judgments (annual only).",
    "X-1A": "Weighted and unweighted filings per authorized judgeship, per district; workload per judge.",
    "V-1": "Visiting-judge services provided/received between districts.",
    "JCI": "Judicial Caseload Indicators summary (work of the federal judiciary).",
    "S-19": "JPML: cases transferred by order of the Panel, by transferee/transferor district (annual, FY).",
    "S-20": "JPML: cumulative summary of multidistrict litigation since 1968 (annual, FY).",
    "S-22": "Judicial conduct complaints filed and action taken (28 U.S.C. 351-364).",
    "M-5": "Civil consent cases terminated by magistrate judges under 28 U.S.C. 636(c).",
}
KEEP_STFJ = ["C", "C-1", "C-2", "C-3", "C-4", "C-5", "T-1", "T-2", "T-3", "X-1A", "V-1", "JCI"]
KEEP_FJCS = ["C", "C-1", "C-2", "C-3", "C-4", "C-5", "T-3", "X-1A"]
rows_out, seen = [], set()


def fmt_of(url):
    m = re.search(r"\.(xlsx|xls|pdf|csv|zip)($|\?)", url, re.I)
    return m.group(1).lower() if m else "html"


def add(url, title, table_id, period, category, parent, why, packet, priority, publication=None, size_label=None, alt=None, note=None, delay=None):
    if url in seen:
        return
    seen.add(url)
    host = urlparse(url).netloc
    rec = {"url": url, "host": host, "title": title, "table_id": table_id, "period_label": period, "format": fmt_of(url),
           "category": category, "parent_page": parent, "why": why, "publication": publication, "packet": packet,
           "priority": priority, "size_label": size_label, "alt_pdf_url": alt,
           "verified": "listing+HEAD" if url in HEAD else "listing", "head": HEAD.get(url),
           "min_delay_s": delay or (10 if "jpml" in host else (30 if "fjc.gov" in host else 3)),
           "already_in_directory_db": False, "note": note}
    rows_out.append(rec)


def ao_rows(page, pub_filter, period, keep=None):
    heads, rows, pager = parse(page)
    for r in rows:
        if r["Publication Name"] != pub_filter or r["Reporting Period"] != period:
            continue
        if keep is not None and r["Table Number"] not in keep:
            continue
        xl = [f for f in r["_files"] if f[0].lower().endswith(".xlsx")]
        pdf = [f for f in r["_files"] if f[0].lower().endswith(".pdf")]
        yield r, xl, pdf


def size(lbl):
    m = re.search(r"([\d.]+ [KM]B)", lbl or "")
    return m.group(1) if m else None


# ---- P1: AO statistical tables, xlsx (latest period of each publication)
for page, pub, period, keep, prio, cat in [
    ("dt_civil", "Statistical Tables For The Federal Judiciary", "June 30, 2026", KEEP_STFJ, 1, "civil_caseload_quarterly"),
    ("dt_trials", "Statistical Tables For The Federal Judiciary", "June 30, 2026", KEEP_STFJ, 1, "civil_caseload_quarterly"),
    ("dt_jb_civil", "Judicial Business", "September 30, 2025", None, 1, "civil_caseload_annual"),
    ("dt_trials", "Judicial Business", "September 30, 2025", ["M-5"], 2, "civil_caseload_annual"),
    ("dt_judges", "Judicial Business", "September 30, 2025", ["S-22"], 3, "judges_judgeships"),
    ("dt_jff_civil", "Judicial Facts and Figures", "September 30, 2025", None, 2, "civil_trend_multiyear"),
    ("dt_judges", "Judicial Facts and Figures", "September 30, 2025", None, 2, "judges_judgeships"),
    ("dt_civil", "Federal Judicial Caseload Statistics", "March 31, 2026", KEEP_FJCS, 3, "civil_caseload_quarterly"),
]:
    for r, xl, pdf in ao_rows(page, pub, period, keep):
        tid = r["Table Number"]
        c = cat
        if tid in ("S-19", "S-20"):
            c = "mdl_statistics"
        elif tid.startswith("T-") or tid in ("6.3", "6.4", "6.5"):
            c = "trials_time_to_disposition"
        elif tid in ("X-1A", "6.2", "1.1", "6.6", "V-1"):
            c = "judges_judgeships"
        why = WHY.get(tid) or ("Judicial Facts and Figures multi-year trend table: " + r["Title"].split(" - ", 1)[-1] + ".")
        if xl:
            add(xl[0][0], r["Title"], tid, "Reporting period ending " + period, c, r["_detail"] or DT, why,
                "P1_uscourts_tables_xlsx", prio, pub, size(xl[0][1]), pdf[0][0] if pdf else None)

# ---- P2: FCMS (xlsx + pdf) and CJRA (pdf only)
FCMS_PARENT = "https://www.uscourts.gov/data-news/reports/statistical-reports/federal-court-management-statistics/federal-court-management-statistics-june-2026"
heads, rows, pager = parse("dt_fcms")
for r in rows:
    if r["Reporting Period"] != "June 30, 2026":
        continue
    dist = "District" in r["Title"]
    why = ("Per-district management profile (94 districts + national): filings, terminations, pending, weighted filings per judgeship, "
           "median months filing-to-disposition and filing-to-trial (civil), civil cases over three years old, vacant judgeship months; six-period history per court."
           if "Profiles" in r["Title"] and dist else
           "District comparison within circuit / national ranking of the same profile measures." if dist else
           "Courts of appeals management statistics; appellate context for MDL appeals.")
    for f in r["_files"]:
        add(f[0], r["Title"], "FCMS (no table number)", "12-month profile period ending June 30, 2026 (as listed: June 30, 2026)",
            "district_court_management_profiles" if dist else "appellate_management_statistics", r["_detail"] or FCMS_PARENT, why,
            "P2_uscourts_fcms_cjra", 1 if dist else 3, "Federal Court Management Statistics", size(f[1]))
for u, t in [("https://www.uscourts.gov/file/27866/download", "Explanation of Judicial Caseload Profiles: District Courts (xls, via /file/ID/download redirect)"),
             ("https://www.uscourts.gov/file/27865/download", "Explanation of Judicial Caseload Profiles: Courts of Appeals (xls, via /file/ID/download redirect)"),
             ("https://www.uscourts.gov/media/25754", "FCMS Explanation of Selected Terms (pdf media page)")]:
    add(u, t, None, "undated on listing", "methodology", FCMS_PARENT, "Definitions needed to label every FCMS measure correctly (weighted filings, median time, etc.).",
        "P2_uscourts_fcms_cjra", 2, "Federal Court Management Statistics", note="Final file URL/format not resolved (no request made); resolve at capture time and record the redirect.")

CJRA_PARENT = "https://www.uscourts.gov/data-news/reports/statistical-reports/civil-justice-reform-act-report/march-2026-civil-justice-reform-act"
CJRA_WHY = {
    "CJRA 7": "PER-JUDGE list of civil cases pending more than three years (district and magistrate judges, with case identifiers and status codes). Largest file (listed 17.97 MB); the primary official per-judge aging source, heavily populated by MDL member cases.",
    "CJRA 8": "PER-JUDGE list of motions pending more than six months, with case identifiers; motion-backlog evidence per judge.",
    "CJRA 9": "PER-JUDGE bench trials submitted more than six months.",
    "CJRA 10": "Per-judge bankruptcy appeals pending more than six months; low mass-tort relevance.",
    "CJRA 11": "Per-judge Social Security appeals pending more than six months; low mass-tort relevance.",
    "CJRA 1": "National totals of reportable matters by type of matter and type of judge; denominators for CJRA 7/8.",
    "CJRA 2": "Total pending matters by type and circuit (comparison).",
    "CJRA 3": "Total matters pending by type and circuit.",
    "CJRA 4": "Average number of cases and motions pending per judge, by circuit.",
    "N/A": "CJRA Appendices A-D (status-code legend and methodology); required to decode the per-judge tables.",
}
heads, rows, pager = parse("dt_cjra")
for r in rows:
    if r["Reporting Period"] == "March 31, 2026":
        tid = r["Table Number"]
        for f in r["_files"]:
            add(f[0], r["Title"], tid, "As of March 31, 2026 (semiannual CJRA report)", "cjra_per_judge" if tid in ("CJRA 7", "CJRA 8", "CJRA 9", "CJRA 10", "CJRA 11") else "cjra_summary",
                r["_detail"] or CJRA_PARENT, CJRA_WHY.get(tid, "CJRA table."), "P2_uscourts_fcms_cjra",
                1 if tid in ("CJRA 7", "CJRA 8", "CJRA 9", "CJRA 1") else (2 if tid in ("CJRA 2", "CJRA 3", "CJRA 4") else 3),
                "Civil Justice Reform Act (CJRA)", size(f[1]))
# appendices appear only on the report page
doc = load("cjra_2026_03")
for a in doc.xpath("//main//a[@href]"):
    h = urljoin("https://www.uscourts.gov/", a.get("href"))
    if h.endswith("cjra_na_0331.2026.pdf"):
        add(h, "Civil Justice Reform Act (CJRA) Appendices A,B,C,D", "CJRA Appendices", "As of March 31, 2026 (semiannual CJRA report)", "methodology",
            CJRA_PARENT, CJRA_WHY["N/A"], "P2_uscourts_fcms_cjra", 1, "Civil Justice Reform Act (CJRA)", size(" ".join(a.text_content().split())))

# ---- P3: JPML current
JP = "https://www.jpml.uscourts.gov/"
doc = load("jpml_pending")
PWHY = {"By_District": "Every pending MDL grouped by transferee district with transferee judge, MDL number/caption, actions pending and total actions; the authoritative judge<->MDL<->district map.",
        "By_MDL_Number": "Same inventory keyed by MDL number; primary key for joining to MDL dockets, CourtListener and local MDL-3080-style collections.",
        "By_MDL_Type": "Pending MDLs by docket type (products liability, antitrust, sales practices, etc.); category label per MDL.",
        "By_Actions_Pending": "Pending MDLs ranked by actions pending; identifies the largest mass-tort MDLs.",
        "Recently_Terminated": "MDLs terminated in the calendar year to date; status changes."}
for a in doc.xpath("//body//a[@href]"):
    h = urljoin(JP, a.get("href")); t = " ".join(a.text_content().split())
    if "/sites/jpml/files/" in h:
        key = next((k for k in PWHY if k in h), None)
        add(h, "JPML " + re.sub(r"[-_]", " ", h.rsplit("/", 1)[1].rsplit(".", 1)[0]), key, t, "mdl_pending_dockets", JP + "pending-mdls-0", PWHY.get(key, "JPML report."),
            "P3_jpml_current", 1, "JPML Pending MDL reports")
for name, parent, cat, pub in [("jpml_quarterly", JP + "mdl-quarterly-caseload-summary", "mdl_statistics", "JPML MDL Quarterly Caseload Summary"),
                               ("jpml_judges", JP + "content/panel-judges", "judges_judgeships", "JPML Panel Judges")]:
    doc = load(name)
    for a in doc.xpath("//body//a[@href]"):
        h = urljoin(JP, a.get("href")); t = " ".join(a.text_content().split())
        if "/sites/jpml/files/" in h:
            if name == "jpml_quarterly":
                add(h, "JPML Pending MDL Dockets by Circuit (quarterly caseload summary)", "By_Circuit", t + " (file name date: " + re.search(r"Circuit-(.*)\.pdf", h).group(1) + ")", cat, parent,
                    "Quarterly MDL caseload summary by circuit; only two quarters are posted.", "P3_jpml_current", 1 if "June-30-2026" in h else 2, pub)
            else:
                add(h, t, "Panel roster", "Roster file dated 6-3-2026 in file name", cat, parent, "Current and former JPML panel judges; links Panel membership to judge entities.", "P3_jpml_current", 1, pub)
for name, parent in [("jpml_stats", JP + "statistics-info"), ("jpml_stats_p2", JP + "statistics-info?page=1")]:
    doc = load(name)
    for a in doc.xpath("//body//a[@href]"):
        h = urljoin(JP, a.get("href")); t = " ".join(a.text_content().split())
        if "/sites/jpml/files/" not in h:
            continue
        m = re.search(r"(\d{4})$", t)
        yr = int(m.group(1)) if m else 0
        latest = yr == 2025
        if t.startswith("Calendar Year"):
            tid, why = "JPML CY statistics", "Calendar-year JPML statistics: motions decided, MDLs created/denied, actions transferred, by docket type and district."
        elif t.startswith("Fiscal Year"):
            tid, why = "JPML FY statistical analysis", "Fiscal-year Statistical Analysis of Multidistrict Litigation: per-MDL cumulative actions transferred/terminated/remanded/pending by district and judge."
        else:
            tid, why = "JPML cumulative terminated", "Cumulative list of terminated MDLs through the fiscal year (MDL number, caption, transferee district/judge, totals); historical MDL universe."
        add(h, "JPML " + t, tid, t, "mdl_statistics", parent, why, "P3_jpml_current" if latest else "P4_jpml_history", 1 if latest else 3, "JPML Statistical Information")
doc = load("jpml_archive")
for a in doc.xpath("//body//a[@href]"):
    h = urljoin(JP, a.get("href")); t = " ".join(a.text_content().split())
    if "/sites/jpml/files/" in h:
        m = re.search(r"-([A-Z][a-z]+-\d{1,2}-\d{4})\.pdf$", h)
        add(h, "JPML " + t + " (archive)", t, "As of " + (m.group(1).replace("-", " ") if m else "date in file name"), "mdl_pending_dockets_history",
            JP + "pending-mdl-reports-archive", "Monthly snapshots (archive page covers Sept 2024 - Aug 2026) allow temporal tracking of actions pending per MDL and judge reassignment.",
            "P4_jpml_history", 3, "JPML Pending MDL reports archive")

# ---- P5: judgeships / vacancies
AJ = "https://www.uscourts.gov/about-federal-courts/about-federal-judges/authorized-judgeships"
doc = load("auth_judgeships")
main = doc.xpath("//main")[0]
for a in main.xpath(".//a[@href]"):
    h = urljoin("https://www.uscourts.gov/", a.get("href")); t = " ".join(a.text_content().split())
    if "/sites/default/files/" in h or "/file/" in h:
        add(h, "Authorized Judgeships: " + t, None, "Folder date in URL (2025-01 / 2025-03) is an upload path, not an effective date", "judges_judgeships", AJ,
            "Authorized (permanent/temporary) judgeships per court; denominator for per-judgeship workload and vacancy rates.", "P5_judgeships_vacancies", 2, "Authorized Judgeships",
            note="Links to /file/ID/download were not resolved." if "/file/" in h else None)
for u, t, why, prio in [
    ("https://www.uscourts.gov/data-news/judicial-vacancies/current-judicial-vacancies", "Current Judicial Vacancies (HTML table: Court, Incumbent, Vacancy Reason, Vacancy Date, Nominee, Nomination Date)", "Live vacancy table; page stated 'as of 09/18/2026', 26 vacancies, 12 nominees pending when scouted.", 1),
    ("https://www.uscourts.gov/data-news/judicial-vacancies/future-judicial-vacancies", "Future Judicial Vacancies", "Announced future vacancies (not fetched).", 2),
    ("https://www.uscourts.gov/data-news/judicial-vacancies/judicial-emergencies", "Judicial Emergencies", "Courts with judicial emergencies (not fetched).", 2),
    ("https://www.uscourts.gov/data-news/judicial-vacancies/confirmation-listing", "Confirmation Listing", "Confirmed judges in the current Congress (not fetched).", 2),
    ("https://www.uscourts.gov/data-news/judicial-vacancies/archive-judicial-vacancies", "Archive of Judicial Vacancies", "Monthly archive index (not fetched).", 3),
    ("https://www.uscourts.gov/data-news/reports/statistical-reports/judicial-business-united-states-courts/judicial-business-2025/status-article-iii-judgeships-judicial-business-2025", "Status of Article III Judgeships - Judicial Business 2025", "Annual narrative + tables 12/13-style judgeship status (not fetched).", 2),
]:
    add(u, t, None, "Live page; record capture date and the page's own 'as of' date separately", "judges_judgeships", "https://www.uscourts.gov/judges-judgeships/judicial-vacancies", why, "P5_judgeships_vacancies", prio, "Judicial Vacancies")

# ---- P6: FJC biographical export (robots Crawl-delay: 30)
FE = "https://www.fjc.gov/history/judges/biographical-directory-article-iii-federal-judges-export"
doc = load("fjc_export")
for a in doc.xpath("//body//a[@href]"):
    h = urljoin("https://www.fjc.gov/", a.get("href")); t = " ".join(a.text_content().split())
    if "/sites/default/files/history/" in h:
        add(h, "FJC Biographical Directory export: " + t, None, "Continuously updated export; no period on page", "judges_biographical", FE,
            "Relational Article III judge data (service, education, career, demographics) using the FJC's own identifiers (column names not re-verified in this scout); complements the judges.csv already in the directory DB.",
            "P6_fjc_export", 2, "FJC Biographical Directory of Article III Federal Judges", delay=30,
            note="judges.csv is already referenced by 8,148 directory records; other files were not found locally by file name." if h.endswith("judges.csv") else None)
for rec in rows_out:
    if rec["url"].endswith("/history/judges.csv"):
        rec["already_in_directory_db"] = True

# ---- P7: context pages (HTML captures)
JB = "https://www.uscourts.gov/data-news/reports/statistical-reports/judicial-business-united-states-courts/judicial-business-2025"
for u, t, why, prio in [
    (JB + "/judicial-panel-multidistrict-litigation-judicial-business-2025", "Judicial Business 2025 - Judicial Panel on Multidistrict Litigation (narrative)", "AO narrative on MDL activity for FY2025 (not fetched).", 1),
    (JB + "/us-district-courts-judicial-business-2025", "Judicial Business 2025 - U.S. District Courts (narrative)", "AO narrative explaining civil filing swings, usually naming the MDLs that drove them (not fetched).", 1),
    (JB + "/judicial-business-2025-tables", "Judicial Business 2025 Tables (index)", "Complete index of JB 2025 tables (not fetched); use to confirm no civil table is missing.", 2),
    (JB, "Judicial Business 2025 (landing)", "Annual report landing page.", 3),
    (CJRA_PARENT, "March 2026 Civil Justice Reform Act (report page)", "Official description and 28 U.S.C. 476 basis; page says 'Last updated: March 31, 2026'.", 2),
    (FCMS_PARENT, "Federal Court Management Statistics, June 2026 (report page)", "Report page; says 'Last updated: June 30, 2026'.", 2),
    (DT, "Caseload Statistics Data Tables (searchable index)", "Index of all AO tables; filters pn (publication), term_node_tid_depth (topic), tn (table number), m (quarter), y (year).", 2),
    ("https://www.uscourts.gov/data-news/reports/handbooks-manuals/civil-litigation-management-manual", "Civil Litigation Management Manual (landing)", "Judicial Conference manual on civil/MDL case management (not fetched).", 2),
    ("https://www.uscourts.gov/about-federal-courts/court-role-and-structure/court-website-links/highly-sensitive-document-procedures-and-court-orders", "Highly Sensitive Document Procedures and Court Orders (directory page)", "Per-court HSD orders directory; see federal_hsd_order_urls.jsonl.", 2),
    ("https://www.uscourts.gov/administration-policies/judiciary-policies", "Judiciary Policies (landing)", "Guide to Judiciary Policy entry point (not fetched).", 3),
    ("https://www.uscourts.gov/administration-policies/judiciary-financial-disclosure-reports", "Judiciary Financial Disclosure Reports (landing)", "Entry point for judge financial disclosures (database itself is a separate request-based system; not fetched).", 3),
    ("https://www.uscourts.gov/administration-policies/judicial-conduct-disability", "Judicial Conduct & Disability (landing)", "Conduct rules and orders entry point (not fetched).", 3),
    ("https://www.jpml.uscourts.gov/panel-orders", "JPML Panel Orders (landing)", "Transfer orders by hearing session (not fetched this run).", 2),
    ("https://www.jpml.uscourts.gov/hearing-information", "JPML Hearing Information", "Hearing session notices; September 24, 2026 notice PDF is already in the directory DB.", 3),
]:
    add(u, t, None, "Live page", "context_page", urljoin(u, "."), why, "P7_context_pages", prio)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    for rec in rows_out:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# ---- HSD secondary list
doc = load("hsd")
main = doc.xpath("//main")[0]
for nav in main.xpath(".//nav|.//aside"):
    nav.getparent().remove(nav)
hsd, last_court, hs, section = [], None, set(), None
for a in main.iter():
    if a.tag in ("h2", "h3", "h4"):
        section = " ".join(a.text_content().split())
        continue
    if a.tag != "a" or not a.get("href"):
        continue
    h = urljoin("https://www.uscourts.gov/", a.get("href")); t = " ".join(a.text_content().split())
    host = urlparse(h).netloc
    if host.endswith("uscourts.gov") and host != "www.uscourts.gov" and urlparse(h).path in ("", "/"):
        last_court = {"court_label": t, "court_home": h}
        continue
    if host == "www.uscourts.gov" or not last_court or h in hs:
        continue
    hs.add(h)
    hsd.append({"url": h, "host": host, "title": t, "page_section": section, "court_label": last_court["court_label"], "court_home": last_court["court_home"],
                "format": fmt_of(h), "category": "court_order_hsd", "period_label": "undated on directory page",
                "parent_page": "https://www.uscourts.gov/about-federal-courts/court-role-and-structure/court-website-links/highly-sensitive-document-procedures-and-court-orders",
                "why": "Court-specific standing/general order on filing highly sensitive documents; a per-court filing instruction.",
                "note": "court_label is the preceding court link on the AO page (explicit page evidence), not inferred from the host."})
with open(OUT_HSD, "w", encoding="utf-8", newline="\n") as f:
    for rec in hsd:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

from collections import Counter
print("total", len(rows_out))
print(Counter(r["packet"] for r in rows_out))
print(Counter((r["packet"], r["priority"]) for r in rows_out))
print(Counter(r["format"] for r in rows_out))
print(Counter(r["host"] for r in rows_out))
print("HEAD verified", sum(1 for r in rows_out if r["head"]))
print("hsd", len(hsd), "hosts", len({r["host"] for r in hsd}), Counter(r["format"] for r in hsd))
