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

# Cloudflare Tunnel terminates TLS externally and forwards plain HTTP internally.
# SECURE_SSL_REDIRECT must stay False to avoid infinite redirect loops.
# Django learns the connection is HTTPS via the X-Forwarded-Proto header.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookies are transmitted securely because the browser↔Cloudflare leg is HTTPS.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=31536000)  # noqa: F405
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

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
