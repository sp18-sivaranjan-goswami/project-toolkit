"""Abstract base classes for framework plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from proj_toolkit.config import Language


@dataclass
class FileSpec:
    """Represents a single file to be generated."""

    relative_path: str  # relative to /frontend or /backend
    content: str


class FrameworkPlugin(ABC):
    """Base class for all framework plugins."""

    name: str
    supported_languages: List[Language]

    @abstractmethod
    def generate_files(self, language: Language, project_name: str) -> List[FileSpec]:
        """Return list of FileSpec objects to be written."""
        ...

    @abstractmethod
    def readme_snippet(self, language: Language) -> str:
        """Return a Markdown snippet injected into CLAUDE.md."""
        ...

    @abstractmethod
    def dockerfile_content(self, language: Language, project_name: str) -> str:
        """Return the content of the Dockerfile for this framework."""
        ...
