from django.urls import path
from .views import RecommandationView, ProfilCompletView, RoadmapView, ChatbotView, GrokChatbotView

urlpatterns = [
    path('recommandation/', RecommandationView.as_view(), name='scoring-recommandation'),
    path('profil-complet/', ProfilCompletView.as_view(), name='scoring-profil-complet'),
    path('roadmap/',        RoadmapView.as_view(),       name='scoring-roadmap'),
    path('chatbot/',        ChatbotView.as_view(),       name='scoring-chatbot'),
    path('chatbot/grok/',   GrokChatbotView.as_view(),   name='scoring-chatbot-grok'),
]