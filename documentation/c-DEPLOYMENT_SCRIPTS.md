# Deployment Scripts - Infrastructure

Este documento describe los scripts disponibles en el directorio `infrastructure/` para el despliegue y mantenimiento de la aplicación en producción.

## Scripts Disponibles

### 1. `deploy.sh` - Deployment Inicial Automatizado

**Propósito:** Script principal para el despliegue inicial de la aplicación en producción.

**Uso:**
```bash
cd /opt/intell/infrastructure
chmod +x deploy.sh
./deploy.sh
```

**Qué hace:**
1. Verifica que Docker y Docker Compose estén instalados
2. Verifica que existan `.docker.env` y `.django.env`
3. Verifica certificados SSL (opcional)
4. Construye y arranca todos los servicios
5. Espera a que los servicios estén saludables
6. Ejecuta migraciones de base de datos
7. Recopila archivos estáticos
8. Crea superusuario si no existe

**Requisitos:**
- Docker y Docker Compose instalados
- Archivos `.docker.env` y `.django.env` configurados
- Certificados SSL en `nginx/ssl/` (opcional, pero recomendado)

---

### 2. `setup-ssl.sh` - Configuración de Certificados SSL

**Propósito:** Script interactivo para configurar certificados SSL (Let's Encrypt o certificados personalizados).

**Uso:**
```bash
cd /opt/intell/infrastructure
chmod +x setup-ssl.sh
./setup-ssl.sh
```

**Opciones:**
- **Opción 1:** Let's Encrypt (automático) - Requiere que el DNS esté configurado correctamente
- **Opción 2:** Certificado personalizado - Permite especificar rutas a certificados existentes
- **Opción 3:** Saltar configuración SSL

**Qué hace:**
- Instala Certbot si es necesario (para Let's Encrypt)
- Genera o copia certificados a `nginx/ssl/`
- Configura permisos correctos
- Configura renovación automática (para Let's Encrypt)
- Valida configuración de nginx

---

### 3. `backup-db.sh` - Backup de Base de Datos

**Propósito:** Crea backups timestamped de la base de datos PostgreSQL.

**Uso:**
```bash
cd /opt/intell/infrastructure
chmod +x backup-db.sh

# Backup simple
./backup-db.sh

# Backup con limpieza automática de backups antiguos (>30 días)
./backup-db.sh --cleanup
```

**Qué hace:**
1. Lee credenciales de `.docker.env`
2. Crea directorio `backups/` si no existe
3. Genera backup timestamped: `intell_backup_YYYYMMDD_HHMMSS.sql.gz`
4. Lista backups recientes
5. Opcionalmente limpia backups antiguos (>30 días)

**Ubicación de backups:**
- `infrastructure/backups/intell_backup_YYYYMMDD_HHMMSS.sql.gz`

**Recomendación:**
- Ejecutar diariamente via cron:
```bash
# Agregar a crontab: crontab -e
0 2 * * * cd /opt/intell/infrastructure && ./backup-db.sh --cleanup
```

---

### 4. `restore-db.sh` - Restaurar Base de Datos

**Propósito:** Restaura la base de datos desde un archivo de backup.

**Uso:**
```bash
cd /opt/intell/infrastructure
chmod +x restore-db.sh

# Listar backups disponibles
ls -lh backups/

# Restaurar desde backup
./restore-db.sh backups/intell_backup_YYYYMMDD_HHMMSS.sql.gz
```

**Qué hace:**
1. Verifica que el archivo de backup exista
2. Lee credenciales de `.docker.env`
3. Detiene servicios que usan la base de datos (opcional)
4. Restaura backup (soporta `.sql` y `.sql.gz`)
5. Reinicia servicios

**⚠️ Advertencia:**
- Este script **REEMPLAZA** la base de datos actual
- Haz un backup antes de restaurar
- Los servicios pueden estar inactivos durante la restauración

---

### 5. `update.sh` - Actualizar Código en Producción

**Propósito:** Actualiza el código desde git, reconstruye contenedores y reinicia servicios.

**Uso:**
```bash
cd /opt/intell/infrastructure
chmod +x update.sh
./update.sh
```

**Qué hace:**
1. Hace `git pull` (si es un repositorio git)
2. Crea backup de base de datos automático
3. Detiene servicios
4. Reconstruye imágenes Docker (`--no-cache`)
5. Inicia servicios
6. Ejecuta migraciones
7. Recopila archivos estáticos

**⚠️ Nota:**
- Este script **reconstruye imágenes** en el servidor (consume recursos y tiempo)
- **Método recomendado:** Usar `build-and-push.sh` para construir imágenes localmente y luego `docker compose pull` en el servidor

---

### 6. `build-and-push.sh` / `build-and-push.ps1` - Construir y Subir Imágenes Docker

**Propósito:** Construye las imágenes Docker (backend y frontend) y las sube a Docker Hub.

**Uso:**
```bash
# Linux/macOS
cd infrastructure
chmod +x build-and-push.sh
./build-and-push.sh v1.0.1

# Windows PowerShell
cd infrastructure
.\build-and-push.ps1 v1.0.1
```

**Qué hace:**
1. Lee configuración de `.build.env`
2. Construye imagen backend: `sicedia/intell-backend:VERSION`
3. Construye imagen frontend: `sicedia/intell-frontend:VERSION`
4. Etiqueta ambas imágenes con `latest` también
5. Las sube a Docker Hub

**Requisitos:**
- Estar logueado en Docker Hub: `docker login`
- Archivo `.build.env` configurado con `PRODUCTION_DOMAIN` o URLs de API/WS

**Workflow recomendado:**
```bash
# 1. En desarrollo: construir y subir
./build-and-push.sh v1.0.2

# 2. En servidor: actualizar .docker.env con IMAGE_TAG=v1.0.2
# 3. En servidor: docker compose pull && docker compose up -d
```

---

## Scripts No Disponibles / Eliminados

Los siguientes scripts **NO EXISTEN** y no deben ser referenciados en documentación:

- ❌ `setup.sh` - No existe (usar `docker-compose up -d` manualmente)
- ❌ `setup.ps1` - No existe (usar `docker-compose up -d` manualmente)

---

## Orden de Ejecución Recomendado (Primera Vez)

```bash
cd /opt/intell/infrastructure

# 1. Configurar variables de entorno
cp .docker.env.example .docker.env
cp .django.env.example .django.env
nano .docker.env  # Editar valores
nano .django.env  # Editar valores

# 2. Configurar SSL
chmod +x setup-ssl.sh
./setup-ssl.sh

# 3. Desplegar
chmod +x deploy.sh
./deploy.sh
```

---

## Orden de Ejecución para Actualización

**Método Recomendado (con imágenes Docker pre-construidas):**

```bash
# En desarrollo: construir y subir
cd infrastructure
./build-and-push.sh v1.0.2

# En servidor: actualizar
cd /opt/intell/infrastructure
nano .docker.env  # Cambiar IMAGE_TAG=v1.0.2
docker compose -f docker-compose.prod.yml --env-file .docker.env pull
docker compose -f docker-compose.prod.yml --env-file .docker.env up -d
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py collectstatic --noinput
```

**Método Alternativo (build en servidor):**

```bash
cd /opt/intell/infrastructure
./update.sh
```

---

## Permisos Requeridos

Todos los scripts deben ser ejecutables:

```bash
chmod +x deploy.sh setup-ssl.sh backup-db.sh restore-db.sh update.sh build-and-push.sh
```

---

## Variables de Entorno Requeridas

Los scripts leen las siguientes variables de entorno:

- **`.docker.env`**: Usado por `docker-compose.prod.yml`, `backup-db.sh`, `restore-db.sh`
- **`.django.env`**: Usado por el contenedor backend (Django)
- **`.build.env`**: Usado por `build-and-push.sh` para construir frontend con URLs correctas

Ver [e-ENV_FILES_README.md](e-ENV_FILES_README.md) para más detalles sobre las variables de entorno.

---

## Troubleshooting

### Script no se ejecuta

```bash
# Verificar permisos
ls -la deploy.sh

# Hacer ejecutable
chmod +x deploy.sh
```

### Error de variables de entorno

```bash
# Verificar que los archivos existen
ls -la .docker.env .django.env

# Verificar sintaxis
cat .docker.env | grep -v '^#' | grep -v '^$'
```

### Error de Docker Compose

```bash
# Usar --env-file explícitamente
docker compose -f docker-compose.prod.yml --env-file .docker.env config
```

---

Para más información sobre deployment en producción, consulta [b-DEPLOYMENT.md](b-DEPLOYMENT.md).
