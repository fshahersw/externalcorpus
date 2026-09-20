"""Replace the MDL layer renderer with one that shows type chips (filtered links) and firm rows. Idempotent."""
import re

P = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/areas.js'
text = open(P, encoding='utf-8').read()
start = text.index('  function mdlLayerBlock(title, block, view) {')
end = text.index('  /* ---- Related-material blocks from optional data layers')
NEW = r"""  function mdlLayerBlock(title, block, view) {
    if (!block) return null; const total = block.total ?? block.total_appearances_extended_linkage; const typed = block.by_doc_type || block.by_entry_type; const typeFilter = block.by_doc_type ? 'doc_type' : 'entry_type';
    const rows = block.results || block.sample || block.firms || (typed ? [] : (block.latest || block.latest_25 || []));
    if (!total && !rows.length) return null;
    const box = el('section', 'panel'); box.append(append(el('div', 'section-heading'), el('h2', '', title), el('small', '', total !== undefined ? `${count(total)} in the saved docket sample` : '')));
    const bits = []; for (const [k, v] of Object.entries(block)) if (/^by_(?!doc_type|entry_type)/.test(k) && v && typeof v === 'object' && !Array.isArray(v)) bits.push(`${human(k.slice(3))}: ` + Object.entries(v).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([name, n]) => `${human(String(name))} ${count(n)}`).join(', '));
    if (block.date_first || block.first_date) bits.push(`entries dated ${block.date_first || block.first_date} to ${block.date_last || block.last_date || '?'}`); if (block.capped) bits.push('entries capped by the source release');
    if (block.total_appearances_direct_linkage !== undefined) bits.push(`${count(block.total_appearances_direct_linkage)} appearances on the master docket itself, ${count((block.total_appearances_extended_linkage || 0) - block.total_appearances_direct_linkage)} on linked member cases`);
    if (block.lead_attorney_appearance_count) bits.push(`${count(block.lead_attorney_appearance_count)} marked lead attorney`);
    if (block.party_counts_by_category) { const c = block.party_counts_by_category; bits.push(`parties: ${count(c.organization || 0)} organizations, ${count(c.natural_person_count_only || 0)} individuals (counted, never named)`); }
    if (bits.length) box.append(el('p', 'record-subline', bits.join(' · ')));
    if (typed) { const chips = el('div', 'chip-row'); const entries = Object.entries(typed).filter(([, n]) => n > 0).sort((a, b) => (a[0] === 'other') - (b[0] === 'other') || b[1] - a[1]); for (const [kind, n] of entries) chips.append(routeLink(`${human(kind)} ${count(n)}`, view, { mdl: block.mdl_number || '', [typeFilter]: kind }, 'chip')); box.append(chips); }
    if (rows.length) { const list = el('ul', 'related-list'); for (const r of rows.slice(0, 10)) { const li = el('li'); const label = r.title || r.name || r.canonical_name || r.firm_name || r.description || r.id; if (r.id !== undefined) li.append(action(String(label).slice(0, 140), () => openGenericDetail(view, String(r.id)), 'document-title')); else li.append(el('span', 'document-title', String(label).slice(0, 140))); const sub = r.subtitle || [r.date_filed || r.date || r.entry_date, r.status, r.court_id, r.appearance_count !== undefined ? `${count(r.appearance_count)} appearances` : ''].filter(Boolean).join(' · '); if (sub) li.append(el('div', 'record-subline', sub)); list.append(li); } box.append(list); }
    { const target = block.mdl_number ? makeHash(view, { mdl: block.mdl_number }) : block.link; if (target) { const a = el('a', 'button-link', 'See all →'); a.href = target; box.append(a); } }
    if (block.qualification) { const q = el('p', 'coverage-footnote', String(block.qualification).slice(0, 420) + (String(block.qualification).length > 420 ? ' …' : '')); q.title = block.qualification; box.append(q); }
    return box;
  }

"""
text = text[:start] + NEW + text[end:]
open(P, 'w', encoding='utf-8', newline='').write(text)
print('replaced')
