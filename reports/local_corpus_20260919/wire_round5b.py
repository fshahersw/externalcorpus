"""One-off wiring of three validated layers (court documents, state mass torts, judge disclosures). Idempotent: each
replacement asserts its anchor exists exactly once and is skipped when the new text is already present."""
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
    ("'uscourts':'uscourts_pages','uscourts_pages':'uscourts_pages'}",
     "'uscourts':'uscourts_pages','uscourts_pages':'uscourts_pages',\n               'state-proceedings':'state_proceedings','court-documents':'court_documents','judge-disclosures':'judge_disclosures'}"),
    ("                    item=mdl_registry.detail(p.get('number',''))\n",
     "                    item=mdl_registry.detail(p.get('number',''))\n"
     "                    if item:\n"
     "                        try:item['state_proceedings']=judge_layer('state_proceedings','for_mdl',int(str(item.get('mdl_number') or p.get('number','')).strip()))\n"
     "                        except (TypeError,ValueError):pass\n"),
    ("                    profile['evidence']=judge_layer('judge_evidence','evidence_for',profile.get('entity_id') or p.get('id',''))\n",
     "                    profile['evidence']=judge_layer('judge_evidence','evidence_for',profile.get('entity_id') or p.get('id',''))\n"
     "                    profile['disclosures']=judge_layer('judge_disclosures','for_judge',profile.get('entity_id') or p.get('id',''))\n"),
    ("            if path=='/api/urls/block':",
     "            if path=='/api/blocks':\n"
     "                # Optional related-material blocks for a state or court page; each layer is lazy and failure-tolerant.\n"
     "                if p.get('state'):return self.send_body(200,{'state_proceedings':judge_layer('state_proceedings','for_state',p.get('state')),'court_documents':judge_layer('court_documents','for_state',p.get('state'))})\n"
     "                if p.get('court'):return self.send_body(200,{'court_documents':judge_layer('court_documents','for_court',p.get('court')),'urls':judge_layer('url_directory','for_court',p.get('court'))})\n"
     "                return self.send_body(200,{})\n"
     "            if path=='/api/urls/block':"),
])

RELATED = r"""  /* ---- Related-material blocks from optional data layers (same shape everywhere: total, results, link, qualification) ---- */
  function relatedBlock(title, block, view, max = 8) {
    if (!block || !block.total) return null; const box = el('section', 'panel'); box.append(append(el('div', 'section-heading'), el('h2', '', title), el('small', '', `${count(block.total)} records`)));
    const list = el('ul', 'related-list'); for (const r of (block.results || []).slice(0, max)) { const li = el('li'); li.append(action(r.title || r.id, () => openGenericDetail(view, r.id), 'document-title')); if (r.subtitle) li.append(el('div', 'record-subline', r.subtitle)); if (r.evidence) li.append(el('div', 'record-subline', r.evidence)); list.append(li); }
    box.append(list); if (block.link) { const a = el('a', 'button-link', 'See all →'); a.href = block.link; box.append(a); } if (block.qualification) box.append(el('p', 'coverage-footnote', block.qualification)); return box;
  }
  window.judgeDisclosuresSection = function (profile) {
    const d = profile.disclosures; if (!d || !d.available) return null; const box = el('section', 'judge-structured'); box.append(el('h2', '', 'Financial disclosures (CourtListener snapshot 2026-06-30)'));
    if (d.state === 'no_filing_in_snapshot') { box.append(el('p', 'quiet-empty', 'No filing for this judge in the snapshot. That is a gap in the snapshot, not a statement about holdings.')); return box; }
    const years = d.years_filed || []; box.append(el('p', 'record-subline', `Filed for ${years.length} year${years.length === 1 ? '' : 's'}${years.length ? ` (${years[0]}–${years[years.length - 1]})` : ''} · ${count(d.total_holdings || 0)} holding rows in all filings · latest year ${d.latest_year || 'not stated'}`));
    const top = d.top_holdings_latest_year || []; if (top.length) { box.append(el('h3', '', `Holdings named in the ${d.latest_year} filing (alphabetical, first ${top.length})`)); const chips = el('div', 'chip-row'); for (const h of top) chips.append(el('span', 'chip', String(h).slice(0, 80))); box.append(chips); } else box.append(el('p', 'quiet-empty', 'The latest filing lists no reportable holdings.'));
    if (d.link) { const a = el('a', 'button-link', 'All filings and holdings →'); a.href = d.link; box.append(a); } if (d.qualification) box.append(el('p', 'coverage-footnote', d.qualification)); return box;
  };

  /* ---- US state grid and state pages ---- */"""

