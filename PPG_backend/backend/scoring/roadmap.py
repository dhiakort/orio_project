"""
roadmap.py — Génération de roadmap via Groq LLM
=========================================================
Prend le profil complet de l'élève + les domaines recommandés
et demande à Groq de générer une roadmap personnalisée.

C'est ici que l'IA (LLM) entre vraiment dans ORIO.
"""

import json
import urllib.request
import urllib.error

from django.conf import settings


# URL de l'API Groq (compatible OpenAI)
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "mixtral-8x7b-32768"


def generer_roadmap(profil: dict, top_domaines: list) -> dict:
    """
    Génère une roadmap personnalisée pour l'élève.

    Paramètres
    ----------
    profil : {
        'niveau': '4eme_s',
        'specialite': 'sciences_info',
        'notes': {
            'moyenne_ponderee': 15.2,
            'points_forts': ['mathematiques', 'informatique'],
            'points_faibles': ['philosophie'],
        },
        'bigfive': { 'profil_dominant': 'Conscienciosité', ... },
        'riasec':  { 'code_holland': 'ICR', ... },
        'competences': { 'score_global': 78, ... },
    }
    top_domaines : liste des 3-5 domaines recommandés depuis scoring.py

    Retour
    ------
    {
        "domaine_principal": "informatique",
        "roadmap": [
            {
                "etape": 1,
                "titre": "Consolider les mathématiques",
                "description": "...",
                "actions": ["...", "..."],
                "duree": "2 mois"
            },
            ...
        ],
        "competences_a_developper": ["Python", "algorithmique", "..."],
        "ressources": ["...", "..."],
        "message_encouragement": "..."
    }
    """

    # ── 1. Construire le prompt ─────────────────────────────────────
    prompt = _construire_prompt(profil, top_domaines)

    # ── 2. Appeler Claude Haiku ─────────────────────────────────────
    try:
        reponse_brute = _appeler_claude(prompt)
        roadmap_json  = _parser_reponse(reponse_brute)
        return {"success": True, "roadmap": roadmap_json}

    except Exception as e:
        # En cas d'erreur → roadmap générique de secours
        fallback_roadmap = _roadmap_secours(top_domaines)
        return {
            "success": False,
            "error":   str(e),
            "roadmap": fallback_roadmap,
        }


def _normaliser_etape_roadmap(step):
    if isinstance(step, dict):
        return step
    if isinstance(step, str):
        return {
            'etape': '?',
            'titre': step,
            'description': '',
            'actions': [],
            'duree': '',
        }
    return {'etape': '?', 'titre': 'Sans titre', 'description': '', 'actions': [], 'duree': ''}


def _normaliser_roadmap(roadmap):
    if not isinstance(roadmap, list):
        return []
    return [_normaliser_etape_roadmap(step) for step in roadmap]


def generer_reponse_chatbot(question: str, profil: dict, roadmap: list) -> dict:
    """
    Génère une réponse chatbot naturelle basée sur la roadmap.
    """
    roadmap = _normaliser_roadmap(roadmap)
    if not roadmap:
        return {
            "success": False,
            "error": "Pas de roadmap disponible pour répondre à la question.",
        }

    prompt = _construire_prompt_chatbot(question, profil, roadmap)
    try:
        reponse = _appeler_claude(prompt)
        if reponse and isinstance(reponse, str) and reponse.strip():
            return {"success": True, "answer": reponse.strip()}
    except Exception as e:
        error_text = str(e)
        fallback_answer = _reponse_chatbot_fallback(question, roadmap)
        return {
            "success": True,
            "answer": fallback_answer,
            "fallback": True,
            "error": error_text,
        }

    return {
        "success": True,
        "answer": _reponse_chatbot_fallback(question, roadmap),
        "fallback": True,
    }


