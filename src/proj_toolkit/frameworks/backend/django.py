"""Django backend framework plugin."""

from __future__ import annotations

from typing import List

from proj_toolkit.config import Language, register_backend
from proj_toolkit.frameworks.base import FileSpec, FrameworkPlugin


@register_backend
class DjangoPlugin(FrameworkPlugin):
    name = "django"
    supported_languages = [Language.PYTHON]

    def generate_files(self, language: Language, project_name: str) -> List[FileSpec]:
        slug = project_name.lower().replace("-", "_").replace(" ", "_")
        files: List[FileSpec] = []

        # manage.py
        files.append(FileSpec(
            relative_path="manage.py",
            content=f"""\
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{slug}.config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
""",
        ))

        # config/settings.py
        files.append(FileSpec(
            relative_path="config/settings.py",
            content=f"""\
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

DEBUG = os.environ.get("DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {{
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {{
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        }},
    }},
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {{
    "default": {{
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }}
}}

STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
""",
        ))

        # config/urls.py
        files.append(FileSpec(
            relative_path="config/urls.py",
            content="""\
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
]
""",
        ))

        # config/wsgi.py
        files.append(FileSpec(
            relative_path="config/wsgi.py",
            content=f"""\
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{slug}.config.settings")
application = get_wsgi_application()
""",
        ))

        # config/asgi.py
        files.append(FileSpec(
            relative_path="config/asgi.py",
            content=f"""\
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{slug}.config.settings")
application = get_asgi_application()
""",
        ))

        # config/__init__.py
        files.append(FileSpec(relative_path="config/__init__.py", content=""))

        # requirements.txt
        files.append(FileSpec(
            relative_path="requirements.txt",
            content="""\
django>=5.0
gunicorn>=22.0
python-dotenv>=1.0
""",
        ))

        # .env.example
        files.append(FileSpec(
            relative_path=".env.example",
            content="""\
SECRET_KEY=change-me
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1
""",
        ))

        # README.md
        files.append(FileSpec(
            relative_path="README.md",
            content=f"""\
# {project_name} — Backend (Django)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Health check: `GET /health/`
""",
        ))

        return files

    def readme_snippet(self, language: Language) -> str:
        return """\
### Backend (Django)

- Config lives in `backend/config/`
- Run `python manage.py runserver` from `backend/` to start the dev server (default port 8000)
- Use `python manage.py startapp <name>` to create new Django apps
- Health endpoint: `GET /health/`
- Always run `python manage.py migrate` after pulling schema changes
"""

    def dockerfile_content(self, language: Language, project_name: str) -> str:
        return """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
"""
