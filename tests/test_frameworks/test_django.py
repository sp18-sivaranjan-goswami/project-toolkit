"""Tests for the Django framework plugin."""

from __future__ import annotations

from proj_toolkit.config import Language
from proj_toolkit.frameworks.backend.django import DjangoPlugin


def _files() -> dict:
    plugin = DjangoPlugin()
    specs = plugin.generate_files(Language.PYTHON, "my-app")
    return {s.relative_path: s.content for s in specs}


def test_manage_py_exists():
    files = _files()
    assert "manage.py" in files


def test_manage_py_has_main_guard():
    files = _files()
    assert '__name__ == "__main__"' in files["manage.py"]


def test_settings_exists():
    files = _files()
    assert "config/settings.py" in files


def test_settings_has_installed_apps():
    files = _files()
    assert "INSTALLED_APPS" in files["config/settings.py"]


def test_urls_has_health_endpoint():
    files = _files()
    assert "health" in files["config/urls.py"]


def test_wsgi_exists():
    files = _files()
    assert "config/wsgi.py" in files


def test_asgi_exists():
    files = _files()
    assert "config/asgi.py" in files


def test_requirements_txt_has_django():
    files = _files()
    assert "django" in files["requirements.txt"].lower()


def test_env_example_exists():
    files = _files()
    assert ".env.example" in files


def test_readme_exists():
    files = _files()
    assert "README.md" in files


def test_readme_snippet_mentions_manage():
    plugin = DjangoPlugin()
    snippet = plugin.readme_snippet(Language.PYTHON)
    assert "manage.py" in snippet