def _reponse_chatbot_fallback(question: str, roadmap: list) -> str:
    """
    Génère une réponse intelligente basée sur le contenu de la question.
    Combine réponse contextuelle + roadmap recommandée.
    """
    question_lower = question.lower()
    
    # ── 1. Réponses aux questions spécifiques sur les universités tunisiennes ──
    if any(word in question_lower for word in ['faculté', 'université', 'university', 'faculty', 'filière', 'specialite', 'speciality', 'programme']):
        if any(word in question_lower for word in ['tunisie', 'tunisia', 'tunis', 'disponible', 'available']):
            uni_response = _repondre_universite_tunisia(question_lower)
            if uni_response:
                return uni_response
    
    # ── 2. Questions sur les étapes de la roadmap ──
    if any(word in question_lower for word in ['comment', 'how', 'quoi', 'what', 'étape', 'step', 'faire', 'do']):
        step_response = _repondre_roadmap_specific(question_lower, roadmap)
        if step_response:
            return step_response
    
    # ── 3. Questions sur les compétences à développer ──
    if any(word in question_lower for word in ['compétence', 'skill', 'competence', 'améliorer', 'improve', 'renforcer', 'strengthen']):
        comp_response = _repondre_competences(question_lower)
        if comp_response:
            return comp_response
    
    # ── 4. Questions générales sur l'orientation ──
    if any(word in question_lower for word in ['orientation', 'orientation', 'conseil', 'advice', 'recommandation', 'recommendation']):
        orient_response = _repondre_orientation(roadmap)
        if orient_response:
            return orient_response
    
    # ── 5. Fallback final : combiner roadmap + question ──
    return _repondre_roadmap_generic(question_lower, roadmap)


def _repondre_universite_tunisia(question: str) -> str:
    """Répond aux questions sur les universités et filières disponibles en Tunisie."""
    universites_tunisie = {
        "Université de Tunis": {
            "filières": ["Informatique", "Mathématiques", "Physique", "Chimie", "Biologie"],
            "description": "Une des principales universités du pays avec des programmes reconnus en sciences."
        },
        "Université de Sousse": {
            "filières": ["Ingénierie", "Informatique", "Sciences appliquées", "Management"],
            "description": "Spécialisée dans les sciences appliquées et l'ingénierie."
        },
        "Université de Sfax": {
            "filières": ["Ingénierie", "Sciences", "Technologie", "Économie"],
            "description": "Réputée pour ses programmes d'ingénierie et ses recherches scientifiques."
        },
        "Université de Jendouba": {
            "filières": ["Agronomie", "Lettres", "Sciences", "Droit"],
            "description": "Couvre une large gamme de domaines d'études."
        },
        "Université de Manouba": {
            "filières": ["Lettres", "Sciences humaines", "Droit", "Sciences sociales"],
            "description": "Spécialisée dans les sciences humaines et sociales."
        }
    }
    
    response_lines = [
        "Voici les principales universités disponibles en Tunisie avec leurs filières :"
    ]
    
    for uni_name, details in universites_tunisie.items():
        filieres_text = ", ".join(details["filières"][:3])
        response_lines.append(f"• {uni_name} : {filieres_text}")
    
    response_lines.append("\nJe te recommande d'explorer ces universités en fonction de ta roadmap et tes domaines d'intérêt !")
    return " ".join(response_lines)


def _repondre_roadmap_specific(question: str, roadmap: list) -> str:
    """Répond avec détails spécifiques d'une étape de la roadmap."""
    if not roadmap:
        return ""
    
    best_match = None
    best_score = 0
    
    q_tokens = set(question.split())
    
    for step in roadmap:
        titre = str(step.get('titre', '')).lower()
        description = str(step.get('description', '')).lower()
        all_text = f"{titre} {description}".split()
        
        match_count = len(set(all_text) & q_tokens)
        if match_count > best_score:
            best_score = match_count
            best_match = step
    
    if best_match and best_score > 0:
        titre = best_match.get('titre', '')
        description = best_match.get('description', '')
        actions = best_match.get('actions', [])
        
        response = f"Pour cette étape, voici ce que je te conseille :\n\n{titre}\n{description}"
        if actions:
            response += f"\n\nActions concrètes :\n"
            for i, action in enumerate(actions, 1):
                response += f"{i}. {action}\n"
        return response.strip()
    
    return ""


