"""
scoring.py — Moteur de scoring expert ORIO v2
=============================================
Logique en 4 étapes :
  1. Filtre admissibilité   (conditions minimales → élimine les sections impossibles)
  2. Bonus/Malus cohérence  (parcours actuel compatible ? matière critique faible ?)
  3. Score pondéré hybride  (55% notes/domaines + 30% RIASEC + 10% BigFive + 5% comp)
  4. Résultat enrichi       (score, niveau risque, forces, axes amélioration, explication)
"""

from .mapping import NIVEAU_TO_CIBLES, POIDS_SCORING


# ══════════════════════════════════════════════════════════════════════
#  ÉTAPE 1 — FILTRE D'ADMISSIBILITÉ
#  Retourne True si l'élève satisfait les conditions minimales
# ══════════════════════════════════════════════════════════════════════
def est_admissible(notes_dict: dict, scores_domaines: dict,
                   specialite_actuelle: str, domaine_config: dict) -> tuple:
    """
    Vérifie si l'élève peut accéder à ce domaine/section.

    Retourne (admissible: bool, raisons_elimination: list)
    """
    raisons = []

    # 1a. Conditions minimales sur les notes
    for matiere, note_min in domaine_config.get('conditions_minimales', {}).items():
        note = notes_dict.get(matiere)
        if note is None:
            continue  # matière non saisie → on ignore (pas bloquant)
        if note < note_min:
            raisons.append(
                f"{matiere.replace('_',' ').title()} insuffisant "
                f"({note:.1f} < {note_min} requis)"
            )

    # 1b. Score domaine minimum
    for dom_key, score_min in domaine_config.get('score_domaine_min', {}).items():
        score = scores_domaines.get(dom_key)
        # scores_domaines sont sur 20, score_domaine_min aussi dans mapping
        if score is not None and score < score_min:
            raisons.append(
                f"Score {dom_key.replace('score_','')} trop faible "
                f"({score:.1f}/20 < {score_min}/20 requis)"
            )

    # 1c. Cohérence de parcours (filtre dur pour certaines sections)
    #     Ex: Bac Math UNIQUEMENT depuis 2ème scientifique
    sections_source = domaine_config.get('sections_source', [])
    if sections_source and specialite_actuelle:
        if specialite_actuelle not in sections_source:
            # On met juste un avertissement, pas une élimination totale
            # (l'élève peut venir d'une autre section avec très bon dossier)
            # SAUF pour les sections scientifiques strictes
            sections_strictes = ['mathematiques','sciences_exp','sciences_tech','sciences_info']
            if (domaine_config.get('score_domaine_key') in ['score_scientifique','score_informatique']
                    and specialite_actuelle in ['lettres','lettres_bac','economique','eco_gestion']):
                raisons.append(
                    f"Parcours actuel ({specialite_actuelle}) incompatible "
                    f"avec cette section scientifique"
                )

    admissible = len(raisons) == 0
    return admissible, raisons


# ══════════════════════════════════════════════════════════════════════
#  ÉTAPE 2 — BONUS / MALUS DE COHÉRENCE
# ══════════════════════════════════════════════════════════════════════
def calculer_bonus_malus(notes_dict: dict, specialite_actuelle: str,
                          domaine_config: dict) -> float:
    """
    Retourne un ajustement entre -15 et +10 points.

    Bonus  : +10 si section source compatible
    Malus  : -15 si matière critique très faible (< note_critique_min - 3)
             -8  si matière critique légèrement faible (< note_critique_min)
    """
    ajustement = 0.0

    # Bonus parcours compatible
    sections_source  = domaine_config.get('sections_source', [])
    if specialite_actuelle and specialite_actuelle in sections_source:
        ajustement += 10.0

    # Malus matière critique
    matiere_critique = domaine_config.get('matiere_critique')
    note_critique_min = domaine_config.get('note_critique_min', 0)

    if matiere_critique and note_critique_min > 0:
        note = notes_dict.get(matiere_critique)
        if note is not None:
            if note < note_critique_min - 3:
                ajustement -= 15.0  # très faible → fort malus
            elif note < note_critique_min:
                ajustement -= 8.0   # légèrement faible → malus modéré

    return ajustement


