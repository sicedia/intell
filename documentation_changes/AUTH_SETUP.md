# Authentication Setup Guide

This document describes the session-based authentication system implemented in this project, including Microsoft OAuth2 integration.

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Next.js       │────▶│   Django        │────▶│   PostgreSQL    │
│   Frontend      │     │   Backend       │     │   Database      │
│                 │◀────│                 │◀────│                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │   Cookies:            │        ┌─────────────────┐
        │   - sessionid (HttpOnly)       │                 │
        │   - csrftoken (readable)  ────▶│   Microsoft     │
        │                       │        │   Entra ID      │
        └───────────────────────┘        └─────────────────┘
```

## Supported Authentication Methods

1. **Username/Password** - Traditional Django auth
2. **Microsoft OAuth2** - Azure AD / Entra ID (Authorization Code Flow with PKCE)

## Authentication Flow

### 1. Initial Load
1. App loads, `AuthProvider` mounts
2. `useAuth` hook triggers `/api/auth/csrf/` to get CSRF cookie
3. `useAuth` triggers `/api/auth/me/` to check session
4. If 401 → user is not authenticated
5. If 200 → user data stored in Zustand

### 2. Login Flow
1. User submits credentials
2. Frontend calls `POST /api/auth/login/` with `X-CSRFToken` header
3. Django authenticates and creates session
4. `sessionid` cookie set (HttpOnly)
5. User data returned and stored in Zustand
6. Redirect to dashboard

### 3. Authenticated Requests
1. All `fetch` calls include `credentials: "include"`
2. Browser automatically sends `sessionid` cookie
3. Mutating requests include `X-CSRFToken` header
4. Django validates session and CSRF

### 4. Logout Flow
1. Frontend calls `POST /api/auth/logout/`
2. Django invalidates session
3. `sessionid` cookie cleared
4. Zustand store cleared
5. Redirect to login

### 5. Microsoft OAuth2 Flow
1. User clicks "Sign in with Microsoft" button
2. Frontend redirects to `GET /api/auth/microsoft/login/`
3. Backend generates PKCE codes and state, stores in session
4. Backend redirects to Microsoft authorization endpoint
5. User authenticates with Microsoft
6. Microsoft redirects to `GET /api/auth/microsoft/callback/` with code
7. Backend exchanges code for tokens using PKCE
8. Backend calls Microsoft Graph API to get user info
9. Backend creates/updates Django user
10. Backend creates Django session
11. Backend redirects to frontend dashboard

## Configuration

### Backend Environment Variables

```bash
# .env (development)
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=True

# Microsoft OAuth2 (Azure AD / Entra ID)
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id-or-common
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/auth/microsoft/callback/
MICROSOFT_LOGIN_REDIRECT_URL=http://localhost:3000/en/dashboard
MICROSOFT_LOGIN_ERROR_URL=http://localhost:3000/en/login
```

### Frontend Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_ENV=development
```

## File Structure

### Backend
```
backend/apps/authentication/
├── __init__.py
├── apps.py
├── authentication.py   # Custom SessionAuthentication (CSRF exempt for GET)
├── microsoft.py        # Microsoft OAuth2 service
├── serializers.py      # LoginSerializer, UserSerializer
├── urls.py             # All auth endpoints
├── views.py            # CSRFTokenView, LoginView, LogoutView, MeView
├── views_microsoft.py  # MicrosoftLoginView, MicrosoftCallbackView
├── README.md
└── tests/
    ├── __init__.py
    └── test_auth.py    # Comprehensive auth tests
```

### Frontend
```
frontend/src/
├── proxy.ts                         # Route protection (Next.js 16)
├── features/auth/
│   ├── api/auth.ts                 # API functions
│   ├── hooks/useAuth.ts            # Auth hook with TanStack Query
│   ├── stores/useAuthStore.ts      # Zustand store
│   ├── ui/
│   │   ├── AuthProvider.tsx        # Initializes auth
│   │   ├── LoginForm.tsx           # Login form with Microsoft button
│   │   └── MicrosoftLoginButton.tsx # Microsoft OAuth2 button
│   └── index.ts                    # Exports
├── shared/lib/
│   ├── api-client.ts               # Modified: credentials + CSRF
│   └── csrf.ts                     # CSRF token utilities
└── app/[locale]/login/
    ├── page.tsx                    # Login page
    └── layout.tsx                  # Minimal layout
```

## Route Protection

### Middleware (UX Layer)
- Checks for `sessionid` cookie presence
- Redirects unauthenticated users to `/login`
- Redirects authenticated users away from `/login`
- **Note:** This is UX only, not security

### Server Validation (Security Layer)
- `AuthProvider` calls `/api/auth/me/` on mount
- Returns 401 if session is invalid/expired
- Zustand store updated accordingly

## API Endpoints

