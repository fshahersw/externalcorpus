"""Parse a saved uscourts.gov data-tables listing page (Drupal view).
parse(name) -> (headers, rows); CLI: tables.py <name> [--opts] prints ASCII-safe JSONL."""
import sys, os, json
from urllib.parse import urljoin
import lxml.html
OUT = "C:/Users/firas/AppData/Local/Temp/claude/C--Users-firas-Downloads-SCRAPE/94e14568-82ad-45ac-8fbc-ddcfb15f37d7/scratchpad/fedstats"
BASE = "https://www.uscourts.gov/"


def load(name):
    return lxml.html.fromstring(open(os.path.join(OUT, name + ".html"), "rb").read().decode("utf-8", "replace"))


def parse(name):
    doc = load(name)
    heads, rows = [], []
    for table in doc.xpath("//main//table"):
        heads = [" ".join(th.text_content().split()) for th in table.xpath(".//thead//th")]
        for tr in table.xpath(".//tbody/tr"):
            row = {}
            for h, td in zip(heads, tr.xpath("./td")):
                row[h] = " ".join(td.text_content().split())
            links = [(urljoin(BASE, a.get("href")), " ".join(a.text_content().split())) for a in tr.xpath(".//a[@href]")]
            det = [l for l, t in links if "/sites/default/files/" not in l]
            row["_detail"] = det[0] if det else None
            row["_files"] = [[l, t] for l, t in links if "/sites/default/files/" in l]
            rows.append(row)
    pager = [a.get("href") for a in doc.xpath("//nav[contains(@class,'pager')]//a[@href]")]
    return heads, rows, pager


if __name__ == "__main__":
    name = sys.argv[1]
    if "--opts" in sys.argv:
        doc = load(name)
        for sel in doc.xpath("//main//select"):
            print("SELECT", sel.get("name"))
            for o in sel.xpath(".//option"):
                print("   ", o.get("value"), "|", " ".join(o.text_content().split()).encode("ascii", "replace").decode())
        sys.exit()
    heads, rows, pager = parse(name)
    print(json.dumps({"_headers": heads, "_pager": pager, "_n": len(rows)}))
    for r in rows:
        print(json.dumps(r))