def _repondre_competences(question: str) -> str:
    """Répond aux questions sur les compétences à développer."""
    competences_recommandees = {
        "informatique": ["Programmation", "Algorithmes", "Bases de données", "Développement web"],
        "sciences": ["Recherche", "Analyse critique", "Expérimentation", "Communication scientifique"],
        "management": ["Leadership", "Communication", "Gestion de projet", "Prise de décision"],
        "lettres": ["Analyse critique", "Expression écrite", "Recherche documentaire", "Communication orale"],
        "ingenierie": ["Résolution de problèmes", "Modélisation", "Travail en équipe", "Innovation"]
    }
    
    response = "Voici les compétences clés à développer pour réussir :\n"
    competences_list = []
    for domain, skills in competences_recommandees.items():
        competences_list.extend(skills[:2])
    
    competences_list = list(set(competences_list))[:5]
    for comp in competences_list:
        response += f"✓ {comp}\n"
    
    response += "\nFocuse-toi sur ces domaines tout en suivant ta roadmap personnalisée."
    return response.strip()


def _repondre_orientation(roadmap: list) -> str:
    """Répond aux questions générales sur l'orientation."""
    if not roadmap:
        return "Je te conseille de compléter ta roadmap en répondant aux tests et en renseignant tes notes pour obtenir des recommandations personnalisées."
    
    first_step = roadmap[0]
    titre = first_step.get('titre', 'Débuter')
    description = first_step.get('description', '')
    
    return f"Basé sur ton profil, je te recommande de commencer par ceci :\n\n{titre}\n\n{description}\n\nSuis les étapes de ta roadmap pour progresser vers ton orientation idéale."


def _repondre_roadmap_generic(question: str, roadmap: list) -> str:
    """Réponse générique basée sur la roadmap si aucune correspondance spécifique."""
    if not roadmap:
        return "Pour mieux répondre à tes questions, complète d'abord tes notes et tes tests. Cela me permettra de te proposer une roadmap vraiment personnalisée !"
    
    first_three_steps = roadmap[:3]
    response = f"Concernant ta question sur l'orientation, voici mon conseil :\n\n"
    
    for i, step in enumerate(first_three_steps, 1):
        titre = step.get('titre', '')
        if titre:
            response += f"{i}. {titre}\n"
    
    response += "\nSuis ces étapes progressivement et n'hésite pas à me poser d'autres questions !"
    return response.strip()



def _construire_prompt_chatbot(question: str, profil: dict, roadmap: list) -> str:
    niveau_labels = {
        '1ere':   '1ère année secondaire',
        '2eme_s': '2ème année secondaire',
        '3eme_s': '3ème année secondaire',
        '4eme_s': 'Terminale (Bac)',
    }
    niveau_label = niveau_labels.get(profil.get('niveau', ''), profil.get('niveau', 'non défini'))

    notes_info = profil.get('notes') or {}
    moy = notes_info.get('moyenne_ponderee', 'non disponible')
    forts = ', '.join(notes_info.get('points_forts', [])) or 'aucun identifié'
    faibles = ', '.join(notes_info.get('points_faibles', [])) or 'aucun identifié'
    bf_info = profil.get('bigfive') or {}
    ri_info = profil.get('riasec') or {}

    étapes = []
    for step in roadmap:
        titre = step.get('titre', 'Sans titre')
        description = step.get('description', '')
        actions = step.get('actions', [])
        actions_text = ' ; '.join(actions) if actions else ''
        étapes.append(f"Étape {step.get('etape', '?')}: {titre}. {description} Actions: {actions_text}")

    prompt = f"""Tu es un assistant d'orientation universitaire tunisien expert, empathique et motivant.

Tu dois répondre PRÉCISÉMENT et DIRECTEMENT à la question posée par l'élève.
Ne donne pas de conseils génériques - personnalise ta réponse au profil et à la question.

QUESTION DE L'ÉLÈVE : {question}

PROFIL DE L'ÉLÈVE :
- Niveau : {niveau_label}
- Moyenne pondérée : {moy}/20
- Forces académiques : {forts}
- Points à améliorer : {faibles}
- Profil psychologique (Big Five) : {bf_info.get('profil_dominant', 'non disponible')}
- Code RIASEC (intérêts) : {ri_info.get('code_holland', 'non disponible')}

ROADMAP PERSONNALISÉE :
{chr(10).join(étapes)}

INSTRUCTIONS :
1. Lis bien la question et comprends exactement ce que l'élève demande
2. Si c'est une question sur les universités tunisiennes → donne les détails précis
3. Si c'est une question sur une étape de la roadmap → explique cette étape en détail
4. Si c'est une question sur comment faire quelque chose → donne des actions concrètes
5. Réponds en français, de manière claire, structurée et motivante
6. Relie ta réponse au profil et à la roadmap quand c'est pertinent
7. Soit bref mais complet (max 5-6 lignes)

Réponds maintenant à la question de l'élève de manière précise et utile."""

    return prompt


