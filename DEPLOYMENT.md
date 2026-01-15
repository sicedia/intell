# Guía de Deployment en Producción - Intelli

Esta guía proporciona instrucciones paso a paso para desplegar Intelli en un servidor Ubuntu 24.04 LTS en producción.

## Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Preparación del Servidor](#preparación-del-servidor)
3. [Configuración Inicial](#configuración-inicial)
4. [Configuración de SSL](#configuración-de-ssl)
5. [Deployment](#deployment)
6. [Verificación](#verificación)
7. [Mantenimiento](#mantenimiento)
8. [Troubleshooting](#troubleshooting)

---

## Requisitos Previos

### Hardware Mínimo Recomendado

- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disco**: 50 GB SSD
- **Red**: Conexión estable con puertos 80 y 443 abiertos

### Software Requerido

- **Sistema Operativo**: Ubuntu 24.04 LTS
- **Docker**: Versión 24.0 o superior
- **Docker Compose**: Versión 2.0 o superior
- **Git**: Para clonar el repositorio

### Dominio y DNS

- Dominio configurado: `openintell.cedia.edu.ec`
- Registros DNS A/AAAA apuntando al servidor
- Certificado SSL (wildcard `*.cedia.edu.ec` o específico)

---

## Preparación del Servidor

### 1. Actualizar el Sistema

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y curl wget git ufw
```

### 2. Instalar Docker

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker (reemplazar 'usuario' con tu usuario)
sudo usermod -aG docker $USER

# Instalar Docker Compose Plugin
sudo apt install -y docker-compose-plugin

# Verificar instalación
docker --version
docker compose version
```

**Nota**: Cierra sesión y vuelve a iniciar sesión para que los cambios de grupo surtan efecto.

### 3. Configurar Firewall (UFW)

```bash
# Habilitar UFW
sudo ufw enable

# Permitir SSH (IMPORTANTE: hacerlo antes de bloquear todo)
sudo ufw allow 22/tcp

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verificar estado
sudo ufw status
```

### 4. Clonar el Repositorio

```bash
# Crear directorio para la aplicación
sudo mkdir -p /opt/intell
sudo chown $USER:$USER /opt/intell

# Clonar repositorio (reemplazar con tu URL)
cd /opt/intell
git clone <tu-repositorio-url> .

# O si ya tienes el código, copiarlo al servidor
```

---

## Configuración Inicial

### 1. Configurar Variables de Entorno

```bash
cd /opt/intell/infrastructure

# Copiar archivos de ejemplo
cp .docker.env.example .docker.env
cp .django.env.example .django.env

# Editar con tus valores
nano .docker.env
nano .django.env
```

**Configuración mínima en `.docker.env`**:

```env
POSTGRES_DB=intell
POSTGRES_USER=intell_user
POSTGRES_PASSWORD=<contraseña-fuerte-generada>
NEXT_PUBLIC_API_BASE_URL=https://openintell.cedia.edu.ec/api
NEXT_PUBLIC_WS_BASE_URL=wss://openintell.cedia.edu.ec/ws
```

**Configuración mínima en `.django.env`**:

```env
SECRET_KEY=<generar-nueva-clave-secreta>
DEBUG=False
ALLOWED_HOSTS=openintell.cedia.edu.ec
CORS_ALLOWED_ORIGINS=https://openintell.cedia.edu.ec
CSRF_TRUSTED_ORIGINS=https://openintell.cedia.edu.ec
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

**Generar SECRET_KEY**:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Configurar Microsoft OAuth (si aplica)

Si usas autenticación con Microsoft, actualiza en `.django.env`:

```env
MICROSOFT_CLIENT_ID=<tu-client-id>
MICROSOFT_CLIENT_SECRET=<tu-client-secret>
MICROSOFT_TENANT_ID=<tu-tenant-id>
MICROSOFT_REDIRECT_URI=https://openintell.cedia.edu.ec/api/auth/microsoft/callback/
MICROSOFT_LOGIN_REDIRECT_URL=https://openintell.cedia.edu.ec/en/dashboard
MICROSOFT_LOGIN_ERROR_URL=https://openintell.cedia.edu.ec/en/login
```

**Importante**: Configura estos mismos URLs en Azure Portal > App Registrations > Redirect URIs.

---

## Configuración de SSL

### Opción 1: Certificado Wildcard Existente

Si ya tienes un certificado wildcard `*.cedia.edu.ec`:

```bash
cd /opt/intell/infrastructure

# Crear directorio para certificados
mkdir -p nginx/ssl

# Copiar certificados (ajustar rutas según tu caso)
cp /ruta/a/tu/fullchain.pem nginx/ssl/
cp /ruta/a/tu/privkey.pem nginx/ssl/

# Establecer permisos correctos
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem
```

### Opción 2: Let's Encrypt (Automático)

```bash
cd /opt/intell/infrastructure

# Hacer ejecutable el script
chmod +x setup-ssl.sh

# Ejecutar script de configuración SSL
./setup-ssl.sh
```

El script te guiará a través del proceso:
1. Selecciona opción 1 para Let's Encrypt
2. Asegúrate de que el DNS apunta correctamente al servidor
3. El certificado se generará automáticamente

### Opción 3: Certificado Personalizado

```bash
cd /opt/intell/infrastructure

# Ejecutar script
./setup-ssl.sh

# Seleccionar opción 2
# Proporcionar rutas a tus archivos de certificado
```

---

## Deployment

### Método 1: Despliegue con Imágenes Pre-construidas (Recomendado)

Este método utiliza imágenes Docker pre-construidas y subidas a Docker Hub, evitando builds en el servidor.

#### Paso 1: Construir y Subir Imágenes Localmente

En tu máquina de desarrollo:

```bash
cd infrastructure

# Copiar archivo de configuración de build
cp .build.env.example .build.env

# Editar .build.env con tus valores de producción
nano .build.env
```

**Configuración mínima en `.build.env`**:
```env
NEXT_PUBLIC_API_BASE_URL=https://openintell.cedia.edu.ec/api
NEXT_PUBLIC_WS_BASE_URL=wss://openintell.cedia.edu.ec/ws
NEXT_PUBLIC_APP_ENV=production
```

**Construir y subir imágenes**:

```bash
# Linux/macOS
./build-and-push.sh v1.0.1

# Windows PowerShell
.\build-and-push.ps1 v1.0.1
```

El script:
1. Construye las imágenes backend y frontend
2. Las etiqueta con la versión especificada (ej: `v1.0.1`) y `latest`
3. Las sube a Docker Hub (`sicedia/intell-backend` y `sicedia/intell-frontend`)

**Nota**: Asegúrate de estar logueado en Docker Hub:
```bash
docker login
```

#### Paso 2: Configurar el Servidor

En el servidor de producción:

```bash
cd /opt/intell/infrastructure

# Copiar archivos de ejemplo
cp .docker.env.example .docker.env
cp .django.env.example .django.env

# Editar .docker.env
nano .docker.env
```

**Agregar en `.docker.env`**:
```env
# Docker Image Configuration
IMAGE_TAG=v1.0.1  # o la versión que subiste
```

#### Paso 3: Desplegar en el Servidor

```bash
cd /opt/intell/infrastructure

# Descargar imágenes desde Docker Hub
docker compose -f docker-compose.prod.yml pull

# Iniciar servicios
docker compose -f docker-compose.prod.yml up -d

# Esperar a que los servicios estén listos
sleep 15

# Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput

# Recopilar archivos estáticos
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Crear superusuario (si no existe)
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

#### Actualizar a Nueva Versión

Cuando tengas una nueva versión:

```bash
# 1. En desarrollo: construir y subir nueva versión
./build-and-push.sh v1.0.2

# 2. En servidor: actualizar .docker.env
# Cambiar IMAGE_TAG=v1.0.2

# 3. En servidor: descargar y reiniciar
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# 4. Ejecutar migraciones si hay cambios en la BD
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput
```

#### Rollback a Versión Anterior

Si necesitas volver a una versión anterior:

```bash
# Cambiar IMAGE_TAG en .docker.env a la versión anterior
# Ejemplo: IMAGE_TAG=v1.0.1

# Descargar y reiniciar
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Método 2: Script Automatizado (Build en Servidor)

```bash
cd /opt/intell/infrastructure

# Hacer ejecutables los scripts
chmod +x deploy.sh setup-ssl.sh backup-db.sh update.sh restore-db.sh

# Ejecutar deployment
./deploy.sh
```

El script realizará:
1. Verificación de requisitos
2. Validación de archivos de configuración
3. Construcción de imágenes Docker
4. Inicio de servicios
5. Ejecución de migraciones
6. Recopilación de archivos estáticos
7. Creación de superusuario (si no existe)

### Método 3: Manual (Build en Servidor)

**Nota**: Este método requiere construir las imágenes en el servidor, lo cual consume más recursos y tiempo.

```bash
cd /opt/intell/infrastructure

# Construir imágenes (requiere modificar docker-compose.prod.yml para usar build:)
docker compose -f docker-compose.prod.yml build

# Iniciar servicios
docker compose -f docker-compose.prod.yml up -d

# Esperar a que los servicios estén listos
sleep 15

# Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput

# Recopilar archivos estáticos
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Crear superusuario
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

---

## Verificación

### 1. Verificar Estado de Servicios

```bash
cd /opt/intell/infrastructure
docker compose -f docker-compose.prod.yml ps
```

Todos los servicios deben mostrar estado "Up" y "healthy".

### 2. Verificar Logs

```bash
# Ver todos los logs
docker compose -f docker-compose.prod.yml logs -f

# Ver logs de un servicio específico
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
docker compose -f docker-compose.prod.yml logs -f nginx
```

### 3. Probar Endpoints

```bash
# Health check
curl https://openintell.cedia.edu.ec/api/health/

# Verificar HTTPS
curl -I https://openintell.cedia.edu.ec

# Verificar redirección HTTP → HTTPS
curl -I http://openintell.cedia.edu.ec
```

### 4. Verificar en Navegador

1. Abrir `https://openintell.cedia.edu.ec`
2. Verificar que el certificado SSL es válido
3. Probar login y funcionalidades principales

---

## Mantenimiento

### Actualizar la Aplicación

```bash
cd /opt/intell/infrastructure

# Usar script automatizado
./update.sh

# O manualmente:
git pull
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

### Backup de Base de Datos

```bash
cd /opt/intell/infrastructure

# Backup manual
./backup-db.sh

# Backup con limpieza de backups antiguos
./backup-db.sh --cleanup

# Los backups se guardan en: infrastructure/backups/
```

### Restaurar Base de Datos

```bash
cd /opt/intell/infrastructure

# Listar backups disponibles
ls -lh backups/

# Restaurar desde backup
./restore-db.sh backups/intell_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Reiniciar Servicios

```bash
cd /opt/intell/infrastructure

# Reiniciar todos los servicios
docker compose -f docker-compose.prod.yml restart

# Reiniciar un servicio específico
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
docker compose -f docker-compose.prod.yml restart nginx
```

### Detener Servicios

```bash
cd /opt/intell/infrastructure

# Detener sin eliminar volúmenes
docker compose -f docker-compose.prod.yml down

# Detener y eliminar volúmenes (¡CUIDADO! Elimina datos)
docker compose -f docker-compose.prod.yml down -v
```

### Ver Uso de Recursos

```bash
# Ver uso de recursos de contenedores
docker stats

# Ver uso de disco
docker system df

# Limpiar recursos no utilizados
docker system prune -a
```

### Monitoreo de Logs

```bash
# Ver logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f

# Ver últimos 100 líneas
docker compose -f docker-compose.prod.yml logs --tail=100

# Ver logs de un servicio específico
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## Troubleshooting

### Problema: Servicios no inician

**Solución**:
```bash
# Ver logs de errores
docker compose -f docker-compose.prod.yml logs

# Verificar configuración
docker compose -f docker-compose.prod.yml config

# Reiniciar Docker
sudo systemctl restart docker
```

### Problema: Error de conexión a base de datos

**Solución**:
```bash
# Verificar que PostgreSQL está corriendo
docker compose -f docker-compose.prod.yml ps db

# Verificar logs de PostgreSQL
docker compose -f docker-compose.prod.yml logs db

# Verificar variables de entorno
docker compose -f docker-compose.prod.yml exec backend env | grep DATABASE
```

### Problema: Error 502 Bad Gateway

**Solución**:
```bash
# Verificar que backend está corriendo
docker compose -f docker-compose.prod.yml ps backend

# Verificar logs de backend
docker compose -f docker-compose.prod.yml logs backend

# Verificar logs de nginx
docker compose -f docker-compose.prod.yml logs nginx

# Reiniciar nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Problema: Certificado SSL no funciona

**Solución**:
```bash
# Verificar que los certificados existen
ls -lh nginx/ssl/

# Verificar permisos
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem

# Verificar configuración de nginx
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Reiniciar nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Problema: Celery no procesa tareas

**Solución**:
```bash
# Verificar que Celery worker está corriendo
docker compose -f docker-compose.prod.yml ps celery-worker

# Ver logs de Celery
docker compose -f docker-compose.prod.yml logs celery-worker

# Verificar conexión a Redis
docker compose -f docker-compose.prod.yml exec celery-worker celery -A config inspect active

# Reiniciar Celery
docker compose -f docker-compose.prod.yml restart celery-worker
```

### Problema: WebSocket no funciona

**Solución**:
```bash
# Verificar que Redis está corriendo (Channels usa Redis)
docker compose -f docker-compose.prod.yml ps redis

# Verificar configuración de Channels
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "from channels.layers import get_channel_layer; print(get_channel_layer())"

# Verificar logs de backend
docker compose -f docker-compose.prod.yml logs backend | grep -i websocket
```

### Problema: Archivos estáticos no se cargan

**Solución**:
```bash
# Recopilar archivos estáticos
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Verificar que el volumen está montado
docker compose -f docker-compose.prod.yml exec nginx ls -la /var/www/static/

# Reiniciar nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Problema: Alto uso de memoria

**Solución**:
```bash
# Ver uso de recursos
docker stats

# Ajustar límites en docker-compose.prod.yml
# Reducir concurrency de Celery
# Reiniciar servicios
docker compose -f docker-compose.prod.yml restart
```

---

## Comandos Útiles

### Gestión de Contenedores

```bash
# Ver estado de todos los servicios
docker compose -f docker-compose.prod.yml ps

# Ver logs en tiempo real
docker compose -f docker-compose.prod.yml logs -f

# Ejecutar comando en contenedor
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
docker compose -f docker-compose.prod.yml exec backend python manage.py dbshell
```

### Base de Datos

```bash
# Acceder a PostgreSQL
docker compose -f docker-compose.prod.yml exec db psql -U intell_user -d intell

# Backup manual
docker compose -f docker-compose.prod.yml exec db pg_dump -U intell_user intell > backup.sql

# Restaurar manual
docker compose -f docker-compose.prod.yml exec -T db psql -U intell_user intell < backup.sql
```

### Django

```bash
# Crear superusuario
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Ejecutar migraciones
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Crear migraciones
docker compose -f docker-compose.prod.yml exec backend python manage.py makemigrations

# Shell de Django
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

---

## Seguridad Adicional

### Configurar Backups Automáticos

Agregar a crontab:

```bash
crontab -e

# Backup diario a las 2 AM
0 2 * * * cd /opt/intell/infrastructure && ./backup-db.sh --cleanup >> /var/log/intell-backup.log 2>&1
```

### Monitoreo de Logs

Considerar configurar log rotation y monitoreo:

```bash
# Configurar logrotate para logs de Docker
sudo nano /etc/logrotate.d/docker-containers
```

### Actualizaciones de Seguridad

```bash
# Actualizar sistema regularmente
sudo apt update && sudo apt upgrade -y

# Actualizar imágenes Docker
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

---

## Soporte

Para problemas o preguntas:
1. Revisar logs: `docker compose -f docker-compose.prod.yml logs`
2. Verificar configuración: `docker compose -f docker-compose.prod.yml config`
3. Consultar esta documentación
4. Contactar al equipo de desarrollo

---

## Notas Finales

- **Nunca** commits archivos `.docker.env` o `.django.env` al repositorio
- **Siempre** haz backup antes de actualizar
- **Monitorea** los logs regularmente
- **Mantén** el sistema y las imágenes Docker actualizadas
- **Revisa** los backups periódicamente

¡Buena suerte con tu deployment!