| Endpoint | Method | Auth | CSRF | Description |
|----------|--------|------|------|-------------|
| `/api/auth/csrf/` | GET | No | No | Get CSRF cookie |
| `/api/auth/login/` | POST | No | Yes | Username/password login |
| `/api/auth/logout/` | POST | Yes | Yes | Logout |
| `/api/auth/me/` | GET | Yes | No | Get current user |
| `/api/auth/microsoft/login/` | GET | No | No | Initiate Microsoft OAuth2 |
| `/api/auth/microsoft/callback/` | GET | No | No | Microsoft OAuth2 callback |

## Development vs Production

### Development (Cross-Origin)
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Requires: `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`
- Cookies: `SameSite=Lax` works with `credentials: "include"`

### Production (Same Origin)
- Both served via nginx reverse proxy on same domain
- No CORS needed (same origin)
- Cookies work natively
- Add: `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`

## Testing

### Backend Tests
```bash
cd backend
pytest apps/authentication/tests/ -v
```

### Manual Testing
```bash
# 1. Create a superuser
python manage.py createsuperuser

# 2. Get CSRF token
curl -c cookies.txt http://localhost:8000/api/auth/csrf/

# 3. Extract token from cookies.txt and login
curl -b cookies.txt -c cookies.txt \
  -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_TOKEN" \
  -d '{"username": "admin", "password": "yourpassword"}'

# 4. Check auth
curl -b cookies.txt http://localhost:8000/api/auth/me/
```

## Security Considerations

1. **Session Cookie (sessionid)**
   - HttpOnly: Yes (cannot be accessed by JavaScript)
   - Secure: True in production (HTTPS only)
   - SameSite: Lax (default)

2. **CSRF Cookie (csrftoken)**
   - HttpOnly: No (must be readable by JavaScript)
   - Secure: True in production
   - SameSite: Lax

3. **Password Handling**
   - Never logged
   - Never returned in responses
   - write_only in serializer

4. **Failed Login**
   - Generic "Invalid credentials" message
   - No indication of which field was wrong
   - Attempts logged (without password)

## Troubleshooting

### "CSRF Failed" Error
- Ensure `CSRF_TRUSTED_ORIGINS` includes frontend URL
- Check that `X-CSRFToken` header is sent
- Verify `credentials: "include"` in fetch

### "Not Authenticated" After Login
- Check `credentials: "include"` in all requests
- Verify `sessionid` cookie is set (check browser DevTools)
- Check CORS allows credentials

### Session Not Persisting
- Ensure `SESSION_COOKIE_SAMESITE = 'Lax'`
- In production, verify same domain for frontend/backend
- Check `SESSION_COOKIE_SECURE` matches HTTPS usage

## Microsoft OAuth2 Setup

### 1. Register App in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com) > Azure Active Directory > App Registrations
2. Click "New registration"
3. Configure:
   - **Name**: Your app name
   - **Supported account types**: Choose based on your needs
     - "Single tenant" for organization only
     - "Multitenant" for any Azure AD account
     - "Multitenant + personal" for Microsoft accounts too
   - **Redirect URI**: `http://localhost:8000/api/auth/microsoft/callback/` (Web platform)
4. Click "Register"

### 2. Configure App Credentials

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Copy the secret value (shown only once)
4. Note down:
   - **Application (client) ID** - from Overview page
   - **Directory (tenant) ID** - from Overview page
   - **Client secret** - from step 3

### 3. Configure API Permissions

1. Go to "API permissions"
2. Ensure these permissions are granted:
   - `openid` (delegated)
   - `profile` (delegated)
   - `email` (delegated)
   - `User.Read` (delegated)
3. Click "Grant admin consent" if required

### 4. Set Environment Variables

```bash
# Backend .env
MICROSOFT_CLIENT_ID=<Application (client) ID>
MICROSOFT_CLIENT_SECRET=<Client secret value>
MICROSOFT_TENANT_ID=<Directory (tenant) ID>  # or 'common' for multi-tenant
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/auth/microsoft/callback/
MICROSOFT_LOGIN_REDIRECT_URL=http://localhost:3000/en/dashboard
MICROSOFT_LOGIN_ERROR_URL=http://localhost:3000/en/login
```

### 5. Production Configuration

For production, update the redirect URIs:
1. In Azure Portal, add production redirect URI
2. Update environment variables:
   ```bash
   MICROSOFT_REDIRECT_URI=https://yourdomain.com/api/auth/microsoft/callback/
   MICROSOFT_LOGIN_REDIRECT_URL=https://yourdomain.com/dashboard
   MICROSOFT_LOGIN_ERROR_URL=https://yourdomain.com/login
   ```

### Microsoft Auth Flow Security

- **PKCE** (Proof Key for Code Exchange) prevents authorization code interception
- **State parameter** prevents CSRF attacks
- **Tokens never reach frontend** - all token exchange happens server-side
- **Session-based** - after Microsoft auth, uses same Django session as password login
