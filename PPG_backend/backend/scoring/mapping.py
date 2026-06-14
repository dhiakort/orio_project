"""
mapping.py — Règles métier d'orientation ORIO (version 2 — système expert)
==========================================================================
Nouveautés v2 :
  - conditions_minimales   : filtre dur avant scoring (admissibilité)
  - bonus_coherence        : bonus si parcours actuel compatible
  - malus_matiere_critique : malus si matière essentielle très faible
  - sections_source        : sections d'où peut venir l'élève
  - score_domaine_requis   : score minimum par domaine depuis NotesEleve
"""

# ══════════════════════════════════════════════════════════════════════
#  POIDS GLOBAUX
#  Notes augmentées à 55% car orientation tunisienne = fortement académique
#  On utilise les scores domaines (déjà calculés dans app notes)
# ══════════════════════════════════════════════════════════════════════
POIDS_SCORING = {
    'notes':       0.70,   # inclut les scores domaines de NotesEleve
    'riasec':      0.15,
    'bigfive':     0.10,
    'competences': 0.05,
}

# Poids utilisés pour fusionner le score psychométrique et académique
# psychometrique : importance relative des composantes psychométriques
# academique     : importance relative des composantes académiques
POIDS_FUSION = {
    'psychometrique': 0.7,
    'academique': 0.3,
}

