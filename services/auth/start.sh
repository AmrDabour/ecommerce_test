#!/bin/sh
set -e

# Try to run migrations with --fake-initial first (for existing tables)
python manage.py migrate --fake-initial --noinput 2>/dev/null || python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput || true

# Start Gunicorn
exec gunicorn config.wsgi:application --bind 0.0.0.0:8002 --workers 2 --timeout 120


