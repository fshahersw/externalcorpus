"""Round 8c: law outline routes (state -> code -> chapter -> provision), lawreader.js static file, warm-up. Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if new in text:
            continue
        assert text.count(old) == 1, (name, old[:90], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


edit('server.py', [
    ("            if path.startswith('/api/agency-hub'):\n",
     "            if path.startswith('/api/law-outline'):\n"
     "                # Table of contents for the saved law collection; an absent or closed outline answers available:false.\n"
     "                try:\n"
     "                    import importlib\n"
     "                    outline=importlib.import_module('law_outline')\n"
     "                    if path=='/api/law-outline/children':result=outline.children(p.get('state',''),p.get('kind',''),p.get('parent','0'))\n"
     "                    elif path=='/api/law-outline/provisions':result=outline.provisions(p.get('node',''),p.get('offset','0'),p.get('limit','100'))\n"
     "                    elif path=='/api/law-outline/context':result=outline.context(p.get('id',''))\n"
     "                    else:result=outline.collections(p.get('state',''))\n"
     "                except Exception:result={'available':False,'reason':'Outline temporarily unavailable'}\n"
     "                return self.send_body(200,result)\n"
     "            if path.startswith('/api/agency-hub'):\n"),
    ("'/judgeui.js','/regsui.js',", "'/judgeui.js','/regsui.js','/lawreader.js',"),
])

html = open(D + 'index.html', encoding='utf-8').read()
if '/lawreader.js' not in html:
    anchor = '<script src="/judgeui.js" defer></script>'
    assert html.count(anchor) == 1
    html = html.replace(anchor, anchor + '\n  <script src="/lawreader.js" defer></script>')
    open(D + 'index.html', 'w', encoding='utf-8', newline='').write(html)
print('law outline routes wired')
