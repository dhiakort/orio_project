from django.urls import path
from .views import NotesView

urlpatterns = [
    path('', NotesView.as_view(), name='notes'),
]