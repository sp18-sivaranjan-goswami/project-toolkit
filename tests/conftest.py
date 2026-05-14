"""Shared pytest fixtures."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def empty_dir(tmp_path: Path) -> Path:
    """Return a fresh empty temporary directory."""
    return tmp_path


@pytest.fixture
def prd_file(tmp_path: Path) -> Path:
    """Return a temporary PRD markdown file."""
    prd = tmp_path / "prd.md"
    prd.write_text(
        textwrap.dedent("""\
            # PRD: Test Project

            ## Overview
            A test project for scaffolding.
        """),
        encoding="utf-8",
    )
    return prd
