"""
Custom authentication classes for the authentication app.
"""
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication that only enforces CSRF on mutating methods.
    
    DRF's default SessionAuthentication enforces CSRF on ALL requests,
    including GET, which causes 403 errors when the frontend hasn't
    fetched the CSRF token yet.
    
    This class only enforces CSRF on POST, PUT, PATCH, DELETE methods,
    which is the correct behavior for session-based auth.
    """
    
    def enforce_csrf(self, request):
        """
        Only enforce CSRF for mutating methods.
        GET, HEAD, OPTIONS, TRACE are safe methods that don't need CSRF.
        """
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return None
        return super().enforce_csrf(request)
