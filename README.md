# Intelli - Patent Analysis Platform

Monorepo application for patent data analysis and visualization with Django backend (REST API + WebSocket), Next.js frontend (TypeScript), Celery workers, and Redis.

## 📚 Documentation

All project documentation is located in the [`documentation/`](documentation/) folder.

**Start here:**
- **First time:** Read [`documentation/README.md`](documentation/README.md) to see the recommended reading order
- **Development:** Check [`documentation/a-README.md`](documentation/a-README.md) for Quick Start
- **Production:** Follow the guide in [`documentation/b-DEPLOYMENT.md`](documentation/b-DEPLOYMENT.md)

## 🚀 Quick Start

To get started quickly:

```bash
# 1. Clone the repository
git clone <repo-url>
cd intell

# 2. Start infrastructure (PostgreSQL, Redis)
cd infrastructure
docker-compose up -d

# 3. Setup backend with Poetry
cd ../backend

# Install Poetry if not already installed
pip install poetry

# Install dependencies
poetry install

# Activate Poetry shell (or use poetry run for commands)
poetry shell

# Copy environment file
cp env.example .env
# Edit .env with your configurations

# Run migrations
poetry run python manage.py migrate

# Create superuser
poetry run python manage.py createsuperuser

# 4. Start backend (in Poetry shell or use poetry run)
poetry run python manage.py runserver

# 5. Setup frontend (in another terminal)
cd ../frontend
npm install
cp env.example .env.local
# Edit .env.local with your configurations
npm run dev
```

For a complete guide, see [`documentation/a-README.md`](documentation/a-README.md).

## 📁 Project Structure

```
intell/
├── backend/              # Django REST API + WebSocket (Channels)
├── frontend/             # Next.js Application
├── infrastructure/       # Docker Compose configs
└── documentation/        # Toda la documentación organizada
```

## 🔗 Quick Links

- [Main Documentation](documentation/README.md) - Documentation index
- [Deployment Guide](documentation/b-DEPLOYMENT.md) - Production deployment
- [Deployment Scripts](documentation/c-DEPLOYMENT_SCRIPTS.md) - Script documentation
- [Environment Variables](documentation/d-ENV_SETUP.md) - Environment configuration
- [Infrastructure](documentation/f-INFRASTRUCTURE_README.md) - Docker Compose and services

## 📖 More Information

See [`documentation/README.md`](documentation/README.md) to view all available guides and the recommended reading order.