# ══════════════════════════════════════════════════════════════════════
#  CONSTRUCTION DU PROMPT
# ══════════════════════════════════════════════════════════════════════
def _construire_prompt(profil: dict, top_domaines: list) -> str:
    """
    Construit un prompt structuré pour Claude Haiku.
    On lui donne le profil en JSON et on lui demande
    une réponse JSON stricte — pas de texte libre.
    """

    # Préparer les infos du profil de façon lisible
    niveau_labels = {
        '1ere':   '1ère année secondaire',
        '2eme_s': '2ème année secondaire',
        '3eme_s': '3ème année secondaire',
        '4eme_s': 'Terminale (Bac)',
    }
    niveau_label = niveau_labels.get(profil.get('niveau', ''), profil.get('niveau', ''))

    # Top domaine
    domaine_principal = top_domaines[0]['label'] if top_domaines else 'Non défini'
    score_principal   = top_domaines[0]['score_final'] if top_domaines else 0

    # Notes
    notes_info  = profil.get('notes') or {}
    moy         = notes_info.get('moyenne_ponderee', 'non disponible')
    forts       = ', '.join(notes_info.get('points_forts', [])) or 'aucun identifié'
    faibles     = ', '.join(notes_info.get('points_faibles', [])) or 'aucun identifié'

    # Psycho
    bf_info     = profil.get('bigfive') or {}
    ri_info     = profil.get('riasec') or {}
    comp_info   = profil.get('competences') or {}

    prompt = f"""Tu es un conseiller d'orientation scolaire tunisien expert et bienveillant.

Voici le profil d'un lycéen tunisien :

NIVEAU : {niveau_label}
MOYENNE PONDÉRÉE : {moy}/20
MATIÈRES FORTES : {forts}
MATIÈRES FAIBLES : {faibles}
PROFIL BIG FIVE dominant : {bf_info.get('profil_dominant', 'non disponible')}
CODE RIASEC : {ri_info.get('code_holland', 'non disponible')}
SCORE COGNITIF GLOBAL : {comp_info.get('score_global', 'non disponible')}/100

DOMAINES RECOMMANDÉS PAR L'IA :
{chr(10).join(f"  {i+1}. {d['label']} — {d['score_final']}% de compatibilité" for i, d in enumerate(top_domaines))}

DOMAINE PRINCIPAL RECOMMANDÉ : {domaine_principal} ({score_principal}%)

Ta mission : génère une roadmap d'orientation personnalisée et motivante pour ce lycéen.

RÈGLES STRICTES :
- Réponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant ou après
- La roadmap doit être réaliste pour le contexte tunisien
- Utilise un langage encourageant adapté à un lycéen
- Les ressources doivent être accessibles en Tunisie (gratuites de préférence)

FORMAT JSON ATTENDU (respecte exactement cette structure) :
{{
  "domaine_principal": "clé du domaine en minuscules (ex: informatique)",
  "message_encouragement": "message personnalisé et motivant de 2-3 phrases",
  "roadmap": [
    {{
      "etape": 1,
      "titre": "titre court de l'étape",
      "description": "description en 1-2 phrases",
      "actions": ["action concrète 1", "action concrète 2", "action concrète 3"],
      "duree": "durée estimée (ex: 1 mois)"
    }}
  ],
  "competences_a_developper": ["compétence 1", "compétence 2", "compétence 3"],
  "ressources": [
    {{
      "titre": "nom de la ressource",
      "type": "site web | livre | plateforme | application",
      "lien_ou_description": "url ou description courte",
      "gratuit": true
    }}
  ]
}}

Génère exactement 3 étapes dans la roadmap et 3-4 ressources."""

    return prompt


