from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):

    class NiveauScolaire(models.TextChoices):
        PREMIERE   = '1ere',  '1ère année secondaire'
        DEUXIEME   = '2eme_s','2ème année secondaire'
        TROISIEME  = '3eme_s','3ème année secondaire'
        TERMINALE  = '4eme_s','4ème année secondaire (Bac)'
    
    class Specialite(models.TextChoices):
        # 2ème année
        SCIENTIFIQUE = 'scientifique', 'Scientifique'
        ECONOMIQUE   = 'economique',   'Économie & Gestion'
        LETTRES_2    = 'lettres',      'Lettres'
        INFO_2       = 'informatique', 'Informatique'
        # 3ème / Bac
        MATHS        = 'mathematiques',        'Mathématiques'
        SCIENCES_EXP = 'sciences_exp',         'Sciences Expérimentales'
        SCIENCES_TEC = 'sciences_tech',        'Sciences Techniques'
        SCIENCES_INF = 'sciences_info',        'Sciences de l\'Informatique'
        ECO_GESTION  = 'eco_gestion',          'Économie & Gestion'
        LETTRES_BAC  = 'lettres_bac',          'Lettres'
        SPORT_BAC    = 'sport_bac',            'Sport'

    email        = models.EmailField(unique=True)
    first_name   = models.CharField(max_length=50)
    last_name    = models.CharField(max_length=50)
    niveau       = models.CharField(max_length=10,choices=NiveauScolaire.choices,null=True,blank=True)
    specialite   = models.CharField(max_length=30, choices=Specialite.choices, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'Utilisateur'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_niveau_display_label(self):
        return self.get_niveau_display()
