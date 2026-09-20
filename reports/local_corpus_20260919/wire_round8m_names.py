"""Round 8m: vendor names leave the prose of three status/about responses at display time.

Only prose fields are rewritten (qualification, licence text, descriptions, notes). Identifiers, keys, file paths and source
addresses are untouched, and the on-disk validation files and READMEs keep the full attribution (the law snapshot stays
credited as "Open US Law", CC BY 4.0). Idempotent.
"""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'
text = open(D + 'server.py', encoding='utf-8').read()

helper = '''
PROSE_KEYS={'qualification','license_ref','license','licence','description','note','notes','attribution','label','title','summary'}
PROSE_NAMES=(('Open US Law index by Vaquill AI','Open US Law index'),('Open US Law by Vaquill AI','Open US Law'),('Vaquill AI / ',''),('Vaquill AI','the snapshot publisher'),('Vaquill','the snapshot publisher'),
             ('Trellis publisher page','Publisher page'),('Trellis publisher-reported','Publisher-reported'),('Trellis county-profile','county-profile'),('Trellis county profile','county court profile'),
             ('Trellis Law','the county directory publisher'),('Trellis','the county directory publisher'))
def display_prose(value,key=None):
    """Vendor names out of reader-facing prose; identifiers, paths and addresses are never touched."""
    if isinstance(value,dict):return {k:display_prose(v,k) for k,v in value.items()}
    if isinstance(value,list):return [display_prose(v,key) for v in value]
    if isinstance(value,str) and key in PROSE_KEYS and ('Trellis' in value or 'Vaquill' in value) and not value.startswith(('http://','https://','/')):
        for old,new in PROSE_NAMES:value=value.replace(old,new)
    return value

'''
if 'def display_prose(' not in text:
    anchor = 'def supplement_status(max_age=45):'
    assert text.count(anchor) == 1
    text = text.replace(anchor, helper.lstrip('\n') + anchor)
pairs = [
    ("                if path=='/api/coverage/matrix':return self.send_body(200,jurisdiction_coverage.matrix())",
     "                if path=='/api/coverage/matrix':return self.send_body(200,display_prose(jurisdiction_coverage.matrix()))"),
    ("                if path=='/api/regulations/info':return self.send_body(200,federal_regulations.info())",
     "                if path=='/api/regulations/info':return self.send_body(200,display_prose(federal_regulations.info()))"),
    ("        try:_SUPPLEMENT_CACHE['value']=supplements.status();_SUPPLEMENT_CACHE['at']=time.time()",
     "        try:_SUPPLEMENT_CACHE['value']=display_prose(supplements.status());_SUPPLEMENT_CACHE['at']=time.time()  # scrubbed once per scan, not per request"),
    ("                    return self.send_body(200,item) if item else self.send_body(404,{'error':'Supplement not found'})",
     "                    return self.send_body(200,display_prose(item)) if item else self.send_body(404,{'error':'Supplement not found'})"),
]
for old, new in pairs:
    if new in text:
        continue
    assert text.count(old) == 1, old[:80]
    text = text.replace(old, new)
open(D + 'server.py', 'w', encoding='utf-8', newline='').write(text)
print('prose names scrubbed at display time')
