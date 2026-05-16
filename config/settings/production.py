"""
Django settings for LabSynch — production environment.
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# Security
# =============================================================================

DEBUG = False

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# These default to False so the app works over plain HTTP on the VPS.
# Flip to True once you add a TLS certificate + domain.
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)  # noqa: F405
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE", default=False)  # noqa: F405
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE", default=False)  # noqa: F405
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)  # noqa: F405
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)  # noqa: F405

# CORS origins come from the .env file (CORS_ALLOWED_ORIGINS is set in base.py)
CORS_ALLOW_ALL_ORIGINS = False

# =============================================================================
# Static files — WhiteNoise
# =============================================================================

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =============================================================================
# Media files — local filesystem (served by Nginx via Docker volume)
# =============================================================================

# DEFAULT_FILE_STORAGE is already the Django default (FileSystemStorage).
# MEDIA_ROOT / MEDIA_URL are set in base.py.  No change needed here.

# =============================================================================
# Logging — production level
# =============================================================================

LOGGING["loggers"]["apps"]["level"] = "INFO"  # noqa: F405
