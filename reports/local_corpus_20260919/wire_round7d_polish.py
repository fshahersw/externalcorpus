"""Rail polish: date presets as small chips, nested filter grids stacked, scope/view switches replaced by collections. Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if new in text:
            continue
        assert text.count(old) == 1, (name, old[:80], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


edit('app.js', [
    # Historical biographies and the federal/DOJ document scope become collections in the rail instead of pills above the page.
    ("{view:'judges',label:'Judge profiles',hint:'Current judges with appointments, MDLs and evidence'}",
     "{view:'judges',label:'Judge profiles',hint:'Current judges with appointments, MDLs and evidence'},{view:'people',label:'Historical biographies',hint:'Past and present judges from the CourtListener people database'}"),
    ("    {view:'documents',label:'All documents'}]},",
     "    {view:'documents',label:'All documents',segments:[{view:'documents',label:'Whole library',hint:'Every saved document, by jurisdiction and category'},{view:'federal',label:'Federal court & DOJ sources',hint:'Federal court and Justice Department references'}]}]},"),
    ("({judge:'judges',people:'judges',person:'judges',county:'counties',collection:'mdls',collections:'mdls',federal:'documents',source:'sources',record:'documents'}[route.view]||route.view)",
     "({judge:'judges',person:'people',county:'counties',collection:'mdls',collections:'mdls',source:'sources',record:'documents'}[route.view]||route.view)"),
])

css = open(D + 'styles.css', encoding='utf-8').read()
if '/* rail polish */' not in css:
    css += """
/* rail polish */
#main:has(> .workbench .rail-collections) > .scope-switch,#main:has(> .workbench .rail-collections) > .view-switch{display:none}
.rail form.filters .button,.rail form.filters button{width:auto}
.rail form.filters>.button,.rail form.filters>button{width:100%;justify-content:center;min-height:34px}
.rail form.filters .date-presets{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin:0}.rail form.filters .date-presets>span{flex:0 0 100%;font-size:11px;color:var(--muted);letter-spacing:.2px}
.rail form.filters .date-presets .chip,.rail form.filters .date-presets button{min-height:26px;padding:2px 9px;font-size:11.5px;border-radius:999px}
.rail form.filters details{border-top:1px solid var(--line);padding-top:9px}.rail form.filters details>summary{cursor:pointer;font-size:12px;font-weight:600;color:var(--teal-dark);list-style-position:inside}
.rail form.filters details>div,.rail form.filters .source-more-grid{display:flex;flex-direction:column;gap:11px;margin-top:10px;grid-template-columns:none}
.rail form.filters details label{width:100%}
.workbench-body>.active-filters{margin:0 0 12px}.workbench-body .results-heading{padding-top:4px}
.workbench-body .judge-grid{grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
"""
    open(D + 'styles.css', 'w', encoding='utf-8', newline='').write(css)
print('polish applied')
