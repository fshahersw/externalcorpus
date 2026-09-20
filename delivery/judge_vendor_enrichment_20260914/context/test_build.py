"""Offline regressions for visibility, source attribution, and literal evidence."""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('context_preview_build', Path(__file__).with_name('build.py'))
b = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = b
SPEC.loader.exec_module(b)


class ContextPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.caps = {key: b.Capture(key) for key in b.FILES}
        cls.facts, cls.areas, cls.professional, cls.hidden, cls.court = b.extract_overview(cls.caps['overview'])
        cls.motions, cls.breakdowns, cls.method = b.extract_motion(cls.caps['motions'], cls.caps['motion_method'])
        cls.opinions = b.extract_citations(cls.caps['opinions'], 'opinion')
        cls.judges = b.extract_citations(cls.caps['judges'], 'judge')

    def test_only_observed_visible_area_rows_are_measures(self):
        self.assertEqual([a['label'] for a in self.areas], ['Civil Procedure', 'Business & Corporate Compliance', 'Governments', 'Torts', 'Constitutional Law'])
        self.assertEqual(len(self.hidden), 5)
        self.assertTrue(all('class="hidden"' in h['evidence']['quote'] for h in self.hidden))

    def test_hidden_ancestor_is_enforced(self):
        tree = b.IndexedHTML('<div hidden><li>A</li></div><div style="display: none"><li>B</li></div><li>C</li>')
        self.assertEqual([tree.visible(n) for n in tree.nodes if n.tag == 'li'], [False, False, True])

    def test_missing_outcome_is_unknown_not_zero(self):
        by = {g['motion_type']: g for g in self.breakdowns}
        self.assertIsNone(by['motion for remand']['reported_outcomes']['partial grant'])
        self.assertIsNone(by['motion for sanctions']['reported_outcomes']['granted'])
        self.assertEqual(sum(v is None for g in by.values() for v in g['reported_outcomes'].values()), 120)

    def test_chart_and_result_list_remain_distinct(self):
        dismissal = [a for a in self.motions if a.get('motion_type') == 'motion to dismiss']
        self.assertEqual(next(a['value'] for a in dismissal if a['metric'] == 'motion_type_cases'), 542)
        self.assertEqual(next(a['value'] for a in dismissal if a['metric'] == 'motion_case_result_list_count'), 489)
        self.assertTrue(all(a['denominator'] is None for a in dismissal))

    def test_wrong_post_click_tab_rejected(self):
        stale = copy.copy(self.caps['motions'])
        data = json.loads((b.SOURCES / 'sabraw_motion_browser.capture.json').read_text(encoding='utf-8-sig'))
        stale.text = data['response']['stdout']
        with self.assertRaisesRegex(AssertionError, 'required rendered heading'):
            b.extract_motion(stale, self.caps['motion_method'])

    def test_duplicate_citation_labels_have_separate_native_ids(self):
        dup = [a for a in self.opinions if a['label'] == 'Andrews v. Cervantes']
        self.assertEqual([a['value'] for a in dup], [72, 71])
        self.assertNotEqual(dup[0]['analysis_id'], dup[1]['analysis_id'])
        self.assertTrue(all(a['referenced_entity']['resolved_identity'] is None for a in dup))

    def test_cited_judges_are_not_the_metric_subject(self):
        first = self.judges[0]
        self.assertEqual((first['label'], first['value']), ('Anthony M. Kennedy', 834))
        self.assertEqual(first['source_observation_id'], b.NATIVE_ID)
        self.assertEqual(first['referencing_judge'], 'Dana M. Sabraw')
        self.assertEqual(first['referenced_entity']['entity_type'], 'judge')
        self.assertEqual(next(a['value'] for a in self.judges if a['label'] == b.NAME), 217)

    def test_professional_history_stays_with_its_labeled_card(self):
        education = [x['as_reported'] for x in self.professional['education']]
        self.assertEqual([(r['year_as_reported'], r['credential']) for r in education], [('1985', 'Doctor of Jurisprudence'), ('1980', 'B.S.'), ('1978', 'A.A.')])
        service = self.professional['judicial_experience']
        self.assertTrue(service[0]['interpretation']['present_is_publisher_literal'])
        self.assertFalse(service[0]['interpretation']['current_service_verified'])
        self.assertEqual(service[-1]['interpretation']['court_system'], 'state')
        self.assertEqual(service[-1]['as_reported']['court'], 'California Superior Court, San Diego County')
        self.assertNotIn('court_system', service[-1]['as_reported'])
        self.assertTrue(all(r['as_reported']['time_label'] is None for r in self.professional['other_experience']))

    def test_unknown_context_and_native_counts_preserved(self):
        rows = self.areas + self.motions + self.opinions + self.judges
        self.assertEqual(len(rows), 449)
        self.assertTrue(all(a[k] is None for a in rows for k in ['period', 'denominator', 'numerator', 'cohort', 'methodology_url', 'completeness']))
        self.assertTrue(all(a['source_reported'] and not a['independently_computed'] for a in rows))
        self.assertFalse(any(a['metric'] == 'opinions_per_year' for a in rows))
        self.assertIn('does not currently detect appellate reversals', self.method['value'])

    def test_all_original_evidence_and_tampering(self):
        receipts = {c.relpath: c.receipt() for c in self.caps.values()}
        rows = self.facts + [self.method] + self.areas + self.motions + self.opinions + self.judges
        self.assertEqual(len(rows), 464)
        for row in rows:
            b.validate_evidence(row['evidence'], receipts)
        sample = copy.deepcopy(self.areas[0]['evidence'])
        self.assertEqual(sample['embedded_json_pointer'], '/html')
        sample['quote'] += 'invented'
        with self.assertRaises(AssertionError):
            b.validate_evidence(sample, receipts)
        sample = copy.deepcopy(self.motions[0]['evidence'])
        sample['source_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            b.validate_evidence(sample, receipts)


if __name__ == '__main__':
    unittest.main()
