from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import BigFiveResult, RiasecResult, CompetencesResult
from .serializers import BigFiveSerializer, RiasecSerializer, CompetencesSerializer, ProfilCompletSerializer


class BigFiveView(APIView):
    """
    GET    /api/tests/bigfive/  → récupère les résultats Big Five
    POST   /api/tests/bigfive/  → crée ou met à jour (upsert)
    DELETE /api/tests/bigfive/  → supprime
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            result = BigFiveResult.objects.get(user=request.user)
            return Response(BigFiveSerializer(result).data)
        except BigFiveResult.DoesNotExist:
            return Response({"detail": "Test Big Five non encore complété."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            result = BigFiveResult.objects.get(user=request.user)
            serializer = BigFiveSerializer(result, data=request.data)
        except BigFiveResult.DoesNotExist:
            serializer = BigFiveSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "message": "Résultats Big Five sauvegardés ✅",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            BigFiveResult.objects.get(user=request.user).delete()
            return Response({"message": "Résultats Big Five supprimés."})
        except BigFiveResult.DoesNotExist:
            return Response({"detail": "Aucun résultat à supprimer."}, status=status.HTTP_404_NOT_FOUND)


class RiasecView(APIView):
    """
    GET    /api/tests/riasec/  → récupère les résultats RIASEC
    POST   /api/tests/riasec/  → crée ou met à jour (upsert)
    DELETE /api/tests/riasec/  → supprime
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            result = RiasecResult.objects.get(user=request.user)
            return Response(RiasecSerializer(result).data)
        except RiasecResult.DoesNotExist:
            return Response({"detail": "Test RIASEC non encore complété."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            result = RiasecResult.objects.get(user=request.user)
            serializer = RiasecSerializer(result, data=request.data)
        except RiasecResult.DoesNotExist:
            serializer = RiasecSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "message": "Résultats RIASEC sauvegardés ✅",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            RiasecResult.objects.get(user=request.user).delete()
            return Response({"message": "Résultats RIASEC supprimés."})
        except RiasecResult.DoesNotExist:
            return Response({"detail": "Aucun résultat à supprimer."}, status=status.HTTP_404_NOT_FOUND)


class CompetencesView(APIView):
    """
    GET    /api/tests/competences/  → récupère les résultats compétences
    POST   /api/tests/competences/  → crée ou met à jour (upsert partiel possible)
    DELETE /api/tests/competences/  → supprime
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            result = CompetencesResult.objects.get(user=request.user)
            return Response(CompetencesSerializer(result).data)
        except CompetencesResult.DoesNotExist:
            return Response({"detail": "Test compétences non encore complété."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            result = CompetencesResult.objects.get(user=request.user)
            # partial=True pour soumettre jeu par jeu
            serializer = CompetencesSerializer(result, data=request.data, partial=True)
        except CompetencesResult.DoesNotExist:
            serializer = CompetencesSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "message": "Résultats compétences sauvegardés ✅",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            CompetencesResult.objects.get(user=request.user).delete()
            return Response({"message": "Résultats compétences supprimés."})
        except CompetencesResult.DoesNotExist:
            return Response({"detail": "Aucun résultat à supprimer."}, status=status.HTTP_404_NOT_FOUND)


class ProfilCompletView(APIView):
    """
    GET /api/tests/profil/
    Retourne une vue synthétique de TOUS les résultats de l'utilisateur.
    Utilisé par la page résultats finale pour l'analyse IA.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        def get_or_none(model, user):
            try:
                return model.objects.get(user=user)
            except model.DoesNotExist:
                return None

        bf = get_or_none(BigFiveResult, request.user)
        ri = get_or_none(RiasecResult, request.user)
        co = get_or_none(CompetencesResult, request.user)

        data = {
            'bigfive':     BigFiveSerializer(bf).data     if bf else None,
            'riasec':      RiasecSerializer(ri).data      if ri else None,
            'competences': CompetencesSerializer(co).data if co else None,
        }

        serializer = ProfilCompletSerializer(data)
        return Response(serializer.data)