# ══════════════════════════════════════════════════════════════════════
#  APPEL API CLAUDE HAIKU
# ══════════════════════════════════════════════════════════════════════
def _appeler_claude(prompt: str) -> str:
    """
    Appelle l'API Groq (compatible OpenAI).
    Utilise urllib pour éviter une dépendance à requests.
    La clé API est lue depuis la variable d'environnement GROQ_API_KEY.
    """
    api_key = getattr(settings, 'GROQ_API_KEY', '') or ''
    if not api_key or api_key == 'sk-ant-xxxxxxxx':
        raise ValueError(
            "GROQ_API_KEY non définie ou invalide. "
            "Veuillez définir une clé API Groq valide dans les variables d'environnement."
        )

    payload = {
        "model":       GROQ_MODEL,
        "max_tokens":  1500,
        "temperature": 0.7,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    data    = json.dumps(payload).encode('utf-8')
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(
        GROQ_API_URL,
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise ValueError(
            f"Erreur API Groq ({e.code}): {error_body}"
        )
    except urllib.error.URLError as e:
        raise ValueError(
            f"Erreur réseau lors de la connexion à l'API Groq: {str(e)}"
        )

    # Extraire le texte de la réponse (format OpenAI)
    return result['choices'][0]['message']['content']


# ══════════════════════════════════════════════════════════════════════
#  PARSER LA RÉPONSE JSON
# ══════════════════════════════════════════════════════════════════════
def _parser_reponse(texte: str) -> dict:
    """
    Parse la réponse de Claude.
    Claude peut parfois ajouter des backticks markdown — on nettoie.
    """
    texte = texte.strip()

    # Nettoyer les balises markdown si présentes
    if texte.startswith('```json'):
        texte = texte[7:]
    if texte.startswith('```'):
        texte = texte[3:]
    if texte.endswith('```'):
        texte = texte[:-3]

    return json.loads(texte.strip())


# ══════════════════════════════════════════════════════════════════════
#  ROADMAP DE SECOURS (si l'API est indisponible)
# ══════════════════════════════════════════════════════════════════════
def _roadmap_secours(top_domaines: list) -> dict:
    """
    Roadmap générique retournée si l'appel API échoue.
    Évite de bloquer l'élève si Claude Haiku est indisponible.
    """
    domaine = top_domaines[0]['label'] if top_domaines else 'ton domaine'

    return {
        "domaine_principal":       "general",
        "message_encouragement":   (
            f"Tu as un excellent profil pour {domaine} ! "
            "Continue à travailler dur et tu atteindras tes objectifs 🎯"
        ),
        "roadmap": [
            {
                "etape":       1,
                "titre":       "Consolider tes bases académiques",
                "description": "Renforce tes matières principales avant l'entrée à l'université.",
                "actions": [
                    "Révise régulièrement tes cours",
                    "Fais des exercices supplémentaires dans tes matières clés",
                    "Demande de l'aide à tes professeurs si nécessaire",
                ],
                "duree": "Toute l'année",
            },
            {
                "etape":       2,
                "titre":       "Explorer ton domaine d'intérêt",
                "description": "Commence à découvrir le domaine qui te correspond.",
                "actions": [
                    "Regarde des vidéos et tutoriels en ligne",
                    "Lis des articles sur les métiers du domaine",
                    "Parle à des professionnels ou étudiants dans ce domaine",
                ],
                "duree": "3 mois",
            },
            {
                "etape":       3,
                "titre":       "Préparer ton dossier d'orientation",
                "description": "Prépare-toi pour l'orientation universitaire.",
                "actions": [
                    "Renseigne-toi sur les universités tunisiennes",
                    "Prépare tes documents administratifs",
                    "Passe tes examens avec confiance",
                ],
                "duree": "Avant le Bac",
            },
        ],
        "competences_a_developper": [
            "Autonomie dans le travail",
            "Organisation et gestion du temps",
            "Curiosité intellectuelle",
            "Travail en équipe",
            "Communication",
        ],
        "ressources": [
            {
                "titre":               "Khan Academy",
                "type":                "plateforme",
                "lien_ou_description": "https://fr.khanacademy.org",
                "gratuit":             True,
            },
            {
                "titre":               "YouTube Éducation",
                "type":                "plateforme",
                "lien_ou_description": "Chaînes éducatives en arabe et français",
                "gratuit":             True,
            },
            {
                "titre":               "Coursera",
                "type":                "plateforme",
                "lien_ou_description": "Cours gratuits de universités mondiales",
                "gratuit":             True,
            },
            {
                "titre":               "Bibliothèque Numérique Tunisienne",
                "type":                "site web",
                "lien_ou_description": "Ressources académiques accessibles en Tunisie",
                "gratuit":             True,
            },
        ],
    }