# Configuración de Variables de Entorno - Intelli

Esta guía explica cómo configurar las variables de entorno para desarrollo y producción.

## Estructura de Archivos .env

### Backend (Django)

```
backend/
├── env.example              # Ejemplo general (referencia)
├── env.development.example  # Para desarrollo local
├── env.production.example   # Para producción
└── .env                     # Tu archivo real (NO commitear)
```

**Para desarrollo:**
```bash
cd backend
cp env.development.example .env
# Editar .env con tus valores
```

**Para producción:**
```bash
cd backend
cp env.production.example .env
# Editar .env con valores de producción
```

### Frontend (Next.js)

```
frontend/
├── env.example              # Ejemplo general (referencia)
├── env.development.example  # Para desarrollo local
├── env.production.example   # Para producción (referencia)
└── .env.local               # Tu archivo real para desarrollo (NO commitear)
```

**Para desarrollo:**
```bash
cd frontend
cp env.development.example .env.local
# Editar .env.local con tus valores
```

**Para producción:**
Las variables de producción se configuran en `infrastructure/.env` y se pasan al contenedor Docker durante el build.

### Infrastructure (Docker Compose)

```
infrastructure/
├── .docker.env.example      # Variables para Docker Compose
├── .django.env.example      # Variables para Django en Docker
├── .docker.env              # Tu archivo real (NO commitear)
└── .django.env              # Tu archivo real (NO commitear)
```

**Para producción:**
```bash
cd infrastructure
cp .docker.env.example .docker.env
cp .django.env.example .django.env
# Editar ambos archivos con valores de producción
```

## Explicación de la Estructura

### ¿Por qué dos archivos en infrastructure?

1. **`infrastructure/.env`** - Variables para Docker Compose:
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - Configuración de PostgreSQL
   - `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_BASE_URL` - URLs para el build del frontend
   - `REDIS_PASSWORD` (opcional) - Contraseña de Redis

2. **`infrastructure/.django.env`** - Variables para Django backend en Docker:
   - `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` - Configuración de Django
   - `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` - Seguridad
   - `MICROSOFT_CLIENT_ID`, etc. - OAuth
   - Variables de email, logging, etc.

**Razón:** Docker Compose necesita variables para construir servicios, mientras que Django necesita sus propias variables de configuración. Separarlos hace la configuración más clara y mantenible.

## Variables Importantes

### Backend - Desarrollo

| Variable | Valor Desarrollo | Descripción |
|----------|------------------|-------------|
| `DEBUG` | `True` | Habilita modo debug |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts permitidos |
| `DATABASE_URL` | `postgresql://...@localhost:5432/intell` | Base de datos local |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Origen del frontend |

### Backend - Producción

| Variable | Valor Producción | Descripción |
|----------|------------------|-------------|
| `DEBUG` | `False` | **CRÍTICO:** Siempre False en producción |
| `ALLOWED_HOSTS` | `openintell.cedia.edu.ec` | Tu dominio |
| `SECRET_KEY` | `[generar nuevo]` | Clave secreta única y fuerte |
| `SECURE_SSL_REDIRECT` | `True` | Redirigir HTTP a HTTPS |
| `CORS_ALLOWED_ORIGINS` | `https://openintell.cedia.edu.ec` | Origen del frontend |

### Frontend - Desarrollo

| Variable | Valor Desarrollo | Descripción |
|----------|------------------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api` | API backend local |
| `NEXT_PUBLIC_WS_BASE_URL` | `ws://localhost:8000/ws` | WebSocket local |
| `NEXT_PUBLIC_APP_ENV` | `development` | Entorno de la app |

### Frontend - Producción

| Variable | Valor Producción | Descripción |
|----------|------------------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://openintell.cedia.edu.ec/api` | API en producción |
| `NEXT_PUBLIC_WS_BASE_URL` | `wss://openintell.cedia.edu.ec/ws` | WebSocket seguro |
| `NEXT_PUBLIC_APP_ENV` | `production` | Entorno de la app |

### Infrastructure - Docker Compose

| Variable | Descripción |
|----------|-------------|
| `POSTGRES_DB` | Nombre de la base de datos |
| `POSTGRES_USER` | Usuario de PostgreSQL |
| `POSTGRES_PASSWORD` | **IMPORTANTE:** Contraseña fuerte |
| `NEXT_PUBLIC_API_BASE_URL` | URL de API para build del frontend |
| `NEXT_PUBLIC_WS_BASE_URL` | URL de WebSocket para build del frontend |

## Generar SECRET_KEY

Para producción, genera una nueva SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Checklist de Configuración

### Desarrollo Local

- [ ] Copiar `backend/env.development.example` a `backend/.env`
- [ ] Copiar `frontend/env.development.example` a `frontend/.env.local`
- [ ] Configurar `DATABASE_URL` si usas PostgreSQL
- [ ] Configurar Microsoft OAuth si lo usas
- [ ] Verificar que `DEBUG=True` en backend

### Producción

- [ ] Copiar `infrastructure/.docker.env.example` a `infrastructure/.docker.env`
- [ ] Copiar `infrastructure/.django.env.example` a `infrastructure/.django.env`
- [ ] Generar nueva `SECRET_KEY` para backend
- [ ] Configurar contraseña fuerte para PostgreSQL
- [ ] Verificar que `DEBUG=False` en backend
- [ ] Configurar `ALLOWED_HOSTS` con tu dominio
- [ ] Configurar `CORS_ALLOWED_ORIGINS` con tu dominio
- [ ] Habilitar todas las configuraciones de seguridad SSL
- [ ] Configurar Microsoft OAuth con URLs de producción
- [ ] Configurar email SMTP si es necesario

## Seguridad

⚠️ **NUNCA**:
- Commitees archivos `.env`, `.env.local`, `.docker.env`, `.django.env` al repositorio
- Compartas secretos en texto plano
- Uses la misma `SECRET_KEY` en desarrollo y producción
- Dejes `DEBUG=True` en producción

✅ **SIEMPRE**:
- Usa contraseñas fuertes y únicas
- Genera nueva `SECRET_KEY` para cada entorno
- Revisa los archivos `.env.example` antes de crear los reales
- Mantén los archivos `.env` fuera del control de versiones

## Troubleshooting

### Backend no lee variables de entorno

1. Verifica que el archivo se llama `.env` (no `env`)
2. Verifica que está en el directorio `backend/`
3. Reinicia el servidor Django

### Frontend no lee variables de entorno

1. Verifica que el archivo se llama `.env.local` (no `.env`)
2. Verifica que está en el directorio `frontend/`
3. Las variables deben empezar con `NEXT_PUBLIC_`
4. Reinicia el servidor Next.js

### Variables no se pasan en Docker

1. Verifica que `infrastructure/.docker.env` existe
2. Verifica que `infrastructure/.django.env` existe
3. Verifica la sintaxis en `docker-compose.prod.yml`
4. Reconstruye los contenedores: `docker-compose build --no-cache`
