#!/bin/sh
set -e

python manage.py migrate --fake-initial --noinput 2>&1 | grep -v "already exists\|NodeNotFoundError" || \
python manage.py migrate --noinput 2>&1 | grep -v "already exists\|NodeNotFoundError" || \
echo "Migrations completed or skipped"

python manage.py collectstatic --noinput || true
exec gunicorn config.wsgi:application --bind 0.0.0.0:8005 --workers 2 --timeout 120

