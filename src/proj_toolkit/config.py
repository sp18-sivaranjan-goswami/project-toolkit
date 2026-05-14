"""ProjectConfig dataclass and framework registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Type

if TYPE_CHECKING:
    from proj_toolkit.frameworks.base import FrameworkPlugin


class Language(str, Enum):
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    PYTHON = "python"


class FrontendFramework(str, Enum):
    REACT = "react"


class BackendFramework(str, Enum):
    DJANGO = "django"
    FASTAPI = "fastapi"
    NODE = "node"


@dataclass
class RetrofitConfig:
    project_name: str
    doc_paths: List[Path] = field(default_factory=list)
    model: str = "claude-sonnet-4-6"


@dataclass
class ProjectConfig:
    project_name: str
    prd_path: str
    frontend_framework: FrontendFramework
    frontend_language: Language
    backend_framework: BackendFramework
    backend_language: Language


# Registry: framework name -> plugin class
_frontend_registry: Dict[str, Type["FrameworkPlugin"]] = {}
_backend_registry: Dict[str, Type["FrameworkPlugin"]] = {}


def register_frontend(cls: Type["FrameworkPlugin"]) -> Type["FrameworkPlugin"]:
    _frontend_registry[cls.name] = cls
    return cls


def register_backend(cls: Type["FrameworkPlugin"]) -> Type["FrameworkPlugin"]:
    _backend_registry[cls.name] = cls
    return cls


def get_frontend_plugin(name: str) -> "FrameworkPlugin":
    if name not in _frontend_registry:
        raise KeyError(f"Unknown frontend framework: {name!r}")
    return _frontend_registry[name]()


def get_backend_plugin(name: str) -> "FrameworkPlugin":
    if name not in _backend_registry:
        raise KeyError(f"Unknown backend framework: {name!r}")
    return _backend_registry[name]()
