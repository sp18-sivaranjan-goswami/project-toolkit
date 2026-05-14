"""Integration tests for the scaffolder."""

from __future__ import annotations

from pathlib import Path

import pytest

from proj_toolkit.config import (
    BackendFramework,
    FrontendFramework,
    Language,
    ProjectConfig,
)
from proj_toolkit.scaffolder import scaffold


def _make_config(
    fe: FrontendFramework,
    fe_lang: Language,
    be: BackendFramework,
    be_lang: Language,
    prd_file: Path,
) -> ProjectConfig:
    return ProjectConfig(
        project_name="test-project",
        prd_path=str(prd_file),
        frontend_framework=fe,
        frontend_language=fe_lang,
        backend_framework=be,
        backend_language=be_lang,
    )


@pytest.mark.parametrize(
    "fe,fe_lang,be,be_lang",
    [
        (FrontendFramework.REACT, Language.TYPESCRIPT, BackendFramework.FASTAPI, Language.PYTHON),
        (FrontendFramework.REACT, Language.JAVASCRIPT, BackendFramework.DJANGO, Language.PYTHON),
        (FrontendFramework.REACT, Language.TYPESCRIPT, BackendFramework.NODE, Language.TYPESCRIPT),
        (FrontendFramework.REACT, Language.JAVASCRIPT, BackendFramework.NODE, Language.JAVASCRIPT),
    ],
)
def test_scaffold_creates_structure(
    tmp_path: Path,
    prd_file: Path,
    fe: FrontendFramework,
    fe_lang: Language,
    be: BackendFramework,
    be_lang: Language,
) -> None:
    config = _make_config(fe, fe_lang, be, be_lang, prd_file)
    scaffold(config, tmp_path)

    assert (tmp_path / "frontend").is_dir()
    assert (tmp_path / "backend").is_dir()
    assert (tmp_path / "claude").is_dir()
    assert (tmp_path / "CLAUDE.md").is_file()


def test_claude_dir_contents(tmp_path: Path, prd_file: Path) -> None:
    config = _make_config(
        FrontendFramework.REACT,
        Language.TYPESCRIPT,
        BackendFramework.FASTAPI,
        Language.PYTHON,
        prd_file,
    )
    scaffold(config, tmp_path)

    claude = tmp_path / "claude"
    assert (claude / "prd.md").is_file()
    assert (claude / "context.md").is_file()
    assert (claude / "AGENTS.md").is_file()
    assert (claude / "tasks" / ".gitkeep").is_file()
    assert (claude / "decisions" / ".gitkeep").is_file()


def test_prd_copied_verbatim(tmp_path: Path, prd_file: Path) -> None:
    config = _make_config(
        FrontendFramework.REACT,
        Language.TYPESCRIPT,
        BackendFramework.FASTAPI,
        Language.PYTHON,
        prd_file,
    )
    scaffold(config, tmp_path)
    original = prd_file.read_text()
    copied = (tmp_path / "claude" / "prd.md").read_text()
    assert original == copied


def test_claude_md_contains_framework_names(tmp_path: Path, prd_file: Path) -> None:
    config = _make_config(
        FrontendFramework.REACT,
        Language.TYPESCRIPT,
        BackendFramework.FASTAPI,
        Language.PYTHON,
        prd_file,
    )
    scaffold(config, tmp_path)
    claude_md = (tmp_path / "CLAUDE.md").read_text()
    assert "react" in claude_md.lower()
    assert "fastapi" in claude_md.lower()
    assert "typescript" in claude_md.lower()
