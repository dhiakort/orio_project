from django.test import SimpleTestCase

from scoring.normalisation import normaliser_note_sur_100, normaliser_notes_dict
from scoring.roadmap import _normaliser_etape_roadmap, _normaliser_roadmap


class NormalisationUtilsTests(SimpleTestCase):
    def test_normaliser_note_sur_100_converts_correctly(self):
        self.assertEqual(normaliser_note_sur_100(15), 75.0)
        self.assertEqual(normaliser_note_sur_100(20), 100.0)
        self.assertEqual(normaliser_note_sur_100(0), 0.0)
        self.assertIsNone(normaliser_note_sur_100(None))
        self.assertIsNone(normaliser_note_sur_100('abc'))

    def test_normaliser_notes_dict_returns_normalized_values(self):
        result = normaliser_notes_dict({'mathematiques': 16, 'francais': 12})
        self.assertEqual(result['mathematiques'], 80.0)
        self.assertEqual(result['francais'], 60.0)

    def test_normaliser_notes_dict_ignores_invalid_values(self):
        result = normaliser_notes_dict({'mathematiques': '16', 'francais': None, 'histoire': 'abc'})
        self.assertEqual(result['mathematiques'], 80.0)
        self.assertNotIn('francais', result)
        self.assertNotIn('histoire', result)


class RoadmapNormalizationUtilsTests(SimpleTestCase):
    def test_normaliser_etape_roadmap_with_dict(self):
        step = {
            'etape': 2,
            'titre': 'Avance',
            'description': 'Fais ceci',
            'actions': ['A'],
            'duree': '1 mois',
        }
        normalized = _normaliser_etape_roadmap(step)
        self.assertEqual(normalized['titre'], 'Avance')
        self.assertEqual(normalized['actions'], ['A'])
        self.assertEqual(normalized['duree'], '1 mois')

    def test_normaliser_etape_roadmap_with_string(self):
        normalized = _normaliser_etape_roadmap('Simple étape')
        self.assertEqual(normalized['titre'], 'Simple étape')
        self.assertEqual(normalized['description'], '')
        self.assertEqual(normalized['actions'], [])

    def test_normaliser_roadmap_handles_mixed_content(self):
        roadmap = [
            {'etape': 1, 'titre': 'Étape 1'},
            'Étape 2',
            {'titre': 'Étape 3', 'description': 'Description'},
        ]
        normalized = _normaliser_roadmap(roadmap)
        self.assertEqual(len(normalized), 3)
        self.assertEqual(normalized[0]['titre'], 'Étape 1')
        self.assertEqual(normalized[1]['titre'], 'Étape 2')
        self.assertEqual(normalized[2]['description'], 'Description')

    def test_normaliser_roadmap_rejects_non_list_input(self):
        self.assertEqual(_normaliser_roadmap('not a list'), [])
