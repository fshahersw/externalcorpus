"""Round 8i: grouped, denser collection rail; downloaded source documents sit with Sources under an accurate name. Idempotent."""
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
    # the downloaded files are mostly court forms, rules and e-filing guides; settlement agreements are still arriving
    ("      {view:'source-documents',label:'Settlement agreements',hint:'Multistate settlements, consent judgments and other official documents with full text',supplement:'source_directory_documents_20260919'},\n", ""),
    ("      {view:'saved-pages',label:'Saved web pages',hint:'Searchable text of captured court and government pages',supplement:'saved_web_pages_20260919'}]},",
     "      {view:'saved-pages',label:'Saved web pages',hint:'Searchable text of captured court and government pages',supplement:'saved_web_pages_20260919'},\n"
     "      {view:'source-documents',label:'Downloaded source files',hint:'Court forms, rules, e-filing guides and settlement documents with full text',supplement:'source_directory_documents_20260919'}]},"),
    # group headings for the long MDL list
    ("      {view:'mdls',label:'MDL registry',hint:'Pending multidistrict litigation with judges and counts',supplement:'jpml_mdl_20260919'},",
     "      {view:'mdls',group:'Federal MDLs',label:'MDL registry',hint:'Pending multidistrict litigation with judges and counts',supplement:'jpml_mdl_20260919'},"),
    ("      {view:'state-proceedings',label:'State mass torts',", "      {view:'state-proceedings',group:'State courts',label:'State mass torts',"),
    ("      {view:'settlements',label:'Settlement notices',", "      {view:'settlements',group:'Outcomes',label:'Settlement notices',"),
    ("  for(const seg of segments){const a=el('a',seg.view===active?'rail-item active':'rail-item');a.href=`#${seg.view}`;if(seg.view===active)a.setAttribute('aria-current','page');a.append(el('strong','',seg.label));if(seg.hint)a.append(el('span','',seg.hint));group.append(a);}",
     "  const dense=segments.length>5;if(dense)group.classList.add('is-dense');\n"
     "  for(const seg of segments){if(seg.group)group.append(el('h3','rail-subtitle',seg.group));const a=el('a',seg.view===active?'rail-item active':'rail-item');a.href=`#${seg.view}`;if(seg.view===active)a.setAttribute('aria-current','page');a.append(el('strong','',seg.label));if(seg.hint&&(!dense||seg.view===active))a.append(el('span','',seg.hint));else if(seg.hint)a.title=seg.hint;group.append(a);}"),
])

css = open(D + 'styles.css', encoding='utf-8').read()
if '.rail-subtitle' not in css:
    css += ("\n/* grouped, denser collection rail */\n"
            ".rail-subtitle{font-size:9.5px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted);font-weight:600;margin:9px 6px 3px}.rail-title+.rail-subtitle{margin-top:2px}\n"
            ".rail-collections.is-dense .rail-item{padding:5px 8px}.rail-collections.is-dense .rail-item strong{font-size:12.5px;font-weight:600}\n")
    open(D + 'styles.css', 'w', encoding='utf-8', newline='').write(css)

areas = open(D + 'areas.js', encoding='utf-8').read()
old = "{ view: 'source-documents', title: "
if old in areas:
    import re
    found = re.search(r"\{ view: 'source-documents', title: '([^']*)', nav: '([^']*)',", areas)
    if found and found.group(1) != 'Downloaded source files':
        areas = areas.replace(found.group(0), "{ view: 'source-documents', title: 'Downloaded source files', nav: 'Source files',")
        open(D + 'areas.js', 'w', encoding='utf-8', newline='').write(areas)
print('rail regrouped')
