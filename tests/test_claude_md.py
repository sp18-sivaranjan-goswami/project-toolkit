"""Tests for CLAUDE.md rendering."""

from __future__ import annotations

from pathlib import Path

from proj_toolkit.claude_md import render_claude_md
from proj_toolkit.config import (
    BackendFramework,
    FrontendFramework,
    Language,
    ProjectConfig,
)
from proj_toolkit.frameworks.backend.fastapi import FastAPIPlugin
from proj_toolkit.frameworks.frontend.react import ReactPlugin


def _config(**kwargs) -> ProjectConfig:
    defaults = dict(
        project_name="my-app",
        prd_path="/tmp/prd.md",
        frontend_framework=FrontendFramework.REACT,
        frontend_language=Language.TYPESCRIPT,
        backend_framework=BackendFramework.FASTAPI,
        backend_language=Language.PYTHON,
    )
    defaults.update(kwargs)
    return ProjectConfig(**defaults)


def test_render_contains_project_name() -> None:
    cfg = _config(project_name="awesome-app")
    result = render_claude_md(cfg, ReactPlugin(), FastAPIPlugin())
    assert "awesome-app" in result


def test_render_contains_framework_names() -> None:
    cfg = _config()
    result = render_claude_md(cfg, ReactPlugin(), FastAPIPlugin())
    assert "react" in result.lower()
    assert "fastapi" in result.lower()


def test_render_contains_language() -> None:
    cfg = _config(frontend_language=Language.JAVASCRIPT)
    result = render_claude_md(cfg, ReactPlugin(), FastAPIPlugin())
    assert "javascript" in result.lower()


def test_render_contains_prd_reference() -> None:
    cfg = _config()
    result = render_claude_md(cfg, ReactPlugin(), FastAPIPlugin())
    assert "prd.md" in result


def test_render_contains_snippets() -> None:
    cfg = _config()
    result = render_claude_md(cfg, ReactPlugin(), FastAPIPlugin())
    # snippets injected from plugins
    assert "frontend/src/" in result or "src/" in result
    assert "health" in result.lower()
