"""
Microsoft OAuth2 Authentication Views.

Endpoints:
- GET  /api/auth/microsoft/login/    - Initiate Microsoft OAuth2 flow
- GET  /api/auth/microsoft/callback/ - Handle Microsoft OAuth2 callback
"""
import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from asgiref.sync import async_to_sync

from .microsoft import (
    build_authorization_url,
    generate_pkce_pair,
    generate_state,
    exchange_code_for_tokens,
    get_user_info,
    get_or_create_user,
    MicrosoftAuthError,
)

logger = logging.getLogger(__name__)

# Session keys for OAuth2 state
OAUTH_STATE_KEY = 'microsoft_oauth_state'
OAUTH_VERIFIER_KEY = 'microsoft_oauth_verifier'
OAUTH_REDIRECT_KEY = 'microsoft_oauth_redirect'


class MicrosoftLoginView(APIView):
    """
    Initiate Microsoft OAuth2 login flow.
    
    Redirects user to Microsoft login page.
    After authentication, Microsoft redirects back to the callback URL.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Initiate Microsoft login",
        description="Redirects to Microsoft login page. After auth, redirects back to callback.",
        parameters=[
            OpenApiParameter(
                name='redirect_uri',
                description='URL to redirect to after successful login (default: frontend dashboard)',
                required=False,
                type=str,
            ),
        ],
        responses={
            302: OpenApiResponse(description="Redirect to Microsoft login"),
        },
        tags=["Authentication"],
    )
    def get(self, request):
        # Store redirect URI for after callback
        redirect_after_login = request.GET.get('redirect_uri', settings.MICROSOFT_LOGIN_REDIRECT_URL)
        
        # Generate PKCE pair
        code_verifier, code_challenge = generate_pkce_pair()
        
        # Generate state for CSRF protection
        state = generate_state()
        
        # Store in session (will be verified in callback)
        request.session[OAUTH_STATE_KEY] = state
        request.session[OAUTH_VERIFIER_KEY] = code_verifier
        request.session[OAUTH_REDIRECT_KEY] = redirect_after_login
        request.session.save()
        
        # Build authorization URL and redirect
        auth_url = build_authorization_url(state, code_challenge)
        
        logger.info("Microsoft OAuth2: initiating login flow")
        return HttpResponseRedirect(auth_url)


@method_decorator(csrf_exempt, name='dispatch')
class MicrosoftCallbackView(APIView):
    """
    Handle Microsoft OAuth2 callback.
    
    Microsoft redirects here after user authenticates.
    This view exchanges the code for tokens, creates/updates the user,
    creates a Django session, and redirects to the frontend.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Microsoft OAuth2 callback",
        description="Handles callback from Microsoft after authentication.",
        parameters=[
            OpenApiParameter(name='code', description='Authorization code', required=False, type=str),
            OpenApiParameter(name='state', description='CSRF state', required=False, type=str),
            OpenApiParameter(name='error', description='Error code if auth failed', required=False, type=str),
            OpenApiParameter(name='error_description', description='Error description', required=False, type=str),
        ],
        responses={
            302: OpenApiResponse(description="Redirect to frontend with success or error"),
        },
        tags=["Authentication"],
    )
    def get(self, request):
        # Check for errors from Microsoft
        error = request.GET.get('error')
        if error:
            error_description = request.GET.get('error_description', 'Authentication failed')
            logger.warning(f"Microsoft OAuth2 error: {error} - {error_description}")
            return self._redirect_with_error(request, error, error_description)
        
        # Get authorization code
        code = request.GET.get('code')
        if not code:
            logger.warning("Microsoft OAuth2: no code in callback")
            return self._redirect_with_error(request, 'no_code', 'No authorization code received')
        
        # Verify state (CSRF protection)
        state = request.GET.get('state')
        stored_state = request.session.get(OAUTH_STATE_KEY)
        
        if not state or state != stored_state:
            logger.warning("Microsoft OAuth2: state mismatch")
            return self._redirect_with_error(request, 'state_mismatch', 'Invalid state parameter')
        
        # Get stored values
        code_verifier = request.session.get(OAUTH_VERIFIER_KEY)
        redirect_url = request.session.get(OAUTH_REDIRECT_KEY, settings.MICROSOFT_LOGIN_REDIRECT_URL)
        
        if not code_verifier:
            logger.warning("Microsoft OAuth2: no code verifier in session")
            return self._redirect_with_error(request, 'session_error', 'Session expired, please try again')
        
        try:
            # Exchange code for tokens (async to sync wrapper)
            tokens = async_to_sync(exchange_code_for_tokens)(code, code_verifier)
            
            # Get user info from Microsoft Graph
            access_token = tokens.get('access_token')
            if not access_token:
                raise MicrosoftAuthError("No access token received", "no_token")
            
            user_info = async_to_sync(get_user_info)(access_token)
            
            # Get or create Django user
            user = get_or_create_user(user_info)
            
            # Create Django session
            login(request, user)
            
            # Clean up OAuth session data
            self._clear_oauth_session(request)
            
            logger.info(f"Microsoft OAuth2: successful login for {user.email}")
            
            # Redirect to frontend
            return HttpResponseRedirect(redirect_url)
            
        except MicrosoftAuthError as e:
            logger.error(f"Microsoft OAuth2 error: {e.error_code} - {e.message}")
            return self._redirect_with_error(request, e.error_code, e.message)
        except Exception as e:
            logger.exception(f"Microsoft OAuth2 unexpected error: {e}")
            return self._redirect_with_error(request, 'server_error', 'An unexpected error occurred')
    
    def _redirect_with_error(self, request, error_code: str, error_message: str):
        """Redirect to frontend with error parameters."""
        self._clear_oauth_session(request)
        
        # Get error redirect URL from settings
        error_url = getattr(settings, 'MICROSOFT_LOGIN_ERROR_URL', settings.MICROSOFT_LOGIN_REDIRECT_URL)
        
        # Add error params
        params = urlencode({
            'error': error_code,
            'error_description': error_message,
        })
        
        return HttpResponseRedirect(f"{error_url}?{params}")
    
    def _clear_oauth_session(self, request):
        """Clear OAuth-related session data."""
        for key in [OAUTH_STATE_KEY, OAUTH_VERIFIER_KEY, OAUTH_REDIRECT_KEY]:
            request.session.pop(key, None)
        request.session.save()
