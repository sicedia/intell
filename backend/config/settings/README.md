# Django Settings Structure

This directory contains the split settings configuration for the Intelli Django project. The settings are organized into separate files for different environments, following Django best practices.

## Structure

```
settings/
├── __init__.py          # Environment detection and default export
├── base.py              # Common settings shared across all environments
├── development.py       # Development-specific settings
├── production.py        # Production-specific settings
├── testing.py           # Testing-specific settings
└── README.md            # This file
```

## Files Overview

### `base.py`
Contains all common settings that are shared across all environments:
- `INSTALLED_APPS` - Django apps and third-party packages
- `MIDDLEWARE` - Middleware configuration
- Templates, password validators, internationalization
- Static and media file settings
- Django REST Framework configuration
- CORS base configuration
- Logging configuration

### `development.py`
Development-specific settings:
- `DEBUG = True`
- SQLite database (default) or PostgreSQL from docker-compose
- Console email backend
- CORS allows `localhost:3000`
- Detailed logging with SQL query logging
- Browsable API enabled

### `production.py`
Production-specific settings:
- `DEBUG = False`
- Database from `DATABASE_URL` environment variable
- Security headers and HTTPS settings
- Production email configuration
- Optimized logging
- Static files collection
- Restricted CORS origins

### `testing.py`
Testing-specific settings:
- In-memory SQLite database
- Faster password hashing
- Disabled migrations (optional)
- Simplified logging
- Dummy cache backend

### `__init__.py`
Handles environment detection and exports the appropriate settings module. Defaults to development settings.

## Usage

### Development (Default)

```bash
python manage.py runserver
```

Or explicitly:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py runserver
```

### Production

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py runserver
```

Or set in your deployment environment:
```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
```

### Testing

```bash
export DJANGO_SETTINGS_MODULE=config.settings.testing
python manage.py test
```

Or Django will automatically use testing settings when running tests if configured.

## Environment Variables

All settings are configured via environment variables loaded from the `.env` file using `python-decouple`. See `backend/env.example` for all available environment variables.

### Required for Development
- `SECRET_KEY` - Django secret key
- `DEBUG=True`
- `ALLOWED_HOSTS=localhost,127.0.0.1`

### Required for Production
- `SECRET_KEY` - Strong, unique secret key
- `DEBUG=False`
- `ALLOWED_HOSTS` - Your domain(s)
- `DATABASE_URL` - Database connection string
- `CORS_ALLOWED_ORIGINS` - Frontend URL(s)

## Environment Detection

The `__init__.py` file automatically detects the environment based on:
1. `DJANGO_SETTINGS_MODULE` environment variable (highest priority)
2. `ENVIRONMENT` variable in `.env` file
3. Defaults to `development`

## Adding New Settings

### Common Settings (All Environments)
Add to `base.py`:
```python
# In base.py
MY_SETTING = config('MY_SETTING', default='default_value')
```

### Environment-Specific Settings
Add to the appropriate environment file:
```python
# In development.py
MY_SETTING = config('MY_SETTING', default='dev_value')

# In production.py
MY_SETTING = config('MY_SETTING', default='prod_value')
```

## Best Practices

1. **Never commit `.env` file** - It contains sensitive information
2. **Use environment variables** - Never hardcode secrets
3. **Test settings changes** - Use `python manage.py check` to validate
4. **Keep base.py clean** - Only common settings should be here
5. **Document custom settings** - Add comments explaining non-standard configurations

## Migration from Single Settings File

If you're migrating from a single `settings.py` file:

1. Common settings → `base.py`
2. Development-specific → `development.py`
3. Production-specific → `production.py`
4. Test-specific → `testing.py`

The old `config/settings.py` file is kept for backward compatibility and imports from `development.py`.

## Troubleshooting

### Settings Module Not Found
- Ensure `DJANGO_SETTINGS_MODULE` is set correctly
- Check that all `__init__.py` files exist in the settings directory
- Verify Python path includes the project root

### Environment Variables Not Loading
- Ensure `.env` file exists in `backend/` directory
- Check that `python-decouple` is installed
- Verify variable names match exactly (case-sensitive)

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that imports in settings files are correct
- Verify Python version compatibility (Python 3.8+)

## Additional Resources

- [Django Settings Documentation](https://docs.djangoproject.com/en/stable/topics/settings/)
- [python-decouple Documentation](https://github.com/henriquebastos/python-decouple)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)