edit('areas.js', [
    ("    { view: 'coverage', title: 'Coverage & gaps',",
     "    { view: 'state-proceedings', title: 'State mass torts', nav: 'State mass torts', supplement: 'state_coordinated_proceedings_20260919', description: 'New Jersey Multicounty Litigation and California coordinated proceedings (JCCP) as listed in the saved registries, with counties, judges as printed, and federal MDLs the source itself names.' },\n"
     "    { view: 'court-documents', title: 'Court documents', nav: 'Court documents', supplement: 'court_document_library_20260919', description: 'Forms, local rules, standing orders, fee schedules and other files downloaded from court websites in August 2026, served from the saved copies.' },\n"
     "    { view: 'judge-disclosures', title: 'Judge financial disclosures', nav: 'Disclosures', supplement: 'judge_financial_disclosures_20260919', description: 'Annual financial disclosure filings from a CourtListener snapshot: holdings as described by the filer with value codes only.' },\n"
     "    { view: 'coverage', title: 'Coverage & gaps',"),
    ("for (const view of ['settlements', 'statistics', 'courts', 'counsel', 'urls', 'uscourts'])",
     "for (const view of ['settlements', 'statistics', 'courts', 'counsel', 'urls', 'uscourts', 'state-proceedings', 'court-documents', 'judge-disclosures'])"),
    ("  /* ---- US state grid and state pages ---- */", RELATED),
    ("    try { const u = (await api(`/api/urls/block?state=",
     "    try { const b = await api(`/api/blocks?state=${encodeURIComponent(abbr)}`, signal); if (!signal.aborted) { const sp = relatedBlock('State coordinated mass-tort proceedings', b.state_proceedings, 'state-proceedings'); if (sp) main.append(sp); const cd = relatedBlock('Court documents saved for this state', b.court_documents, 'court-documents', 6); if (cd) main.append(cd); } } catch (error) { if (error.name === 'AbortError') return; }\n"
     "    try { const u = (await api(`/api/urls/block?state="),
    ("    if (local.length) { const box = el('section', 'panel'); box.append(el('h2', '', 'Saved filings, orders and exhibits'));",
     "    { const sp = relatedBlock('Related state coordinated proceedings (named by the state registry)', m.state_proceedings, 'state-proceedings'); if (sp) main.append(sp); }\n"
     "    if (local.length) { const box = el('section', 'panel'); box.append(el('h2', '', 'Saved filings, orders and exhibits'));"),
])

edit('app.js', [
    ("      if(typeof judgeEvidenceSection==='function'){const evidence=judgeEvidenceSection(profile);if(evidence)article.append(evidence);}",
     "      if(typeof judgeEvidenceSection==='function'){const evidence=judgeEvidenceSection(profile);if(evidence)article.append(evidence);}\n"
     "      if(typeof judgeDisclosuresSection==='function'){const disclosures=judgeDisclosuresSection(profile);if(disclosures)article.append(disclosures);}"),
    ("['uscourts','U.S. Courts pages','uscourts_pages_20260919'],",
     "['state-proceedings','State mass torts','state_coordinated_proceedings_20260919'],['court-documents','Court documents','court_document_library_20260919'],['uscourts','U.S. Courts pages','uscourts_pages_20260919'],"),
])

css = open(D + 'styles.css', encoding='utf-8').read()
if '.related-list' not in css:
    open(D + 'styles.css', 'a', encoding='utf-8', newline='').write(
        "\n/* Related-material blocks */\n.related-list{list-style:none;margin:0 0 .5rem;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.35rem .9rem}\n"
        ".related-list li{padding:.3rem 0;border-bottom:1px solid var(--line,#e6e2d8);min-width:0}\n.related-list .record-subline{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n")
print('wired')
