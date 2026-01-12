"""
Authentication views for session-based auth with CSRF protection.

Endpoints:
- GET  /api/auth/csrf/   - Get CSRF token cookie
- POST /api/auth/login/  - Login with credentials
- POST /api/auth/logout/ - Logout current session
- GET  /api/auth/me/     - Get current authenticated user
"""
import logging
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import LoginSerializer, UserSerializer

logger = logging.getLogger(__name__)


class CSRFTokenView(APIView):
    """
    Get CSRF token.
    
    Sets the CSRF cookie and returns 204 No Content.
    Call this endpoint before making any mutating requests (POST, PUT, PATCH, DELETE).
    """
    permission_classes = [AllowAny]
    
    @method_decorator(ensure_csrf_cookie)
    @extend_schema(
        summary="Get CSRF token",
        description="Sets the CSRF cookie. Call before making POST/PUT/PATCH/DELETE requests.",
        responses={
            204: OpenApiResponse(description="CSRF cookie set successfully"),
        },
        tags=["Authentication"],
    )
    def get(self, request):
        # Force CSRF cookie to be set
        get_token(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    """
    Login with username and password.
    
    On success, sets the session cookie (HttpOnly) and returns user data.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Login",
        description="Authenticate with username and password. Sets session cookie on success.",
        request=LoginSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid credentials or validation error"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid request data", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            # Log failed attempt without exposing which field was wrong
            logger.warning(f"Failed login attempt for username: {username}")
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            return Response(
                {"detail": "Account is disabled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create session
        login(request, user)
        logger.info(f"User logged in: {username}")
        
        # Return user data
        user_serializer = UserSerializer(user)
        return Response(user_serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Logout current session.
    
    Invalidates the session and clears the session cookie.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Logout",
        description="Invalidates the current session and clears cookies.",
        responses={
            204: OpenApiResponse(description="Logged out successfully"),
            401: OpenApiResponse(description="Not authenticated"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        username = request.user.username
        logout(request)
        logger.info(f"User logged out: {username}")
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """
    Get current authenticated user.
    
    Returns user data if authenticated, 401 if not.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get current user",
        description="Returns the currently authenticated user's data.",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Not authenticated"),
        },
        tags=["Authentication"],
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