# ══════════════════════════════════════════════════════════════════════
#  ÉTAPE 3 — SOUS-SCORES
# ══════════════════════════════════════════════════════════════════════

def calculer_score_academique(notes_dict: dict, scores_domaines: dict,
                               domaine_config: dict) -> float:
    """
    Utilise en priorité le score domaine de NotesEleve (déjà pondéré par coefficients).
    Fallback sur les notes clés si le score domaine n'est pas disponible.
    Score sur 100.
    """
    # Priorité : score domaine pré-calculé depuis NotesEleve
    dom_key = domaine_config.get('score_domaine_key')
    if dom_key and scores_domaines.get(dom_key) is not None:
        # Les scores domaines sont sur 20 → on convertit sur 100
        score_sur_20 = scores_domaines[dom_key]
        return round(min((score_sur_20 / 20) * 100, 100), 2)

    # Fallback : calculer depuis les notes clés
    notes_cles  = domaine_config.get('notes_cles', {})
    total_pts   = 0.0
    total_poids = 0.0
    for matiere, poids in notes_cles.items():
        note = notes_dict.get(matiere)
        if note is not None:
            total_pts   += note * poids
            total_poids += poids

    if total_poids == 0:
        return 50.0
    return round((total_pts / total_poids / 20) * 100, 2)


def calculer_score_riasec(riasec_dict: dict, domaine_config: dict) -> float:
    riasec_favorables = domaine_config.get('riasec_favorables', {})
    if not riasec_favorables or not riasec_dict:
        return 50.0
    total_pts, total_poids = 0.0, 0.0
    for code, poids in riasec_favorables.items():
        total_pts   += riasec_dict.get(code, 0) * poids
        total_poids += poids
    return round(total_pts / total_poids, 2) if total_poids else 50.0


def calculer_score_bigfive(bigfive_dict: dict, domaine_config: dict) -> float:
    bigfive_favorables = domaine_config.get('bigfive_favorables', {})
    if not bigfive_favorables or not bigfive_dict:
        return 50.0
    total_pts, total_poids = 0.0, 0.0
    for trait, poids in bigfive_favorables.items():
        score = (100 - bigfive_dict.get(trait, 50)) if trait == 'nevrosisme' \
                else bigfive_dict.get(trait, 50)
        total_pts   += score * poids
        total_poids += poids
    return round(total_pts / total_poids, 2) if total_poids else 50.0


def calculer_score_competences(competences_dict: dict, domaine_key: str) -> float:
    if not competences_dict:
        return 50.0
    POIDS_COMP = {
        'informatique': {'calcul': 0.7, 'logique': 1.0, 'memoire': 0.4},
        'medecine':     {'calcul': 0.5, 'logique': 0.8, 'memoire': 1.0},
        'sciences':     {'calcul': 1.0, 'logique': 0.9, 'memoire': 0.4},
        'genie':        {'calcul': 0.8, 'logique': 1.0, 'memoire': 0.3},
        'economie':     {'calcul': 0.7, 'logique': 0.7, 'memoire': 0.5},
        'droit':        {'calcul': 0.2, 'logique': 0.7, 'memoire': 0.8},
        'lettres':      {'calcul': 0.1, 'logique': 0.5, 'memoire': 0.9},
        'default':      {'calcul': 0.6, 'logique': 0.7, 'memoire': 0.6},
    }
    poids  = POIDS_COMP.get(domaine_key, POIDS_COMP['default'])
    scores = []
    if competences_dict.get('score_calcul')  is not None:
        scores.append(competences_dict['score_calcul']  * poids['calcul'])
    if competences_dict.get('score_logique') is not None:
        scores.append(competences_dict['score_logique'] * poids['logique'])
    if competences_dict.get('score_memoire') is not None:
        scores.append(competences_dict['score_memoire'] * poids['memoire'])
    return round(sum(scores) / len(scores), 2) if scores else 50.0


