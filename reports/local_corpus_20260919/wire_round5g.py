"""One-off wiring of the saved web pages layer (tab + state page block). Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if new in text:
            continue
        assert text.count(old) == 1, (name, old[:70], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


edit('server.py', [
    ("               'agency-documents':'agency_science_documents','agency_science_documents':'agency_science_documents'}",
     "               'agency-documents':'agency_science_documents','agency_science_documents':'agency_science_documents',\n"
     "               'saved-pages':'saved_pages','saved_pages':'saved_pages'}"),
    ("'court_documents':judge_layer('court_documents','for_state',p.get('state'))})",
     "'court_documents':judge_layer('court_documents','for_state',p.get('state')),'saved_pages':judge_layer('saved_pages','for_state',p.get('state'))})"),
])
edit('areas.js', [
    ("    { view: 'coverage', title: 'Coverage & gaps',",
     "    { view: 'saved-pages', title: 'Saved web pages', nav: 'Saved pages', supplement: 'saved_web_pages_20260919', description: 'Searchable text of pages captured in the August 2026 crawls: Justice Department and federal court pages, Illinois circuit courts, Pennsylvania and Philadelphia courts, D.C. Courts, the Montana Code and the Nevada Legislature.' },\n"
     "    { view: 'coverage', title: 'Coverage & gaps',"),
    ("'sd-statutes', 'agency-documents'])", "'sd-statutes', 'agency-documents', 'saved-pages'])"),
    ("const cd = relatedBlock('Court documents saved for this state', b.court_documents, 'court-documents', 6); if (cd) main.append(cd);",
     "const cd = relatedBlock('Court documents saved for this state', b.court_documents, 'court-documents', 6); if (cd) main.append(cd); const pg = relatedBlock('Saved web pages for this state (courts and legislature)', b.saved_pages, 'saved-pages', 6); if (pg) main.append(pg);"),
])
edit('app.js', [
    ("['urls','URL directory','url_directory_20260919'],", "['saved-pages','Saved pages','saved_web_pages_20260919'],['urls','URL directory','url_directory_20260919'],"),
])
print('wired')
