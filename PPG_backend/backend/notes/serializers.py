from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import NotesEleve, Trimestre, NoteMatiere
from .coefficients import COEFFICIENTS, resolve_section_key

User = get_user_model()

# ──────────────────────────────────────────────────────────────────────
#  Labels lisibles pour les matières
# ──────────────────────────────────────────────────────────────────────
LABELS = {
    'mathematiques':       'Mathématiques',
    'physique':            'Physique',
    'sciences_naturelles': 'Sciences naturelles',
    'informatique':        'Informatique',
    'technologie':         'Technologie',
    'arabe':               'Arabe',
    'francais':            'Français',
    'anglais':             'Anglais',
    'philosophie':         'Philosophie',
    'histoire_geo':        'Histoire-Géo',
    'education_islamique': 'Éd. islamique',
    'education_civique':   'Éd. civique',
    'economie':            'Économie',
    'gestion':             'Gestion',
    'sport':               'Sport',
}


# ══════════════════════════════════════════════════════════════════════
#  NoteMatiere
# ══════════════════════════════════════════════════════════════════════
class NoteMatiereSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model  = NoteMatiere
        fields = ('matiere', 'valeur', 'coefficient', 'label')
        read_only_fields = ('coefficient', 'label')

    def get_label(self, obj):
        return LABELS.get(obj.matiere, obj.matiere)

    def validate_valeur(self, value):
        if not (0 <= value <= 20):
            raise serializers.ValidationError("La note doit être entre 0 et 20.")
        return value


# ══════════════════════════════════════════════════════════════════════
#  Trimestre (lecture imbriquée)
# ══════════════════════════════════════════════════════════════════════
class TrimestreSerializer(serializers.ModelSerializer):
    notes = NoteMatiereSerializer(many=True, read_only=True)

    points_forts_labels   = serializers.SerializerMethodField()
    points_faibles_labels = serializers.SerializerMethodField()

    class Meta:
        model = Trimestre
        fields = (
            'numero',
            'moyenne_generale',
            'moyenne_ponderee',
            'niveau_global',
            'points_forts',
            'points_faibles',
            'points_forts_labels',
            'points_faibles_labels',
            'notes',
            'updated_at',
        )
        read_only_fields = fields  # tout est en lecture dans ce serializer

    def _labels(self, keys):
        return [LABELS.get(k, k) for k in keys]

    def get_points_forts_labels(self, obj):
        return self._labels(obj.points_forts)

    def get_points_faibles_labels(self, obj):
        return self._labels(obj.points_faibles)


# ══════════════════════════════════════════════════════════════════════
#  NotesEleve (lecture complète)
# ══════════════════════════════════════════════════════════════════════
class NotesEleveSerializer(serializers.ModelSerializer):
    trimestres = TrimestreSerializer(many=True, read_only=True)

    points_forts_annuels_labels   = serializers.SerializerMethodField()
    points_faibles_annuels_labels = serializers.SerializerMethodField()
    coefficients_section          = serializers.SerializerMethodField()

    class Meta:
        model = NotesEleve
        fields = (
            # Indicateurs annuels
            'moyenne_generale_annuelle',
            'moyenne_ponderee_annuelle',
            'niveau_global_annuel',
            'points_forts_annuels',
            'points_faibles_annuels',
            'points_forts_annuels_labels',
            'points_faibles_annuels_labels',
            # Scores domaines
            'score_scientifique',
            'score_litteraire',
            'score_economique',
            'score_informatique',
            # Trimestres imbriqués
            'trimestres',
            # Meta
            'coefficients_section',
            'updated_at',
        )
        read_only_fields = fields

    def _labels(self, keys):
        return [LABELS.get(k, k) for k in keys]

    def get_points_forts_annuels_labels(self, obj):
        return self._labels(obj.points_forts_annuels)

    def get_points_faibles_annuels_labels(self, obj):
        return self._labels(obj.points_faibles_annuels)

    def get_coefficients_section(self, obj):
        key = resolve_section_key(
            getattr(obj.user, 'specialite', None),
            getattr(obj.user, 'niveau', None),
        )
        return COEFFICIENTS.get(key, {})


# ══════════════════════════════════════════════════════════════════════
#  TrimestreUpsert — payload en écriture
#  Format attendu :
#    { "trimestre": 1, "notes": { "mathematiques": 15.5, "physique": 12, … } }
# ══════════════════════════════════════════════════════════════════════
class TrimestreUpsertSerializer(serializers.Serializer):
    trimestre = serializers.IntegerField(min_value=1, max_value=3)
    notes     = serializers.DictField(
        child=serializers.FloatField(min_value=0, max_value=20),
        allow_empty=False,
    )

    def validate_trimestre(self, value):
        if value not in (1, 2, 3):
            raise serializers.ValidationError("Le numéro de trimestre doit être 1, 2 ou 3.")
        return value

    def validate_notes(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("Saisis au moins 1 note.")
        # Vérifier que les valeurs sont entre 0 et 20
        for matiere, val in value.items():
            if not (0 <= val <= 20):
                raise serializers.ValidationError(
                    f"La note de '{matiere}' doit être entre 0 et 20."
                )
        return value

    def save(self, user):
        """
        Upsert : crée ou met à jour NotesEleve → Trimestre → NoteMatiere.
        Retourne l'instance NotesEleve mise à jour.
        """
        t_num  = self.validated_data['trimestre']
        notes_data = self.validated_data['notes']

        # 1. NotesEleve (upsert)
        notes_eleve, _ = NotesEleve.objects.get_or_create(user=user)

        # 2. Trimestre (upsert)
        trimestre, _ = Trimestre.objects.get_or_create(
            notes_eleve=notes_eleve,
            numero=t_num,
        )

        # 3. NoteMatiere — upsert chaque matière, supprimer les absentes
        matieres_recues = set(notes_data.keys())

        # Supprimer les notes qui ne sont plus dans le payload
        trimestre.notes.exclude(matiere__in=matieres_recues).delete()

        # Créer / mettre à jour
        for matiere, valeur in notes_data.items():
            NoteMatiere.objects.update_or_create(
                trimestre=trimestre,
                matiere=matiere,
                defaults={'valeur': valeur},
            )

        # 4. Recalculer indicateurs (trimestre.save() → recalculer_annuel())
        #    NoteMatiere.save() appelle déjà trimestre.save(), mais si on a
        #    seulement supprimé des notes, on force un recalcul explicite.
        trimestre.save()

        return notes_eleve