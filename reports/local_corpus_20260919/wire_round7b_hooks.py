"""Tolerant hooks for the two new front-end modules (they activate only when the module is loaded). Idempotent."""
import re

D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'

areas = open(D + 'areas.js', encoding='utf-8').read()
if 'window.StatsViz' not in areas:
    found = re.search(r"  for \(const view of \[[^\]]*\]\) if \(registry\[view\] && !registry\[view\]\.page\) registry\[view\]\.page = genericPage\(view\);\n", areas)
    assert found, 'generic registration not found'
    hook = ("  /* The statistics dashboard module (statsviz.js) replaces the generic table page when it is loaded. */\n"
            "  if (registry.statistics) { const genericStatistics = registry.statistics.page; registry.statistics.page = function (signal, supplement) { return (window.StatsViz && typeof window.StatsViz.page === 'function') ? window.StatsViz.page(signal, route, supplement) : genericStatistics(signal, supplement); }; }\n")
    areas = areas.replace(found.group(0), found.group(0) + hook)
    open(D + 'areas.js', 'w', encoding='utf-8', newline='').write(areas)

app = open(D + 'app.js', encoding='utf-8').read()
changed = False
# Judge profile: hand the page body to JudgeUI.profile when the module is loaded.
old = "    document.title=`${profile.name} · Legal Archive`;document.querySelector('#breadcrumb-current').textContent=profile.name;\n    const previous=route.params.get('from'),back=el('a','back-link','← Back to judges');back.href=previous&&/^#judges(?:\\?|$)/.test(previous)?previous:'#judges';main.append(back);\n"
new = old + "    if(window.JudgeUI&&typeof window.JudgeUI.profile==='function'){const host=el('div','ju-host');main.append(host);window.JudgeUI.profile(host,profile,{back:()=>{location.hash=back.getAttribute('href');}});main.removeAttribute('aria-busy');announce(`${profile.name} opened.`);return;}\n"
if 'window.JudgeUI.profile' not in app:
    assert app.count(old) == 1, 'judge profile anchor not found'
    app = app.replace(old, new)
    changed = True
if changed:
    open(D + 'app.js', 'w', encoding='utf-8', newline='').write(app)
print('hooks installed')
