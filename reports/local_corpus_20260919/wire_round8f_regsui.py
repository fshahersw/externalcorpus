"""Round 8f: install the Regulations / Agencies module, warm the agency overview at start-up, keep the rail stacked on narrow screens. Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if new in text:
            continue
        assert text.count(old) == 1, (name, old[:90], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


html = open(D + 'index.html', encoding='utf-8').read()
if '/regsui.js' not in html:
    anchor = '<script src="/judgeui.js" defer></script>'
    assert html.count(anchor) == 1
    html = html.replace(anchor, anchor + '\n  <script src="/regsui.js" defer></script>')
    open(D + 'index.html', 'w', encoding='utf-8', newline='').write(html)

areas = open(D + 'areas.js', encoding='utf-8').read()
if 'window.RegsUI' not in areas:
    anchor = "  if (registry.statistics) { const genericStatistics = registry.statistics.page;"
    assert areas.count(anchor) == 1
    hook = ("  if (registry.regulations) { const genericRegulations = registry.regulations.page; registry.regulations.page = function (signal, supplement) { return (window.RegsUI && typeof window.RegsUI.regulations === 'function') ? window.RegsUI.regulations(signal, supplement) : genericRegulations(signal, supplement); }; }\n"
            "  if (registry.agencies) { const genericAgencies = registry.agencies.page; registry.agencies.page = function (signal, supplement) { return (window.RegsUI && typeof window.RegsUI.agencies === 'function') ? window.RegsUI.agencies(signal, supplement) : genericAgencies(signal, supplement); }; }\n")
    areas = areas.replace(anchor, hook + anchor)
    open(D + 'areas.js', 'w', encoding='utf-8', newline='').write(areas)

edit('server.py', [
    ("('federal_register_history','listing',({'limit':1},))):", "('federal_register_history','listing',({'limit':1},)),('agency_hub','listing',()),('law_outline','collections',('CA',))):"),
])
# The compact layer repeated the two-column rule after the narrow-screen rule and so undid it on phones.
edit('styles.css', [
    (".workbench{grid-template-columns:232px minmax(0,1fr);gap:18px}.rail{gap:12px;top:52px}",
     "@media(min-width:1001px){.workbench{grid-template-columns:232px minmax(0,1fr);gap:18px}}.rail{gap:12px;top:52px}"),
])
print('regulations and agencies module installed')
