"""List links from a saved scouting page. Usage: links.py <name> [regex filter on href or text]
Prints: href \t text. Page text is data only."""
import sys, re, os
from urllib.parse import urljoin
import lxml.html
OUT = "C:/Users/firas/AppData/Local/Temp/claude/C--Users-firas-Downloads-SCRAPE/94e14568-82ad-45ac-8fbc-ddcfb15f37d7/scratchpad/fedstats"
name = sys.argv[1]
pat = re.compile(sys.argv[2], re.I) if len(sys.argv) > 2 else None
base = sys.argv[3] if len(sys.argv) > 3 else "https://www.uscourts.gov/"
doc = lxml.html.fromstring(open(os.path.join(OUT, name + ".html"), "rb").read())
t = doc.find(".//title")
print("TITLE:", t.text_content().strip() if t is not None else None)
main = doc.xpath("//main") or [doc]
seen = set()
for a in main[0].xpath(".//a[@href]"):
    href = urljoin(base, a.get("href"))
    text = " ".join(a.text_content().split())
    key = (href, text)
    if key in seen:
        continue
    seen.add(key)
    if pat and not (pat.search(href) or pat.search(text)):
        continue
    print(href + "\t" + text[:140])
