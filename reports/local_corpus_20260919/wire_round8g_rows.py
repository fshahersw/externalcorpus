"""Round 8g: generic table rows stop repeating a count that a column already shows ("77 saved dockets" beside a 77 column). Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'
text = open(D + 'areas.js', encoding='utf-8').read()
pairs = [
    ("        const subtitle = String(r.subtitle || '').split(' · ').map(part => part.trim()).filter(part => part && !columnValues.has(part.toLowerCase())).join(' · ');",
     "        const repeats = part => { const lower = part.toLowerCase(); if (columnValues.has(lower)) return true; const lead = lower.match(/^([\\d,]+)\\s+\\S/); return Boolean(lead && (columnValues.has(lead[1]) || columnValues.has(lead[1].replace(/,/g, '')))); };\n"
     "        const subtitle = String(r.subtitle || '').split(' · ').map(part => part.trim()).filter(part => part && !repeats(part)).join(' · ');"),
    ("        const picked = (Array.isArray(r.badges) ? r.badges : []).map(x => String(x).trim()).filter(x => x && !visible.has(x.toLowerCase())).slice(0, 2);",
     "        const picked = (Array.isArray(r.badges) ? r.badges : []).map(x => String(x).trim()).filter(x => x && !visible.has(x.toLowerCase()) && !repeats(x)).slice(0, 2);"),
]
for old, new in pairs:
    if new in text:
        continue
    assert text.count(old) == 1, old[:80]
    text = text.replace(old, new)
open(D + 'areas.js', 'w', encoding='utf-8', newline='').write(text)
print('row de-duplication applied')
