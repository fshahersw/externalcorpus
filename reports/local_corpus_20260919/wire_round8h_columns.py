"""Round 8h: a generic table whose first declared column is a data value (amount, date) no longer loses it under the title. Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if new in text:
            continue
        assert text.count(old) == 1, (name, old[:90], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


edit('areas.js', [
    ("      hr.append(el('th', '', cols[0]?.label || 'Record')); for (const c of cols.slice(1)) hr.append(el('th', '', c.label)); t.append(append(el('thead'), hr)); const tb = el('tbody');",
     "      // The first declared column is the title column only when it does not carry a value of its own (or carries the title itself).\n"
     "      const sample = data.results[0] || {}, firstKey = cols[0]?.key, ownTitle = !firstKey || !(sample.cells && firstKey in sample.cells) || String(sample.cells[firstKey] ?? '') === String(sample.title ?? '');\n"
     "      const dataCols = ownTitle ? cols.slice(1) : cols, TITLE_LABEL = { 'verdict-reports': 'Case', 'expert-rulings': 'Filing', 'cpsc-injury-data': 'Record' };\n"
     "      hr.append(el('th', '', ownTitle ? (cols[0]?.label || 'Record') : (data.title_label || TITLE_LABEL[view] || 'Record'))); for (const c of dataCols) hr.append(el('th', '', c.label)); t.append(append(el('thead'), hr)); const tb = el('tbody');"),
    ("        const columnValues = new Set(cols.slice(1).map(c => String((r.cells || {})[c.key] ?? '').trim().toLowerCase()).filter(Boolean));",
     "        const columnValues = new Set(dataCols.map(c => String((r.cells || {})[c.key] ?? '').trim().toLowerCase()).filter(Boolean));"),
    ("        tr.append(c1); for (const c of cols.slice(1)) tr.append(el('td', '', r.cells && r.cells[c.key] !== undefined && r.cells[c.key] !== null ? String(r.cells[c.key]) : '')); tb.append(tr); }",
     "        tr.append(c1); for (const c of dataCols) tr.append(el('td', '', r.cells && r.cells[c.key] !== undefined && r.cells[c.key] !== null ? String(r.cells[c.key]) : '')); tb.append(tr); }"),
])
edit('verdict_reports.py', [
    ("{'name': 'state', 'label': 'State (as printed by the publisher)', 'type': 'select',", "{'name': 'state', 'label': 'State', 'type': 'select',"),
    ("{'name': 'amount_band', 'label': 'Amount (as printed)', 'type': 'select',", "{'name': 'amount_band', 'label': 'Amount', 'type': 'select',"),
])
print('generic columns fixed')