# ══════════════════════════════════════════════════════════════════════
#  ÉTAPE 4 — GÉNÉRATION DE L'EXPLICATION INTELLIGENTE
# ══════════════════════════════════════════════════════════════════════
def generer_explication(domaine_key: str, domaine_config: dict,
                         notes_dict: dict, scores_domaines: dict,
                         score_final: float, admissible: bool,
                         bonus_malus: float, specialite_actuelle: str) -> dict:
    """
    Génère une explication structurée pour chaque domaine.
    Retourne : forces, axes_amelioration, niveau_risque, message
    """
    forces             = []
    axes_amelioration  = []

    # Analyser les notes clés
    notes_cles = domaine_config.get('notes_cles', {})
    for mat, poids in notes_cles.items():
        note = notes_dict.get(mat)
        if note is None:
            continue
        mat_label = mat.replace('_', ' ').title()
        if note >= 14:
            forces.append(f"{mat_label} ({note:.1f}/20) ✅")
        elif note < domaine_config.get('note_critique_min', 0):
            axes_amelioration.append(f"{mat_label} ({note:.1f}/20) — à améliorer")

    # Analyser le score domaine
    dom_key = domaine_config.get('score_domaine_key')
    if dom_key and scores_domaines.get(dom_key) is not None:
        s = scores_domaines[dom_key]
        dom_label = dom_key.replace('score_', '').title()
        if s >= 14:
            forces.append(f"Score {dom_label} ({s:.1f}/20)")
        elif s < 10:
            axes_amelioration.append(f"Score {dom_label} faible ({s:.1f}/20)")

    # Niveau de risque
    if score_final >= 75:
        niveau_risque = 'faible'
        risque_emoji  = '🟢'
    elif score_final >= 60:
        niveau_risque = 'modéré'
        risque_emoji  = '🟡'
    else:
        niveau_risque = 'élevé'
        risque_emoji  = '🔴'

    # Message d'explication
    if score_final >= 75 and bonus_malus >= 0:
        message = f"Excellente compatibilité ! Ton profil académique et psychologique correspond bien à ce domaine."
    elif score_final >= 60:
        message = f"Bonne compatibilité. Quelques points à renforcer mais le profil global est positif."
    elif axes_amelioration:
        message = f"Compatibilité moyenne. Tu devras renforcer : {', '.join([a.split('—')[0].strip() for a in axes_amelioration[:2]])}."
    else:
        message = f"Score de compatibilité calculé sur la base de ton profil actuel."

    # Ajouter info parcours
    sections_source = domaine_config.get('sections_source', [])
    if specialite_actuelle and specialite_actuelle in sections_source:
        message += " Ton parcours actuel est bien aligné avec cette orientation."

    return {
        'forces':            forces[:3],
        'axes_amelioration': axes_amelioration[:3],
        'niveau_risque':     niveau_risque,
        'risque_emoji':      risque_emoji,
        'message':           message,
    }


