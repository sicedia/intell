"""
Tests for authentication endpoints.

Tests cover:
- CSRF token retrieval
- Login with valid/invalid credentials
- Logout
- Get current user (/me)
- Session cookie behavior
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return an API client that handles cookies."""
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def user(db):
    """Create a test user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def inactive_user(db):
    """Create an inactive test user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='inactiveuser',
        email='inactive@example.com',
        password='testpass123',
        is_active=False
    )


class TestCSRFEndpoint:
    """Tests for GET /api/auth/csrf/"""
    
    def test_csrf_returns_204_and_sets_cookie(self, api_client):
        """CSRF endpoint should return 204 and set csrftoken cookie."""
        response = api_client.get(reverse('authentication:csrf'))
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert 'csrftoken' in response.cookies
    
    def test_csrf_accessible_without_auth(self, api_client):
        """CSRF endpoint should be accessible without authentication."""
        response = api_client.get(reverse('authentication:csrf'))
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestLoginEndpoint:
    """Tests for POST /api/auth/login/"""
    
    def test_login_success(self, api_client, user):
        """Valid credentials should return user data and set session cookie."""
        # First get CSRF token
        api_client.get(reverse('authentication:csrf'))
        
        response = api_client.post(
            reverse('authentication:login'),
            data={'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
        assert response.data['email'] == 'test@example.com'
        assert 'password' not in response.data
        assert 'sessionid' in response.cookies
    
    def test_login_invalid_password(self, api_client, user):
        """Invalid password should return 400."""
        api_client.get(reverse('authentication:csrf'))
        
        response = api_client.post(
            reverse('authentication:login'),
            data={'username': 'testuser', 'password': 'wrongpassword'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid credentials' in response.data['detail']
    
    def test_login_invalid_username(self, api_client, user):
        """Invalid username should return 400."""
        api_client.get(reverse('authentication:csrf'))
        
        response = api_client.post(
            reverse('authentication:login'),
            data={'username': 'nonexistent', 'password': 'testpass123'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid credentials' in response.data['detail']
    
    def test_login_inactive_user(self, api_client, inactive_user):
        """Inactive user should get 400 with appropriate message."""
        api_client.get(reverse('authentication:csrf'))
        
        response = api_client.post(
            reverse('authentication:login'),
            data={'username': 'inactiveuser', 'password': 'testpass123'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'disabled' in response.data['detail'].lower()
    
    def test_login_missing_fields(self, api_client):
        """Missing fields should return 400."""
        api_client.get(reverse('authentication:csrf'))
        
        response = api_client.post(
            reverse('authentication:login'),
            data={'username': 'testuser'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_login_without_csrf_fails(self, api_client, user):
        """Login without CSRF token should fail (CSRF protection enabled)."""
        # Don't get CSRF token first
        response = api_client.post(
            reverse('authentication:login'),
            data={'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        
        # Should fail due to missing CSRF
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestLogoutEndpoint:
    """Tests for POST /api/auth/logout/"""
    
    def test_logout_success(self, api_client, user):
        """Authenticated user should be able to logout."""
        # Login first
        api_client.get(reverse('authentication:csrf'))
        api_client.post(
            reverse('authentication:login'),
            data={'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        
        # Logout
        response = api_client.post(reverse('authentication:logout'))
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify session is invalidated
        me_response = api_client.get(reverse('authentication:me'))
        assert me_response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout_unauthenticated(self, api_client):
        """Unauthenticated user should get 401."""
        api_client.get(reverse('authentication:csrf'))
        
        response = api_client.post(reverse('authentication:logout'))
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMeEndpoint:
    """Tests for GET /api/auth/me/"""
    
    def test_me_authenticated(self, api_client, user):
        """Authenticated user should get their data."""
        # Login first
        api_client.get(reverse('authentication:csrf'))
        api_client.post(
            reverse('authentication:login'),
            data={'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        
        response = api_client.get(reverse('authentication:me'))
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'testuser'
        assert response.data['email'] == 'test@example.com'
        assert response.data['first_name'] == 'Test'
        assert response.data['last_name'] == 'User'
        assert 'password' not in response.data
    
    def test_me_unauthenticated(self, api_client):
        """Unauthenticated user should get 401."""
        response = api_client.get(reverse('authentication:me'))
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSessionPersistence:
    """Tests for session cookie behavior."""
    
    def test_session_persists_across_requests(self, api_client, user):
        """Session should persist across multiple requests."""
        # Login
        api_client.get(reverse('authentication:csrf'))
        api_client.post(
            reverse('authentication:login'),
            data={'username': 'testuser', 'password': 'testpass123'},
            format='json'
        )
        
        # Multiple requests should work
        for _ in range(3):
            response = api_client.get(reverse('authentication:me'))
            assert response.status_code == status.HTTP_200_OK
            assert response.data['username'] == 'testuser'
