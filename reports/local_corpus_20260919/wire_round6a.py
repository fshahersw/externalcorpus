"""Server-side wiring only (the UI agent owns the front-end files): county filing routes + public-laws area. Idempotent."""
P = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/server.py'
text = open(P, encoding='utf-8').read()
pairs = [
    ("'indiana-code':'indiana_code','indiana_code':'indiana_code'}",
     "'indiana-code':'indiana_code','indiana_code':'indiana_code','public-laws':'public_laws','public_laws':'public_laws'}"),
    ("            if path=='/api/blocks':",
     "            if path.startswith('/api/county-filing'):\n"
     "                # Official rules, forms, e-filing and fee sources by county; an absent or failing layer answers available:false.\n"
     "                if path=='/api/county-filing/state':result=judge_layer('county_filing','for_state',p.get('state',''))\n"
     "                elif path=='/api/county-filing/coverage':\n"
     "                    try:\n"
     "                        import importlib\n"
     "                        result=importlib.import_module('county_filing').coverage()\n"
     "                    except Exception:result=None\n"
     "                else:result=judge_layer('county_filing','for_county',p.get('fips',''))\n"
     "                return self.send_body(200,result or {'available':False})\n"
     "            if path=='/api/blocks':"),
]
for old, new in pairs:
    if new in text:
        continue
    assert text.count(old) == 1, old[:60]
    text = text.replace(old, new)
open(P, 'w', encoding='utf-8', newline='').write(text)
print('server wired')
