"""Deterministic, evidence-returning litigation classification; no network."""
import re
from urllib.parse import urlsplit
VERSION='county-litigation-classifier-2'
KINDS={'local_rule','court_form','standing_order','filing_guidance','fee_schedule','court_information','court_contact','court_staff','source_directory','unknown'}
COURT=re.compile(r'\b(?:(?:superior|circuit|district|municipal|probate|family|juvenile|civil|criminal|county)\s+court|clerk of (?:the )?court|court clerk|judicial circuit|judicial district)\b',re.I)
EXCLUDE=re.compile(r'\b(?:election|voter|candidate filing|driver.?s? licen[sc]e|business licen[sc]e|tax assessor|property tax|recreation|parks?|camping|animal control|building permit|employment application|job application|commissioners? (?:meeting|calendar))\b',re.I)

def evidence(pattern,text,label):
    match=re.search(pattern,text,re.I)
    return {'field':label,'excerpt':text[max(0,match.start()-90):min(len(text),match.end()+180)],'offset':match.start()} if match else None

def classify_link(anchor,url):
    value=' '.join((anchor or '').split());combined=value+' '+urlsplit(url).path
    if EXCLUDE.search(combined):return {'resource_type':'unknown','eligible':False,'reason':'Non-litigation administrative topic','priority':99}
    checks=[('local_rule',r'local.?rules?|rules? of (?:practice|court)',1),('standing_order',r'standing.?orders?|administrative.?orders?|general.?orders?',1),
            ('fee_schedule',r'(?:court|filing|civil).{0,20}fees?|fee.?schedule',2),('filing_guidance',r'e.?filing|filing.{0,20}(?:guide|procedure|instruction)|how to file',2),
            ('court_form',r'court.{0,25}\bforms?\b|(?:civil|criminal|family|probate|juvenile).{0,20}\bforms?\b|\bforms?\b.{0,20}(?:court|civil)|/forms?/',2),
            ('court_contact',r'(?:court|clerk).{0,25}contact|contact.{0,25}(?:court|clerk)',3),('court_information',r'court|circuit clerk|law.?justice',3)]
    for kind,pattern,priority in checks:
        if re.search(pattern,combined,re.I):return {'resource_type':kind,'eligible':True,'reason':'Observed anchor/path topic; destination content must be reviewed','priority':priority}
    return {'resource_type':'unknown','eligible':False,'reason':'No explicit litigation signal in observed anchor/path','priority':99}

