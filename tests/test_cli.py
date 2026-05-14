"""CLI integration tests using typer's test client."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from proj_toolkit.cli import app
from proj_toolkit.config import (
    BackendFramework,
    FrontendFramework,
    Language,
    ProjectConfig,
)

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scaffold" in result.output.lower() or "monorepo" in result.output.lower()


def test_non_empty_directory_enters_retrofit_mode(tmp_path: Path) -> None:
    """Non-empty directory should route to retrofit mode, not exit with an error."""
    (tmp_path / "existing.txt").touch()
    with patch("proj_toolkit.cli._run_retrofit") as mock_retrofit:
        result = runner.invoke(app, [str(tmp_path)])
    assert result.exit_code == 0
    mock_retrofit.assert_called_once()


def test_scaffold_called_on_confirm(tmp_path: Path, prd_file: Path) -> None:
    """scaffold() is called for an empty target directory."""
    # prd_file lives in tmp_path; use a separate empty subdir as the scaffold target
    target = tmp_path / "new_project"
    target.mkdir()

    config = ProjectConfig(
        project_name="cli-test",
        prd_path=str(prd_file),
        frontend_framework=FrontendFramework.REACT,
        frontend_language=Language.TYPESCRIPT,
        backend_framework=BackendFramework.FASTAPI,
        backend_language=Language.PYTHON,
    )

    with patch("proj_toolkit.cli.collect_config", return_value=config) as mock_collect, \
         patch("proj_toolkit.cli.scaffold") as mock_scaffold:
        result = runner.invoke(app, [str(target)])

    assert result.exit_code == 0
    mock_collect.assert_called_once()
    mock_scaffold.assert_called_once_with(config, target)
