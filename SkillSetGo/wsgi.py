"""
WSGI config for SkillSetGo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SkillSetGo.settings")
django.setup()

# Ensure all database tables and superuser are initialized when the container boots
try:
    call_command("migrate", interactive=False)
    call_command("setup_admin")
except Exception as e:
    print(f"WSGI startup auto-initialization message: {e}")

application = get_wsgi_application()
