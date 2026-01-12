"""
Microsoft OAuth2 Authentication Service.

Handles the Authorization Code Flow with PKCE for Microsoft Entra ID (Azure AD).
This service manages token exchange, user info retrieval, and user creation/update.
"""
import logging
import secrets
import hashlib
import base64
from typing import Optional, TypedDict
from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class MicrosoftConfig(TypedDict):
    """Microsoft OAuth2 configuration."""
    client_id: str
    client_secret: str
    tenant_id: str
    redirect_uri: str
    scopes: list[str]


class MicrosoftUserInfo(TypedDict):
    """User info from Microsoft Graph API."""
    id: str
    mail: Optional[str]
    userPrincipalName: str
    displayName: str
    givenName: Optional[str]
    surname: Optional[str]


class MicrosoftAuthError(Exception):
    """Exception raised for Microsoft auth errors."""
    def __init__(self, message: str, error_code: str = "auth_error"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


def get_microsoft_config() -> MicrosoftConfig:
    """Get Microsoft OAuth2 configuration from Django settings."""
    return {
        'client_id': settings.MICROSOFT_CLIENT_ID,
        'client_secret': settings.MICROSOFT_CLIENT_SECRET,
        'tenant_id': settings.MICROSOFT_TENANT_ID,
        'redirect_uri': settings.MICROSOFT_REDIRECT_URI,
        'scopes': getattr(settings, 'MICROSOFT_SCOPES', ['openid', 'profile', 'email', 'User.Read']),
    }


def generate_pkce_pair() -> tuple[str, str]:
    """
    Generate PKCE code verifier and challenge.
    
    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    # Generate a random code verifier (43-128 characters)
    code_verifier = secrets.token_urlsafe(64)[:128]
    
    # Create code challenge using S256 method
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    return code_verifier, code_challenge


def generate_state() -> str:
    """Generate a random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


def build_authorization_url(state: str, code_challenge: str) -> str:
    """
    Build the Microsoft authorization URL.
    
    Args:
        state: Random state for CSRF protection
        code_challenge: PKCE code challenge
        
    Returns:
        Full authorization URL to redirect user to
    """
    config = get_microsoft_config()
    
    params = {
        'client_id': config['client_id'],
        'response_type': 'code',
        'redirect_uri': config['redirect_uri'],
        'response_mode': 'query',
        'scope': ' '.join(config['scopes']),
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    
    base_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/authorize"
    return f"{base_url}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str, code_verifier: str) -> dict:
    """
    Exchange authorization code for tokens.
    
    Args:
        code: Authorization code from Microsoft
        code_verifier: PKCE code verifier
        
    Returns:
        Token response containing access_token, id_token, etc.
        
    Raises:
        MicrosoftAuthError: If token exchange fails
    """
    config = get_microsoft_config()
    
    token_url = f"https://login.microsoftonline.com/{config['tenant_id']}/oauth2/v2.0/token"
    
    data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': code,
        'redirect_uri': config['redirect_uri'],
        'grant_type': 'authorization_code',
        'code_verifier': code_verifier,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            logger.error(f"Microsoft token exchange failed: {error_data}")
            raise MicrosoftAuthError(
                error_data.get('error_description', 'Token exchange failed'),
                error_data.get('error', 'token_error')
            )
        except Exception as e:
            logger.error(f"Microsoft token exchange error: {e}")
            raise MicrosoftAuthError(str(e), 'network_error')


async def get_user_info(access_token: str) -> MicrosoftUserInfo:
    """
    Get user information from Microsoft Graph API.
    
    Args:
        access_token: Microsoft access token
        
    Returns:
        User information from Microsoft
        
    Raises:
        MicrosoftAuthError: If API call fails
    """
    graph_url = "https://graph.microsoft.com/v1.0/me"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                graph_url,
                headers={'Authorization': f'Bearer {access_token}'}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            logger.error(f"Microsoft Graph API error: {error_data}")
            raise MicrosoftAuthError(
                error_data.get('message', 'Failed to get user info'),
                'graph_error'
            )
        except Exception as e:
            logger.error(f"Microsoft Graph API error: {e}")
            raise MicrosoftAuthError(str(e), 'network_error')


def get_or_create_user(user_info: MicrosoftUserInfo) -> User:
    """
    Get or create a Django user from Microsoft user info.
    
    Args:
        user_info: User information from Microsoft Graph API
        
    Returns:
        Django User instance
    """
    # Use email or userPrincipalName as identifier
    email = user_info.get('mail') or user_info.get('userPrincipalName', '')
    microsoft_id = user_info.get('id', '')
    
    if not email:
        raise MicrosoftAuthError("No email found in Microsoft account", "no_email")
    
    # Normalize email to lowercase
    email = email.lower()
    
    # Try to find existing user by email
    try:
        user = User.objects.get(email=email)
        # Update user info from Microsoft
        user.first_name = user_info.get('givenName', '') or user.first_name
        user.last_name = user_info.get('surname', '') or user.last_name
        user.save(update_fields=['first_name', 'last_name'])
        logger.info(f"Microsoft login: existing user {email}")
        return user
    except User.DoesNotExist:
        pass
    
    # Create new user
    # Use email prefix as username (before @)
    username_base = email.split('@')[0]
    username = username_base
    
    # Ensure unique username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{username_base}{counter}"
        counter += 1
    
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=user_info.get('givenName', ''),
        last_name=user_info.get('surname', ''),
        # No password - user authenticates via Microsoft
    )
    
    logger.info(f"Microsoft login: created new user {email}")
    return user
