"""Remove vendor names from what the interface shows. Identifiers, routes, file paths, error messages raised during validation
and on-disk licence/README files are left alone; attribution stays recorded in the data folders' own README/licence files."""
import re

D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'

JS_PHRASES = [
    ('Counties with matched Trellis profiles', 'Counties with a matched court profile'),
    ('County website listed by Trellis ↗', 'County website listed in the saved profile ↗'),
    ('County website reported by Trellis ↗', 'County website reported in the saved profile ↗'),
    ('Links listed in the saved Trellis profile;', 'Links listed in the saved county profile;'),
    ('Refreshed Trellis county details are temporarily unavailable.', 'Refreshed county profile details are temporarily unavailable.'),
    ('Trellis county profile', 'County court profile'),
    ('Trellis lists this county in its saved state coverage response.', 'This county appears in the saved statewide coverage list.'),
    ('Trellis reports document coverage for this county.', 'The saved coverage list reports document coverage for this county.'),
    ('Trellis county backfill', 'County profile backfill'),
    ('Trellis profile coverage refreshed', 'County profile coverage refreshed'),
    ('Unsaved Trellis county profiles', 'Counties without a saved court profile'),
    ('With saved Trellis profile', 'With a saved court profile'),
]
for name in ('app.js', 'areas.js'):
    text = open(D + name, encoding='utf-8').read()
    for old, new in JS_PHRASES:
        text = text.replace(old, new)
    # any remaining capitalised mention inside display text
    text = re.sub(r'\bTrellis(?=[ \'’.,;:)])', 'the county directory', text)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)
    print(name, 'remaining capitalised mentions:', len(re.findall(r'Trellis', text)))

PY = {
    'server.py': [
        ("'Trellis county profile backfill'", "'County court profile backfill'"),
        ("('Has refreshed Trellis details',", "('Has refreshed county profile details',"),
        ("'attribution':'Vaquill AI / o", None),  # handled by regex below
        ("'description':'Vaquill AI snapshot with verified file checksums:", "'description':'Structured law snapshot with verified file checksums:"),
    ],
    'federal_regulations.py': [("'Open US Law index by Vaquill AI (CC BY 4.0):", "'Open US Law index (CC BY 4.0):")],
    'trellis_coverage.py': [("LABEL = 'Trellis publisher-reported coverage metadata; internal research use; not for redistribution'", "LABEL = 'Publisher-reported coverage metadata; internal research use; not for redistribution'")],
}
for name, pairs in PY.items():
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if new is not None:
            text = text.replace(old, new)
    text = re.sub(r"'attribution':'Vaquill AI / ([^']*)'", r"'attribution':'\1'", text)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)
text = open(D + 'bulk_laws.py', encoding='utf-8').read()
text = re.sub(r"'attribution':'Vaquill AI / ([^']*)'", r"'attribution':'\1'", text)
open(D + 'bulk_laws.py', 'w', encoding='utf-8', newline='').write(text)
print('vendor names removed from display text')