# ══════════════════════════════════════════════════════════════════════
#  DOMAINES UNIVERSITAIRES  (3ème et Bac)
#
#  conditions_minimales : dict {matiere: note_min}
#    → si l'élève n'atteint pas ces seuils, la section est ELIMINÉE
#  score_domaine_min : score domaine minimum depuis NotesEleve
#    → ex: score_scientifique >= 50 pour accéder à Bac Math
#  sections_source : sections du lycée compatibles (bonus cohérence)
#  matiere_critique : matière dont la faiblesse génère un malus fort
# ══════════════════════════════════════════════════════════════════════
DOMAINES_UNIVERSITAIRES = {

    'informatique': {
        'label':       '💻 Informatique',
        'description': 'Développement, IA, réseaux, cybersécurité',

        # Filtre dur — conditions minimales
        'conditions_minimales': {
            'mathematiques': 11,
            'informatique':  10,   # optionnel si absent → ignoré
        },
        'score_domaine_min': {
            'score_informatique': 9.0,   # score domaine info depuis NotesEleve
        },

        # Parcours lycée compatibles → bonus
        'sections_source': ['mathematiques','sciences_info','sciences_exp','sciences_tech','scientifique'],

        # Matière dont l'absence/faiblesse crée un malus
        'matiere_critique': 'mathematiques',
        'note_critique_min': 12,

        # Scoring psycho
        'riasec_favorables': {'I': 1.0, 'C': 0.8, 'R': 0.4},
        'bigfive_favorables': {'conscienciosite': 1.0, 'ouverture': 0.9},

        # Quel score domaine utiliser depuis NotesEleve
        'score_domaine_key': 'score_informatique',

        # Notes clés pour le score académique (fallback si pas de score domaine)
        'notes_cles': {'mathematiques': 1.0, 'informatique': 1.0, 'physique': 0.6},
    },

    'medecine': {
        'label':       '🏥 Médecine & Santé',
        'description': 'Médecine, pharmacie, dentaire, paramédical',
        'conditions_minimales': {
            'sciences_naturelles': 13,
            'physique':            12,
            'mathematiques':       11,
        },
        'score_domaine_min': {'score_scientifique': 11.0},
        'sections_source': ['sciences_exp', 'mathematiques'],
        'matiere_critique': 'sciences_naturelles',
        'note_critique_min': 13,
        'riasec_favorables': {'I': 1.0, 'S': 0.9, 'R': 0.3},
        'bigfive_favorables': {'conscienciosite': 1.0, 'agreabilite': 0.8},
        'score_domaine_key': 'score_scientifique',
        'notes_cles': {'sciences_naturelles': 1.0, 'physique': 0.9, 'mathematiques': 0.7},
    },

    'sciences': {
        'label':       '🔬 Sciences fondamentales',
        'description': 'Physique, chimie, biologie, mathématiques pures',
        'conditions_minimales': {
            'mathematiques': 11,
            'physique':      10,
        },
        'score_domaine_min': {'score_scientifique': 9.0},
        'sections_source': ['mathematiques','sciences_exp','sciences_tech','scientifique'],
        'matiere_critique': 'mathematiques',
        'note_critique_min': 11,
        'riasec_favorables': {'I': 1.0, 'R': 0.5, 'A': 0.3},
        'bigfive_favorables': {'ouverture': 1.0, 'conscienciosite': 0.8},
        'score_domaine_key': 'score_scientifique',
        'notes_cles': {'mathematiques': 1.0, 'physique': 1.0, 'sciences_naturelles': 0.7},
    },

    'genie': {
        'label':       '⚙️ Génie & Ingénierie',
        'description': 'Génie civil, mécanique, électrique, industriel',
        'conditions_minimales': {
            'mathematiques': 11,
            'physique':      10,
        },
        'score_domaine_min': {'score_scientifique': 9.0},
        'sections_source': ['mathematiques','sciences_tech','sciences_exp','scientifique'],
        'matiere_critique': 'mathematiques',
        'note_critique_min': 11,
        'riasec_favorables': {'R': 1.0, 'I': 0.8, 'C': 0.5},
        'bigfive_favorables': {'conscienciosite': 1.0, 'ouverture': 0.5},
        'score_domaine_key': 'score_scientifique',
        'notes_cles': {'mathematiques': 1.0, 'physique': 1.0, 'technologie': 0.8},
    },

    'economie': {
        'label':       '💼 Économie & Gestion',
        'description': 'Gestion, finance, commerce, management',
        'conditions_minimales': {
            'mathematiques': 9,
        },
        'score_domaine_min': {'score_economique': 8.0},
        'sections_source': ['eco_gestion','economique','mathematiques','sciences_exp'],
        'matiere_critique': 'economie',
        'note_critique_min': 10,
        'riasec_favorables': {'E': 1.0, 'C': 0.9, 'S': 0.4},
        'bigfive_favorables': {'extraversion': 0.9, 'conscienciosite': 0.8},
        'score_domaine_key': 'score_economique',
        'notes_cles': {'economie': 1.0, 'gestion': 1.0, 'mathematiques': 0.6},
    },

    'droit': {
        'label':       '⚖️ Droit & Sciences politiques',
        'description': 'Droit, justice, sciences politiques, diplomatie',
        'conditions_minimales': {
            'philosophie': 10,
            'francais':    10,
        },
        'score_domaine_min': {'score_litteraire': 8.0},
        'sections_source': ['lettres_bac','eco_gestion','mathematiques','lettres'],
        'matiere_critique': 'philosophie',
        'note_critique_min': 10,
        'riasec_favorables': {'E': 1.0, 'S': 0.8, 'I': 0.4},
        'bigfive_favorables': {'extraversion': 1.0, 'ouverture': 0.7},
        'score_domaine_key': 'score_litteraire',
        'notes_cles': {'philosophie': 1.0, 'arabe': 0.8, 'francais': 0.8, 'histoire_geo': 0.6},
    },

    'lettres': {
        'label':       '📚 Lettres & Sciences humaines',
        'description': 'Lettres, psychologie, sociologie, histoire',
        'conditions_minimales': {
            'arabe':   10,
            'francais': 9,
        },
        'score_domaine_min': {'score_litteraire': 8.0},
        'sections_source': ['lettres_bac','lettres','eco_gestion'],
        'matiere_critique': 'arabe',
        'note_critique_min': 10,
        'riasec_favorables': {'A': 1.0, 'S': 0.8, 'I': 0.4},
        'bigfive_favorables': {'ouverture': 1.0, 'agreabilite': 0.8},
        'score_domaine_key': 'score_litteraire',
        'notes_cles': {'arabe': 1.0, 'francais': 1.0, 'philosophie': 0.9, 'histoire_geo': 0.7},
    },

    'architecture': {
        'label':       '🎨 Architecture & Design',
        'description': 'Architecture, design, arts appliqués, urbanisme',
        'conditions_minimales': {
            'mathematiques': 10,
        },
        'score_domaine_min': {},  # pas de score domaine spécifique
        'sections_source': ['mathematiques','sciences_tech','sciences_exp','lettres_bac'],
        'matiere_critique': 'mathematiques',
        'note_critique_min': 10,
        'riasec_favorables': {'A': 1.0, 'R': 0.8, 'I': 0.4},
        'bigfive_favorables': {'ouverture': 1.0, 'conscienciosite': 0.6},
        'score_domaine_key': None,
        'notes_cles': {'mathematiques': 0.8, 'physique': 0.6, 'technologie': 0.7},
    },

    'education': {
        'label':       '🏫 Éducation & Formation',
        'description': 'Enseignement, formation professionnelle, pédagogie',
        'conditions_minimales': {},  # ouvert à tous les parcours
        'score_domaine_min': {},
        'sections_source': [
            'lettres_bac','sciences_exp','mathematiques',
            'eco_gestion','sciences_info','lettres','scientifique','informatique',
        ],
        'matiere_critique': None,
        'note_critique_min': 0,
        'riasec_favorables': {'S': 1.0, 'A': 0.6, 'E': 0.4},
        'bigfive_favorables': {'agreabilite': 1.0, 'extraversion': 0.8},
        'score_domaine_key': None,
        'notes_cles': {'arabe': 0.7, 'francais': 0.7, 'anglais': 0.5},
    },
}


