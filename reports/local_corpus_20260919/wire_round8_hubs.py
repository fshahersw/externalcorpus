"""Round 8 navigation: rename hubs, move state law next to the map, merge Courts & litigation tabs, drop single-state code tabs.
Idempotent (replaces the whole HUBS literal)."""
import re

D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'
app = open(D + 'app.js', encoding='utf-8').read()
start = app.index('const HUBS=[')
end = app.index('];', start) + 2
HUBS = r"""const HUBS=[
  {id:'places',views:[
    {view:'overview',label:'Map'},
    {view:'laws',label:'State law'},
    {view:'counties',label:'Counties'},
    {view:'coverage',label:'Coverage'},
    {view:'resources',label:'State resources',supplement:'doj_state_resource_map_20260919'}]},
  {id:'law',views:[
    {view:'regulations',label:'Law & regulations',segments:[
      {view:'regulations',label:'Code of Federal Regulations',hint:'Section text with amendment history',supplement:'federal_regulations_20260919'},
      {view:'federal-register',label:'Federal Register',hint:'Rules, proposed rules and notices, 1994 to 2026',supplement:'federal_register_history_20260919'},
      {view:'public-laws',label:'Public Laws & U.S. Code',hint:'Acts of Congress and the Code sections they change',supplement:'public_law_uscode_20260919'}]},
    {view:'agencies',label:'Agencies',segments:[
      {view:'agencies',label:'Agencies & safety data',hint:'Agency profiles, recalls, approvals, enforcement',supplement:'agency_safety_20260919'},
      {view:'agency-documents',label:'Agency & science documents',hint:'Downloaded reports, profiles and orders with full text',supplement:'agency_science_documents_20260919'},
      {view:'cpsc-injury-data',label:'Injury & incident data',hint:'Product injury surveillance records',supplement:'cpsc_injury_data_20260919'}]},
    {view:'sources',label:'Sources',segments:[
      {view:'sources',label:'Source directory',hint:'Curated official sources and APIs'},
      {view:'urls',label:'URL directory',hint:'Every known official address, by category and place',supplement:'url_directory_20260919'},
      {view:'saved-pages',label:'Saved web pages',hint:'Searchable text of captured court and government pages',supplement:'saved_web_pages_20260919'}]},
    {view:'documents',label:'All documents',segments:[
      {view:'documents',label:'Whole library',hint:'Every saved document, by jurisdiction and category'},
      {view:'federal',label:'Federal court & DOJ sources',hint:'Federal court and Justice Department references'}]}]},
  {id:'litigation',views:[
    {view:'judges',label:'Judges',segments:[
      {view:'judges',label:'Judge profiles',hint:'Current judges with appointments, MDLs and evidence'},
      {view:'people',label:'Historical biographies',hint:'Past and present judges, career and education records'},
      {view:'judge-disclosures',label:'Financial disclosures',hint:'Annual filings and holdings as filed',supplement:'judge_financial_disclosures_20260919'}]},
    {view:'mdls',label:'MDLs & mass torts',supplement:'jpml_mdl_20260919',segments:[
      {view:'mdls',label:'MDL registry',hint:'Pending multidistrict litigation with judges and counts',supplement:'jpml_mdl_20260919'},
      {view:'mdl-documents',label:'Docket documents',hint:'Orders and filings on the master dockets',supplement:'mdl_docket_documents_20260919'},
      {view:'mdl-activity',label:'Docket activity',hint:'Docket entries by type',supplement:'mdl_docket_activity_20260919'},
      {view:'mdl-cases',label:'Member cases',hint:'Cases in the saved docket sample',supplement:'mdl_case_inventory_20260919'},
      {view:'expert-rulings',label:'Expert challenges',hint:'Docket filings about expert admissibility',supplement:'expert_rulings_scan_20260919'},
      {view:'state-proceedings',label:'State mass torts',hint:'New Jersey MCL and California coordinated proceedings',supplement:'state_coordinated_proceedings_20260919'},
      {view:'settlements',label:'Settlement notices',hint:'Class and mass settlement notices with deadlines',supplement:'settlements_20260919'},
      {view:'verdict-reports',label:'Verdict & settlement reports',hint:'Publisher-reported results by state, year and amount',supplement:'verdict_settlement_reports_20260919'}]},
    {view:'courts',label:'Courts',supplement:'court_spine_20260919',segments:[
      {view:'courts',label:'Court registry',hint:'Every court with identifiers and marks',supplement:'court_spine_20260919'},
      {view:'court-documents',label:'Court documents',hint:'Forms, local rules, orders and fee schedules',supplement:'court_document_library_20260919'},
      {view:'uscourts',label:'U.S. Courts publications',hint:'Saved uscourts.gov pages and reports',supplement:'uscourts_pages_20260919'},
      {view:'statistics',label:'Court statistics',hint:'Caseload tables and per-judge reports',supplement:'federal_court_statistics_20260919'}]},
    {view:'counsel',label:'Counsel & firms',segments:[
      {view:'counsel-directory',label:'Firms & attorneys',hint:'Firms and counsel across the saved dockets',supplement:'counsel_directory_20260919'},
      {view:'counsel',label:'MDL master-docket counsel',hint:'Counsel recorded on six MDL master dockets',supplement:'mdl_counsel_20260919'},
      {view:'mdl-appearances',label:'Appearances by docket',hint:'Appearances and party counts in the saved release',supplement:'mdl_counsel_appearances_20260919'}]}]}
];"""
app = app[:start] + HUBS + app[end:]
# single-state code pages stay reachable by link but sit under State law
old_map = "({judge:'judges',person:'people',county:'counties',collection:'mdls',collections:'mdls',source:'sources',record:'documents'}[route.view]||route.view)"
new_map = "({judge:'judges',person:'people',county:'counties',collection:'mdls',collections:'mdls',source:'sources',record:'documents','indiana-code':'laws','sd-statutes':'laws','state-codes':'laws'}[route.view]||route.view)"
if new_map not in app:
    assert app.count(old_map) == 1
    app = app.replace(old_map, new_map)
