from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import NotesEleve, Trimestre
from .serializers import NotesEleveSerializer, TrimestreUpsertSerializer


class NotesView(APIView):
    """
    GET    /api/notes/              → récupère les notes complètes (3 trimestres + annuel)
    POST   /api/notes/              → crée ou met à jour un trimestre (upsert)
    DELETE /api/notes/              → supprime TOUTES les notes de l'élève
    DELETE /api/notes/?trimestre=N  → supprime uniquement le trimestre N (1, 2 ou 3)
    """
    permission_classes = [IsAuthenticated]

    # ── GET ──────────────────────────────────────────────────────────
    def get(self, request):
        try:
            notes = (
                NotesEleve.objects
                .prefetch_related('trimestres__notes')
                .get(user=request.user)
            )
            return Response(NotesEleveSerializer(notes).data)
        except NotesEleve.DoesNotExist:
            return Response(
                {"detail": "Aucune note saisie pour le moment."},
                status=status.HTTP_404_NOT_FOUND,
            )

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        """
        Payload attendu :
        {
            "trimestre": 1,
            "notes": {
                "mathematiques": 15.5,
                "physique": 12,
                ...
            }
        }
        Upsert : crée les objets s'ils n'existent pas, met à jour sinon.
        Les matières absentes du payload sont supprimées du trimestre.
        """
        serializer = TrimestreUpsertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        notes_eleve = serializer.save(user=request.user)

        # Recharger avec les relations pour la réponse
        notes_eleve.refresh_from_db()
        notes_eleve_full = (
            NotesEleve.objects
            .prefetch_related('trimestres__notes')
            .get(pk=notes_eleve.pk)
        )

        t_num = serializer.validated_data['trimestre']
        return Response(
            {
                "message": f"Trimestre {t_num} sauvegardé avec succès ✅",
                "data": NotesEleveSerializer(notes_eleve_full).data,
            },
            status=status.HTTP_200_OK,
        )

    # ── DELETE ───────────────────────────────────────────────────────
    def delete(self, request):
        """
        Sans paramètre  → supprime NotesEleve et tout ce qui est lié (cascade).
        ?trimestre=N    → supprime uniquement le Trimestre N ; recalcule l'annuel.
        """
        t_param = request.query_params.get('trimestre')

        try:
            notes_eleve = NotesEleve.objects.get(user=request.user)
        except NotesEleve.DoesNotExist:
            return Response(
                {"detail": "Aucune note à supprimer."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Suppression d'un seul trimestre
        if t_param is not None:
            try:
                t_num = int(t_param)
                assert t_num in (1, 2, 3)
            except (ValueError, AssertionError):
                return Response(
                    {"detail": "Le paramètre 'trimestre' doit être 1, 2 ou 3."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                trimestre = Trimestre.objects.get(notes_eleve=notes_eleve, numero=t_num)
                trimestre.delete()
                # Recalculer les indicateurs annuels après suppression
                notes_eleve.recalculer_annuel()
                return Response({"message": f"Trimestre {t_num} supprimé."})
            except Trimestre.DoesNotExist:
                return Response(
                    {"detail": f"Le trimestre {t_num} n'existe pas."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # Suppression totale
        notes_eleve.delete()
        return Response({"message": "Toutes les notes supprimées."})