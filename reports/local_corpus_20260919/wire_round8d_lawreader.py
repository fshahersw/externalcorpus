"""Round 8d: law browser on the State law page, reading layout + previous/next in the record reader, category pills removed. Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if new in text:
            continue
        assert text.count(old) == 1, (name, old[:90], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


edit('app.js', [
    # 1. heading-by-heading browser above the category cards of one jurisdiction
    ("  const section=el('section','law-categories');append(section,el('h2','',state?`${state} law library`:'Browse by category'),",
     "  if(state&&window.LawReader){const host=el('div','lawb-host');target.append(host);window.LawReader.browser(host,state,{open:id=>openRecord({id},document.activeElement),start:{kind:route.params.get('toc'),node:route.params.get('node')}});}\n"
     "  const section=el('section','law-categories');append(section,el('h2','',state?`${state} documents by category`:'Browse by category'),"),
    # 2. the category pills duplicated the Category filter
    ("  if(route.view==='laws'&&!lawHubOpen()){const categories=el('div','category-links');",
     "  if(false&&route.view==='laws'&&!lawHubOpen()){const categories=el('div','category-links');"),
    # 3. reader: position in the code, previous / next, reading layout
    ("  const title=el('h2','',displayTitle(item));title.id='record-title';append(body,el('p','reader-context',[item.state,item.county,kindLabel(item.kind)].filter(Boolean).join(' · ')),title);",
     "  const lawRecord=item.dataset==='open_us_law'&&window.LawReader;\n"
     "  if(lawRecord){const where=el('div','lawctx-host');body.append(where);window.LawReader.context(where,item.id,{open:id=>openRecord({id})});}\n"
     "  const lawCitation=lawRecord&&(item.metadata?.citation||'');\n"
     "  const title=el('h2','',lawCitation&&lawCitation!==displayTitle(item)?`${lawCitation} — ${displayTitle(item)}`:displayTitle(item));title.id='record-title';append(body,lawRecord?null:el('p','reader-context',[item.state,item.county,kindLabel(item.kind)].filter(Boolean).join(' · ')),title);if(lawRecord)body.classList.add('law-record');else body.classList.remove('law-record');"),
    ("  if(item.dataset==='open_us_law')body.append(el('p','reader-caution',`Publisher-supplied law text; verify its edition and current status.${!item.source_url?' This record has no original-source URL in the publisher data; the saved data file is available above.':''}`));",
     "  if(item.dataset==='open_us_law')body.append(el('p','reader-note',`Publisher snapshot text. Check the edition and current status at the official source.${!item.source_url?' No official address is recorded for this provision.':''}`));"),
    ("body.append(item.dataset==='county_litigation'?countyResourceProse(item.text,item.title):prose(item.text,'record-text reading-content'));",
     "body.append(item.dataset==='county_litigation'?countyResourceProse(item.text,item.title):lawRecord?window.LawReader.reading(item.text):prose(item.text,'record-text reading-content'));"),
])

css = open(D + 'styles.css', encoding='utf-8').read()
if '/* law reader */' not in css:
    css += """
