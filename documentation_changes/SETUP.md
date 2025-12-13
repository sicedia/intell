# Backend Setup Guide

This comprehensive guide will help you set up the Django backend for the Intelli project following industry best practices.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Environment Configuration](#environment-configuration)
- [Settings Structure](#settings-structure)
- [Running the Server](#running-the-server)
- [Verification](#verification)
- [Directory Structure](#directory-structure)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Next Steps](#next-steps)

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.8+** (Python 3.11+ recommended)
- **pip** (Python package manager)
- **Git** (for version control)
- **Virtual environment tool** (venv, which comes with Python 3.3+)

### Verify Installation

```bash
# Check Python version
python --version
# or
python3 --version

# Check pip version
pip --version
# or
pip3 --version
```

## Initial Setup

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Virtual Environment

**Why use a virtual environment?** It isolates project dependencies and prevents conflicts with other Python projects.

#### Windows

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

#### Linux/macOS

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

**Note:** When activated, your terminal prompt will show `(venv)` at the beginning.

**To deactivate** (when you're done working):
```bash
deactivate
```

### Step 3: Upgrade pip (Recommended)

```bash
# Windows/Linux/macOS
pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

**If `requirements.txt` doesn't exist**, install core dependencies manually:

```bash
pip install django>=5.0
pip install djangorestframework
pip install django-cors-headers
pip install python-decouple  # For environment variable management
```

Then create `requirements.txt`:

```bash
pip freeze > requirements.txt
```

### Step 5: Create Environment File

Create a `.env` file in the `backend/` directory to manage environment variables securely.

#### Option A: Copy from Example (if exists)

```bash
# Linux/macOS
cp env.example .env

# Windows
copy env.example .env
```

#### Option B: Create Manually

Create a `.env` file with the following content:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Optional for development - SQLite is default)
# DATABASE_URL=sqlite:///db.sqlite3

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000
CORS_ALLOW_CREDENTIALS=True

# Email Configuration (Optional)
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-password
```

### Step 6: Generate Secret Key

**Important:** Never use the default secret key in production!

```bash
# Generate a secure secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and replace `your-secret-key-here` in your `.env` file.

### Step 7: Run Migrations

```bash
python manage.py migrate
```

This creates the database tables required by Django and installed apps.

### Step 8: Create Superuser (Optional but Recommended)

Create an admin user to access the Django admin panel:

```bash
python manage.py createsuperuser
```

Follow the prompts to set:
- Username
- Email address (optional)
- Password (will be hidden for security)

### Step 9: Collect Static Files (For Production)

```bash
python manage.py collectstatic --noinput
```

**Note:** This is primarily for production. In development, Django serves static files automatically.

## Environment Configuration

### Environment Variables Overview

All sensitive configuration should be stored in the `.env` file, which is **never committed to version control**.

### Required Variables for Development

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key for cryptographic signing | Generated key (50+ characters) |
| `DEBUG` | Enable/disable debug mode | `True` for development |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames | `localhost,127.0.0.1` |

### Required Variables for Production

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Strong, unique secret key | Generated secure key |
| `DEBUG` | Must be `False` in production | `False` |
| `ALLOWED_HOSTS` | Your domain(s) | `example.com,www.example.com` |
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@host:5432/dbname` |
| `CORS_ALLOWED_ORIGINS` | Frontend URL(s) | `https://example.com` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ALLOW_CREDENTIALS` | Allow credentials in CORS requests | `True` |
| `TIME_ZONE` | Django timezone | `UTC` |
| `LANGUAGE_CODE` | Default language | `en-us` |

### Loading Environment Variables

If using `python-decouple`, your settings should load variables like this:

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
```

## Settings Structure

### Current Structure (Single File)

The project currently uses a single `settings.py` file located at:
```
backend/config/settings.py
```

### Recommended Structure (Split Settings)

For better organization, especially in production, consider splitting settings into:

```
backend/config/settings/
├── __init__.py          # Exports the appropriate settings module
├── base.py              # Common settings shared across all environments
├── development.py       # Development-specific settings
├── production.py        # Production-specific settings
├── testing.py           # Testing-specific settings
└── README.md            # Settings documentation
```

**Benefits:**
- Clear separation of concerns
- Easier to manage environment-specific configurations
- Better security (production settings isolated)
- Easier testing configuration

**To implement split settings**, you would:
1. Create `config/settings/` directory
2. Move common settings to `base.py`
3. Create environment-specific files that import from `base.py`
4. Update `manage.py` and `wsgi.py` to use the appropriate settings module

## Running the Server

### Development Server

```bash
# Default (runs on http://127.0.0.1:8000/)
python manage.py runserver

# Custom port
python manage.py runserver 8000

# Custom IP and port
python manage.py runserver 0.0.0.0:8000
```

### Using Different Settings Modules

If you have split settings:

```bash
# Development (default)
python manage.py runserver

# Explicitly set development
# Windows
set DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver

# Linux/macOS
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver

# Production
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py runserver

# Testing
export DJANGO_SETTINGS_MODULE=config.settings.testing
python manage.py test
```

### Running with Environment Variables

You can also set environment variables inline:

**Windows (PowerShell):**
```powershell
$env:DJANGO_SETTINGS_MODULE="config.settings.development"
python manage.py runserver
```

**Linux/macOS:**
```bash
DJANGO_SETTINGS_MODULE=config.settings.development python manage.py runserver
```

## Verification

After setup, verify everything is working:

### 1. Check Server is Running

Visit these URLs in your browser:

- **Main site:** http://127.0.0.1:8000/
- **Admin panel:** http://127.0.0.1:8000/admin/
- **API root:** http://127.0.0.1:8000/api/ (if configured)

### 2. Test Database Connection

```bash
python manage.py dbshell
```

If using SQLite, this opens the SQLite shell. Type `.quit` to exit.

### 3. Check Installed Apps

```bash
python manage.py check
```

This validates your Django installation and configuration.

### 4. List Available Commands

```bash
python manage.py help
```

## Directory Structure

After complete setup, your backend directory should look like this:

```
backend/
├── config/                 # Django project configuration
│   ├── __init__.py
│   ├── settings.py        # Main settings file (or settings/ directory)
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── apps/                   # Django applications
│   └── core/              # Main application (if exists)
│       ├── __init__.py
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       └── admin.py
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User-uploaded files
├── templates/              # HTML templates
├── logs/                   # Application logs (if configured)
├── venv/                   # Virtual environment (not in git)
├── .env                    # Environment variables (not in git)
├── .gitignore              # Git ignore rules
├── db.sqlite3              # SQLite database (not in git)
├── manage.py               # Django management script
└── requirements.txt        # Python dependencies
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Error: No module named 'decouple'

**Solution:**
```bash
pip install python-decouple
# or
pip install -r requirements.txt
```

#### 2. ModuleNotFoundError: No module named 'django'

**Solution:**
- Ensure virtual environment is activated (you should see `(venv)` in your prompt)
- Install dependencies: `pip install -r requirements.txt`

#### 3. Settings Module Not Found

**Solution:**
- Check that you're using the correct settings module path
- Verify `DJANGO_SETTINGS_MODULE` environment variable
- Ensure `manage.py` has the correct default settings module

#### 4. Database Connection Error

**Symptoms:**
- `django.db.utils.OperationalError`
- `no such table` errors

**Solutions:**
- Run migrations: `python manage.py migrate`
- Check `DATABASE_URL` in `.env` file (if using external database)
- For SQLite: Ensure write permissions in the backend directory
- Verify database file exists: `ls db.sqlite3` (Linux/macOS) or `dir db.sqlite3` (Windows)

#### 5. CORS Errors

**Symptoms:**
- Browser console shows CORS policy errors
- Frontend cannot connect to backend API

**Solutions:**
- Verify `CORS_ALLOWED_ORIGINS` in `.env` includes your frontend URL
- Default should be: `CORS_ALLOWED_ORIGINS=http://localhost:3000`
- Check that `django-cors-headers` is installed and in `INSTALLED_APPS`
- Verify `CorsMiddleware` is in `MIDDLEWARE` (should be near the top)

#### 6. Port Already in Use

**Symptoms:**
```
Error: That port is already in use.
```

**Solutions:**
- Use a different port: `python manage.py runserver 8001`
- Find and kill the process using the port:
  - **Windows:** `netstat -ano | findstr :8000` then `taskkill /PID <pid> /F`
  - **Linux/macOS:** `lsof -ti:8000 | xargs kill`

#### 7. Migration Issues

**Symptoms:**
- `No changes detected`
- Migration conflicts

**Solutions:**
```bash
# Create migrations for specific app
python manage.py makemigrations <app_name>

# Show migration status
python manage.py showmigrations

# Apply specific migration
python manage.py migrate <app_name> <migration_number>

# Reset migrations (use with caution!)
# Delete migration files and run makemigrations again
```

#### 8. Static Files Not Loading

**Solutions:**
```bash
# Collect static files
python manage.py collectstatic

# Check STATIC_URL and STATIC_ROOT in settings
# Ensure static files middleware is configured
```

#### 9. Secret Key Warning

**Symptoms:**
- Django warns about insecure secret key

**Solution:**
- Generate a new secret key (see Step 6 in Initial Setup)
- Update `SECRET_KEY` in `.env` file
- Never commit secret keys to version control

#### 10. Virtual Environment Issues

**Symptoms:**
- Packages installed but not found
- Wrong Python version

**Solutions:**
```bash
# Deactivate and recreate virtual environment
deactivate
rm -rf venv  # Linux/macOS
# or
rmdir /s venv  # Windows

# Recreate and reinstall
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Security Best Practices

### Development

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Use strong secret keys** - Generate unique keys for each environment
3. **Keep `DEBUG=True` only in development** - Never in production
4. **Limit `ALLOWED_HOSTS`** - Only include necessary hosts
5. **Use virtual environments** - Isolate dependencies

### Production

1. **Set `DEBUG=False`** - Critical for security
2. **Use environment variables** - Never hardcode secrets
3. **Use HTTPS** - Configure SSL/TLS certificates
4. **Secure database credentials** - Use strong passwords
5. **Configure proper CORS** - Only allow trusted origins
6. **Use production database** - PostgreSQL, MySQL, etc. (not SQLite)
7. **Set up proper logging** - Monitor for security issues
8. **Keep dependencies updated** - Regularly update packages
9. **Use Django security middleware** - Enable security features
10. **Configure `SECURE_SSL_REDIRECT`** - Force HTTPS in production

### Checklist Before Production Deployment

- [ ] `DEBUG = False`
- [ ] Strong, unique `SECRET_KEY`
- [ ] `ALLOWED_HOSTS` configured with production domain
- [ ] Database configured (not SQLite)
- [ ] Static files collected and served properly
- [ ] CORS configured for production frontend URL
- [ ] HTTPS enabled
- [ ] Environment variables secured
- [ ] Logging configured
- [ ] Error tracking set up (Sentry, etc.)
- [ ] Backup strategy in place

## Next Steps

After completing the setup:

1. **Review Settings:** Check `config/settings.py` and customize as needed
2. **Configure URLs:** Set up API endpoints in `config/urls.py`
3. **Create Apps:** Use `python manage.py startapp <app_name>` to create new Django apps
4. **Set Up API:** Configure Django REST Framework if not already done
5. **Database Models:** Create models in your apps' `models.py`
6. **Admin Interface:** Register models in `admin.py` for easy management
7. **Testing:** Write tests in `tests.py` files
8. **Documentation:** Document your API endpoints

### Useful Commands Reference

```bash
# Create a new Django app
python manage.py startapp <app_name>

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Django shell (interactive Python shell with Django context)
python manage.py shell

# Check for common problems
python manage.py check

# Show all migrations
python manage.py showmigrations

# Collect static files
python manage.py collectstatic
```

### Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)
- [12 Factor App Methodology](https://12factor.net/)

---

**Need Help?** If you encounter issues not covered here, check:
- Django's official documentation
- Stack Overflow (tag: django)
- Project's main README.md
- GitHub issues (if applicable)
