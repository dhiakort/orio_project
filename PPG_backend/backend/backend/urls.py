
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from backend.graphql_config import SafeGraphQLView
from backend.schema import schema

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/notes/', include('notes.urls')),
    path('api/tests/',  include('tests.urls')),
    path('api/scoring/', include('scoring.urls')), 
    path('graphql/', csrf_exempt(SafeGraphQLView.as_view(schema=schema))),
]