/* law reader */
.lawb{background:var(--surface,#fff);border:1px solid var(--line);border-radius:10px;padding:14px 16px 8px;margin:0 0 18px}
.lawb-head h2{margin:0;font-size:16px}.lawb-sub{margin:2px 0 10px;color:var(--muted);font-size:12.5px}
.lawb-tabs{display:flex;gap:2px;flex-wrap:wrap;border-bottom:1px solid var(--line);margin:0 -16px;padding:0 16px}
.lawb-tab{appearance:none;background:none;border:0;border-bottom:2px solid transparent;padding:7px 10px 8px;font:inherit;font-size:12.5px;font-weight:600;color:var(--muted);cursor:pointer;display:flex;gap:6px;align-items:baseline;margin-bottom:-1px}
.lawb-tab small{font-weight:500;font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums}.lawb-tab:hover{color:var(--ink)}
.lawb-tab.is-on{color:var(--teal-dark);border-bottom-color:var(--teal-dark)}
.lawb-path,.lawctx-path{list-style:none;display:flex;flex-wrap:wrap;gap:0;margin:10px 0 6px;padding:0;font-size:12px;color:var(--muted)}
.lawb-path li+li::before,.lawctx-path li+li::before{content:'›';margin:0 6px;color:var(--muted)}
.lawb-path button{appearance:none;background:none;border:0;padding:0;font:inherit;color:var(--teal-dark);cursor:pointer}.lawb-path button:hover,.lawctx-path a:hover{text-decoration:underline}
.lawb-path .is-here{color:var(--ink);font-weight:600}
.lawb-list,.lawb-sections{list-style:none;margin:0;padding:0}
.lawb-list{columns:2;column-gap:22px}@media(max-width:1100px){.lawb-list{columns:1}}
.lawb-list li{break-inside:avoid}
.lawb-row,.lawb-section{appearance:none;width:100%;background:none;border:0;border-bottom:1px solid var(--line);padding:7px 2px;font:inherit;font-size:13px;text-align:left;cursor:pointer;display:grid;gap:10px;align-items:baseline;color:var(--ink)}
.lawb-row{grid-template-columns:1fr auto 10px}.lawb-row:hover,.lawb-section:hover{background:rgba(15,76,68,.045)}
.lawb-count{font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums}.lawb-chev{color:var(--muted)}
.lawb-section{grid-template-columns:minmax(150px,210px) 1fr auto}.lawb-cite{font-weight:600;font-variant-numeric:tabular-nums;color:var(--teal-dark)}
.lawb-title{color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.lawb-status{font-size:11px;color:#8a5a00}
.lawb-sub-h{font-size:12px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin:16px 0 2px;font-weight:600}
.lawb-more{appearance:none;background:none;border:0;color:var(--teal-dark);font:inherit;font-size:12.5px;font-weight:600;padding:9px 2px;cursor:pointer}
.lawb-body[aria-busy=true]{opacity:.55}.lawb-empty{color:var(--muted);font-size:13px}
.lawb-body{max-height:520px;overflow:auto;margin:0 -6px;padding:0 6px 6px}
.lawctx{display:flex;flex-direction:column;gap:6px;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:14px}
.lawctx-path{margin:0}.lawctx-path a{color:var(--teal-dark);text-decoration:none}
.lawctx-pager{display:flex;align-items:center;justify-content:space-between;gap:10px}
.lawctx-step{appearance:none;background:none;border:1px solid var(--line);border-radius:7px;padding:4px 9px;font:inherit;font-size:12px;color:var(--ink);cursor:pointer;display:flex;gap:6px;align-items:center;max-width:42%}
.lawctx-step:disabled{opacity:.4;cursor:default}.lawctx-step:not(:disabled):hover{border-color:var(--teal-dark);color:var(--teal-dark)}
.lawctx-cite{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.lawctx-place{font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums}
.law-record h2{font-family:Georgia,'Times New Roman',serif;font-size:21px;line-height:1.3;margin:2px 0 8px}
.reader-note{font-size:12px;color:var(--muted);margin:6px 0 12px}
.lawtext-wrap{margin-top:6px}.lawtext-bar{display:flex;justify-content:space-between;gap:12px;align-items:center;font-size:11.5px;color:var(--muted);margin-bottom:8px}
.lawtext-toggle{appearance:none;background:none;border:0;color:var(--teal-dark);font:inherit;font-size:11.5px;font-weight:600;cursor:pointer;white-space:nowrap}
.lawtext{font-family:Georgia,'Times New Roman',serif;font-size:15.5px;line-height:1.7;color:var(--ink);max-width:76ch}
.lawtext-p{margin:0 0 .7em}.lawtext-p[data-level='1']{margin-left:1.6em}.lawtext-p[data-level='2']{margin-left:3.2em}.lawtext-p[data-level='3']{margin-left:4.8em}.lawtext-p[data-level='4']{margin-left:6.4em}.lawtext-p[data-level='5']{margin-left:8em}
.lawtext-enum{font-weight:700;margin-right:.35em;font-variant-numeric:tabular-nums}
.lawtext-raw{white-space:pre-wrap;font-family:ui-monospace,Consolas,monospace;font-size:12.5px;line-height:1.55;max-width:90ch;background:none;border:0;padding:0}
"""
    open(D + 'styles.css', 'w', encoding='utf-8', newline='').write(css)
print('law reader hooked')