# ══════════════════════════════════════════════════════════════════════
#  SECTIONS 2ÈME ANNÉE  (recommandées aux élèves de 1ère)
# ══════════════════════════════════════════════════════════════════════
SECTIONS_2EME = {

    'scientifique': {
        'label':       '🔬 Section Scientifique',
        'description': 'Maths, Physique, Sciences naturelles, Informatique',
        'conditions_minimales': {'mathematiques': 10, 'physique': 9},
        'score_domaine_min': {'score_scientifique': 8.0},
        'sections_source': ['tronc_commun'],
        'matiere_critique': 'mathematiques',
        'note_critique_min': 10,
        'riasec_favorables': {'I': 1.0, 'R': 0.7, 'C': 0.5},
        'bigfive_favorables': {'conscienciosite': 1.0, 'ouverture': 0.8},
        'score_domaine_key': 'score_scientifique',
        'notes_cles': {'mathematiques': 1.0, 'physique': 0.9, 'sciences_naturelles': 0.7},
    },

    'economique': {
        'label':       '💰 Section Économie & Gestion',
        'description': 'Économie, Gestion, Mathématiques',
        'conditions_minimales': {'mathematiques': 8},
        'score_domaine_min': {},
        'sections_source': ['tronc_commun'],
        'matiere_critique': None,
        'note_critique_min': 0,
        'riasec_favorables': {'E': 1.0, 'C': 0.9, 'S': 0.4},
        'bigfive_favorables': {'extraversion': 0.8, 'conscienciosite': 0.8},
        'score_domaine_key': 'score_economique',
        'notes_cles': {'mathematiques': 0.8, 'arabe': 0.5, 'francais': 0.5},
    },

    'lettres': {
        'label':       '📚 Section Lettres',
        'description': 'Arabe, Philosophie, Histoire-Géo, Langues',
        'conditions_minimales': {'arabe': 9},
        'score_domaine_min': {'score_litteraire': 7.0},
        'sections_source': ['tronc_commun'],
        'matiere_critique': None,
        'note_critique_min': 0,
        'riasec_favorables': {'A': 1.0, 'S': 0.8, 'I': 0.3},
        'bigfive_favorables': {'ouverture': 1.0, 'agreabilite': 0.7},
        'score_domaine_key': 'score_litteraire',
        'notes_cles': {'arabe': 1.0, 'francais': 0.8, 'anglais': 0.7},
    },

    'informatique': {
        'label':       '💻 Section Informatique',
        'description': 'Maths, Physique, Technologie, Programmation',
        'conditions_minimales': {'mathematiques': 10, 'informatique': 9},
        'score_domaine_min': {'score_informatique': 8.0},
        'sections_source': ['tronc_commun'],
        'matiere_critique': 'mathematiques',
        'note_critique_min': 10,
        'riasec_favorables': {'I': 1.0, 'C': 0.9, 'R': 0.4},
        'bigfive_favorables': {'conscienciosite': 1.0, 'ouverture': 0.9},
        'score_domaine_key': 'score_informatique',
        'notes_cles': {'mathematiques': 1.0, 'informatique': 1.0, 'physique': 0.7},
    },
}


