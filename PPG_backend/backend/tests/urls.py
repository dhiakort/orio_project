from django.urls import path
from .views import BigFiveView, RiasecView, CompetencesView, ProfilCompletView

urlpatterns = [
    path('bigfive/',     BigFiveView.as_view(),      name='test-bigfive'),
    path('riasec/',      RiasecView.as_view(),        name='test-riasec'),
    path('competences/', CompetencesView.as_view(),   name='test-competences'),
    path('profil/',      ProfilCompletView.as_view(),  name='test-profil-complet'),
]