#!/bin/sh
set -e

# Try fake-initial first, if it fails, try normal migrate, if that fails, skip
python manage.py migrate --fake-initial --noinput 2>&1 | grep -v "already exists" || \
python manage.py migrate --noinput 2>&1 | grep -v "already exists" || \
echo "Migrations completed or skipped"

python manage.py collectstatic --noinput || true
exec gunicorn config.wsgi:application --bind 0.0.0.0:8003 --workers 2 --timeout 120