# ══════════════════════════════════════════════════════════════════════
#  FONCTION PRINCIPALE
# ══════════════════════════════════════════════════════════════════════
def calculer_recommandation(
    niveau: str,
    specialite_actuelle: str,
    notes_dict: dict,
    scores_domaines: dict,      # ← NOUVEAU : scores depuis NotesEleve
    riasec_dict: dict,
    bigfive_dict: dict,
    competences_dict: dict,
) -> dict:
    """
    Paramètres
    ----------
    niveau              : '1ere' | '2eme_s' | '3eme_s' | '4eme_s'
    specialite_actuelle : section actuelle de l'élève (ex: 'scientifique')
    notes_dict          : {'mathematiques': 15.5, ...}
    scores_domaines     : {
        'score_scientifique': 14.2,
        'score_informatique': 15.8,
        'score_litteraire':   10.1,
        'score_economique':   11.5,
    }  ← directement depuis NotesEleve
    riasec_dict         : {'R':45,'I':80,'A':30,'S':55,'E':60,'C':70}
    bigfive_dict        : {'ouverture':80,'conscienciosite':88,...}
    competences_dict    : {'score_calcul':85,'score_logique':90,'score_memoire':70}
    """
    config_niveau = NIVEAU_TO_CIBLES.get(niveau, NIVEAU_TO_CIBLES['4eme_s'])
    mode          = config_niveau['mode']
    cibles        = config_niveau['cibles']
    label         = config_niveau['label']
    poids         = POIDS_SCORING

    # Ajuster poids selon données disponibles
    poids = _ajuster_poids(notes_dict, riasec_dict, bigfive_dict, competences_dict, poids)

    resultats     = []
    elimines      = []

    for cle, domaine_config in cibles.items():

        # ── ÉTAPE 1 : Admissibilité ─────────────────────────────────
        admissible, raisons = est_admissible(
            notes_dict, scores_domaines, specialite_actuelle, domaine_config
        )

        if not admissible:
            elimines.append({
                'cle':    cle,
                'label':  domaine_config['label'],
                'raisons': raisons,
            })
            continue

        # ── ÉTAPE 2 : Bonus/Malus ───────────────────────────────────
        bonus_malus = calculer_bonus_malus(
            notes_dict, specialite_actuelle, domaine_config
        )

        # ── ÉTAPE 3 : Sous-scores ───────────────────────────────────
        s_acad = calculer_score_academique(notes_dict, scores_domaines, domaine_config)
        s_ri   = calculer_score_riasec(riasec_dict, domaine_config)
        s_bf   = calculer_score_bigfive(bigfive_dict, domaine_config)
        s_comp = calculer_score_competences(competences_dict, cle)

        # ══ Score psychométrique combiné (pour affichage côté front)
        # Composition par défaut : 40% RIASEC, 40% BigFive, 20% Compétences
        s_psy = round(0.4 * s_ri + 0.4 * s_bf + 0.2 * s_comp, 2)

        # Score pondéré
        score_brut = (
            s_acad * poids['notes']
          + s_ri   * poids['riasec']
          + s_bf   * poids['bigfive']
          + s_comp * poids['competences']
        )

        # Appliquer bonus/malus (plafonné entre 0 et 100)
        score_final = round(min(max(score_brut + bonus_malus, 0), 100), 1)

        # ── ÉTAPE 4 : Explication ───────────────────────────────────
        explication = generer_explication(
            cle, domaine_config, notes_dict, scores_domaines,
            score_final, admissible, bonus_malus, specialite_actuelle
        )

        resultats.append({
            'cle':         cle,
            'label':       domaine_config['label'],
            'description': domaine_config['description'],
            'score_final': score_final,
            'detail': {
                'score_academique':  s_acad,
                'score_riasec':      s_ri,
                'score_bigfive':     s_bf,
                'score_competences': s_comp,
                'score_psychometrique': s_psy,
                'bonus_malus':       bonus_malus,
            },
            **explication,
        })

    # Classer du meilleur au moins bon
    resultats.sort(key=lambda x: x['score_final'], reverse=True)
    nb_top = 3 if mode == 'section_lycee' else 5
    top    = resultats[:nb_top]

    # Poids de fusion exposés au front (fallback si non fournis côté client)
    poids_fusion = {'psychometrique': 0.7, 'academique': 0.3}

    return {
        'mode':      mode,
        'label':     label,
        'resultats': top,
        'elimines':  elimines,   # sections éliminées + raisons (pour debug/front)
        'poids_fusion': poids_fusion,
    }


def _ajuster_poids(notes_dict, riasec_dict, bigfive_dict, competences_dict, poids_base):
    disponibles = {
        'notes':       bool(notes_dict),
        'riasec':      bool(riasec_dict),
        'bigfive':     bool(bigfive_dict),
        'competences': bool(competences_dict),
    }
    if all(disponibles.values()):
        return poids_base
    poids_dispo = {k: poids_base[k] for k, v in disponibles.items() if v}
    total       = sum(poids_dispo.values())
    return {
        k: (poids_base[k] / total if disponibles[k] else 0.0)
        for k in poids_base
    }