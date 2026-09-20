"""One-off wiring of the downloaded agency and science documents page. Idempotent."""
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
    ("'mdl-crosswalk':'mdl_crosswalk','mdl_crosswalk':'mdl_crosswalk','sd-statutes':'sd_statutes','sd_statutes':'sd_statutes'}",
     "'mdl-crosswalk':'mdl_crosswalk','mdl_crosswalk':'mdl_crosswalk','sd-statutes':'sd_statutes','sd_statutes':'sd_statutes',\n"
     "               'agency-documents':'agency_science_documents','agency_science_documents':'agency_science_documents'}"),
])
edit('areas.js', [
    ("    { view: 'coverage', title: 'Coverage & gaps',",
     "    { view: 'agency-documents', title: 'Agency & science documents', nav: 'Agency documents', supplement: 'agency_science_documents_20260919', description: 'Toxicological profiles, safety reports, recall and investigation files and JPML orders downloaded from official agency and science sites, with searchable text and the saved original.' },\n"
     "    { view: 'coverage', title: 'Coverage & gaps',"),
    ("'mdl-cases', 'mdl-appearances', 'mdl-documents', 'mdl-activity', 'sd-statutes'])", "'mdl-cases', 'mdl-appearances', 'mdl-documents', 'mdl-activity', 'sd-statutes', 'agency-documents'])"),
])
edit('app.js', [
    ("['agencies','Agencies & safety','agency_safety_20260919'],", "['agencies','Agencies & safety','agency_safety_20260919'],['agency-documents','Agency documents','agency_science_documents_20260919'],"),
])
print('wired')
