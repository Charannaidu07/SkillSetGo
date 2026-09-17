#!/usr/bin/env bash
# Exit immediately on error
set -o errexit

# Apply database migrations
echo "==> Running database migrations..."
python manage.py migrate --no-input

# Create / sync superuser credentials
echo "==> Setting up superuser..."
python manage.py setup_admin

# Launch WSGI server
echo "==> Starting Gunicorn WSGI Server..."
exec gunicorn SkillSetGo.wsgi:application
