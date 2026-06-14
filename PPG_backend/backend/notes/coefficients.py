# notes/coefficients.py — fichier séparé propre

COEFFICIENTS = {

    # ── 1ère secondaire — Tronc commun ───────────────────────────────
    'tronc_commun': {
        'mathematiques':      {'coeff': 3, 'type': 'principale'},
        'sciences_naturelles':{'coeff': 1.5, 'type': 'principale'},
        'physique':           {'coeff': 2.5, 'type': 'principale'},
        'technologie':        {'coeff': 1, 'type': 'principale'},
        'arabe':              {'coeff': 3, 'type': 'principale'},
        'francais':           {'coeff': 2.5, 'type': 'principale'},
        'anglais':            {'coeff': 1.5, 'type': 'principale'},
        'histoire_geo':       {'coeff': 3, 'type': 'secondaire'},
        'education_islamique':{'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
        'education_civique':  {'coeff': 1, 'type': 'secondaire'},
    },

    # ── 2ème — Section Math/Sciences/Technique (base scientifique) ───
    'scientifique': {
        'mathematiques':      {'coeff': 4, 'type': 'principale'},
        'physique':           {'coeff': 4, 'type': 'principale'},
        'sciences_naturelles':{'coeff': 2, 'type': 'principale'},
        'technologie':        {'coeff': 2, 'type': 'secondaire'},
        'informatique':       {'coeff': 1, 'type': 'principale'},
        'arabe':              {'coeff': 2, 'type': 'secondaire'},
        'francais':           {'coeff': 2, 'type': 'secondaire'},
        'anglais':            {'coeff': 2, 'type': 'secondaire'},
        'histoire_geo':       {'coeff': 1, 'type': 'secondaire'},
        'education_civique':  {'coeff': 1, 'type': 'secondaire'},
        'education_islamique':{'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
    },

     'informatique': {
        'mathematiques':      {'coeff': 4, 'type': 'principale'},
        'physique':           {'coeff': 3, 'type': 'principale'},
        'technologie':        {'coeff': 2, 'type': 'secondaire'},
        'informatique':       {'coeff': 3, 'type': 'principale'},
        'arabe':              {'coeff': 2, 'type': 'secondaire'},
        'francais':           {'coeff': 2, 'type': 'secondaire'},
        'anglais':            {'coeff': 2, 'type': 'secondaire'},
        'histoire_geo':       {'coeff': 1, 'type': 'secondaire'},
        'education_civique':  {'coeff': 1, 'type': 'secondaire'},
        'education_islamique':{'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
    },

    # ── 2ème — Économie et Gestion ───────────────────────────────────
    'economique': {
        'economie':           {'coeff': 3, 'type': 'principale'},
        'gestion':            {'coeff': 3, 'type': 'principale'},
        'mathematiques':      {'coeff': 2.5, 'type': 'principale'},
        'histoire_geo':       {'coeff': 3, 'type': 'principale'},
        'arabe':              {'coeff': 2, 'type': 'secondaire'},
        'francais':           {'coeff': 2, 'type': 'secondaire'},
        'anglais':            {'coeff': 2, 'type': 'secondaire'},
        'informatique':       {'coeff': 1, 'type': 'secondaire'},
        'education_islamique':{'coeff': 1, 'type': 'secondaire'},
        'education_civique':  {'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
    },

    # ── 2ème — Lettres ───────────────────────────────────────────────
    'lettres_2': {
        'arabe':              {'coeff': 4, 'type': 'principale'},
        'francais':           {'coeff': 4, 'type': 'principale'},
        'anglais':            {'coeff': 3, 'type': 'principale'},
        'histoire_geo':       {'coeff': 3, 'type': 'principale'},
        'education_islamique':{'coeff': 1, 'type': 'principale'},
        'education_civique':  {'coeff': 1, 'type': 'secondaire'},
        'mathematiques':      {'coeff': 1, 'type': 'secondaire'},
        'sciences_naturelles':{'coeff': 1, 'type': 'secondaire'},
        'informatique':       {'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},

    },

    # ── Bac — Mathématiques ──────────────────────────────────────────
    'mathematiques': {
        'mathematiques':      {'coeff': 4, 'type': 'principale'},
        'physique':           {'coeff': 4, 'type': 'principale'},
        'informatique':       {'coeff': 1.5,'type': 'principale'},
        'sciences_naturelles':{'coeff': 1.5,'type': 'principale'},
        'philosophie':        {'coeff': 1,  'type': 'secondaire'},
        'arabe':              {'coeff': 1, 'type': 'secondaire'},
        'francais':           {'coeff': 1, 'type': 'secondaire'},
        'anglais':            {'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
    },

    # ── Bac — Sciences expérimentales ────────────────────────────────
    'sciences_exp': {
        'sciences_naturelles':{'coeff': 4, 'type': 'principale'},
        'physique':           {'coeff': 4, 'type': 'principale'},
        'mathematiques':      {'coeff': 3, 'type': 'principale'},
        'philosophie':        {'coeff': 1, 'type': 'secondaire'},
        'arabe':              {'coeff': 1, 'type': 'secondaire'},
        'francais':           {'coeff': 1, 'type': 'secondaire'},
        'anglais':            {'coeff': 1, 'type': 'secondaire'},
        'informatique':       {'coeff': 1, 'type': 'secondaire'},
        'sport':            {'coeff': 1, 'type': 'secondaire'},
    },

    # ── Bac — Sciences techniques ────────────────────────────────────
    'sciences_tech': {
        'technologie':        {'coeff': 4, 'type': 'principale'},
        'mathematiques':      {'coeff': 4, 'type': 'principale'},
        'physique':           {'coeff': 4, 'type': 'principale'},
        'informatique':       {'coeff': 1, 'type': 'secondaire'},
        'francais':           {'coeff': 1, 'type': 'secondaire'},
        'anglais':            {'coeff': 1, 'type': 'secondaire'},
        'arabe':              {'coeff': 1, 'type': 'secondaire'},
        'philosophie':        {'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
    },

    # ── Bac — Informatique ───────────────────────────────────────────
    'sciences_info': {
        'Informatique et TIC':               {'coeff': 3, 'type': 'principale'},
        'Algorithme et programmation':       {'coeff': 3, 'type': 'principale'},
        'STI':                               {'coeff': 3, 'type': 'principale'},
        'mathematiques':                     {'coeff': 3, 'type': 'principale'},
        'physique':           {'coeff': 2, 'type': 'principale'},
        'francais':           {'coeff': 1, 'type': 'secondaire'},
        'anglais':            {'coeff': 1, 'type': 'secondaire'},
        'arabe':              {'coeff': 1, 'type': 'secondaire'},
        'philosophie':        {'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
    
    },

    # ── Bac — Économie et Gestion ────────────────────────────────────
    'eco_gestion': {
        'economie':           {'coeff': 4, 'type': 'principale'},
        'gestion':            {'coeff': 4, 'type': 'principale'},
        'mathematiques':      {'coeff': 2,'type':'principale'},
        'histoire_geo':       {'coeff': 2, 'type': 'principale'},
        'francais':           {'coeff': 1, 'type': 'secondaire'},
        'anglais':            {'coeff': 1, 'type': 'secondaire'},
        'arabe':              {'coeff': 1, 'type': 'secondaire'},
        'informatique':       {'coeff': 1, 'type': 'secondaire'},
        'philosophie':        {'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
        
    },

    # ── Bac — Lettres ────────────────────────────────────────────────
    'lettres_bac': {
        'philosophie':        {'coeff': 4, 'type': 'principale'},
        'arabe':              {'coeff': 4, 'type': 'principale'},
        'histoire_geo':       {'coeff': 3, 'type': 'principale'},
        'francais':           {'coeff': 2, 'type': 'secondaire'},
        'anglais':            {'coeff': 2, 'type': 'secondaire'},
        'education_islamique':{'coeff': 1, 'type': 'secondaire'},
        'informatique':       {'coeff': 1, 'type': 'secondaire'},
        'sport':              {'coeff': 1, 'type': 'secondaire'},
    },

    # ── Bac — Sport ──────────────────────────────────────────────────
    'sport_bac': {
        'sport pratique':     {'coeff': 2.5, 'type': 'principale'},
        'sport theorique':    {'coeff': 0.5, 'type': 'principale'},
        'sciences':           {'coeff': 3, 'type':'principale'},
        'mathematiques':      {'coeff': 1, 'type': 'secondaire'},
        'physique':          {'coeff': 1, 'type': 'secondaire'},
        'francais':           {'coeff': 1.5, 'type':'secondaire'},
        'anglais':            {'coeff': 1.5, 'type':'secondaire'},
        'arabe':              {'coeff': 1, 'type': 'secondaire'},
        'philosophie':        {'coeff': 1.5, 'type': 'secondaire'},
    },
}

# Alias spécialité User → clé coefficients (ex: modèle Django utilise "lettres")
SPECIALITE_TO_COEFF = {
    'lettres': 'lettres_2',
}


def resolve_section_key(specialite=None, niveau=None):
    """Retourne la clé COEFFICIENTS à utiliser pour un élève."""
    if specialite:
        key = SPECIALITE_TO_COEFF.get(specialite, specialite)
        if key in COEFFICIENTS:
            return key
    return NIVEAU_TO_SECTION.get(niveau, 'tronc_commun')


# Mapping niveau → section par défaut (quand pas de spécialité)
NIVEAU_TO_SECTION = {
    '7eme':  'college',
    '8eme':  'college',
    '9eme':  'college',
    '1ere':  'tronc_commun',
    '2eme_s': 'scientifique',  
    '3eme_s': 'mathematiques', 
    '4eme_s': 'mathematiques', 
}