# ══════════════════════════════════════════════════════════════════════
#  SECTIONS BAC  (recommandées aux élèves de 2ème)
#
#  RÈGLE CLÉ : les sections scientifiques exigent une section source
#  scientifique. Un élève de 2ème Lettres ne peut pas aller en Bac Math.
# ══════════════════════════════════════════════════════════════════════
SECTIONS_BAC = {

    'mathematiques': {
        'label':       '🔢 Bac Mathématiques',
        'description': 'La section la plus exigeante, ouvre toutes les portes',
        'conditions_minimales': {'mathematiques': 13, 'physique': 12},
        'score_domaine_min': {'score_scientifique': 12.0},
        'sections_source': ['scientifique', 'informatique'],
        'matiere_critique': 'mathematiques',
        'note_critique_min': 13,
        'riasec_favorables': {'I': 1.0, 'C': 0.8, 'R': 0.5},
        'bigfive_favorables': {'conscienciosite': 1.0, 'ouverture': 0.7},
        'score_domaine_key': 'score_scientifique',
        'notes_cles': {'mathematiques': 1.0, 'physique': 0.9, 'informatique': 0.5},
    },

    'sciences_exp': {
        'label':       '🧪 Bac Sciences expérimentales',
        'description': 'Idéal médecine, pharmacie, biologie',
        'conditions_minimales': {'sciences_naturelles': 11, 'physique': 10, 'mathematiques': 10},
        'score_domaine_min': {'score_scientifique': 10.0},
        'sections_source': ['scientifique', 'informatique'],
        'matiere_critique': 'sciences_naturelles',
        'note_critique_min': 11,
        'riasec_favorables': {'I': 1.0, 'R': 0.6, 'S': 0.4},
        'bigfive_favorables': {'conscienciosite': 1.0, 'ouverture': 0.7},
        'score_domaine_key': 'score_scientifique',
        'notes_cles': {'sciences_naturelles': 1.0, 'physique': 0.9, 'mathematiques': 0.7},
    },

    'sciences_tech': {
        'label':       '⚙️ Bac Sciences techniques',
        'description': 'Ingénierie mécanique, industrielle',
        'conditions_minimales': {'mathematiques': 10, 'physique': 10},
        'score_domaine_min': {'score_scientifique': 9.0},
        'sections_source': ['scientifique', 'informatique'],
        'matiere_critique': 'mathematiques',
        'note_critique_min': 10,
        'riasec_favorables': {'R': 1.0, 'I': 0.7, 'C': 0.5},
        'bigfive_favorables': {'conscienciosite': 1.0, 'ouverture': 0.5},
        'score_domaine_key': 'score_scientifique',
        'notes_cles': {'technologie': 1.0, 'mathematiques': 0.8, 'physique': 0.8},
    },

    'sciences_info': {
        'label':       '💻 Bac Sciences informatique',
        'description': 'Programmation, algorithmes, maths, physique',
        'conditions_minimales': {'mathematiques': 11, 'informatique': 10},
        'score_domaine_min': {'score_informatique': 9.0},
        'sections_source': ['scientifique', 'informatique'],
        'matiere_critique': 'mathematiques',
        'note_critique_min': 11,
        'riasec_favorables': {'I': 1.0, 'C': 0.9, 'R': 0.5},
        'bigfive_favorables': {'conscienciosite': 1.0, 'ouverture': 0.9},
        'score_domaine_key': 'score_informatique',
        'notes_cles': {'informatique': 1.0, 'mathematiques': 0.9, 'physique': 0.6},
    },

    'eco_gestion': {
        'label':       '📈 Bac Économie & Gestion',
        'description': 'Économie, gestion, maths, commerce',
        'conditions_minimales': {'mathematiques': 8},
        'score_domaine_min': {'score_economique': 8.0},
        'sections_source': ['economique', 'scientifique'],  # depuis 2ème éco ou scientifique
        'matiere_critique': 'economie',
        'note_critique_min': 9,
        'riasec_favorables': {'E': 1.0, 'C': 0.9, 'S': 0.4},
        'bigfive_favorables': {'extraversion': 0.8, 'conscienciosite': 0.8},
        'score_domaine_key': 'score_economique',
        'notes_cles': {'economie': 1.0, 'gestion': 1.0, 'mathematiques': 0.6},
    },

    'lettres_bac': {
        'label':       '📖 Bac Lettres',
        'description': 'Philosophie, arabe, histoire-géographie, français',
        'conditions_minimales': {'arabe': 9, 'philosophie': 9},
        'score_domaine_min': {'score_litteraire': 8.0},
        'sections_source': ['lettres', 'economique'],  # depuis 2ème lettres ou éco
        'matiere_critique': 'arabe',
        'note_critique_min': 9,
        'riasec_favorables': {'A': 1.0, 'S': 0.8, 'I': 0.3},
        'bigfive_favorables': {'ouverture': 1.0, 'agreabilite': 0.7},
        'score_domaine_key': 'score_litteraire',
        'notes_cles': {'philosophie': 1.0, 'arabe': 0.9, 'francais': 0.8},
    },

    'sport_bac': {
        'label':       '⚽ Bac Sport',
        'description': 'Éducation physique et sportive',
        'conditions_minimales': {'sport': 12},
        'score_domaine_min': {},
        'sections_source': ['scientifique', 'economique', 'lettres', 'informatique'],
        'matiere_critique': 'sport',
        'note_critique_min': 12,
        'riasec_favorables': {'R': 1.0, 'S': 0.7, 'E': 0.4},
        'bigfive_favorables': {'extraversion': 1.0, 'conscienciosite': 0.6},
        'score_domaine_key': None,
        'notes_cles': {'sport': 1.0, 'sciences_naturelles': 0.6, 'mathematiques': 0.4},
    },
}


# ══════════════════════════════════════════════════════════════════════
#  NIVEAU → CIBLES
# ══════════════════════════════════════════════════════════════════════
NIVEAU_TO_CIBLES = {
    '1ere':   {'mode': 'section_lycee',         'cibles': SECTIONS_2EME,          'label': 'Section de 2ème année'},
    '2eme_s': {'mode': 'section_lycee',         'cibles': SECTIONS_BAC,           'label': 'Section du Bac'},
    '3eme_s': {'mode': 'domaine_universitaire', 'cibles': DOMAINES_UNIVERSITAIRES,'label': 'Domaine universitaire'},
    '4eme_s': {'mode': 'domaine_universitaire', 'cibles': DOMAINES_UNIVERSITAIRES,'label': 'Domaine universitaire'},
}