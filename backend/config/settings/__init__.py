"""
Django settings module for the Intelli project.

This package contains split settings for different environments:
    - development.py - Development settings (default)
    - production.py - Production settings
    - testing.py - Testing settings

Usage:
    Set DJANGO_SETTINGS_MODULE environment variable:
        export DJANGO_SETTINGS_MODULE=config.settings.development
        export DJANGO_SETTINGS_MODULE=config.settings.production
        export DJANGO_SETTINGS_MODULE=config.settings.testing

    Or use the ENVIRONMENT variable in .env file:
        ENVIRONMENT=development
        ENVIRONMENT=production
        ENVIRONMENT=testing

For convenience, this module imports from development by default.
However, Django will use the module specified in DJANGO_SETTINGS_MODULE
when running commands or serving requests.
"""

# Import from development for convenience and IDE support
# The actual module used is determined by DJANGO_SETTINGS_MODULE
from .development import *  # noqa: F403, F401

