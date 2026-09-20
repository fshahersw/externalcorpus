"""Hook the JudgeUI module (profile, historical person, cards) and make its stylesheet install without a blocked <style>. Idempotent."""
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
    # profile: the module renders its own back link, so the old one is only appended on the fallback path
    ("back.href=previous&&/^#judges(?:\\?|$)/.test(previous)?previous:'#judges';main.append(back);\n    if(window.JudgeUI&&typeof window.JudgeUI.profile==='function'){const host=el('div','ju-host');main.append(host);window.JudgeUI.profile(host,profile,{back:()=>{location.hash=back.getAttribute('href');}});main.removeAttribute('aria-busy');announce(`${profile.name} opened.`);return;}\n",
     "back.href=previous&&/^#judges(?:\\?|$)/.test(previous)?previous:'#judges';\n    if(window.JudgeUI&&typeof window.JudgeUI.profile==='function'){window.JudgeUI.profile(main,profile,{back:()=>{location.hash=back.getAttribute('href');}});announce(`${profile.name} opened.`);return;}\n    main.append(back);\n"),
    ("back.href=returnTo;main.append(back);\n    heading(person.name||'Historical biography',",
     "back.href=returnTo;\n    if(window.JudgeUI&&typeof window.JudgeUI.person==='function'){document.title=`${person.name||'Historical biography'} · Legal Archive`;document.querySelector('#breadcrumb-current').textContent=person.name||'Historical biography';window.JudgeUI.person(main,person,{back:()=>{location.hash=returnTo;}});announce(`${person.name||'Historical biography'} opened.`);return;}\n    main.append(back);\n    heading(person.name||'Historical biography',"),
    ("for(const item of data.items)grid.append(judgeCard(item));",
     "for(const item of data.items)grid.append(window.JudgeUI&&typeof window.JudgeUI.card==='function'?window.JudgeUI.card(item):judgeCard(item));"),
    ("for(const person of data.items)grid.append(historicalPersonCard(person,returnTo));",
     "for(const person of data.items)grid.append(window.JudgeUI&&typeof window.JudgeUI.card==='function'?window.JudgeUI.card(person):historicalPersonCard(person,returnTo));"),
])

edit('judgeui.js', [
    ("""  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var node = document.createElement('style');
    node.id = STYLE_ID;
    node.textContent = CSS;
    (document.head || document.documentElement).append(node);
    if (node.sheet) return;
    try {
      var sheet = new CSSStyleSheet();
      sheet.replaceSync(CSS);
      document.adoptedStyleSheets = Array.prototype.slice.call(document.adoptedStyleSheets).concat(sheet);
      node.dataset.applied = 'adopted-stylesheet';
    } catch (error) {
      node.remove();
    }
  }
""",
     """  function ensureStyle() {
    if (document.documentElement.dataset.judgeuiStyle) return;
    document.documentElement.dataset.judgeuiStyle = STYLE_ID;
    // Constructed stylesheet first: the page's policy (style-src 'self') blocks an injected <style> and logs an error for it.
    try {
      var sheet = new CSSStyleSheet();
      sheet.replaceSync(CSS);
      document.adoptedStyleSheets = Array.prototype.slice.call(document.adoptedStyleSheets).concat(sheet);
      return;
    } catch (error) { /* older engine: fall through to a style element */ }
    var node = document.createElement('style');
    node.id = STYLE_ID;
    node.textContent = CSS;
    (document.head || document.documentElement).append(node);
  }
"""),
])
print('judge ui hooked')
