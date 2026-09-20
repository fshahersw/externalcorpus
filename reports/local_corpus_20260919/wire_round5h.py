"""One-off wiring of the 2026 Indiana Code layer (route + Indiana state page button). Idempotent."""
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
    ("               'saved-pages':'saved_pages','saved_pages':'saved_pages'}",
     "               'saved-pages':'saved_pages','saved_pages':'saved_pages','indiana-code':'indiana_code','indiana_code':'indiana_code'}"),
])
edit('areas.js', [
    ("    { view: 'coverage', title: 'Coverage & gaps',",
     "    { view: 'indiana-code', title: 'Indiana Code (2026 edition)', nav: 'Indiana Code', supplement: 'indiana_code_2026_20260919', description: 'Every section of the 2026 Indiana Code from the General Assembly HTML edition saved locally, searchable by text or citation. Not verified against the current code.' },\n"
     "    { view: 'coverage', title: 'Coverage & gaps',"),
    ("'sd-statutes', 'agency-documents', 'saved-pages'])", "'sd-statutes', 'agency-documents', 'saved-pages', 'indiana-code'])"),
    ("    if (abbr === 'SD') quick.append(routeLink('South Dakota Codified Laws (saved text)', 'sd-statutes', {}, 'button'));\n",
     "    if (abbr === 'SD') quick.append(routeLink('South Dakota Codified Laws (saved text)', 'sd-statutes', {}, 'button'));\n"
     "    if (abbr === 'IN') quick.append(routeLink('Indiana Code, 2026 edition (every section)', 'indiana-code', {}, 'button'));\n"),
])
print('wired')
