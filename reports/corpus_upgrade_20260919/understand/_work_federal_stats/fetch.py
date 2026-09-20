"""Polite bounded scouting fetcher (federal-stats-scout). Usage: fetch.py GET|HEAD name=url [name=url ...]
GET bodies go to the session scratchpad (not the project); receipts are appended to request_log.jsonl here.
Delay: 3.5 s per request (10.5 s for jpml.uscourts.gov, whose robots.txt sets Crawl-delay: 10).
No retries. A 401/403/429/503 marks the host blocked for the rest of the run (barrier, not worked around)."""
import sys, time, json, hashlib, urllib.request, urllib.error, os, datetime
from urllib.parse import urlparse
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "C:/Users/firas/AppData/Local/Temp/claude/C--Users-firas-Downloads-SCRAPE/94e14568-82ad-45ac-8fbc-ddcfb15f37d7/scratchpad/fedstats"
LOG = os.path.join(HERE, "request_log.jsonl")
UA = "LegalCorpusResearch/1.0"
method = sys.argv[1]
blocked = set()
first = True
for arg in sys.argv[2:]:
    name, url = arg.split("=", 1)
    host = urlparse(url).netloc
    if host in blocked:
        print(name, "SKIPPED host blocked")
        continue
    if not first:
        time.sleep(10.5 if "jpml" in host else 3.5)
    first = False
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
    rec = {"ts": datetime.datetime.utcnow().isoformat() + "Z", "method": method, "name": name, "url": url, "host": host}
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read() if method == "GET" else b""
            rec.update(status=r.status, final_url=r.geturl(), ctype=r.headers.get("Content-Type"),
                       clen=r.headers.get("Content-Length"), last_modified=r.headers.get("Last-Modified"),
                       size=len(body), sha256=hashlib.sha256(body).hexdigest() if body else None)
            if method == "GET":
                ct = rec["ctype"] or ""
                ext = ".html" if "html" in ct else (".txt" if "text/plain" in ct else ".bin")
                with open(os.path.join(OUT, name + ext), "wb") as f:
                    f.write(body)
    except urllib.error.HTTPError as e:
        rec.update(status=e.code, error=str(e), server=e.headers.get("Server"))
        if e.code in (401, 403, 429, 503):
            blocked.add(host)
    except Exception as e:
        rec.update(status=None, error=repr(e))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(name, rec.get("status"), rec.get("ctype"), rec.get("clen"), rec.get("size"), rec.get("last_modified"),
          rec.get("final_url") if rec.get("final_url") != url else "", rec.get("error", ""))
