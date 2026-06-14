"""
Tests unitaires — moteur de scoring ORIO v2
"""

from django.test import SimpleTestCase

from scoring.scoring import (
    est_admissible, calculer_bonus_malus, calculer_recommandation,
    calculer_score_psychometrique, _fusionner_scores,
)
from scoring.mapping import SECTIONS_BAC, SECTIONS_2EME, POIDS_SCORING, POIDS_FUSION
from scoring.normalisation import normaliser_note_sur_100, normaliser_notes_dict
from scoring.roadmap import _normaliser_etape_roadmap, _normaliser_roadmap
from scoring.psychometric import classifier_profil_psychometrique


class AdmissibiliteTests(SimpleTestCase):
    """Filtre dur avant scoring."""

    def test_bac_math_elimine_si_maths_faibles(self):
        cfg = SECTIONS_BAC['mathematiques']
        ok, raisons = est_admissible(
            {'mathematiques': 10, 'physique': 14},
            {'score_scientifique': 14},
            'scientifique',
            cfg,
        )
        self.assertFalse(ok)
        self.assertTrue(any('mathematiques' in r.lower() for r in raisons))

    def test_bac_math_admis_si_notes_ok(self):
        cfg = SECTIONS_BAC['mathematiques']
        ok, raisons = est_admissible(
            {'mathematiques': 15, 'physique': 13},
            {'score_scientifique': 13},
            'scientifique',
            cfg,
        )
        self.assertTrue(ok)
        self.assertEqual(raisons, [])

    def test_parcours_lettres_bloque_bac_scientifique(self):
        cfg = SECTIONS_BAC['sciences_info']
        ok, raisons = est_admissible(
            {'mathematiques': 16, 'informatique': 15},
            {'score_informatique': 14},
            'lettres',
            cfg,
        )
        self.assertFalse(ok)
        self.assertTrue(any('incompatible' in r for r in raisons))


class BonusMalusTests(SimpleTestCase):
    def test_bonus_parcours_compatible(self):
        cfg = SECTIONS_BAC['sciences_info']
        bonus = calculer_bonus_malus(
            {'mathematiques': 14},
            'scientifique',
            cfg,
        )
        self.assertEqual(bonus, 10.0)

    def test_malus_matiere_critique_tres_faible(self):
        cfg = SECTIONS_BAC['mathematiques']
        # Parcours non compatible → pas de bonus +10, malus seul visible
        malus = calculer_bonus_malus(
            {'mathematiques': 8},
            'economique',
            cfg,
        )
        self.assertLessEqual(malus, -8.0)


class RecommandationIntegrationTests(SimpleTestCase):
    """Scénarios métier tunisiens."""

    def _base_notes_scientifique(self):
        return {
            'mathematiques': 14,
            'physique': 13,
            'informatique': 15,
            'sciences_naturelles': 12,
        }

    def test_2eme_scientifique_prefere_sections_scientifiques(self):
        result = calculer_recommandation(
            niveau='2eme_s',
            specialite_actuelle='scientifique',
            notes_dict=self._base_notes_scientifique(),
            scores_domaines={
                'score_scientifique': 12,
                'score_informatique': 13,
                'score_litteraire': 8,
                'score_economique': 9,
            },
            riasec_dict={'I': 80, 'C': 60, 'R': 40, 'A': 20, 'S': 30, 'E': 25},
            bigfive_dict={'conscienciosite': 70, 'ouverture': 65},
            competences_dict={'score_calcul': 75, 'score_logique': 70},
        )
        top_cles = [r['cle'] for r in result['resultats'][:3]]
        scientifiques = {'sciences_info', 'sciences_exp', 'sciences_tech', 'mathematiques'}
        self.assertTrue(scientifiques.intersection(top_cles))
        self.assertNotIn('sport_bac', top_cles)

    def test_2eme_economique_elimine_bac_math(self):
        result = calculer_recommandation(
            niveau='2eme_s',
            specialite_actuelle='economique',
            notes_dict={'mathematiques': 9, 'economie': 14, 'gestion': 13},
            scores_domaines={'score_economique': 12, 'score_scientifique': 7},
            riasec_dict={'E': 85, 'C': 70, 'I': 30, 'R': 20, 'A': 25, 'S': 40},
            bigfive_dict={'extraversion': 60},
            competences_dict={},
        )
        elim_cles = {e['cle'] for e in result.get('elimines', [])}
        self.assertIn('mathematiques', elim_cles)
        if result['resultats']:
            self.assertEqual(result['resultats'][0]['cle'], 'eco_gestion')

    def test_1ere_recommande_sections_2eme(self):
        result = calculer_recommandation(
            niveau='1ere',
            specialite_actuelle='tronc_commun',
            notes_dict={'mathematiques': 13, 'arabe': 12, 'francais': 11},
            scores_domaines={'score_scientifique': 11, 'score_litteraire': 10},
            riasec_dict={'I': 70, 'A': 50},
            bigfive_dict={},
            competences_dict={},
        )
        cibles_valides = set(SECTIONS_2EME.keys())
        for r in result['resultats']:
            self.assertIn(r['cle'], cibles_valides)

    def test_resultat_contient_explications(self):
        result = calculer_recommandation(
            niveau='2eme_s',
            specialite_actuelle='scientifique',
            notes_dict=self._base_notes_scientifique(),
            scores_domaines={'score_scientifique': 12, 'score_informatique': 13},
            riasec_dict={'I': 80},
            bigfive_dict={'conscienciosite': 70},
            competences_dict={'score_calcul': 60},
        )
        self.assertGreater(len(result['resultats']), 0)
        top = result['resultats'][0]
        self.assertIn('score_final', top)
        self.assertIn('forces', top)
        self.assertIn('detail', top)
        self.assertIn('niveau_risque', top)


