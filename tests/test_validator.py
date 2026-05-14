"""Tests for validator module."""

from __future__ import annotations

from pathlib import Path

import pytest

from proj_toolkit.validator import ValidationError, validate_empty_directory, validate_prd_path


class TestValidateEmptyDirectory:
    def test_empty_dir_passes(self, tmp_path: Path) -> None:
        validate_empty_directory(tmp_path)  # should not raise

    def test_non_empty_dir_raises(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").touch()
        with pytest.raises(ValidationError, match="not empty"):
            validate_empty_directory(tmp_path)

    def test_git_dir_ignored(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        validate_empty_directory(tmp_path)  # .git is ignored

    def test_ds_store_ignored(self, tmp_path: Path) -> None:
        (tmp_path / ".DS_Store").touch()
        validate_empty_directory(tmp_path)  # .DS_Store is ignored

    def test_not_a_directory_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "file.txt"
        f.touch()
        with pytest.raises(ValidationError, match="not a directory"):
            validate_empty_directory(f)


class TestValidatePrdPath:
    def test_valid_file_returns_path(self, prd_file: Path) -> None:
        result = validate_prd_path(str(prd_file))
        assert result == prd_file.resolve()

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="not found"):
            validate_prd_path(str(tmp_path / "missing.md"))

    def test_directory_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="not a file"):
            validate_prd_path(str(tmp_path))

    def test_tilde_expansion(self, tmp_path: Path, monkeypatch) -> None:
        prd = tmp_path / "prd.md"
        prd.write_text("# PRD")
        monkeypatch.setenv("HOME", str(tmp_path))
        result = validate_prd_path("~/prd.md")
        assert result.exists()