# an extension area may sit under another tab: honour the remap for areas too
old_area = "const activeView=area?(area.parent||route.view):"
if old_area in app and "AREA_TAB" not in app:
    app = app.replace(old_area, "const AREA_TAB={'indiana-code':'laws','sd-statutes':'laws','state-codes':'laws'};const activeView=area?(AREA_TAB[route.view]||area.parent||route.view):", 1)
open(D + 'app.js', 'w', encoding='utf-8', newline='').write(app)

html = open(D + 'index.html', encoding='utf-8').read()
html = html.replace('<a href="#overview" data-hub="places"><span aria-hidden="true">◍</span> Map &amp; places</a>', '<a href="#overview" data-hub="places"><span aria-hidden="true">◍</span> States &amp; counties</a>')
html = html.replace('<a href="#laws" data-hub="law"><span aria-hidden="true">§</span> Law &amp; regulation</a>', '<a href="#regulations" data-hub="law"><span aria-hidden="true">§</span> Federal law &amp; agencies</a>')
open(D + 'index.html', 'w', encoding='utf-8', newline='').write(html)

areas = open(D + 'areas.js', encoding='utf-8').read()
# remove the single-state buttons from the state pages: the State law page already carries the full text for every state
for line in ("    if (abbr === 'SD') quick.append(routeLink('South Dakota Codified Laws (saved text)', 'sd-statutes', {}, 'button'));\n",
             "    if (abbr === 'IN') quick.append(routeLink('Indiana Code, 2026 edition (every section)', 'indiana-code', {}, 'button'));\n"):
    areas = areas.replace(line, '')
# new generic areas
if "view: 'counsel-directory'" not in areas:
    anchor = "    { view: 'coverage', title: 'Coverage & gaps',"
    assert areas.count(anchor) == 1
    areas = areas.replace(anchor,
        "    { view: 'counsel-directory', title: 'Firms & attorneys', nav: 'Firms & attorneys', supplement: 'counsel_directory_20260919', description: 'Law firms and counsel of record across the saved dockets, grouped by exact normalised firm name and native attorney ids.' },\n"
        "    { view: 'verdict-reports', title: 'Verdict & settlement reports', nav: 'Verdict reports', supplement: 'verdict_settlement_reports_20260919', description: 'Publisher-reported verdicts and settlements by state, year, practice area and amount. Not verified against court records.' },\n"
        "    { view: 'cpsc-injury-data', title: 'Injury & incident data', nav: 'Injury data', supplement: 'cpsc_injury_data_20260919', description: 'Consumer product injury surveillance records and incident reports as published.' },\n"
        "    { view: 'expert-rulings', title: 'Expert challenges', nav: 'Expert challenges', supplement: 'expert_rulings_scan_20260919', description: 'Docket filings about expert admissibility found in the saved dockets, with links to the docket.' },\n" + anchor)
    found = re.search(r"for \(const view of \[([^\]]*)\]\) if \(registry\[view\] && !registry\[view\]\.page\) registry\[view\]\.page = genericPage\(view\);", areas)
    assert found
    areas = areas.replace(found.group(0), found.group(0).replace(found.group(1), found.group(1) + ", 'counsel-directory', 'verdict-reports', 'cpsc-injury-data', 'expert-rulings'"))
open(D + 'areas.js', 'w', encoding='utf-8', newline='').write(areas)
print('round 8 navigation applied')
