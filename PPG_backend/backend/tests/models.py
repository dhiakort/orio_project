from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class BigFiveResult(models.Model):
    """
    Résultats du test de personnalité Big Five (OCEAN).
    Scores normalisés sur 100.
    Upsert : un seul résultat par utilisateur (OneToOneField).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bigfive'
    )

    # ── 5 dimensions OCEAN ────────────────────────────────────────
    score_ouverture        = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_conscienciosite  = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_extraversion     = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_agreabilite      = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    score_nevrosisme       = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])

    # ── Profil calculé ────────────────────────────────────────────
    profil_dominant        = models.CharField(max_length=50, blank=True)   # ex: "Ouverture"
    profil_secondaire      = models.CharField(max_length=50, blank=True)   # ex: "Conscienciosité"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Résultat Big Five'

    def __str__(self):
        return f"Big Five — {self.user.email} ({self.profil_dominant})"

    def save(self, *args, **kwargs):
        """Calcule automatiquement le profil dominant avant la sauvegarde."""
        dim_map = {
            'Ouverture':       self.score_ouverture,
            'Conscienciosité': self.score_conscienciosite,
            'Extraversion':    self.score_extraversion,
            'Agréabilité':     self.score_agreabilite,
            'Névrosisme':      self.score_nevrosisme,
        }
        sorted_dims = sorted(dim_map.items(), key=lambda x: x[1], reverse=True)
        self.profil_dominant   = sorted_dims[0][0]
        self.profil_secondaire = sorted_dims[1][0]
        super().save(*args, **kwargs)


class RiasecResult(models.Model):
    """
    Résultats du test d'intérêts RIASEC (Holland Codes).
    Scores normalisés sur 100.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='riasec'
    )

    # ── 6 profils Holland ─────────────────────────────────────────
    score_realiste     = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])  # R
    score_investigatif = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])  # I
    score_artistique   = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])  # A
    score_social       = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])  # S
    score_entreprenant = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])  # E
    score_conventionnel= models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])  # C

    # ── Code Holland dominant (ex: "ISA") ─────────────────────────
    code_holland       = models.CharField(max_length=6, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Résultat RIASEC'

    def __str__(self):
        return f"RIASEC — {self.user.email} ({self.code_holland})"

    def save(self, *args, **kwargs):
        """Calcule le code Holland (top 3 dimensions)."""
        dim_map = {
            'R': self.score_realiste,
            'I': self.score_investigatif,
            'A': self.score_artistique,
            'S': self.score_social,
            'E': self.score_entreprenant,
            'C': self.score_conventionnel,
        }
        top3 = sorted(dim_map.items(), key=lambda x: x[1], reverse=True)[:3]
        self.code_holland = ''.join(k for k, _ in top3)
        super().save(*args, **kwargs)


class CompetencesResult(models.Model):
    """
    Résultats des mini-jeux cognitifs :
      - Jeu 1 : Rapidité mathématique (calcul)
      - Jeu 2 : Raisonnement logique (suites)
      - Jeu 3 : Mémoire visuelle (cartes)
    Scores sur 100.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='competences'
    )

    # ── Scores jeux ───────────────────────────────────────────────
    score_calcul    = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score rapidité mathématique (0-100)"
    )
    score_logique   = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score raisonnement logique (0-100)"
    )
    score_memoire   = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score mémoire visuelle (0-100)"
    )

    # ── Métadonnées jeux ──────────────────────────────────────────
    calcul_bonnes_reponses  = models.IntegerField(null=True, blank=True)
    calcul_temps_moyen_ms   = models.IntegerField(null=True, blank=True, help_text="Temps moyen par question en ms")
    logique_bonnes_reponses = models.IntegerField(null=True, blank=True)
    memoire_niveau_max      = models.IntegerField(null=True, blank=True, help_text="Niveau max atteint au jeu mémoire")

    # ── Score global ──────────────────────────────────────────────
    score_global    = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Résultat Compétences'

    def __str__(self):
        return f"Compétences — {self.user.email}"

    def save(self, *args, **kwargs):
        """Calcule le score global (moyenne des jeux complétés)."""
        scores = [s for s in [self.score_calcul, self.score_logique, self.score_memoire] if s is not None]
        self.score_global = round(sum(scores) / len(scores), 2) if scores else None
        super().save(*args, **kwargs)