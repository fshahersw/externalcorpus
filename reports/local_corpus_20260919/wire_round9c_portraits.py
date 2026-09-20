"""Round 9c: portraits on historical biographies (profile and cards) and a credit line on both kinds of profile. Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'
P = D + 'judgeui.js'
t = open(P, encoding='utf-8').read()
pairs = [
    ("    hero.append(avatar(p.name, ''));", "    hero.append(avatar(p.name, p.photo_url || ''));"),
    ("    card.append(avatar(row.name, person ? '' : row.photo_url, 'card'));", "    card.append(avatar(row.name, row.photo_url || '', 'card'));"),
    ("      ['Portrait.', p.photo_reference ? 'The publisher records a photo reference for this person; no portrait file is supplied by this view.' : '']",
     "      ['Portrait.', p.photo_credit ? p.photo_credit + ' Attached by the same CourtListener person id; it may be historical.' : (p.photo_reference ? 'The publisher records a photo reference for this person; no portrait file is supplied by this view.' : '')]"),
]
for old, new in pairs:
    if new in t:
        continue
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)
open(P, 'w', encoding='utf-8', newline='').write(t)
print('portraits hooked')
