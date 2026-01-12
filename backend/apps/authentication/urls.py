"""
URL configuration for authentication endpoints.

All endpoints are prefixed with /api/auth/ (configured in config/urls.py)
"""
from django.urls import path
from .views import CSRFTokenView, LoginView, LogoutView, MeView
from .views_microsoft import MicrosoftLoginView, MicrosoftCallbackView

app_name = 'authentication'

urlpatterns = [
    # Session-based auth
    path('csrf/', CSRFTokenView.as_view(), name='csrf'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', MeView.as_view(), name='me'),
    
    # Microsoft OAuth2
    path('microsoft/login/', MicrosoftLoginView.as_view(), name='microsoft-login'),
    path('microsoft/callback/', MicrosoftCallbackView.as_view(), name='microsoft-callback'),
]
