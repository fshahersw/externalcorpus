"""Round 10: the two footer tabs ("Data downloads" -> #datasets, "Collection status" -> #library) are retired with the data
behind them: the dataset catalogue page and /api/datasets, the collection-status page, and the `datasets` and `live` blocks
of /api/summary that only those pages read. Old #datasets / #library links open the overview. The main database is not
rebuilt; /files/<id> keeps serving record originals. Idempotent.
"""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def load(name):
    return open(D + name, encoding='utf-8', newline='').read()


def save(name, text):
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


def replace_once(text, name, old, new):
    """Exact, single replacement; already-applied edits are skipped."""
    if old not in text:
        return text
    assert text.count(old) == 1, (name, old[:80], text.count(old))
    return text.replace(old, new)


def cut_between(text, name, start, end):
    """Remove from the unique `start` marker up to (not including) the unique `end` marker."""
    if start not in text:
        return text
    assert text.count(start) == 1 and text.count(end) == 1, (name, start[:60])
    a, b = text.index(start), text.index(end)
    assert a < b, (name, start[:60])
    return text[:a] + text[b:]


# --- index.html: the footer keeps its label, loses the two links
name = 'index.html'
text = load(name)
text = replace_once(text, name, '<span class="footer-links"><a href="#datasets">Data downloads</a><a href="#library">Collection status</a></span>', '')
save(name, text)

# --- styles.css: the rule for the removed links
name = 'styles.css'
text = load(name)
for ending in ('\r\n', '\n'):
    text = replace_once(text, name, '.footer-links{display:flex;gap:16px}.footer-links a{color:var(--muted)}' + ending, '')
save(name, text)

# --- app.js: view registry, the two pages, the routes
name = 'app.js'
text = load(name)
for ending in ('\r\n', '\n'):
    text = replace_once(text, name, "  datasets: {title: 'Sources & downloads', description: 'Explore the collections behind your library and download their supporting data.'}," + ending, '')
    text = replace_once(text, name, "  library: {title: 'Collection status', description: 'Coverage, saved sources and collection progress.'}," + ending, '')
text = cut_between(text, name, 'function renderLibraryStatus(data) {', 'function filterField(labelText,id,type,value,placeholder) {')
text = cut_between(text, name, 'async function renderDatasets(signal) {', 'async function renderCollections(signal){')
text = replace_once(text, name, "}else if(route.view==='overview'||route.view==='library') {", "}else if(route.view==='datasets'||route.view==='library'){navigate('overview');return;} // both footer pages were retired\n  else if(route.view==='overview') {")
text = replace_once(text, name, "if(route.view==='library')renderLibraryStatus(data);else renderOverview(data);", 'renderOverview(data);')
for ending in ('\r\n', '\n'):
    text = replace_once(text, name, "  else if(route.view==='datasets')await renderDatasets(signal);" + ending, '')
text = replace_once(text, name, "if(route.view!=='overview'&&route.view!=='library')loadSummary()", "if(route.view!=='overview')loadSummary()")
for leftover in ('renderLibraryStatus', 'renderDatasets', 'renderEnrichment', "'/api/datasets'"):
    assert leftover not in text, leftover
save(name, text)

# --- server.py: the endpoint, the two summary blocks and the helper only they used
name = 'server.py'
text = load(name)
text = replace_once(text, name, "                s=enriched_summary(s);s['live']=live_jobs();return self.send_body(200,s)", "                s=enriched_summary(s);s.pop('datasets',None);return self.send_body(200,s)")
text = cut_between(text, name, "            if path=='/api/datasets':", "            if path=='/api/documents':return self.send_body(200,query_documents(p))")
text = cut_between(text, name, 'def live_jobs():', 'def public_item(row):')
assert 'live_jobs' not in text and "'/api/datasets'" not in text
save(name, text)
print('round 10 applied: footer tabs, their pages and their data removed')
