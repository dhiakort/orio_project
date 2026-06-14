from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from .coefficients import COEFFICIENTS, resolve_section_key


# ─────────────────────────────────────────────
#  Toutes les matières possibles (référence)
# ─────────────────────────────────────────────
ALL_MATIERES = [
    'mathematiques', 'physique', 'sciences_naturelles', 'informatique',
    'technologie', 'arabe', 'francais', 'anglais', 'philosophie',
    'histoire_geo', 'education_islamique', 'economie', 'gestion', 'sport',
]

# Matières regroupées par domaine pour les scores
DOMAINES = {
    'scientifique': ['mathematiques', 'physique', 'sciences_naturelles'],
    'informatique': ['mathematiques', 'physique', 'informatique'],
    'litteraire':   ['francais', 'arabe', 'anglais', 'philosophie', 'histoire_geo'],
    'economique':   ['mathematiques', 'economie', 'gestion', 'anglais', 'francais'],
}


# ─────────────────────────────────────────────
#  Énumérations
# ─────────────────────────────────────────────
class NumeroTrimestre(models.IntegerChoices):
    T1 = 1, '1er Trimestre'
    T2 = 2, '2ème Trimestre'
    T3 = 3, '3ème Trimestre'


class NiveauGlobal(models.TextChoices):
    EXCELLENT   = 'Excellent',   'Excellent (≥ 16)'
    BIEN        = 'Bien',        'Bien (≥ 13)'
    PASSABLE    = 'Passable',    'Passable (≥ 10)'
    INSUFFISANT = 'Insuffisant', 'Insuffisant (< 10)'


