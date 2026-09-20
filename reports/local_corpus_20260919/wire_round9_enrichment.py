"""Round 9 (2026-09-20): open-source enrichment layers wired into the server. Idempotent; asserts every anchor.

  citation guide (reporters-db)          /api/area/citation-guide
  limitation periods                     /api/area/limitation-periods, state-page block
  citation index (eyecite)               /api/area/citation-index, /api/citations/record, authorities inside saved documents
  court reference + seals (courts-db)    merged into the court registry detail, /supplement-files/court_reference/<id>, /api/court-resolve
  judge portraits (judge-pics)           photo_url on biographies and judge profiles, /supplement-files/judge_portraits/<id>
"""
D = 'C:/Users/firas/Downloads/SCRAPE/delivery/archive-directory/'


def edit(name, pairs):
    text = open(D + name, encoding='utf-8').read()
    for old, new in pairs:
        if (new and new in text) or (not new and old not in text):
            continue
        assert text.count(old) == 1, (name, old[:90], text.count(old))
        text = text.replace(old, new)
    open(D + name, 'w', encoding='utf-8', newline='').write(text)


edit('server.py', [
    ("               'source-documents':'source_documents','source_documents':'source_documents'}",
     "               'source-documents':'source_documents','source_documents':'source_documents',\n"
     "               'citation-guide':'citation_reference','citation_reference':'citation_reference','limitation-periods':'limitation_periods','limitation_periods':'limitation_periods',\n"
     "               'citation-index':'citation_index','citation_index':'citation_index','court_reference':'court_reference','judge_portraits':'judge_portraits'}\n"
     "# Saved-document areas whose records carry a list of the authorities they cite (citation index layer name).\n"
     "CITED_IN_AREAS={'agency-documents':'agency-documents','agency_science_documents':'agency-documents','source-documents':'source-documents','source_documents':'source-documents',\n"
     "                'uscourts':'uscourts','uscourts_pages':'uscourts','saved-pages':'saved-pages','saved_pages':'saved-pages'}\n"
     "def enrich_generic_item(name,record_id,item):\n"
     "    \"\"\"Optional additions to one generic record; every layer is lazy and failure-tolerant, and none can remove what the adapter returned.\"\"\"\n"
     "    try:\n"
     "        if name in ('courts','court_spine'):\n"
     "            extra=judge_layer('court_reference','for_court',record_id)\n"
     "            if extra:\n"
     "                item['facts']=list(item.get('facts') or [])+[f for f in extra['facts'] if f[0] not in {x[0] for x in item.get('facts') or []}]\n"
     "                item['sections']=extra['sections'][:1]+list(item.get('sections') or [])+extra['sections'][1:]\n"
     "        elif name in CITED_IN_AREAS:\n"
     "            cited=None\n"
     "            try:\n"
     "                import importlib\n"
     "                cited=importlib.import_module('citation_index').for_document(CITED_IN_AREAS[name],record_id)\n"
     "            except Exception:cited=None\n"
     "            if cited and cited.get('results'):\n"
     "                item['sections']=list(item.get('sections') or [])+[{'heading':'Authorities cited in this document (%d)'%cited['total'],'items':cited['results'][:40]}]\n"
     "    except Exception:pass\n"
     "    return item"),
    ("                    item=adapter.detail(p.get('id',''))\n                    return self.send_body(200,item) if item else self.send_body(404,{'error':'Record not found'})\n                return self.send_body(200,adapter.listing(p))",
     "                    item=adapter.detail(p.get('id',''))\n                    return self.send_body(200,enrich_generic_item(name,p.get('id',''),item)) if item else self.send_body(404,{'error':'Record not found'})\n                return self.send_body(200,adapter.listing(p))"),
    ("            if path.startswith('/api/law-outline'):\n",
     "            if path=='/api/court-resolve':\n"
     "                # Which courts a caption string can mean (courts-db matcher); absent layer -> available:false.\n"
     "                return self.send_body(200,judge_layer('court_reference','resolve',p.get('q','')) or {'available':False,'results':[]})\n"
     "            if path=='/api/citations/record':\n"
     "                # Saved documents that cite one provision of the saved law text.\n"
     "                return self.send_body(200,judge_layer('citation_index','for_record',p.get('id','')) or {'available':False,'total':0,'results':[]})\n"
     "            if path.startswith('/api/law-outline'):\n"),
    ("'court_documents':judge_layer('court_documents','for_state',p.get('state')),'saved_pages':judge_layer('saved_pages','for_state',p.get('state'))})",
     "'court_documents':judge_layer('court_documents','for_state',p.get('state')),'saved_pages':judge_layer('saved_pages','for_state',p.get('state')),'limitation_periods':judge_layer('limitation_periods','for_state',p.get('state'))})"),
    ("                person=people.profile(p.get('id',''))\n                return self.send_body(200,person) if person else self.send_body(404,{'error':'Biographical record not found'})",
     "                person=people.profile(p.get('id',''))\n"
     "                if person:person.update(judge_layer('judge_portraits','for_person',p.get('id','')) or {})\n"
     "                return self.send_body(200,person) if person else self.send_body(404,{'error':'Biographical record not found'})"),
    ("            if path=='/api/people':return self.send_body(200,people.listing(p))",
     "            if path=='/api/people':\n"
     "                listing=people.listing(p)\n"
     "                for row in listing.get('items') or []:row.update(judge_layer('judge_portraits','for_person',row.get('id')) or {})\n"
     "                return self.send_body(200,listing)"),
    ("            if path=='/api/judges':return self.send_body(200,judges.listing(p))",
     "            if path=='/api/judges':\n"
     "                listing=judges.listing(p)\n"
     "                for row in listing.get('items') or []:\n"
     "                    if not row.get('photo_url'):row.update({k:v for k,v in (judge_layer('judge_portraits','for_judge',row.get('entity_id') or row.get('id')) or {}).items()})\n"
     "                return self.send_body(200,listing)"),
    ("                    profile['disclosures']=judge_layer('judge_disclosures','for_judge',profile.get('entity_id') or p.get('id',''))\n",
     "                    profile['disclosures']=judge_layer('judge_disclosures','for_judge',profile.get('entity_id') or p.get('id',''))\n"
     "                    if not profile.get('photo_url'):profile.update(judge_layer('judge_portraits','for_judge',profile.get('entity_id') or p.get('id','')) or {})\n"),
])
print('round 9 server wiring applied')
