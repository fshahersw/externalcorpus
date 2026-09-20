"""Polite bounded probe helper (regulations-scout). Sequential, >=2.6 s per host, no retries,
robots first, <=10 requests per host, UA LegalCorpusResearch/1.0, no keys, no contact data."""
import hashlib, json, os, time, urllib.request, urllib.error, urllib.robotparser
from urllib.parse import urlparse

UA = "LegalCorpusResearch/1.0"
OUT = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.join(OUT, "bodies")
os.makedirs(BODY, exist_ok=True)
RECEIPTS = os.path.join(OUT, "receipts.jsonl")
_last = {}
_robots = {}


def _host_count(host):
    n = 0
    if os.path.exists(RECEIPTS):
        with open(RECEIPTS, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("status", "x") != "x" and urlparse(d.get("url", "")).netloc == host:
                    n += 1
    return n


def _raw(url, method="GET", accept=None, timeout=120):
    host = urlparse(url).netloc
    if _host_count(host) >= 10:
        raise RuntimeError("host budget exceeded " + host)
    wait = 2.6 - (time.time() - _last.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, method=method, headers=headers)
    t = time.time()
    rec = {"url": url, "method": method, "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    body = b""
    hdr = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read() if method == "GET" else b""
            rec["status"] = r.status
            rec["final_url"] = r.geturl()
            hdr = r.headers
    except urllib.error.HTTPError as e:
        rec["status"] = e.code
        hdr = e.headers
        try:
            body = e.read()
        except Exception:
            body = b""
    except Exception as e:  # noqa
        rec["status"] = None
        rec["error"] = repr(e)[:300]
    _last[host] = time.time()
    rec["elapsed_s"] = round(time.time() - t, 2)
    for k in ("Content-Type", "Content-Length", "Last-Modified", "ETag", "Retry-After",
              "X-RateLimit-Limit", "X-RateLimit-Remaining", "Content-Encoding", "Server"):
        v = hdr.get(k) if hdr is not None else None
        if v:
            rec[k.lower()] = v
    rec["bytes"] = len(body)
    rec["sha256"] = hashlib.sha256(body).hexdigest() if body else None
    if body:
        name = rec["sha256"][:16] + ".bin"
        with open(os.path.join(BODY, name), "wb") as f:
            f.write(body)
        rec["body_file"] = name
    with open(RECEIPTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec, body


def robots(host_url):
    p = urlparse(host_url)
    host = p.netloc
    if host in _robots:
        return _robots[host]
    rec, body = _raw(p.scheme + "://" + host + "/robots.txt")
    rp = urllib.robotparser.RobotFileParser()
    info = {"status": rec["status"], "bytes": rec["bytes"]}
    if rec["status"] in (401, 403):
        rp.disallow_all = True
        info["policy"] = "robots fetch refused -> treat as disallow all"
    elif rec["status"] == 200 and body and b"<html" not in body[:400].lower():
        rp.parse(body.decode("utf-8", "replace").splitlines())
        info["crawl_delay"] = rp.crawl_delay(UA)
        info["policy"] = "parsed"
    else:
        rp.allow_all = True
        info["policy"] = "no usable robots.txt -> allow (status %s)" % rec["status"]
    _robots[host] = (rp, info)
    print("ROBOTS", host, info)
    return _robots[host]


def get(url, method="GET", accept=None):
    rp, info = robots(url)
    if not rp.can_fetch(UA, url):
        print("SKIP (robots disallow)", url)
        with open(RECEIPTS, "a", encoding="utf-8") as f:
            f.write(json.dumps({"url": url, "skipped": "robots_disallow"}) + "\n")
        return None, b""
    cd = info.get("crawl_delay")
    if cd and float(cd) > 2.6:
        time.sleep(min(float(cd), 30) - 2.6)
    rec, body = _raw(url, method=method, accept=accept)
    print(method, rec.get("status"), rec.get("bytes"), rec.get("content-type"),
          rec.get("content-length"), rec.get("last-modified"), url[:160])
    return rec, body
