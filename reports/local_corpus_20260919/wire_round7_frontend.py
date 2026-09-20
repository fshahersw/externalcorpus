"""Front-end round 7: replace the segment pills with a left filter rail ("workbench"), fold single-state codes into
Laws & rules, mount the real US map (usmap.js) on the home and state pages, load the new modules. Idempotent."""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if new in text:
            continue
        assert text.count(old) == 1, (name, old[:80], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


# ---------------------------------------------------------------- index.html
edit('index.html', [
    ('      <nav id="hub-segments" class="hub-segments scope-switch" aria-label="Views in this section"></nav>\n', ''),
])
html = open(D + 'index.html', encoding='utf-8').read()
if '/usmap.js' not in html:
    assert html.count('<script src="/areas.js"') == 1 or html.count("areas.js") >= 1
    import re
    html = re.sub(r'(\s*<script[^>]*src="/?areas\.js"[^>]*></script>)', r'\1\n  <script src="/usmap.js" defer></script>\n  <script src="/statsviz.js" defer></script>\n  <script src="/judgeui.js" defer></script>', html, count=1)
    open(D + 'index.html', 'w', encoding='utf-8', newline='').write(html)

# ---------------------------------------------------------------- app.js
LAW_OLD = "{view:'laws',label:'Laws & rules',segments:[{view:'laws',label:'Saved law'},{view:'indiana-code',label:'Indiana Code',supplement:'indiana_code_2026_20260919'},{view:'sd-statutes',label:'South Dakota',supplement:'sd_statutes_20260919'},{view:'public-laws',label:'Public Laws & U.S. Code',supplement:'public_law_uscode_20260919'}]},"
LAW_NEW = "{view:'laws',label:'Laws & rules',segments:[{view:'laws',label:'State & federal law',hint:'Statutes, constitutions, court rules and regulations saved by jurisdiction'},{view:'state-codes',label:'Full-text state codes',hint:'Every section of the codes saved in full; choose the state in the filters'},{view:'public-laws',label:'Public Laws & U.S. Code',hint:'Acts of Congress and the U.S. Code sections they change',supplement:'public_law_uscode_20260919'}]},"
HINTS = {
    "{view:'regulations',label:'CFR sections',": "{view:'regulations',label:'Code of Federal Regulations',hint:'Section text with amendment history',",
    "{view:'federal-register',label:'Federal Register',": "{view:'federal-register',label:'Federal Register',hint:'Rules, proposed rules and notices, 1994 to 2026',",
    "{view:'agencies',label:'Safety data',": "{view:'agencies',label:'Safety & enforcement data',hint:'Recalls, approvals, enforcement records',",
    "{view:'agency-documents',label:'Documents',": "{view:'agency-documents',label:'Agency & science documents',hint:'Downloaded reports, profiles and orders with full text',",
    "{view:'sources',label:'Source directory'}": "{view:'sources',label:'Source directory',hint:'Curated official sources and APIs'}",
    "{view:'urls',label:'URL directory',": "{view:'urls',label:'URL directory',hint:'Every known official address, by category and place',",
    "{view:'saved-pages',label:'Saved pages',": "{view:'saved-pages',label:'Saved web pages',hint:'Searchable text of captured court and government pages',",
    "{view:'judges',label:'Profiles'}": "{view:'judges',label:'Judge profiles',hint:'Current judges with appointments, MDLs and evidence'}",
    "{view:'judge-disclosures',label:'Financial disclosures',": "{view:'judge-disclosures',label:'Financial disclosures',hint:'Annual filings and holdings as filed',",
    "{view:'courts',label:'Courts',supplement:'court_spine_20260919'},{view:'court-documents'": "{view:'courts',label:'Court registry',hint:'Every court with identifiers and marks',supplement:'court_spine_20260919'},{view:'court-documents'",
    "{view:'court-documents',label:'Court documents',": "{view:'court-documents',label:'Court documents',hint:'Forms, local rules, orders and fee schedules saved from court sites',",
    "{view:'uscourts',label:'U.S. Courts pages',": "{view:'uscourts',label:'U.S. Courts publications',hint:'Saved uscourts.gov pages and reports',",
}
pairs = [(LAW_OLD, LAW_NEW)] + list(HINTS.items())
pairs.append((
    "    if(isActive&&strip&&shown.length>1)for(const seg of shown){\n      const chip=el('a',seg.view===activeView?'chip selected':'chip',seg.label);chip.href=`#${seg.view}`;\n      if(seg.view===activeView)chip.setAttribute('aria-current','true');\n      strip.append(chip);\n    }\n",
    "    if(isActive)window.ACTIVE_SEGMENTS={active:activeView,items:shown.length>1?shown:[]};\n"))
pairs.append((
    "  const activeTab=hub.views.find(tab=>hubViews(tab).some(seg=>seg.view===activeView));\n",
    "  const activeTab=hub.views.find(tab=>hubViews(tab).some(seg=>seg.view===activeView));\n  window.ACTIVE_SEGMENTS={active:activeView,items:[]};\n"))
edit('app.js', pairs)

app = open(D + 'app.js', encoding='utf-8').read()
WORKBENCH = r"""
/* Workbench layout. A page that has filters (or belongs to a tab with several collections) gets a left rail: the tab's
   collections as a vertical list, then the page's own filters stacked, with the results to the right. Pages keep rendering
   exactly as before; this only re-parents what they produced, so every route and filter keeps working. */
function applyWorkbench(){
  if(!main||main.querySelector(':scope > .workbench'))return;
  const segments=(window.ACTIVE_SEGMENTS&&window.ACTIVE_SEGMENTS.items)||[],active=window.ACTIVE_SEGMENTS&&window.ACTIVE_SEGMENTS.active;
  const form=main.querySelector(':scope > form.filters');
  const listing=['laws','documents','federal','judges','people','counties','sources'].includes(route.view)||Boolean(extensionArea(route.view));
  if(!form&&(segments.length<2||!listing||route.id))return;
  if(!form&&main.getAttribute('aria-busy')==='true')return;
  const bench=el('div','workbench'),rail=el('aside','rail'),body=el('div','workbench-body');rail.setAttribute('aria-label','Collections and filters');
  if(segments.length>1){
    const group=el('nav','rail-group rail-collections');group.setAttribute('aria-label','Collections');group.append(el('h2','rail-title','Collection'));
    for(const seg of segments){const a=el('a',seg.view===active?'rail-item active':'rail-item');a.href=`#${seg.view}`;if(seg.view===active)a.setAttribute('aria-current','page');a.append(el('strong','',seg.label));if(seg.hint)a.append(el('span','',seg.hint));group.append(a);}
    rail.append(group);
  }
  const anchor=form||[...main.children].find(node=>!node.matches('.page-heading,.home-hero,.notice,.view-switch,.scope-switch'))||null;
  if(form){const group=el('div','rail-group');group.append(el('h2','rail-title','Filters'));const toggle=el('details','rail-filters');toggle.open=window.matchMedia('(min-width: 1001px)').matches;toggle.append(el('summary','','Show filters'));
    main.insertBefore(bench,form);toggle.append(form);group.append(toggle);rail.append(group);}
  else if(anchor)main.insertBefore(bench,anchor);else main.append(bench);
  let node=bench.nextSibling;while(node){const next=node.nextSibling;body.append(node);node=next;}
  bench.append(rail,body);
}
const workbenchObserver=new MutationObserver(()=>{workbenchObserver.disconnect();try{applyWorkbench();}finally{workbenchObserver.observe(main,{childList:true});}});
"""
if 'function applyWorkbench' not in app:
    marker = "document.addEventListener('DOMContentLoaded'"
    assert app.count(marker) == 1
    app = app.replace(marker, WORKBENCH + "workbenchObserver.observe(main,{childList:true});\n" + marker)
    open(D + 'app.js', 'w', encoding='utf-8', newline='').write(app)

# ---------------------------------------------------------------- areas.js
MAP_NEW = r"""  window.renderUsMap = async function (target, signal) {
    target.append(append(el('div', 'section-heading'), el('h2', '', 'Browse by state'), el('small', '', 'Select a state for its counties, laws, judges and sources')));
    let data; try { data = matrixCache || (matrixCache = await api('/api/coverage/matrix', signal)); } catch (error) { target.append(el('p', 'registry-empty', 'State coverage is not available right now.')); return; }
    if (signal?.aborted || !data.available) return;
    if (window.UsMap) {
      try {
        let filing = null; try { filing = await api('/api/county-filing/coverage', signal); } catch (error) { if (error.name === 'AbortError') return; }
        const rows = data.rows || [], values = fn => Object.fromEntries(rows.map(r => [r.abbr, fn(r)]));
        const metrics = METRICS.map(([key, label, fn]) => ({ key, label, values: values(fn) }));
        if (filing && filing.available) { const by = Object.fromEntries((filing.states || []).map(s => [s.state, s]));
          metrics.unshift({ key: 'filing', label: 'Counties with court rules and filing sources', unit: 'counties with official rules or filing sources', values: Object.fromEntries(Object.keys(by).map(k => [k, by[k].with_any || 0])) }); }
        const holder = el('div', 'map-holder'); target.append(holder);
        await window.UsMap.national(holder, { metrics, onState: usps => navigate(`state/${usps}`) });
        const extra = rows.filter(r => !window.UsMap.USPS_FIPS[r.abbr]); if (extra.length) { const line = el('p', 'record-subline'); line.append(document.createTextNode('Territories: ')); for (const r of extra) line.append(routeLink(r.name, `state/${r.abbr}`, {}, 'button-link'), document.createTextNode('  ')); target.append(line); }
        return;
      } catch (error) { if (error.name === 'AbortError') return; }
    }
    const controls = el('div', 'map-controls'), grid = el('div', 'us-grid'), legend = el('p', 'coverage-footnote');
    append(target, controls, grid, legend);
"""
MAP_OLD_HEAD = """  window.renderUsMap = async function (target, signal) {
    target.append(append(el('div', 'section-heading'), el('h2', '', 'Browse by state'), el('small', '', 'Select a state for its counties, laws, judges and sources')));
    const controls = el('div', 'map-controls'), grid = el('div', 'us-grid'), legend = el('p', 'coverage-footnote');
    append(target, controls, grid, legend);
    let data; try { data = matrixCache || (matrixCache = await api('/api/coverage/matrix', signal)); } catch (error) { grid.append(el('p', 'registry-empty', 'State coverage is not available right now.')); return; }
    if (signal?.aborted || !data.available) return;
"""
COUNTY_OLD = "    const grid = el('div', 'county-chip-grid'); counties.append(grid); main.append(counties);\n"
COUNTY_NEW = ("    const countyMap = el('div', 'map-holder state-map'); counties.append(countyMap);\n"
              "    const grid = el('div', 'county-chip-grid'); counties.append(grid); main.append(counties);\n"
              "    if (window.UsMap && window.UsMap.USPS_FIPS[abbr]) (async () => { try { const f = await api(`/api/county-filing/state-counties?state=${encodeURIComponent(abbr)}`, signal); if (signal.aborted) return; const info = Object.fromEntries(((f && f.counties) || []).map(c => [c.fips, c])); await window.UsMap.state(countyMap, abbr, { counties: info, onCounty: fips => navigate(`county/${fips}`, { state: s.name }) }); } catch (error) { countyMap.remove(); } })(); else countyMap.remove();\n")
edit('areas.js', [(MAP_OLD_HEAD, MAP_NEW), (COUNTY_OLD, COUNTY_NEW)])

areas = open(D + 'areas.js', encoding='utf-8').read()
if "view: 'state-codes'" not in areas:
    anchor = "    { view: 'coverage', title: 'Coverage & gaps',"
    assert areas.count(anchor) == 1
    areas = areas.replace(anchor, "    { view: 'state-codes', title: 'Full-text state codes', nav: 'State codes', description: 'Complete state codes saved in full text, searchable by citation or words. Choose the state in the filters.' },\n" + anchor)
    import re
    found = re.search(r"for \(const view of \[([^\]]*)\]\) if \(registry\[view\] && !registry\[view\]\.page\) registry\[view\]\.page = genericPage\(view\);", areas)
    assert found, 'generic page registration not found'
    areas = areas.replace(found.group(0), found.group(0).replace(found.group(1), found.group(1) + ", 'state-codes'"))
    open(D + 'areas.js', 'w', encoding='utf-8', newline='').write(areas)

# ---------------------------------------------------------------- styles.css
css = open(D + 'styles.css', encoding='utf-8').read()
if '.workbench{' not in css:
    css += """
/* ---- Workbench: collections and filters in a left rail, results to the right ---- */
.workbench{display:grid;grid-template-columns:264px minmax(0,1fr);gap:24px;align-items:start}
.rail{position:sticky;top:64px;display:flex;flex-direction:column;gap:18px;max-height:calc(100vh - 84px);overflow:auto;padding-right:2px;scrollbar-width:thin}
.rail-group{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px}
.rail-title{font:600 10.5px/1 system-ui,sans-serif;letter-spacing:.9px;text-transform:uppercase;color:var(--muted);margin:2px 4px 10px}
.rail-item{display:block;padding:8px 10px 8px 12px;border-radius:7px;border-left:3px solid transparent;color:var(--ink);text-decoration:none;line-height:1.35}
.rail-item+.rail-item{margin-top:2px}.rail-item strong{display:block;font-size:13px;font-weight:600}.rail-item span{display:block;font-size:11.5px;color:var(--muted);margin-top:1px}
.rail-item:hover{background:#f3f6f1}.rail-item.active{background:var(--teal-light);border-left-color:var(--teal)}.rail-item.active strong{color:var(--teal-dark)}
.rail-filters>summary{display:none}
.rail form.filters{display:flex;flex-direction:column;gap:11px;padding:0;margin:0;border:0;background:transparent;box-shadow:none}
.rail form.filters>label,.rail form.filters>div{width:100%;min-width:0;grid-column:auto}.rail form.filters label{font-size:11px;letter-spacing:.2px}
.rail form.filters input,.rail form.filters select{width:100%;min-height:34px;font-size:13px}
.rail form.filters .button,.rail form.filters button{width:100%;justify-content:center;min-height:34px}
.rail form.filters .date-presets,.rail form.filters .chip-row{display:flex;flex-wrap:wrap;gap:5px}
.workbench-body{min-width:0}.workbench-body>.table-panel:first-child,.workbench-body>.results-heading:first-child{margin-top:0}
.map-holder{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px 12px;margin-bottom:16px}.map-holder.state-map{max-width:760px}
@media(max-width:1000px){.workbench{grid-template-columns:1fr;gap:14px}.rail{position:static;max-height:none;overflow:visible;gap:10px}.rail-collections{display:flex;gap:6px;overflow-x:auto;padding:8px}.rail-collections .rail-title{display:none}.rail-collections .rail-item{flex:0 0 auto;border-left:0;border-bottom:2px solid transparent;border-radius:6px;padding:6px 10px}.rail-collections .rail-item span{display:none}.rail-collections .rail-item.active{border-bottom-color:var(--teal)}.rail-filters>summary{display:block;cursor:pointer;font-size:13px;font-weight:600;padding:2px 4px 8px;color:var(--teal-dark)}.rail-group .rail-title{display:none}}
"""
    open(D + 'styles.css', 'w', encoding='utf-8', newline='').write(css)
print('front-end round 7 applied')
