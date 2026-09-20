"""Round 8e: compact header for law provisions in the reader (one status line, official source first). Idempotent."""
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
    ("sourceMetadata=observation.metadata||{};body.append(evidenceDates(item.source_as_of,item.saved_at));\n  const meta=el('dl','record-meta important-meta');\n  for(const [key,label] of [['citation',",
     "sourceMetadata=observation.metadata||{};if(!lawRecord||item.source_as_of||item.saved_at)body.append(evidenceDates(item.source_as_of,item.saved_at));\n"
     "  if(lawRecord){const line=[human(observation.status),observation.snapshot?`Publisher snapshot ${observation.snapshot}`:'',item.state,kindLabel(item.kind)].filter(Boolean).join(' · ');if(line)body.append(el('p','law-record-line',line));}\n"
     "  const meta=el('dl','record-meta important-meta');\n  for(const [key,label] of lawRecord?[]:[['citation',"),
    ("  const actions=el('div','button-row reader-actions');append(actions,link(item.dataset==='open_us_law'?'Source data file ↗':",
     "  const actions=el('div','button-row reader-actions');if(lawRecord)append(actions,link('Official source ↗',item.source_url,true,'button'),link('Full text ↗',item.text_url));else append(actions,link(item.dataset==='open_us_law'?'Source data file ↗':"),
])

css = open(D + 'styles.css', encoding='utf-8').read()
if '.law-record-line' not in css:
    css += "\n.law-record-line{font-size:12.5px;color:var(--muted);margin:0 0 10px;text-transform:none}.law-record .reader-actions{margin:0 0 6px}.law-record .reader-actions .button,.law-record .reader-actions a{min-height:30px;padding:4px 10px;font-size:12.5px}\n"
    open(D + 'styles.css', 'w', encoding='utf-8', newline='').write(css)
print('reader compact applied')
