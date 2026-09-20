import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('geography_under_test',HERE/'reconcile_counties.py')
geography=importlib.util.module_from_spec(spec)
spec.loader.exec_module(geography)


def county(state,usps,geoid,name):
    return {'state':state,'usps':usps,'state_fips':geoid[:2],'county_fips':geoid[2:],'geoid':geoid,'name':name,'geography_vintage':2026}


class GeographyFixtures(unittest.TestCase):
    def setUp(self):
        self.index=geography.GeographyIndex([
            county('Virginia','VA','51159','Richmond County'),county('Virginia','VA','51760','Richmond city'),
            county('Virginia','VA','51810','Virginia Beach city'),county('Connecticut','CT','09110','Capitol Planning Region'),
            county('Delaware','DE','10003','New Castle County'),county('District of Columbia','DC','11001','District of Columbia'),
            county('Arkansas','AR','05123','St. Francis County'),
            county('Florida','FL','12001','Alachua County'),
            county('Virginia','VA','51036','Charles City County'),county('Virginia','VA','51095','James City County'),
            county('Florida','FL','12063','Jackson County'),county('Florida','FL','12115','Sarasota County'),
        ])

    def match(self,state,slug,title):
        return self.index.match({'url':f'https://trellis.law/coverage/{state}/{slug}','state':state,'county_slug':slug,'title':title})

    def test_independent_city_county_collision_requires_explicit_type(self):
        unclear=self.match('virginia','richmond','Richmond Court Records')
        self.assertEqual(unclear['match_status'],'ambiguous')
        self.assertIsNone(unclear['census_geoid'])
        self.assertEqual(set(unclear['candidate_geoids']),{'51159','51760'})
        self.assertEqual(self.match('virginia','richmond','Richmond County Circuit Records')['census_geoid'],'51159')
        self.assertEqual(self.match('virginia','richmond-city','Richmond City Circuit Records')['census_geoid'],'51760')

    def test_wrong_entity_type_does_not_get_unique_name_match(self):
        record=self.match('virginia','virginia-beach','Virginia Beach County Court Records')
        self.assertEqual(record['match_status'],'ambiguous')
        self.assertIsNone(record['census_geoid'])

    def test_embedded_city_word_does_not_override_explicit_county_suffix(self):
        # Exact title from the current Charles City County provider capture.
        title='Charles City County Circuit Records | Charles City County, VA Case & Docket Search | Trellis.Law'
        self.assertEqual(geography.title_identity(title),('Charles City','county'))
        result=self.match('virginia','charlescity',title)
        self.assertEqual(result['match_status'],'matched')
        self.assertEqual(result['census_geoid'],'51036')
        self.assertEqual(result['title_name'],'Charles City')
        # A second real Census name verifies this is not a one-county override.
        self.assertEqual(self.match('virginia','jamescity','James City County Circuit Courts Records')['census_geoid'],'51095')

    def test_city_and_compound_entity_headings_preserve_their_types(self):
        for title,expected in (
            ('Richmond City Circuit Records',('Richmond','independent_city')),
            ('City of Richmond Circuit Records',('Richmond','independent_city')),
            ('Juneau City and Borough Superior Records',('Juneau','city_and_borough')),
            ('Capitol Planning Region Records',('Capitol','planning_region')),
        ):
            with self.subTest(title=title):self.assertEqual(geography.title_identity(title),expected)
        conflict=self.match('virginia','charlescity','Charles City City Circuit Records')
        self.assertEqual(conflict['match_status'],'ambiguous')
        self.assertEqual(conflict['reason'],'explicit_title_entity_type_conflicts_with_census_type')
        self.assertIsNone(conflict['census_geoid'])

    def test_current_florida_title_conflicts_remain_unmatched(self):
        for slug,title in (
            ('jackson','The 14th Judicial Circuit of Florida - Washington County Court Case Search | Trellis.Law'),
            ('sarasota','The 12th Judicial Circuit of Florida - Manatee County Court Case Search | Trellis.Law'),
        ):
            with self.subTest(slug=slug):
                result=self.match('florida',slug,title)
                self.assertEqual(result['match_status'],'ambiguous')
                self.assertEqual(result['reason'],'title_name_and_county_slug_conflict')
                self.assertIsNone(result['census_geoid'])

    def test_connecticut_old_county_is_not_assigned_to_planning_region(self):
        record=self.match('connecticut','hartford','Hartford County Superior Records')
        self.assertEqual(record['match_status'],'non_census_jurisdiction')
        self.assertIsNone(record['census_geoid'])
        exact=self.match('connecticut','capitol-planning-region','Capitol Planning Region Records')
        self.assertEqual(exact['census_geoid'],'09110')

    def test_special_court_dc_and_explicit_spelling_variant(self):
        court=self.match('delaware','courtofchancery','Court of Chancery Superior Records')
        self.assertEqual(court['match_status'],'non_census_jurisdiction')
        self.assertIsNone(court['census_geoid'])
        self.assertEqual(self.match('district-of-columbia','district-of-columbia','District of Columbia Superior Records')['census_geoid'],'11001')
        self.assertEqual(self.match('arkansas','saintfrancis','St. Francis County Circuit Records')['census_geoid'],'05123')
        self.assertEqual(self.match('delaware','newcastle','New Castle County Superior Records')['census_geoid'],'10003')

    def test_bad_website_values_stay_unresolved(self):
        self.assertIsNone(geography.url_value('https://www.county.go\ufffd')[0])
        self.assertIsNone(geography.url_value('https://www.county.go\u2026')[0])
        self.assertIsNone(geography.url_value('javascript:alert(1)')[0])
        self.assertIsNone(geography.url_value('https://user:pass@county.gov/')[0])
        self.assertEqual(geography.url_value('https://www.county.gov')[0],'https://www.county.gov/')

    def test_circuit_prefix_is_preserved_separately_from_county_name(self):
        record=self.match('florida','alachua','The 8th Judicial Circuit of Florida - Alachua County Court Case Search | Trellis.Law')
        self.assertEqual(record['census_geoid'],'12001')
        self.assertEqual(record['source_court_scope'],'The 8th Judicial Circuit of Florida')
        self.assertEqual(record['title_name'],'Alachua')
        wrong=self.match('florida','alachua','The 8th Judicial Circuit of Florida - Baker County Court Case Search')
        self.assertEqual(wrong['match_status'],'ambiguous')
        self.assertIsNone(wrong['census_geoid'])


if __name__=='__main__':unittest.main(verbosity=2)
