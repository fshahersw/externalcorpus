import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('county_catalog_under_test',ROOT/'scripts'/'build_catalog.py')
catalog=importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogWebsiteFixtures(unittest.TestCase):
    def test_truncated_display_retained_and_observed_href_exported(self):
        source='https://trellis.law/coverage/arizona/apache'
        soup=catalog.BeautifulSoup('<section id="court-records"><div><h2>Website</h2><h3><a href="https://www.apachecountyaz.gov/">https://www.apachecountyaz.go\ufffd</a></h3></div></section>','html.parser')
        website,display,status,provenance=catalog.extract_website(soup,'',source,'fixture.firecrawl.json',{'website':'https://www.apachecountyaz.go\ufffd'})
        self.assertEqual(website,'https://www.apachecountyaz.gov/')
        self.assertEqual(display,'https://www.apachecountyaz.go\ufffd')
        self.assertEqual(status,'observed_href')
        self.assertFalse(provenance['site_authority_verified'])
        self.assertEqual(provenance['candidates'][0]['observed_href'],website)

    def test_ambiguous_and_truncated_only_fields_are_not_guessed(self):
        source='https://trellis.law/coverage/example/test'
        soup=catalog.BeautifulSoup('<h2>Website</h2><h3><a href="https://one.gov/">one</a><a href="https://two.gov/">two</a></h3>','html.parser')
        website,_,status,_=catalog.extract_website(soup,'',source,'fixture',{})
        self.assertIsNone(website)
        self.assertEqual(status,'ambiguous_multiple_hrefs')
        soup=catalog.BeautifulSoup('<h2>Website</h2><h3>https://county.go\u2026</h3>','html.parser')
        website,_,status,_=catalog.extract_website(soup,'',source,'fixture',{})
        self.assertIsNone(website)
        self.assertEqual(status,'invalid_or_internal_url')

    def test_version_change_reprocesses_unchanged_source_and_updates_exports(self):
        scratch=Path(__file__).parent/'_tmp'
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='catalog-',dir=scratch) as temporary:
            root=Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(scratch.resolve()))
            source=root/'sources'/'trellis'/'counties'/'arizona_apache.firecrawl.json'
            source.parent.mkdir(parents=True)
            source.write_text(json.dumps({'metadata':{'sourceURL':'https://trellis.law/coverage/arizona/apache','statusCode':200,'title':'Apache County Superior Records'},'html':'<section id="court-records"><h2>Website</h2><h3><a href="https://www.apachecountyaz.gov/">https://www.apachecountyaz.go\ufffd</a></h3></section>','markdown':'','links':[]}),encoding='utf-8')
            out=root/'sources'/'trellis'/'catalog'
            with contextlib.redirect_stdout(io.StringIO()):catalog.main(root)
            self.assertEqual(json.loads((out/'summary.json').read_text())['processed_this_pass'],1)
            with contextlib.redirect_stdout(io.StringIO()):catalog.main(root)
            self.assertEqual(json.loads((out/'summary.json').read_text())['processed_this_pass'],0)
            con=sqlite3.connect(out/'catalog.sqlite3')
            con.execute("UPDATE pages SET extraction_version='legacy'")
            con.execute("UPDATE counties SET official_website='https://broken.go'")
            con.commit();con.close()
            with contextlib.redirect_stdout(io.StringIO()):catalog.main(root)
            summary=json.loads((out/'summary.json').read_text())
            self.assertEqual(summary['processed_this_pass'],1)
            exported=json.loads((out/'official_county_websites.jsonl').read_text(encoding='utf-8').splitlines()[0])
            self.assertEqual(exported['url'],'https://www.apachecountyaz.gov/')
            self.assertEqual(exported['displayed_value'],'https://www.apachecountyaz.go\ufffd')
            self.assertEqual(exported['extraction_version'],catalog.EXTRACTION_VERSION)


if __name__=='__main__':unittest.main(verbosity=2)
