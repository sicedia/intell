# Archivos de Variables de Entorno - Infrastructure

## Estructura de Archivos

```
infrastructure/
├── .docker.env.example    # Variables para Docker Compose (ejemplo)
├── .django.env.example    # Variables para Django backend (ejemplo)
├── .docker.env            # Tu archivo real de Docker (NO commitear)
└── .django.env            # Tu archivo real de Django (NO commitear)
```

## Descripción de Archivos

### `.docker.env.example` / `.docker.env`

**Propósito:** Variables de entorno para Docker Compose que se usan para configurar los servicios de infraestructura.

**Contiene:**
- `POSTGRES_DB` - Nombre de la base de datos
- `POSTGRES_USER` - Usuario de PostgreSQL
- `POSTGRES_PASSWORD` - Contraseña de PostgreSQL (¡cambiar en producción!)
- `REDIS_PASSWORD` - Contraseña de Redis (opcional)
- `NEXT_PUBLIC_API_BASE_URL` - URL de la API para el build del frontend
- `NEXT_PUBLIC_WS_BASE_URL` - URL de WebSocket para el build del frontend

**Uso:**
```bash
cp .docker.env.example .docker.env
# Editar .docker.env con tus valores
```

### `.django.env.example` / `.django.env`

**Propósito:** Variables de entorno específicas para el servicio Django backend en Docker.

**Contiene:**
- `SECRET_KEY` - Clave secreta de Django (¡generar nueva para producción!)
- `DEBUG` - Modo debug (False en producción)
- `ALLOWED_HOSTS` - Hosts permitidos
- `CORS_ALLOWED_ORIGINS` - Orígenes permitidos para CORS
- `CSRF_TRUSTED_ORIGINS` - Orígenes confiables para CSRF
- Configuración de seguridad SSL
- Configuración de Microsoft OAuth
- Configuración de email
- Configuración de logging

**Uso:**
```bash
cp .django.env.example .django.env
# Editar .django.env con tus valores
```

## ¿Por qué dos archivos separados?

1. **`.docker.env`** - Usado por Docker Compose para:
   - Configurar servicios de infraestructura (PostgreSQL, Redis)
   - Pasar variables al build del frontend
   - Variables compartidas entre servicios

2. **`.django.env`** - Usado específicamente por el contenedor Django:
   - Configuración de seguridad de Django
   - Secretos específicos de la aplicación
   - Variables que no deben estar en el archivo de Docker Compose

**Ventajas:**
- Separación clara de responsabilidades
- Mejor organización y mantenibilidad
- Facilita la gestión de secretos
- Permite diferentes niveles de acceso

## Configuración Inicial

### Para Producción

```bash
cd infrastructure

# Copiar archivos de ejemplo
cp .docker.env.example .docker.env
cp .django.env.example .django.env

# Editar con tus valores
nano .docker.env
nano .django.env
```

### Variables Críticas

**En `.docker.env`:**
- `POSTGRES_PASSWORD` - **IMPORTANTE:** Usa una contraseña fuerte
- `NEXT_PUBLIC_API_BASE_URL` - URL de tu API en producción
- `NEXT_PUBLIC_WS_BASE_URL` - URL de WebSocket en producción

**En `.django.env`:**
- `SECRET_KEY` - **CRÍTICO:** Genera una nueva clave única
- `DEBUG` - **CRÍTICO:** Debe ser `False` en producción
- `ALLOWED_HOSTS` - Tu dominio de producción
- `CORS_ALLOWED_ORIGINS` - Tu dominio de producción con https://

## Generar SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Seguridad

⚠️ **NUNCA:**
- Commitees `.docker.env` o `.django.env` al repositorio
- Compartas estos archivos en texto plano
- Uses los mismos valores en desarrollo y producción

✅ **SIEMPRE:**
- Usa contraseñas fuertes y únicas
- Genera nueva `SECRET_KEY` para producción
- Verifica que `DEBUG=False` en producción
- Mantén estos archivos fuera del control de versiones

## Referencias en el Código

- `docker-compose.prod.yml` - Usa `.django.env` para el servicio backend
- `deploy.sh` - Verifica y crea estos archivos si no existen
- `backup-db.sh` - Lee `.docker.env` para credenciales de PostgreSQL
- `restore-db.sh` - Lee `.docker.env` para credenciales de PostgreSQL
