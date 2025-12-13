"""
Django settings for config project.

This file is kept for backward compatibility.
It imports settings from config.settings.development by default.

For new projects, use the split settings structure in config/settings/:
- config.settings.development - Development settings
- config.settings.production - Production settings
- config.settings.testing - Testing settings

To use a different settings module, set DJANGO_SETTINGS_MODULE environment variable:
    export DJANGO_SETTINGS_MODULE=config.settings.production
"""

# Import all settings from development module for backward compatibility
from .settings.development import *  # noqa: F403, F401