# ═══════════════════════════════════════════════════════
#  TABLE 1 — NotesEleve  (1 ligne par élève)
# ═══════════════════════════════════════════════════════
class NotesEleve(models.Model):
    """
    Conteneur principal lié à l'utilisateur.
    Stocke uniquement les indicateurs annuels agrégés.
    Les notes par matière vivent dans NoteMatiere via Trimestre.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes',
    )

    # ── Indicateurs annuels (calculés à chaque save de trimestre) ──
    moyenne_generale_annuelle  = models.FloatField(null=True, blank=True)
    moyenne_ponderee_annuelle  = models.FloatField(null=True, blank=True)
    niveau_global_annuel       = models.CharField(
        max_length=20,
        choices=NiveauGlobal.choices,
        blank=True,
    )
    points_forts_annuels       = models.JSONField(default=list, blank=True)
    points_faibles_annuels     = models.JSONField(default=list, blank=True)

    # Scores domaines annuels (moyennes pondérées sur les 3 trimestres)
    score_scientifique = models.FloatField(null=True, blank=True)
    score_litteraire   = models.FloatField(null=True, blank=True)
    score_economique   = models.FloatField(null=True, blank=True)
    score_informatique = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Notes élève'
        verbose_name_plural = 'Notes élèves'

    def __str__(self):
        return f"Notes de {self.user.get_full_name()}"

    # ── Helpers section / coefficients ──────────────────────────────
    def _get_section_key(self):
        return resolve_section_key(
            getattr(self.user, 'specialite', None),
            getattr(self.user, 'niveau', None),
        )

    def get_coefficients(self):
        return COEFFICIENTS.get(self._get_section_key(), {})

    # ── Recalcul des indicateurs annuels ────────────────────────────
    def recalculer_annuel(self):
        """
        Agrège les moyennes pondérées des trimestres existants
        et recalcule les indicateurs annuels + scores domaines.
        Appelé automatiquement depuis Trimestre.save().
        """
        coeffs    = self.get_coefficients()
        trimestres = self.trimestres.prefetch_related('notes').all()

        if not trimestres.exists():
            self.moyenne_generale_annuelle = None
            self.moyenne_ponderee_annuelle = None
            self.niveau_global_annuel      = ''
            self.points_forts_annuels      = []
            self.points_faibles_annuels    = []
            self.score_scientifique        = None
            self.score_litteraire          = None
            self.score_economique          = None
            self.score_informatique        = None
            self.save()
            return

        # Moyenne annuelle = moyenne des moyennes pondérées des trimestres
        moyennes_pond  = [t.moyenne_ponderee for t in trimestres if t.moyenne_ponderee is not None]
        moyennes_simpl = [t.moyenne_generale  for t in trimestres if t.moyenne_generale  is not None]

        self.moyenne_ponderee_annuelle = (
            round(sum(moyennes_pond) / len(moyennes_pond), 2) if moyennes_pond else None
        )
        self.moyenne_generale_annuelle = (
            round(sum(moyennes_simpl) / len(moyennes_simpl), 2) if moyennes_simpl else None
        )

        # Niveau annuel
        m = self.moyenne_ponderee_annuelle or self.moyenne_generale_annuelle
        if m is not None:
            if m >= 16:   self.niveau_global_annuel = NiveauGlobal.EXCELLENT
            elif m >= 13: self.niveau_global_annuel = NiveauGlobal.BIEN
            elif m >= 10: self.niveau_global_annuel = NiveauGlobal.PASSABLE
            else:          self.niveau_global_annuel = NiveauGlobal.INSUFFISANT

        # Moyenne annuelle par matière (sur tous les trimestres)
        matieres_annuelles = {}
        for trim in trimestres:
            for note in trim.notes.all():
                matieres_annuelles.setdefault(note.matiere, []).append(note.valeur)
        moy_mat = {
            mat: round(sum(vals) / len(vals), 2)
            for mat, vals in matieres_annuelles.items()
        }

        # Points forts / faibles annuels
        self.points_forts_annuels   = [m for m, v in moy_mat.items() if v >= 14]
        self.points_faibles_annuels = [m for m, v in moy_mat.items() if v <  10]

        # Scores domaines
        def score_domaine(mats_domaine):
            items = [
                (moy_mat[m], coeffs.get(m, {}).get('coeff', 1))
                for m in mats_domaine if m in moy_mat
            ]
            if not items:
                return None
            pts = sum(v * c for v, c in items)
            cs  = sum(c for _, c in items)
            return round(pts / cs, 2) if cs else None

        self.score_scientifique = score_domaine(DOMAINES['scientifique'])
        self.score_informatique = score_domaine(DOMAINES['informatique'])
        self.score_litteraire   = score_domaine(DOMAINES['litteraire'])
        self.score_economique   = score_domaine(DOMAINES['economique'])

        self.save()


# ═══════════════════════════════════════════════════════
#  TABLE 2 — Trimestre  (max 3 lignes par élève)
# ═══════════════════════════════════════════════════════
class Trimestre(models.Model):
    """
    Un trimestre scolaire pour un élève.
    Contient les indicateurs calculés pour CE trimestre.
    Les notes matière vivent dans NoteMatiere.
    """
    notes_eleve = models.ForeignKey(
        NotesEleve,
        on_delete=models.CASCADE,
        related_name='trimestres',
    )
    numero = models.IntegerField(
        choices=NumeroTrimestre.choices,
        help_text='1, 2 ou 3',
    )

    # Indicateurs calculés pour ce trimestre
    moyenne_generale  = models.FloatField(null=True, blank=True)
    moyenne_ponderee  = models.FloatField(null=True, blank=True)
    niveau_global     = models.CharField(
        max_length=20,
        choices=NiveauGlobal.choices,
        blank=True,
    )
    points_forts      = models.JSONField(default=list, blank=True)
    points_faibles    = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Trimestre'
        unique_together     = ('notes_eleve', 'numero')   # un seul T1 par élève
        ordering            = ['numero']

    def __str__(self):
        return f"T{self.numero} — {self.notes_eleve.user.get_full_name()}"

    # ── Calcul des indicateurs du trimestre ─────────────────────────
    def calculer_indicateurs(self):
        """Recalcule moyennes et points depuis les NoteMatiere liées."""
        coeffs = self.notes_eleve.get_coefficients()
        notes  = list(self.notes.all())

        if not notes:
            self.moyenne_generale = None
            self.moyenne_ponderee = None
            self.niveau_global    = ''
            self.points_forts     = []
            self.points_faibles   = []
            return

        # Moyenne simple
        valeurs = [n.valeur for n in notes]
        self.moyenne_generale = round(sum(valeurs) / len(valeurs), 2)

        # Moyenne pondérée (selon coefficients de la section)
        total_pts, total_c = 0, 0
        for note in notes:
            c = coeffs.get(note.matiere, {}).get('coeff', 1)
            total_pts += note.valeur * c
            total_c   += c
        self.moyenne_ponderee = round(total_pts / total_c, 2) if total_c else self.moyenne_generale

        # Niveau
        m = self.moyenne_ponderee
        if m >= 16:   self.niveau_global = NiveauGlobal.EXCELLENT
        elif m >= 13: self.niveau_global = NiveauGlobal.BIEN
        elif m >= 10: self.niveau_global = NiveauGlobal.PASSABLE
        else:          self.niveau_global = NiveauGlobal.INSUFFISANT

        # Points forts / faibles
        self.points_forts   = [n.matiere for n in notes if n.valeur >= 14]
        self.points_faibles = [n.matiere for n in notes if n.valeur <  10]

    def save(self, *args, **kwargs):
        # Si l'objet existe déjà, calculer avant de sauver
        if self.pk is not None:
            self.calculer_indicateurs()
        super().save(*args, **kwargs)
        # Propager vers les indicateurs annuels
        self.notes_eleve.recalculer_annuel()

# ═══════════════════════════════════════════════════════
#  TABLE 3 — NoteMatiere  (max 14 lignes par trimestre)
# ═══════════════════════════════════════════════════════
class NoteMatiere(models.Model):
    """
    Une note pour une matière dans un trimestre donné.
    Le coefficient est dénormalisé ici pour conserver l'historique
    même si la section de l'élève change.
    """
    trimestre = models.ForeignKey(
        Trimestre,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    matiere = models.CharField(
        max_length=50,
        help_text='Ex : mathematiques, physique, arabe…',
    )
    valeur = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text='Note sur 20',
    )
    coefficient = models.PositiveSmallIntegerField(
        default=1,
        help_text='Coefficient selon la section de l\'élève',
    )

    class Meta:
        verbose_name        = 'Note matière'
        unique_together     = ('trimestre', 'matiere')  # une seule note par matière/trimestre
        ordering            = ['matiere']

    def __str__(self):
        return f"{self.matiere} : {self.valeur}/20 (T{self.trimestre.numero})"

    def save(self, *args, **kwargs):
        # Auto-remplir le coefficient depuis la section de l'élève
        if not self.coefficient or self.coefficient == 1:
            coeffs = self.trimestre.notes_eleve.get_coefficients()
            self.coefficient = coeffs.get(self.matiere, {}).get('coeff', 1)
        super().save(*args, **kwargs)
        # Recalculer les indicateurs du trimestre parent
        self.trimestre.save()