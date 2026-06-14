import strawberry
import strawberry_django
from strawberry import Info
from django.contrib.auth import get_user_model

from accounts.models import User
from notes.models import NotesEleve, Trimestre, NoteMatiere
from tests.models import BigFiveResult, RiasecResult, CompetencesResult

# Define GraphQL Types

@strawberry_django.type(NoteMatiere)
class NoteMatiereType:
    id: strawberry.ID
    matiere: str
    valeur: float
    coefficient: int

@strawberry_django.type(Trimestre)
class TrimestreType:
    id: strawberry.ID
    numero: int
    moyenne_generale: float | None
    moyenne_ponderee: float | None
    niveau_global: str | None

    @strawberry.field
    def points_forts(self) -> list[str]:
        return self.points_forts or []

    @strawberry.field
    def points_faibles(self) -> list[str]:
        return self.points_faibles or []

    @strawberry.field
    def notes(self) -> list[NoteMatiereType]:
        return list(self.notes.all())

@strawberry_django.type(NotesEleve)
class NotesEleveType:
    id: strawberry.ID
    moyenne_generale_annuelle: float | None
    moyenne_ponderee_annuelle: float | None
    niveau_global_annuel: str | None
    score_scientifique: float | None
    score_litteraire: float | None
    score_economique: float | None
    score_informatique: float | None

    @strawberry.field
    def points_forts_annuels(self) -> list[str]:
        return self.points_forts_annuels or []

    @strawberry.field
    def points_faibles_annuels(self) -> list[str]:
        return self.points_faibles_annuels or []

    @strawberry.field
    def trimestres(self) -> list[TrimestreType]:
        return list(self.trimestres.all())

@strawberry_django.type(BigFiveResult)
class BigFiveResultType:
    id: strawberry.ID
    score_ouverture: float
    score_conscienciosite: float
    score_extraversion: float
    score_agreabilite: float
    score_nevrosisme: float
    profil_dominant: str
    profil_secondaire: str

@strawberry_django.type(RiasecResult)
class RiasecResultType:
    id: strawberry.ID
    score_realiste: float
    score_investigatif: float
    score_artistique: float
    score_social: float
    score_entreprenant: float
    score_conventionnel: float
    code_holland: str

@strawberry_django.type(CompetencesResult)
class CompetencesResultType:
    id: strawberry.ID
    score_calcul: float | None
    score_logique: float | None
    score_memoire: float | None
    score_global: float | None

@strawberry_django.type(User)
class UserType:
    id: strawberry.ID
    email: str
    first_name: str
    last_name: str
    niveau: str | None
    specialite: str | None
    is_staff: bool

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @strawberry.field
    def notes(self) -> NotesEleveType | None:
        try:
            return self.notes
        except Exception:
            return None

    @strawberry.field
    def bigfive(self) -> BigFiveResultType | None:
        try:
            return self.bigfive
        except Exception:
            return None

    @strawberry.field
    def riasec(self) -> RiasecResultType | None:
        try:
            return self.riasec
        except Exception:
            return None

    @strawberry.field
    def competences(self) -> CompetencesResultType | None:
        try:
            return self.competences
        except Exception:
            return None


# Root Query definitions

@strawberry.type
class Query:
    @strawberry.field
    def me(self, info: Info) -> UserType | None:
        """Returns the currently authenticated user"""
        user = info.context.request.user
        if user and user.is_authenticated:
            return user
        return None

    @strawberry.field
    def students(self, info: Info) -> list[UserType]:
        """Returns a list of all students (is_staff=False). Restricted for staff only."""
        user = info.context.request.user
        if not user or not user.is_authenticated or not user.is_staff:
            raise PermissionError("Access denied. Staff only.")
        return list(User.objects.filter(is_staff=False))

    @strawberry.field
    def student_profile(self, info: Info, id: strawberry.ID) -> UserType | None:
        """Returns a single student profile if the requester has permission"""
        user = info.context.request.user
        if not user or not user.is_authenticated:
            raise PermissionError("Authentication required.")

        try:
            target_user = User.objects.get(id=id)
        except User.DoesNotExist:
            return None

        # A student can only see their own profile. Staff can see any student.
        if str(user.id) == str(target_user.id) or user.is_staff:
            return target_user

        raise PermissionError("Access denied.")

schema = strawberry.Schema(query=Query)
