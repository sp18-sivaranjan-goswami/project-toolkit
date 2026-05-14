"""Tests for the FastAPI framework plugin."""

from __future__ import annotations

from proj_toolkit.config import Language
from proj_toolkit.frameworks.backend.fastapi import FastAPIPlugin


def _files() -> dict:
    plugin = FastAPIPlugin()
    specs = plugin.generate_files(Language.PYTHON, "my-app")
    return {s.relative_path: s.content for s in specs}


def test_main_py_exists():
    files = _files()
    assert "app/main.py" in files


def test_main_py_has_health_endpoint():
    files = _files()
    content = files["app/main.py"]
    assert "/health" in content


def test_main_py_creates_fastapi_app():
    files = _files()
    content = files["app/main.py"]
    assert "FastAPI" in content


def test_routers_init_exists():
    files = _files()
    assert "app/routers/__init__.py" in files


def test_models_init_exists():
    files = _files()
    assert "app/models/__init__.py" in files


def test_requirements_has_fastapi():
    files = _files()
    assert "fastapi" in files["requirements.txt"].lower()


def test_requirements_has_uvicorn():
    files = _files()
    assert "uvicorn" in files["requirements.txt"]


def test_env_example_exists():
    files = _files()
    assert ".env.example" in files


def test_readme_exists():
    files = _files()
    assert "README.md" in files


def test_readme_snippet_mentions_uvicorn():
    plugin = FastAPIPlugin()
    snippet = plugin.readme_snippet(Language.PYTHON)
    assert "uvicorn" in snippet
