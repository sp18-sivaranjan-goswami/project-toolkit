"""CLAUDE.md rendering via Jinja2."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from proj_toolkit.config import ProjectConfig
from proj_toolkit.frameworks.base import FrameworkPlugin

# Resolve templates/ directory relative to this package
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def render_claude_md(
    config: ProjectConfig,
    frontend_plugin: FrameworkPlugin,
    backend_plugin: FrameworkPlugin,
) -> str:
    """Render CLAUDE.md content from the Jinja2 template."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
    )
    template = env.get_template("claude_md.jinja2")
    return template.render(
        project_name=config.project_name,
        frontend_framework=config.frontend_framework.value,
        frontend_language=config.frontend_language.value,
        backend_framework=config.backend_framework.value,
        backend_language=config.backend_language.value,
        frontend_snippet=frontend_plugin.readme_snippet(config.frontend_language),
        backend_snippet=backend_plugin.readme_snippet(config.backend_language),
    )
