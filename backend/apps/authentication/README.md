# Authentication App

Django session-based authentication with CSRF protection.

## Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/csrf/` | GET | No | Get CSRF token cookie |
| `/api/auth/login/` | POST | No | Login with credentials |
| `/api/auth/logout/` | POST | Yes | Logout current session |
| `/api/auth/me/` | GET | Yes | Get current user |

## Usage

### 1. Get CSRF Token

Before any mutating request, fetch the CSRF token:

```bash
curl -c cookies.txt http://localhost:8000/api/auth/csrf/
```

### 2. Login

```bash
curl -b cookies.txt -c cookies.txt \
  -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token_from_cookie>" \
  -d '{"username": "admin", "password": "password"}'
```

Response (200 OK):
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User",
  "is_active": true,
  "date_joined": "2024-01-01T00:00:00Z"
}
```

### 3. Check Auth Status

```bash
curl -b cookies.txt http://localhost:8000/api/auth/me/
```

Returns user data if authenticated, 401 if not.

### 4. Logout

```bash
curl -b cookies.txt -X POST http://localhost:8000/api/auth/logout/ \
  -H "X-CSRFToken: <token_from_cookie>"
```

## Cookies

| Cookie | HttpOnly | Purpose |
|--------|----------|---------|
| `sessionid` | Yes | Session identifier (cannot be read by JS) |
| `csrftoken` | No | CSRF protection token (must be read by JS) |

## Configuration

### Development (cross-origin)

In `development.py`:
```python
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000']
CORS_ALLOWED_ORIGINS = ['http://localhost:3000']
CORS_ALLOW_CREDENTIALS = True
```

### Production (same origin via reverse proxy)

CORS not needed when frontend and backend are on the same domain.
Cookies work natively with `SameSite=Lax`.

## Testing

```bash
cd backend
pytest apps/authentication/tests/ -v
```

## Security Notes

- Session cookies are HttpOnly (cannot be accessed by JavaScript)
- CSRF token is required for all mutating requests
- Passwords are never logged or returned in responses
- Failed login attempts are logged (without password)
