"""Validation helpers for directory emptiness and PRD path."""

from __future__ import annotations

import os
from pathlib import Path


class ValidationError(Exception):
    pass


def is_directory_empty(path: Path) -> bool:
    """Return True if *path* is an existing directory with no relevant contents."""
    if not path.is_dir():
        return False
    contents = [
        entry
        for entry in path.iterdir()
        if entry.name not in {".git", ".DS_Store"}
    ]
    return len(contents) == 0


def validate_empty_directory(path: Path) -> None:
    """Raise ValidationError if *path* is not an empty directory."""
    if not path.is_dir():
        raise ValidationError(f"{path} is not a directory")
    contents = [
        entry
        for entry in path.iterdir()
        if entry.name not in {".git", ".DS_Store"}
    ]
    if contents:
        raise ValidationError(
            f"Directory {path} is not empty. "
            "proj-toolkit must be run in an empty directory."
        )


def validate_prd_path(prd_path: str) -> Path:
    """Return resolved Path for the PRD file, or raise ValidationError."""
    p = Path(prd_path).expanduser().resolve()
    if not p.exists():
        raise ValidationError(f"PRD file not found: {p}")
    if not p.is_file():
        raise ValidationError(f"PRD path is not a file: {p}")
    if not os.access(p, os.R_OK):
        raise ValidationError(f"PRD file is not readable: {p}")
    return p
