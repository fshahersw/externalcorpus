import json,unittest
from pathlib import Path
from classify import classify,classify_link
ROOT=Path(__file__).resolve().parents[2]
CHECKPOINT=ROOT/'sources/county_litigation_firecrawl_20260919/checkpoints/20260919T100728840281Z/resources.jsonl'

class ClassifierTests(unittest.TestCase):
    def test_incidental_rule_citation_is_not_page_purpose(self):
        c=classify('Family Law Records | Superior Court of California | County of Orange','Family Law Records\nCalifornia Rules of Court prohibit viewing confidential records. Effective January 1, 2019 is the cited law date.','https://www.occourts.org/divisions/family-law/family-law-records','text/html')
        self.assertEqual(c['resource_type'],'court_information');self.assertEqual(c['legal_status'],'unknown')
    def test_word_boundary(self):
        self.assertEqual(classify_link('Court Information','https://court.example/information')['resource_type'],'court_information')
    def test_real_pilot_regressions(self):
        rows=[json.loads(x) for x in CHECKPOINT.read_text(encoding='utf8').splitlines()]
        expected={'/rules-court':('local_rule','rule_index'),'/l1018.pdf':('court_information','records_retention_guidance'),'/l1038.pdf':('court_form','form_document'),'/index.pdf':('local_rule','rule_index'),'/memo-local-rules.pdf':('local_rule','rule_change_notice')}
        for suffix,pair in expected.items():
            row=next(r for r in rows if r['source_url'].endswith(suffix));text=(ROOT/row['text_path']).read_text(encoding='utf8')
            title=(row.get('seed_provenance') or {}).get('anchor_text') if row['mime_type']=='application/pdf' else row['title']
            result=classify(title or row['title'],text,row['source_url'],row['mime_type'])
            with self.subTest(url=row['source_url']):self.assertEqual((result['resource_type'],result['document_shape']),pair)
        row=next(r for r in rows if r['source_url'].endswith('/09div4.pdf'))
        result=classify(row['title'],(ROOT/row['text_path']).read_text(),row['source_url'],row['mime_type'])
        self.assertEqual(result['legal_status'],'repealed_as_published')
    def test_navigation_and_cited_rule_are_not_body(self):
        result=classify('Rules of Court | Superior Court','See California Rule 10.855.\n[Division 10 - LOCAL EMERGENCY RULE 1](division10.pdf)\n'+'navigation '*400,'https://court.example/rules-court','text/html')
        self.assertEqual(result['document_shape'],'rule_index')

if __name__=='__main__':unittest.main()