def classify(title,text,url='',mime_type='',links=None):
    title=title or '';text=text or '';head=title+'\n'+text[:10000];binary=mime_type in {'application/pdf','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/rtf'}
    # Page purpose comes from the title/path, not incidental citations or a shared
    # navigation menu. Native documents may additionally use their opening caption.
    topic=title+'\n'+urlsplit(url).path.replace('_',' ').replace('-',' ')+(('\n'+text[:650]) if binary else '')
    court=bool(COURT.search(head))
    # A citation embedded in a paragraph or linked index caption is not a rule
    # heading. Actual line-start headings are necessary for a rule-body claim.
    headings=re.findall(r'(?im)^\s*(?:RULE|LCR|LAR|LSPR|CrR|LR)\s*\d[.\d]*(?:\s|[.:(])[^\n]{0,130}',text)
    rule_structure=bool(headings)
    index_topic=bool(re.search(r'\b(?:table of contents|index)\b',title,re.I) or re.search(r'/(?:index|table.of.contents)\.pdf$',url,re.I))
    retention_topic=bool(re.search(r'(?:court )?(?:file|record)s? retention|retention time frames',topic,re.I))
    blank_form=binary and re.search(r'FOR COURT USE ONLY|ATTORNEY OR PARTY WITHOUT ATTORNEY',text[:2500],re.I) and re.search(r'\(Name|TELEPHONE NO|_{4,}',text[:2500],re.I)
    kind='unknown';shape='unclassified';reason=None
    if re.search(r'(?:verify you are human|access denied|checking your browser|just a moment)',text[:400],re.I) and len(text)<2500:
        return {'resource_type':'unknown','document_shape':'access_error','legal_status':'unknown','status':'needs_review','substantive':False,'evidence':[{'excerpt':text[:400],'field':'access_barrier'}],'version':VERSION}
    if EXCLUDE.search(title) and not re.search(r'local rules|standing order',title,re.I):reason='Non-litigation administrative title'
    elif court and retention_topic:
        kind='court_information';shape='records_retention_guidance';reason=evidence(r'(?:file|record)s? retention|retention time frames',head,'document_purpose')
    elif court and blank_form:
        kind='court_form';shape='form_document';reason=evidence(r'FOR COURT USE ONLY|ATTORNEY OR PARTY WITHOUT ATTORNEY',head,'blank_form_template')
        if re.search(r'\bFILED\s+(?:\d{1,2}[/-]|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))',text[:800],re.I):
            kind='unknown';shape='possible_filed_pleading'
    elif re.search(r'local\s+(?:court\s+)?rules|rules of (?:practice|court)|rules court|/rules(?:/|$)|/local.rules/',topic,re.I) or (binary and court and rule_structure):
        kind='local_rule';shape='rule_index' if index_topic else 'rule_body' if rule_structure and len(text)>200 and (binary or len(headings)>=2) else 'rule_index'
        if re.search(r'rules affected by|memo.local.rules',title+' '+url,re.I):shape='rule_change_notice'
        elif re.search(r'preface|civility guidelines',title,re.I):shape='rule_preface'
        reason=evidence(r'local\s+(?:court\s+)?rules|rules of (?:practice|court)|\bRULE\s+\d',head,'rule_topic')
    elif court and re.search(r'standing order|administrative order|general order|notices orders',topic,re.I):
        kind='standing_order';shape='order_body' if binary or re.search(r'IT IS (?:HEREBY )?ORDERED',text,re.I) else 'order_index';reason=evidence(r'standing order|administrative order|general order',head,'order_topic')
    elif court and re.search(r'fee schedule|filing fees?|court fees?',topic,re.I):
        kind='fee_schedule';shape='fee_table' if re.search(r'\$\s*\d',text) else 'fee_information';reason=evidence(r'fee schedule|filing fees?|court fees?',head,'fee_topic')
    elif court and re.search(r'e.?filing|filing (?:instructions|procedures|requirements)|how to file|filing guide',topic,re.I):
        kind='filing_guidance';shape='guide';reason=evidence(r'e.?filing|filing (?:instructions|procedures|requirements)|how to file|filing guide',head,'filing_guidance_topic')
    elif court and ((re.search(r'\bforms?\b|petition|summons|motion',topic,re.I) and (re.search(r'/forms?(?:/|-)',url,re.I) or re.search(r'\bforms?\b|blank|template',title,re.I))) or
                    (binary and re.search(r'FOR COURT USE ONLY|ATTORNEY OR PARTY WITHOUT ATTORNEY',text[:2500],re.I) and re.search(r'\(Name|TELEPHONE NO|_{4,}',text[:2500],re.I))):
        kind='court_form';shape='form_document' if binary else 'form_directory';reason=evidence(r'forms?|petition|summons|motion',head,'form_topic')
        if binary and re.search(r'\bFILED\s+(?:\d{1,2}[/-]|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))',text[:800],re.I):
            kind='unknown';shape='possible_filed_pleading';reason={'excerpt':text[:800],'field':'filed_mark_requires_review'}
    elif court and (re.search(r'contact|phone|telephone|hours of operation|office hours|clerk',topic,re.I)):
        kind='court_contact';shape='contact_page';reason=evidence(r'contact|phone|telephone|hours of operation|office hours|clerk of court',head,'contact_topic')
    elif court and re.search(r'staff directory|court staff|judicial staff',topic,re.I):
        kind='court_staff';shape='staff_directory';reason=evidence(r'staff directory|court staff|judicial staff',head,'staff_topic')
    elif court:
        kind='court_information';shape='records_access_guidance' if re.search(r'\brecords\b',title,re.I) else 'information_page';reason=evidence(COURT.pattern,head,'court_context')
    elif re.search(r'county|government|law.?justice',title,re.I):kind='source_directory';shape='directory';reason={'excerpt':title,'field':'source_title'}
    if isinstance(reason,str):reason={'excerpt':title,'field':'exclusion','note':reason}
    if not reason:reason={'excerpt':title,'field':'insufficient_topic_evidence'}
    legal_status='unknown';status_evidence=[]
    if kind in {'local_rule','standing_order'}:
        repealed=re.search(r'(?im)^\s*(?!rule\b)(?:[A-Z][A-Z ()\d,$/–—-]+)\s*[–—-]\s*Repealed\s*$',text[:600])
        if repealed:
            legal_status='repealed_as_published';status_evidence=[{'field':'opening_document_caption','excerpt':repealed.group(0).strip(),'offset':repealed.start()}]
        elif re.search(r'\b(?:draft|proposed|request for comments|public comment)\b',title,re.I):
            legal_status='draft';status_evidence=[{'field':'document_title','excerpt':title}]
        elif shape in {'rule_body','order_body'}:
            match=re.search(r'(?im)^\s*(effective|adopted)(?:\s+(?:date|on|as of))?\s*[:\-]?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|\d)[^\n]{0,65}',text[:1800])
            if match:
                legal_status='effective_as_published' if match.group(1).lower()=='effective' else 'adopted'
                status_evidence=[{'field':'explicit_document_header_date_label','excerpt':match.group(0).strip(),'offset':match.start()}]
    return {'resource_type':kind,'document_shape':shape,'legal_status':legal_status,'legal_status_evidence':status_evidence,'status':'deterministic_content_classification' if kind!='unknown' else 'needs_review','substantive':shape in {'rule_body','order_body','fee_table','guide','form_document'},'evidence':[reason],'version':VERSION}
