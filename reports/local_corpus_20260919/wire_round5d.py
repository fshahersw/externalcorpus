"""One-off wiring of the four MDL docket layers (cases, appearances, documents, activity) + SD statutes. Idempotent.
Every layer is imported lazily per request, so an adapter that is not written yet simply contributes nothing."""
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
    ("               'federal-register':'federal_register_history','federal_register_history':'federal_register_history'}",
     "               'federal-register':'federal_register_history','federal_register_history':'federal_register_history',\n"
     "               'mdl-cases':'mdl_case_inventory','mdl_case_inventory':'mdl_case_inventory','mdl-appearances':'mdl_appearances','mdl_appearances':'mdl_appearances',\n"
     "               'mdl-documents':'mdl_docket_documents','mdl_docket_documents':'mdl_docket_documents','mdl-activity':'mdl_docket_activity','mdl_docket_activity':'mdl_docket_activity',\n"
     "               'mdl-crosswalk':'mdl_crosswalk','mdl_crosswalk':'mdl_crosswalk','sd-statutes':'sd_statutes','sd_statutes':'sd_statutes'}"),
    ("                        try:item['state_proceedings']=judge_layer('state_proceedings','for_mdl',int(str(item.get('mdl_number') or p.get('number','')).strip()))\n"
     "                        except (TypeError,ValueError):pass\n",
     "                        try:\n"
     "                            number=int(str(item.get('mdl_number') or p.get('number','')).strip())\n"
     "                            item['state_proceedings']=judge_layer('state_proceedings','for_mdl',number)\n"
     "                            for key,module in (('appearances','mdl_appearances'),('docket_documents','mdl_docket_documents'),('docket_activity','mdl_docket_activity'),('cases','mdl_case_inventory')):\n"
     "                                item[key]=judge_layer(module,'for_mdl',number)\n"
     "                        except (TypeError,ValueError):pass\n"),
])

LAYER = r"""  /* MDL docket layers share one tolerant renderer: a counts line from any by_* maps, up to ten rows, a link and the layer's own qualification. */
  function mdlLayerBlock(title, block, view) {
    if (!block || !(block.total || (block.results || block.sample || block.firms || block.latest || []).length)) return null;
    const box = el('section', 'panel'); box.append(append(el('div', 'section-heading'), el('h2', '', title), el('small', '', block.total !== undefined ? `${count(block.total)} in the saved docket sample` : '')));
    const bits = []; for (const [k, v] of Object.entries(block)) if (/^by_/.test(k) && v && typeof v === 'object' && !Array.isArray(v)) bits.push(`${human(k.slice(3))}: ` + Object.entries(v).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([name, n]) => `${human(String(name))} ${count(n)}`).join(', '));
    if (block.date_first || block.first_date) bits.push(`dates ${block.date_first || block.first_date} to ${block.date_last || block.last_date || '?'}`); if (block.capped) bits.push('entries capped by the source release');
    if (bits.length) box.append(el('p', 'record-subline', bits.join(' · ')));
    const rows = block.results || block.sample || block.firms || block.latest || []; const list = el('ul', 'related-list');
    for (const r of rows.slice(0, 10)) { const li = el('li'); const label = r.title || r.name || r.firm_name || r.description || r.id; if (r.id !== undefined) li.append(action(String(label).slice(0, 140), () => openGenericDetail(view, String(r.id)), 'document-title')); else li.append(el('span', 'document-title', String(label).slice(0, 140))); const sub = r.subtitle || [r.date_filed || r.date || r.entry_date, r.doc_type || r.entry_type || r.role || r.status, r.court_id, r.appearances !== undefined ? `${count(r.appearances)} appearances` : ''].filter(Boolean).join(' · '); if (sub) li.append(el('div', 'record-subline', sub)); list.append(li); }
    if (rows.length) box.append(list); if (block.link) { const a = el('a', 'button-link', 'See all →'); a.href = block.link; box.append(a); }
    if (block.qualification) { const q = el('p', 'coverage-footnote', String(block.qualification).slice(0, 420) + (String(block.qualification).length > 420 ? ' …' : '')); q.title = block.qualification; box.append(q); }
    return box;
  }

  /* ---- Related-material blocks from optional data layers"""

edit('areas.js', [
    ("    { view: 'coverage', title: 'Coverage & gaps',",
     "    { view: 'mdl-cases', title: 'MDL member cases (saved docket sample)', nav: 'MDL cases', supplement: 'mdl_case_inventory_20260919', description: 'Dockets in the saved firm-focused docket sample, linked to an MDL by native docket ids. A sample of what this archive holds, not an MDL\\'s member-case list.' },\n"
     "    { view: 'mdl-appearances', title: 'MDL counsel appearances', nav: 'Appearances', supplement: 'mdl_counsel_appearances_20260919', description: 'Counsel appearances, firms and party counts recorded on MDL-linked dockets in the saved docket sample.' },\n"
     "    { view: 'mdl-documents', title: 'MDL docket documents', nav: 'MDL documents', supplement: 'mdl_docket_documents_20260919', description: 'Master-docket documents for the MDLs the saved catalog reaches, typed by order kind, linking out to CourtListener.' },\n"
     "    { view: 'mdl-activity', title: 'MDL docket activity', nav: 'MDL activity', supplement: 'mdl_docket_activity_20260919', description: 'Docket entries on MDL-linked matters in the saved docket release, typed by entry kind.' },\n"
     "    { view: 'sd-statutes', title: 'South Dakota Codified Laws', nav: 'SD statutes', supplement: 'sd_statutes_20260919', description: 'South Dakota statutes as retrieved into the local registry cache; not verified current.' },\n"
     "    { view: 'coverage', title: 'Coverage & gaps',"),
    ("'state-proceedings', 'court-documents', 'judge-disclosures', 'federal-register'])",
     "'state-proceedings', 'court-documents', 'judge-disclosures', 'federal-register', 'mdl-cases', 'mdl-appearances', 'mdl-documents', 'mdl-activity', 'sd-statutes'])"),
    ("  /* ---- Related-material blocks from optional data layers", LAYER),
    ("    { const sp = relatedBlock('Related state coordinated proceedings (named by the state registry)', m.state_proceedings, 'state-proceedings'); if (sp) main.append(sp); }\n",
     "    for (const [title, block, view] of [['Counsel, firms and parties on the saved dockets', m.appearances, 'mdl-appearances'], ['Key orders and settlement-related filings (master docket documents)', m.docket_documents, 'mdl-documents'], ['Docket activity in the saved release', m.docket_activity, 'mdl-activity'], ['Member cases in the saved docket sample', m.cases, 'mdl-cases']]) { const box = mdlLayerBlock(title, block, view); if (box) main.append(box); }\n"
     "    { const sp = relatedBlock('Related state coordinated proceedings (named by the state registry)', m.state_proceedings, 'state-proceedings'); if (sp) main.append(sp); }\n"),
])
print('wired')
