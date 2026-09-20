"""One-off wiring of the Federal Register document index (idempotent; anchors asserted)."""
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
    ("'state_proceedings':'state_proceedings','court_documents':'court_documents','judge_disclosures':'judge_disclosures'}",
     "'state_proceedings':'state_proceedings','court_documents':'court_documents','judge_disclosures':'judge_disclosures',\n"
     "               'federal-register':'federal_register_history','federal_register_history':'federal_register_history'}"),
    ("                    item=federal_regulations.section(p.get('citation',''))\n",
     "                    item=federal_regulations.section(p.get('citation',''))\n"
     "                    if item and item.get('title') and item.get('part'):\n"
     "                        try:\n"
     "                            import importlib\n"
     "                            item['fr_history']=importlib.import_module('federal_register_history').for_cfr(str(item['title']),str(item['part']))\n"
     "                        except Exception:item['fr_history']=None\n"),
])

edit('areas.js', [
    ("    { view: 'coverage', title: 'Coverage & gaps',",
     "    { view: 'federal-register', title: 'Federal Register 1994–2026', nav: 'Federal Register', supplement: 'federal_register_history_20260919', description: 'Every Federal Register document listed by the federalregister.gov API from 1994 to mid-2026: rules, proposed rules, notices and presidential documents with the CFR parts, agencies, dockets and RINs each one lists.' },\n"
     "    { view: 'coverage', title: 'Coverage & gaps',"),
    ("'state-proceedings', 'court-documents', 'judge-disclosures'])", "'state-proceedings', 'court-documents', 'judge-disclosures', 'federal-register'])"),
    ("      const rowEl = el('div', 'button-row'); if (row.ecfr_url) rowEl.append(link('Current eCFR ↗', row.ecfr_url, true)); body.append(rowEl);",
     "      if (row.fr_history && row.fr_history.total) { const h = row.fr_history; body.append(el('h3', '', `Federal Register documents citing ${row.title} CFR part ${row.part}, ${String(h.first_date || '').slice(0, 4)}–${String(h.last_date || '').slice(0, 4)} (${count(h.total)})`)); body.append(el('p', 'record-subline', (h.by_type || []).map(t => `${t.value} ${count(t.count)}`).join(' · '))); const list = el('ul', 'career-timeline'); for (const d of (h.results || []).slice(0, 8)) list.append(el('li', '', `${d.subtitle} — ${d.title}`)); body.append(list); const all = el('a', 'button-link', 'Open the full rule history for this part →'); all.href = h.link; body.append(all); body.append(el('p', 'coverage-footnote', 'A document that cites a part may propose, amend, correct or only discuss it. Index collected 2026-08-20.')); }\n"
     "      const rowEl = el('div', 'button-row'); if (row.ecfr_url) rowEl.append(link('Current eCFR ↗', row.ecfr_url, true)); body.append(rowEl);"),
])

edit('app.js', [
    ("['regulations','Regulations','federal_regulations_20260919'],", "['regulations','Regulations','federal_regulations_20260919'],['federal-register','Federal Register','federal_register_history_20260919'],"),
])
print('wired')
