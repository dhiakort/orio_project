import logging
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.types import ExecutionResult

logger = logging.getLogger('graphql')

class SafeGraphQLView(BaseGraphQLView):
    """
    Custom GraphQLView that handles:
    1. JWT authentication from Authorization Header (Bearer token)
    2. Safe error logging to prevent exposing database exceptions to clients
    """
    
    def get_context(self, request, response):
        # Authenticate JWT if request user is not set or anonymous
        if not hasattr(request, 'user') or not request.user or not request.user.is_authenticated:
            auth = JWTAuthentication()
            try:
                validated = auth.authenticate(request)
                if validated:
                    request.user = validated[0]  # user object
                else:
                    request.user = AnonymousUser()
            except Exception as e:
                request.user = AnonymousUser()
                
        context = super().get_context(request, response)
        return context

    def process_result(self, request, result: ExecutionResult):
        if result.errors:
            for error in result.errors:
                # Safe server-side logging of tracebacks
                logger.error(
                    f"GraphQL query error: {error.message}",
                    exc_info=error.original_error or True
                )
                
                # Strip out sensitive exception names or database traces
                if error.original_error:
                    # Provide clean, generic message for malformed queries or system issues
                    if not isinstance(error.original_error, (ValueError, PermissionError)):
                        error.message = "An internal error occurred."
                        
        return super().process_result(request, result)
