"""
Django settings for LabSynch — development environment.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# Debug
# =============================================================================

DEBUG = True

ALLOWED_HOSTS = ["*"]


# =============================================================================
# Email — console backend for development
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# =============================================================================
# Celery — run tasks synchronously in development (no broker needed)
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = False


# =============================================================================
# Django Debug Toolbar
# =============================================================================

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]


# =============================================================================
# CORS — allow all origins in development
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True


# =============================================================================
# Logging — verbose output in development
# =============================================================================

LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