class MappingSanityTests(SimpleTestCase):
    def test_poids_scoring_somme_100_pourcent(self):
        total = sum(POIDS_SCORING.values())
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_sections_2eme_inclut_informatique(self):
        self.assertIn('informatique', SECTIONS_2EME)


class NormalisationTests(SimpleTestCase):
    def test_note_sur_20_convertie_sur_100(self):
        self.assertEqual(normaliser_note_sur_100(15), 75.0)
        self.assertEqual(normaliser_note_sur_100(20), 100.0)

    def test_normaliser_notes_dict(self):
        result = normaliser_notes_dict({'mathematiques': 16, 'francais': 12})
        self.assertEqual(result['mathematiques'], 80.0)
        self.assertEqual(result['francais'], 60.0)

    def test_normaliser_notes_dict_ignore_non_numeric(self):
        result = normaliser_notes_dict({'mathematiques': '16', 'francais': None, 'histoire': 'abc'})
        self.assertEqual(result['mathematiques'], 80.0)
        self.assertNotIn('francais', result)
        self.assertNotIn('histoire', result)


class RoadmapNormalizationTests(SimpleTestCase):
    def test_normaliser_etape_roadmap_dict(self):
        step = {'etape': 2, 'titre': 'Avance', 'description': 'Fais ceci', 'actions': ['A'], 'duree': '1 mois'}
        normalized = _normaliser_etape_roadmap(step)
        self.assertEqual(normalized['titre'], 'Avance')
        self.assertEqual(normalized['actions'], ['A'])

    def test_normaliser_etape_roadmap_string(self):
        step = 'Simple étape'
        normalized = _normaliser_etape_roadmap(step)
        self.assertEqual(normalized['titre'], 'Simple étape')
        self.assertEqual(normalized['actions'], [])

    def test_normaliser_roadmap_list(self):
        roadmap = [
            {'etape': 1, 'titre': 'Étape 1'},
            'Étape 2',
            {'titre': 'Étape 3', 'description': 'Description'}
        ]
        normalized = _normaliser_roadmap(roadmap)
        self.assertEqual(len(normalized), 3)
        self.assertEqual(normalized[0]['titre'], 'Étape 1')
        self.assertEqual(normalized[1]['titre'], 'Étape 2')
        self.assertEqual(normalized[2]['description'], 'Description')

    def test_normaliser_roadmap_non_list(self):
        normalized = _normaliser_roadmap('not a list')
        self.assertEqual(normalized, [])


class PsychometricTests(SimpleTestCase):
    def test_classification_investigatif(self):
        result = classifier_profil_psychometrique(
            {'R': 30, 'I': 90, 'A': 25, 'S': 40, 'E': 35, 'C': 50},
            {'conscienciosite': 80},
        )
        self.assertEqual(result['profil_dominant'], 'Investigatif')
        self.assertIn('Investigatif', result['profil_combine'])
        self.assertEqual(result['methode'], 'sklearn_knn')

    def test_classification_vide(self):
        result = classifier_profil_psychometrique({}, {})
        self.assertIsNone(result['profil_combine'])


class FusionTests(SimpleTestCase):
    def test_fusion_70_30(self):
        score = _fusionner_scores(80, 60, {'psychometrique': 0.7, 'academique': 0.3})
        self.assertEqual(score, 66.0)  # 60*0.7 + 80*0.3

    def test_score_psychometrique_combine_composantes(self):
        score = calculer_score_psychometrique(
            80, 70, 60,
            {'I': 80}, {'conscienciosite': 70}, {'score_calcul': 60},
        )
        self.assertGreater(score, 60)
        self.assertLessEqual(score, 100)

    def test_recommandation_inclut_classification(self):
        result = calculer_recommandation(
            niveau='2eme_s',
            specialite_actuelle='scientifique',
            notes_dict={'mathematiques': 14, 'physique': 13, 'informatique': 15},
            scores_domaines={'score_scientifique': 12, 'score_informatique': 13},
            riasec_dict={'I': 80, 'C': 60, 'R': 40, 'A': 20, 'S': 30, 'E': 25},
            bigfive_dict={'conscienciosite': 70},
            competences_dict={'score_calcul': 75},
        )
        self.assertIn('classification', result)
        self.assertIn('poids_fusion', result)
        self.assertIn('score_psychometrique', result['resultats'][0]['detail'])
