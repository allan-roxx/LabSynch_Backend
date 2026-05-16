FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cached until requirements change)
COPY requirements/production.txt requirements/production.txt
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy application source
COPY . .

# Non-root user for security
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser \
    && mkdir -p /app/media /app/staticfiles /app/celerybeat \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
