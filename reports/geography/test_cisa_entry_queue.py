import importlib.util
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('cisa_entry_queue_under_test',HERE/'prepare_cisa_county_entries.py')
queue=importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


class CisaEntryFixtures(unittest.TestCase):
    def test_domains_deduplicate_and_exact_exclusions_and_host_pairs_apply(self):
        rows=[{'domain':domain,'usps':'CA','organization':'Example County','candidate_geoid':'06075','discovered_from':'https://registry.example.gov/source'} for domain in ['new.gov','new.gov','captured.gov','queued.gov','paused.gov','http-only.gov']]
        seeds,decisions,invalid,config=queue.make_queue(rows,'snapshot-sha',{'https://captured.gov/':[{'status':'downloaded'}],'http://http-only.gov/':[{'status':'downloaded'}]},{'https://queued.gov/':[{'status':'pending'}]},{'www.paused.gov':[{'pause_reason':'forbidden'}]})
        self.assertEqual({seed['url'] for seed in seeds},{'https://new.gov/','https://http-only.gov/'})
        self.assertEqual(len(decisions),5)
        self.assertEqual(invalid,[])
        self.assertEqual(next(row for row in decisions if row['domain']=='new.gov')['registry_records'],2)
        self.assertFalse(config['follow_links'])
        self.assertEqual(config['max_depth'],0)
        self.assertEqual({row['host'] for row in config['allow']},{'new.gov','www.new.gov','http-only.gov','www.http-only.gov'})
        for seed in seeds:
            self.assertEqual(seed['county_name_association'],'UNREVIEWED')
            self.assertFalse(seed['court_fips_association_verified'])
            self.assertNotIn('geoid',seed['jurisdiction'])
            self.assertIn('candidate_geoid',seed['unreviewed_registry_county_hints'][0])
            self.assertNotIn('scope',seed)


if __name__=='__main__':unittest.main(verbosity=2)
