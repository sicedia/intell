# Intelli - Patent Analysis Platform

Monorepo application for patent data analysis and visualization with Django backend (REST API + WebSocket), Next.js frontend (TypeScript), Celery workers, and Redis.

## 📚 Documentación

Toda la documentación del proyecto se encuentra en la carpeta [`documentation/`](documentation/).

**Empieza aquí:**
- **Primera vez:** Lee [`documentation/README.md`](documentation/README.md) para ver el orden de lectura recomendado
- **Desarrollo:** Consulta [`documentation/a-README.md`](documentation/a-README.md) para Quick Start
- **Producción:** Sigue la guía en [`documentation/b-DEPLOYMENT.md`](documentation/b-DEPLOYMENT.md)

## 🚀 Quick Start

Para comenzar rápidamente:

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd intell

# 2. Iniciar infraestructura (PostgreSQL, Redis)
cd infrastructure
docker-compose up -d

# 3. Configurar backend
cd ../backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# Editar .env con tus configuraciones
python manage.py migrate
python manage.py createsuperuser

# 4. Iniciar backend
python manage.py runserver

# 5. Configurar frontend (en otra terminal)
cd ../frontend
npm install
cp env.example .env.local
# Editar .env.local con tus configuraciones
npm run dev
```

Para una guía completa, consulta [`documentation/a-README.md`](documentation/a-README.md).

## 📁 Estructura del Proyecto

```
intell/
├── backend/              # Django REST API + WebSocket (Channels)
├── frontend/             # Next.js Application
├── infrastructure/       # Docker Compose configs
└── documentation/        # Toda la documentación organizada
```

## 🔗 Enlaces Rápidos

- [Documentación Principal](documentation/README.md) - Índice de documentación
- [Guía de Deployment](documentation/b-DEPLOYMENT.md) - Deployment en producción
- [Scripts de Deployment](documentation/c-DEPLOYMENT_SCRIPTS.md) - Documentación de scripts
- [Configuración de Variables](documentation/d-ENV_SETUP.md) - Variables de entorno
- [Infraestructura](documentation/f-INFRASTRUCTURE_README.md) - Docker Compose y servicios

## 📖 Más Información

Consulta [`documentation/README.md`](documentation/README.md) para ver todas las guías disponibles y el orden de lectura recomendado.
