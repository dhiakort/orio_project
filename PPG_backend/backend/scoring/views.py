"""
views.py — API endpoints du moteur de scoring ORIO v2
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .scoring import calculer_recommandation
from django.core.exceptions import ObjectDoesNotExist


def _normaliser_specialite(specialite, niveau):
    """Aligne la spécialité User avec les clés du moteur de scoring."""
    if not specialite:
        if niveau == '1ere':
            return 'tronc_commun'
        return ''
    return specialite


class RecommandationView(APIView):
    """
    GET /api/scoring/recommandation/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # ── 1. Niveau ───────────────────────────────────────────────
        niveau = getattr(user, 'niveau', None)
        if not niveau:
            return Response(
                {"error": "Niveau scolaire non défini. Complète ton profil."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── 2. Spécialité actuelle ──────────────────────────────────
        specialite_actuelle = _normaliser_specialite(
            getattr(user, 'specialite', None), niveau
        )

        # ── 3. Notes + scores domaines depuis NotesEleve ────────────
        notes_dict      = {}
        scores_domaines = {}
        try:
            ne          = user.notes
            notes_dict  = _extraire_notes(ne)
            scores_domaines = {
                'score_scientifique': ne.score_scientifique,
                'score_informatique': ne.score_informatique,
                'score_litteraire':   ne.score_litteraire,
                'score_economique':   ne.score_economique,
            }
        except (ObjectDoesNotExist, AttributeError):
            # user may not have related objects; leave defaults
            pass

        # ── 4. RIASEC ───────────────────────────────────────────────
        riasec_dict = {}
        try:
            ri = user.riasec
            riasec_dict = {
                'R': ri.score_realiste,
                'I': ri.score_investigatif,
                'A': ri.score_artistique,
                'S': ri.score_social,
                'E': ri.score_entreprenant,
                'C': ri.score_conventionnel,
            }
        except (ObjectDoesNotExist, AttributeError):
            pass

        # ── 5. Big Five ─────────────────────────────────────────────
        bigfive_dict = {}
        try:
            bf = user.bigfive
            bigfive_dict = {
                'ouverture':       bf.score_ouverture,
                'conscienciosite': bf.score_conscienciosite,
                'extraversion':    bf.score_extraversion,
                'agreabilite':     bf.score_agreabilite,
                'nevrosisme':      bf.score_nevrosisme,
            }
        except (ObjectDoesNotExist, AttributeError):
            pass

        # ── 6. Compétences ──────────────────────────────────────────
        competences_dict = {}
        try:
            comp = user.competences
            competences_dict = {
                'score_calcul':  comp.score_calcul,
                'score_logique': comp.score_logique,
                'score_memoire': comp.score_memoire,
            }
        except (ObjectDoesNotExist, AttributeError):
            pass

        # ── 7. Vérification données minimales ───────────────────────
        if not notes_dict and not riasec_dict and not bigfive_dict:
            return Response(
                {
                    "error": "Données insuffisantes.",
                    "detail": "Saisis tes notes et passe au moins un test."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── 8. Calcul recommandation ────────────────────────────────
        resultat = calculer_recommandation(
            niveau              = niveau,
            specialite_actuelle = specialite_actuelle,
            notes_dict          = notes_dict,
            scores_domaines     = scores_domaines,
            riasec_dict         = riasec_dict,
            bigfive_dict        = bigfive_dict,
            competences_dict    = competences_dict,
        )

        # ── 9. Enrichir la réponse ──────────────────────────────────
        donnees_disponibles = {
            'notes':       bool(notes_dict),
            'riasec':      bool(riasec_dict),
            'bigfive':     bool(bigfive_dict),
            'competences': bool(competences_dict),
        }

        return Response({
            **resultat,
            'profil_complet':      all(donnees_disponibles.values()),
            'donnees_disponibles': donnees_disponibles,
            'niveau':              niveau,
            'specialite':          specialite_actuelle,
        })


class ProfilCompletView(APIView):
    """
    GET /api/scoring/profil-complet/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user   = request.user
        profil = {}

        # Notes
        try:
            ne = user.notes
            profil['notes'] = {
                'moyenne_ponderee':  ne.moyenne_ponderee_annuelle,
                'moyenne_generale':  ne.moyenne_generale_annuelle,
                'niveau_global':     ne.niveau_global_annuel,
                'points_forts':      ne.points_forts_annuels,
                'points_faibles':    ne.points_faibles_annuels,
                'scores_domaines': {
                    'scientifique': ne.score_scientifique,
                    'informatique': ne.score_informatique,
                    'litteraire':   ne.score_litteraire,
                    'economique':   ne.score_economique,
                },
            }
        except (ObjectDoesNotExist, AttributeError):
            profil['notes'] = None

        # Big Five
        try:
            bf = user.bigfive
            profil['bigfive'] = {
                'profil_dominant':   bf.profil_dominant,
                'profil_secondaire': bf.profil_secondaire,
                'scores': {
                    'ouverture':       bf.score_ouverture,
                    'conscienciosite': bf.score_conscienciosite,
                    'extraversion':    bf.score_extraversion,
                    'agreabilite':     bf.score_agreabilite,
                    'nevrosisme':      bf.score_nevrosisme,
                },
            }
        except (ObjectDoesNotExist, AttributeError):
            profil['bigfive'] = None

        # RIASEC
        try:
            ri = user.riasec
            profil['riasec'] = {
                'code_holland': ri.code_holland,
                'scores': {
                    'R': ri.score_realiste,
                    'I': ri.score_investigatif,
                    'A': ri.score_artistique,
                    'S': ri.score_social,
                    'E': ri.score_entreprenant,
                    'C': ri.score_conventionnel,
                },
            }
        except (ObjectDoesNotExist, AttributeError):
            profil['riasec'] = None

        # Compétences
        try:
            co = user.competences
            profil['competences'] = {
                'score_global':  co.score_global,
                'score_calcul':  co.score_calcul,
                'score_logique': co.score_logique,
                'score_memoire': co.score_memoire,
            }
        except (ObjectDoesNotExist, AttributeError):
            profil['competences'] = None

        # Complétion
        profil['completion'] = {
            'notes':       profil['notes']       is not None,
            'bigfive':     profil['bigfive']      is not None,
            'riasec':      profil['riasec']       is not None,
            'competences': profil['competences']  is not None,
            'total': sum([
                profil['notes']       is not None,
                profil['bigfive']     is not None,
                profil['riasec']      is not None,
                profil['competences'] is not None,
            ]),
        }

        return Response(profil)


class RoadmapView(APIView):
    """
    POST /api/scoring/roadmap/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .roadmap import generer_roadmap

        user = request.user

        # Construire le profil
        profil = _construire_profil(user)

        if not profil['notes'] and not profil['riasec']:
            return Response(
                {"error": "Complète tes notes et au moins un test avant de générer ta roadmap."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Récupérer les domaines recommandés
        try:
            niveau              = getattr(user, 'niveau', '4eme_s')
            specialite_actuelle = _normaliser_specialite(
                getattr(user, 'specialite', None), niveau
            )
            ne                  = user.notes

            resultat = calculer_recommandation(
                niveau              = niveau,
                specialite_actuelle = specialite_actuelle,
                notes_dict          = _extraire_notes(ne),
                scores_domaines     = {
                    'score_scientifique': ne.score_scientifique,
                    'score_informatique': ne.score_informatique,
                    'score_litteraire':   ne.score_litteraire,
                    'score_economique':   ne.score_economique,
                },
                riasec_dict      = _get_riasec(user),
                bigfive_dict     = _get_bigfive(user),
                competences_dict = _get_competences(user),
            )
            top_domaines = resultat['resultats']
        except Exception:
            top_domaines = []

        # Générer la roadmap via Claude Haiku
        resultat_rm = generer_roadmap(profil, top_domaines)
        return Response(resultat_rm)


class ChatbotView(APIView):
    """
    POST /api/scoring/chatbot/
    Body: { "question": "..." }
    Returns a short answer derived from the generated roadmap.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .roadmap import generer_roadmap, generer_reponse_chatbot

        user = request.user
        question = (request.data.get('question') or '').strip()
        if not question:
            return Response({'error': 'Question manquante.'}, status=status.HTTP_400_BAD_REQUEST)

        profil = _construire_profil(user)

        # récupérer domaines recommandés (silencieusement)
        try:
            niveau = getattr(user, 'niveau', '4eme_s')
            specialite_actuelle = _normaliser_specialite(getattr(user, 'specialite', None), niveau)
            ne = user.notes
            resultat = calculer_recommandation(
                niveau = niveau,
                specialite_actuelle = specialite_actuelle,
                notes_dict = _extraire_notes(ne),
                scores_domaines = {
                    'score_scientifique': ne.score_scientifique,
                    'score_informatique': ne.score_informatique,
                    'score_litteraire':   ne.score_litteraire,
                    'score_economique':   ne.score_economique,
                },
                riasec_dict = _get_riasec(user),
                bigfive_dict = _get_bigfive(user),
                competences_dict = _get_competences(user),
            )
            top_domaines = resultat.get('resultats', [])
        except (ObjectDoesNotExist, AttributeError):
            top_domaines = []

        roadmap_res = generer_roadmap(profil, top_domaines)
        roadmap = roadmap_res.get('roadmap') or []

        chatbot_res = generer_reponse_chatbot(question, profil, roadmap)

        # Simple keyword matching fallback
        q_tokens = [t.lower() for t in question.split() if len(t) > 2]
        matches = []
        for step in roadmap:
            hay = ' '.join([
                str(step.get('titre', '')),
                str(step.get('description', '')),
                ' '.join(step.get('actions', []))
            ]).lower()
            if any(tok in hay for tok in q_tokens):
                matches.append(step)

        if chatbot_res.get('success') and chatbot_res.get('answer'):
            answer = {
                'success': True,
                'question': question,
                'answer': chatbot_res['answer'].strip(),
                'matches': [],
                'meta': {
                    'from_cache': False,
                    'roadmap_generated': roadmap_res.get('success', False),
                }
            }
        else:
            fallback_matches = matches if matches else roadmap
            answer = {
                'success': bool(fallback_matches),
                'question': question,
                'answer': chatbot_res.get('error'),
                'matches': fallback_matches,
                'error': chatbot_res.get('error'),
                'meta': {
                    'from_cache': False,
                    'roadmap_generated': roadmap_res.get('success', False),
                }
            }

        return Response(answer)


class GrokChatbotView(APIView):
    """
    POST /api/scoring/chatbot/grok/
    Body: {
        "question": "...",
        "student_id": "...",  # optional, for counselor mode
        "history": [...]      # optional list of past messages
    }
    Queries xAI's Grok API. If it is rate-limited or unavailable,
    gracefully falls back to the local or Claude-based chatbot.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .roadmap import generer_roadmap, generer_reponse_chatbot, _reponse_chatbot_fallback
        from .grok_client import call_grok_api
        from django.contrib.auth import get_user_model

        User = get_user_model()
        question = (request.data.get('question') or '').strip()
        if not question:
            return Response({'error': 'Question manquante.'}, status=status.HTTP_400_BAD_REQUEST)

        student_id = request.data.get('student_id')
        history = request.data.get('history') or []

        # 1. Determine target user (Student vs Counselor mode)
        target_user = request.user
        is_counselor_mode = False
        if request.user.is_staff and student_id:
            try:
                target_user = User.objects.get(id=student_id)
                is_counselor_mode = True
            except User.DoesNotExist:
                return Response({'error': f"Élève avec l'ID {student_id} introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # 2. Build profile and load roadmap for prompt context
        profil = _construire_profil(target_user)
        try:
            niveau = getattr(target_user, 'niveau', '4eme_s')
            specialite_actuelle = _normaliser_specialite(getattr(target_user, 'specialite', None), niveau)
            ne = target_user.notes
            resultat = calculer_recommandation(
                niveau = niveau,
                specialite_actuelle = specialite_actuelle,
                notes_dict = _extraire_notes(ne),
                scores_domaines = {
                    'score_scientifique': ne.score_scientifique,
                    'score_informatique': ne.score_informatique,
                    'score_litteraire':   ne.score_litteraire,
                    'score_economique':   ne.score_economique,
                },
                riasec_dict = _get_riasec(target_user),
                bigfive_dict = _get_bigfive(target_user),
                competences_dict = _get_competences(target_user),
            )
            top_domaines = resultat.get('resultats', [])
        except (ObjectDoesNotExist, AttributeError):
            top_domaines = []

        roadmap_res = generer_roadmap(profil, top_domaines)
        roadmap = roadmap_res.get('roadmap') or []

        # Format details for prompt
        niveau_labels = {
            '1ere':   '1ère année secondaire',
            '2eme_s': '2ème année secondaire',
            '3eme_s': '3ème année secondaire',
            '4eme_s': 'Terminale (Bac)',
        }
        niveau_label = niveau_labels.get(profil.get('niveau', ''), 'Non défini')
        specialite_label = target_user.get_specialite_display() if target_user.specialite else 'Non définie'

        notes_info = profil.get('notes') or {}
        moy = notes_info.get('moyenne_ponderee', 'Non disponible')
        forts = ', '.join(notes_info.get('points_forts', [])) or 'Aucun'
        faibles = ', '.join(notes_info.get('points_faibles', [])) or 'Aucun'
        bf_info = profil.get('bigfive') or {}
        ri_info = profil.get('riasec') or {}
        comp_info = profil.get('competences') or {}

        étapes = []
        for step in roadmap:
            titre = step.get('titre', 'Sans titre')
            description = step.get('description', '')
            actions_text = ' ; '.join(step.get('actions', [])) if step.get('actions') else ''
            étapes.append(f"Étape {step.get('etape', '?')}: {titre}. {description} Actions: {actions_text}")
        étap_text = '\n'.join(étapes)

        # 3. Construct Tailored System Prompt based on role
        if is_counselor_mode:
            system_prompt = f"""Tu es l'assistant de conseils d'orientation IA d'ORIO, une plateforme d'orientation scolaire en Algérie.
Ton rôle est d'aider un conseiller d'orientation scolaire (le staff ORIO) à analyser et guider un élève.
Tu t'adresses directement au conseiller en français. Sois professionnel, précis, pragmatique et donne des conseils stratégiques pour l'accompagnement de cet élève.

PROFIL DE L'ÉLÈVE ANALYSÉ :
- Nom de l'élève : {target_user.get_full_name()}
- Niveau : {niveau_label}
- Spécialité : {specialite_label}
- Moyenne : {moy}/20
- Forces académiques : {forts}
- Points à améliorer : {faibles}
- Profil dominant (Big Five) : {bf_info.get('profil_dominant', 'Non disponible')}
- Code RIASEC (Intérêts) : {ri_info.get('code_holland', 'Non disponible')}
- Score cognitif : {comp_info.get('score_global', 'Non disponible')}/100

ROADMAP PERSONNALISÉE DE L'ÉLÈVE :
{étap_text}

Réponds à la question du conseiller de manière analytique et constructive. Sois bref (max 6 lignes)."""
        else:
            system_prompt = f"""Tu es l'assistant IA d'ORIO, une plateforme d'orientation scolaire et professionnelle pour les élèves algériens.
Tu réponds directement à l'élève en français de manière bienveillante, motivante et pédagogique.

PROFIL DE L'ÉLÈVE :
- Prénom : {target_user.first_name}
- Niveau : {niveau_label}
- Spécialité : {specialite_label}
- Moyenne pondérée : {moy}/20
- Matières fortes : {forts}
- Matières faibles : {faibles}
- Profil dominant (Big Five) : {bf_info.get('profil_dominant', 'Non disponible')}
- Code RIASEC : {ri_info.get('code_holland', 'Non disponible')}
- Score cognitif : {comp_info.get('score_global', 'Non disponible')}/100

ROADMAP PERSONNALISÉE :
{étap_text}

Sois concis et direct. Réponds en français de manière structurée et motivante (max 5-6 lignes). Réponds en s'adressant à l'élève."""

        # 4. Attempt Grok API call
        messages = [{"role": "system", "content": system_prompt}]
        
        # Append history if valid
        for msg in history[-10:]:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                messages.append({"role": msg['role'], "content": msg['content']})
        
        messages.append({"role": "user", "content": question})

        try:
            answer = call_grok_api(messages)
            return Response({
                "success": True,
                "answer": answer,
                "fallback": False,
                "question": question,
                "warning": None
            })
        except Exception as e:
            # Fallback Mechanism: trigger local/Groq backup chatbot
            import logging
            logging.getLogger('chatbot').warning(f"Grok API failed: {str(e)}. Triggering chatbot fallback.")
            
            # Use existing chatbot generation logic
            chatbot_res = generer_reponse_chatbot(question, profil, roadmap)
            fallback_answer = chatbot_res.get('answer') or _reponse_chatbot_fallback(question, roadmap)
            
            return Response({
                "success": True,
                "answer": fallback_answer,
                "fallback": True,
                "question": question,
                "warning": "L'API Grok AI est temporairement indisponible ou surchargée. Réponses générées en mode secours."
            })


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════
def _extraire_notes(notes_eleve) -> dict:
    """Reconstruit {matiere: moyenne_annuelle} depuis les trimestres."""
    matieres_valeurs = {}
    try:
        for trim in notes_eleve.trimestres.prefetch_related('notes').all():
            for note in trim.notes.all():
                matieres_valeurs.setdefault(note.matiere, []).append(note.valeur)
    except Exception:
        pass
    return {
        mat: round(sum(vals) / len(vals), 2)
        for mat, vals in matieres_valeurs.items()
    }


def _construire_profil(user) -> dict:
    profil = {'niveau': getattr(user, 'niveau', None)}
    try:
        ne = user.notes
        profil['notes'] = {
            'moyenne_ponderee': ne.moyenne_ponderee_annuelle,
            'points_forts':     ne.points_forts_annuels,
            'points_faibles':   ne.points_faibles_annuels,
        }
    except Exception:
        profil['notes'] = None
    try:
        bf = user.bigfive
        profil['bigfive'] = {
            'profil_dominant':   bf.profil_dominant,
            'profil_secondaire': bf.profil_secondaire,
        }
    except Exception:
        profil['bigfive'] = None
    try:
        ri = user.riasec
        profil['riasec'] = {'code_holland': ri.code_holland}
    except Exception:
        profil['riasec'] = None
    try:
        co = user.competences
        profil['competences'] = {'score_global': co.score_global}
    except Exception:
        profil['competences'] = None
    return profil


def _get_riasec(user) -> dict:
    try:
        ri = user.riasec
        return {
            'R': ri.score_realiste,   'I': ri.score_investigatif,
            'A': ri.score_artistique, 'S': ri.score_social,
            'E': ri.score_entreprenant, 'C': ri.score_conventionnel,
        }
    except Exception:
        return {}


def _get_bigfive(user) -> dict:
    try:
        bf = user.bigfive
        return {
            'ouverture':       bf.score_ouverture,
            'conscienciosite': bf.score_conscienciosite,
            'extraversion':    bf.score_extraversion,
            'agreabilite':     bf.score_agreabilite,
            'nevrosisme':      bf.score_nevrosisme,
        }
    except Exception:
        return {}

def _get_competences(user) -> dict:
    try:
        co = user.competences
        return {
            'score_calcul':  co.score_calcul,
            'score_logique': co.score_logique,
            'score_memoire': co.score_memoire,
        }
    except Exception:
        return {}
