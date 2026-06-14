from rest_framework import serializers
from .models import BigFiveResult, RiasecResult, CompetencesResult


class BigFiveSerializer(serializers.ModelSerializer):
    """
    Reçoit les 5 scores depuis le frontend (0-100).
    Le profil dominant/secondaire est calculé automatiquement dans model.save().
    """
    class Meta:
        model  = BigFiveResult
        fields = [
            'score_ouverture', 'score_conscienciosite', 'score_extraversion',
            'score_agreabilite', 'score_nevrosisme',
            'profil_dominant', 'profil_secondaire',
            'updated_at',
        ]
        read_only_fields = ['profil_dominant', 'profil_secondaire', 'updated_at']

    def validate(self, attrs):
        """Vérifie que tous les 5 scores sont présents."""
        required = ['score_ouverture','score_conscienciosite','score_extraversion',
                    'score_agreabilite','score_nevrosisme']
        for field in required:
            if attrs.get(field) is None:
                raise serializers.ValidationError(f"{field} est requis.")
        return attrs


class RiasecSerializer(serializers.ModelSerializer):
    """
    Reçoit les 6 scores RIASEC depuis le frontend (0-100).
    Le code Holland est calculé automatiquement dans model.save().
    """
    class Meta:
        model  = RiasecResult
        fields = [
            'score_realiste', 'score_investigatif', 'score_artistique',
            'score_social', 'score_entreprenant', 'score_conventionnel',
            'code_holland', 'updated_at',
        ]
        read_only_fields = ['code_holland', 'updated_at']

    def validate(self, attrs):
        required = ['score_realiste','score_investigatif','score_artistique',
                    'score_social','score_entreprenant','score_conventionnel']
        for field in required:
            if attrs.get(field) is None:
                raise serializers.ValidationError(f"{field} est requis.")
        return attrs


class CompetencesSerializer(serializers.ModelSerializer):
    """
    Reçoit les scores des 3 jeux cognitifs.
    Le score_global est calculé automatiquement dans model.save().
    Upsert partiel possible (ex: soumettre jeu par jeu).
    """
    class Meta:
        model  = CompetencesResult
        fields = [
            'score_calcul', 'score_logique', 'score_memoire',
            'calcul_bonnes_reponses', 'calcul_temps_moyen_ms',
            'logique_bonnes_reponses', 'memoire_niveau_max',
            'score_global', 'updated_at',
        ]
        read_only_fields = ['score_global', 'updated_at']

    def validate(self, attrs):
        """Au moins un score de jeu doit être présent."""
        scores = [attrs.get('score_calcul'), attrs.get('score_logique'), attrs.get('score_memoire')]
        if all(s is None for s in scores):
            raise serializers.ValidationError("Au moins un score de jeu est requis.")
        return attrs


# ── Serializer synthèse pour la page résultats ────────────────────
class ProfilCompletSerializer(serializers.Serializer):
    """
    Vue synthétique de tous les tests d'un utilisateur.
    Utilisé par GET /api/tests/profil/ pour la page résultats finale.
    """
    bigfive     = BigFiveSerializer(allow_null=True)
    riasec      = RiasecSerializer(allow_null=True)
    competences = CompetencesSerializer(allow_null=True)
    completion  = serializers.SerializerMethodField()

    def get_completion(self, obj):
        return {
            'bigfive':     obj.get('bigfive') is not None,
            'riasec':      obj.get('riasec') is not None,
            'competences': obj.get('competences') is not None,
            'total':       sum([
                obj.get('bigfive') is not None,
                obj.get('riasec') is not None,
                obj.get('competences') is not None,
            ]),
        }