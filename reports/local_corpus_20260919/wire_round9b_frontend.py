"""Round 9b: front end for the open-source enrichment layers. Idempotent; asserts every anchor."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if (new and new in text) or (not new and old not in text):
            continue
        assert text.count(old) == 1, (name, old[:90], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


edit('app.js', [
    # navigation: three new collections, each inside an existing tab
    ("    {view:'laws',label:'State law'},",
     "    {view:'laws',label:'State law',segments:[\n"
     "      {view:'laws',label:'Codes, rules & constitutions',hint:'Full text by state, heading by heading'},\n"
     "      {view:'limitation-periods',label:'Limitation periods',hint:'Filing deadlines by claim type, checked against the saved statutes',supplement:'limitation_periods_20260920'}]},"),
    ("      {view:'public-laws',label:'Public Laws & U.S. Code',hint:'Acts of Congress and the Code sections they change',supplement:'public_law_uscode_20260919'}]},",
     "      {view:'public-laws',label:'Public Laws & U.S. Code',hint:'Acts of Congress and the Code sections they change',supplement:'public_law_uscode_20260919'},\n"
     "      {view:'citation-index',label:'Cited authorities',hint:'Cases, statutes and regulations cited inside saved documents',supplement:'citation_index_20260920'}]},"),
    ("      {view:'statistics',label:'Court statistics',hint:'Caseload tables and per-judge reports',supplement:'federal_court_statistics_20260919'}]},",
     "      {view:'statistics',label:'Court statistics',hint:'Caseload tables and per-judge reports',supplement:'federal_court_statistics_20260919'},\n"
     "      {view:'citation-guide',label:'Reporters & citation forms',hint:'What a reporter or code abbreviation means',supplement:'citation_reference_flp_20260920'}]},"),
    # law reader: saved documents that cite this provision
    ("body.append(item.dataset==='county_litigation'?countyResourceProse(item.text,item.title):lawRecord?window.LawReader.reading(item.text):prose(item.text,'record-text reading-content'));",
     "body.append(item.dataset==='county_litigation'?countyResourceProse(item.text,item.title):lawRecord?window.LawReader.reading(item.text):prose(item.text,'record-text reading-content'));if(lawRecord&&window.LawReader.citedBy){const citing=el('div','lawcited-host');body.append(citing);window.LawReader.citedBy(citing,item.id);}"),
])

areas = open(D + 'areas.js', encoding='utf-8').read()
if "view: 'citation-guide'" not in areas:
    import re
    anchor = "    { view: 'coverage', title: 'Coverage & gaps',"
    assert areas.count(anchor) == 1
    areas = areas.replace(anchor,
        "    { view: 'citation-guide', title: 'Reporters & citation forms', nav: 'Citation guide', supplement: 'citation_reference_flp_20260920', description: 'Case reporters with their series and years, statute and regulation citation forms by jurisdiction, law journals and standard abbreviations.' },\n"
        "    { view: 'limitation-periods', title: 'Limitation periods', nav: 'Limitation periods', supplement: 'limitation_periods_20260920', description: 'Filing deadlines by state and claim type from a published summary table, with personal injury, wrongful death and malpractice periods checked against the statute text saved here.' },\n"
        "    { view: 'citation-index', title: 'Cited authorities', nav: 'Cited authorities', supplement: 'citation_index_20260920', description: 'Cases, statutes, regulations and journal articles cited inside the saved documents, with the documents that cite them.' },\n" + anchor)
    found = re.search(r"for \(const view of \[([^\]]*)\]\) if \(registry\[view\] && !registry\[view\]\.page\) registry\[view\]\.page = genericPage\(view\);", areas)
    assert found
    areas = areas.replace(found.group(0), found.group(0).replace(found.group(1), found.group(1) + ", 'citation-guide', 'limitation-periods', 'citation-index'"))
# state page: limitation periods table
old = "    try { const b = await api(`/api/blocks?state=${encodeURIComponent(abbr)}`, signal); if (!signal.aborted) { const sp = relatedBlock("
new = ("    try { const b = await api(`/api/blocks?state=${encodeURIComponent(abbr)}`, signal); if (!signal.aborted) { const lp = limitationBlock(b.limitation_periods); if (lp) main.append(lp); const sp = relatedBlock(")
if new not in areas:
    assert areas.count(old) == 1
    areas = areas.replace(old, new)
helper_anchor = "  /* ---- Judge profile helpers (used by app.js) ---- */"
helper = ("  /* ---- Limitation periods on a state page ---- */\n"
          "  function limitationBlock(block) {\n"
          "    if (!block || !block.available || !(block.rows || []).length) return null;\n"
          "    const box = el('section', 'panel limitation-block');\n"
          "    box.append(append(el('div', 'section-heading'), el('h2', '', 'Limitation periods'), el('small', '', 'Published summary table; three claim types checked against the saved statutes')));\n"
          "    const wrap = el('div', 'table-scroll'), t = el('table', 'dense-table'), hr = el('tr'); for (const h of ['Claim', 'Period', 'Section looked up', 'Saved statute check']) hr.append(el('th', '', h)); t.append(append(el('thead'), hr));\n"
          "    const tb = el('tbody');\n"
          "    for (const r of block.rows) { const tr = el('tr'), c1 = el('td'); const open = action(r.claim, () => openGenericDetail('limitation-periods', r.id), 'document-title'); c1.append(open); if (r.note) c1.append(el('div', 'record-subline', r.note));\n"
          "      const c3 = el('td'); if (r.record_id) { const a = el('a', '', r.section); a.href = `#record/${encodeURIComponent(r.record_id)}`; c3.append(a); } else c3.textContent = r.section || '';\n"
          "      const c4 = el('td', r.outcome === 'different_wording_found' ? 'limitation-differs' : '', r.check || ''); tr.append(c1, el('td', '', r.period), c3, c4); tb.append(tr); }\n"
          "    t.append(tb); wrap.append(t); box.append(wrap, routeLink('All limitation periods for this state →', 'limitation-periods', { state: (block.link || '').split('state=')[1] || '' }, 'button-link'), dataNote(`${block.qualification} Source table: ${block.attribution}`));\n"
          "    return box;\n"
          "  }\n\n")
if 'function limitationBlock(' not in areas:
    assert areas.count(helper_anchor) == 1
    areas = areas.replace(helper_anchor, helper + helper_anchor)
open(D + 'areas.js', 'w', encoding='utf-8', newline='').write(areas)

law = open(D + 'lawreader.js', encoding='utf-8').read()
if 'async function citedBy(' not in law:
    anchor = "  /* ---------- browse a jurisdiction heading by heading ---------- */"
    assert law.count(anchor) == 1
    law = law.replace(anchor,
        "  /* ---------- saved documents that cite this provision ---------- */\n"
        "  async function citedBy(host, recordId) {\n"
        "    try {\n"
        "      const data = await get('/api/citations/record?' + query({ id: recordId }));\n"
        "      if (!data.available || !data.total) return;\n"
        "      const box = h('section', 'lawcited');\n"
        "      box.append(h('h3', 'lawcited-h', `Cited in ${fmt(data.total)} saved document${data.total === 1 ? '' : 's'}`));\n"
        "      const list = h('ul', 'lawcited-list');\n"
        "      for (const row of data.results) { const li = h('li'); const first = (row.links || [])[0]; const a = h('a', 'lawcited-title', row.title); a.href = first ? first.url : '#citation-index'; li.append(a, h('p', 'lawcited-sub', row.subtitle)); list.append(li); }\n"
        "      const more = h('a', 'lawcited-more', 'Open in Cited authorities \\u2192'); more.href = data.link || '#citation-index';\n"
        "      box.append(list, more); host.replaceChildren(box);\n"
        "    } catch (error) { /* optional block */ }\n"
        "  }\n\n" + anchor)
    law = law.replace("window.LawReader = { format, reading, context, browser, title };", "window.LawReader = { format, reading, context, browser, title, citedBy };")
    # statute audit line in the browser header
    old = "    const tabs = h('div', 'lawb-tabs'); tabs.setAttribute('role', 'tablist');"
    new = ("    if (data.statute_audit) { const a = data.statute_audit, line = h('p', 'lawb-audit' + (a.verdict === 'complete' ? '' : ' is-warn'));\n"
           "      line.append(h('strong', '', 'Statutes: ' + a.verdict_label), document.createTextNode([a.containers, a.notes].filter(Boolean).map(s => ' \\u00b7 ' + s).join('')));\n"
           "      if (/^https?:/.test(a.official_source || '')) { const src = h('a', '', ' Official source \\u2197'); src.href = a.official_source.split(' ')[0]; src.target = '_blank'; src.rel = 'noopener noreferrer'; line.append(src); }\n"
           "      head.append(line); }\n"
           "    const tabs = h('div', 'lawb-tabs'); tabs.setAttribute('role', 'tablist');")
    assert law.count(old) == 1
    law = law.replace(old, new)
    open(D + 'lawreader.js', 'w', encoding='utf-8', newline='').write(law)

css = open(D + 'styles.css', encoding='utf-8').read()
if '/* round 9 */' not in css:
    css += ("\n/* round 9 */\n"
            ".lawb-audit{font-size:12px;color:var(--muted);margin:0 0 10px;line-height:1.5}.lawb-audit strong{color:var(--ink);font-weight:600}.lawb-audit.is-warn{color:#7a4a00}.lawb-audit.is-warn strong{color:#7a4a00}.lawb-audit a{color:var(--teal-dark);white-space:nowrap}\n"
            ".lawcited{border-top:1px solid var(--line);margin-top:18px;padding-top:12px}.lawcited-h{font-size:12px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin:0 0 6px;font-weight:600}\n"
            ".lawcited-list{list-style:none;margin:0;padding:0}.lawcited-list li{padding:7px 0;border-bottom:1px solid var(--line)}.lawcited-title{font-size:13px;font-weight:600;color:var(--teal-dark);text-decoration:none}.lawcited-title:hover{text-decoration:underline}\n"
            ".lawcited-sub{font-size:12px;color:var(--muted);margin:2px 0 0;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.lawcited-more{display:inline-block;margin-top:8px;font-size:12.5px;font-weight:600;color:var(--teal-dark);text-decoration:none}\n"
            ".limitation-block .dense-table td{vertical-align:top}.limitation-differs{color:#8a3b00;font-weight:600}\n"
            ".court-mark{max-width:120px;max-height:120px;object-fit:contain}\n")
    open(D + 'styles.css', 'w', encoding='utf-8', newline='').write(css)
print('round 9 front end applied')
